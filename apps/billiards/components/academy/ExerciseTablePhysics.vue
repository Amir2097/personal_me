<script setup lang="ts">
import type { Ball, Exercise, Point2D } from '~/types/academy'
import {
  createSimState,
  directionBetween,
  isSimulationIdle,
  stepSimulation,
  strikeCueBall,
  type PhysBall,
  type SimState
} from '~/utils/billiardPhysics'

const props = defineProps<{
  exercise: Exercise
}>()

const emit = defineEmits<{
  (e: 'targetPocketed'): void
  (e: 'simulationEnd', payload: { pocketedTarget: boolean }): void
}>()

const svgRef = ref<SVGSVGElement | null>(null)
const sim = ref<SimState | null>(null)
const phase = ref<'idle' | 'aiming' | 'running'>('idle')
const aimPoint = ref<Point2D | null>(null)
const lastAimVector = ref<{ dx: number; dy: number; power: number } | null>(null)
const cueStickProgress = ref(0)
const pocketedTarget = ref(false)

const ballRadius = 1.6
const pockets = [
  { x: 0, y: 0 },
  { x: 50, y: 0 },
  { x: 100, y: 0 },
  { x: 0, y: 50 },
  { x: 50, y: 50 },
  { x: 100, y: 50 }
]

let rafId = 0
let lastTs = 0
let cueAnimId = 0

const cueBallSeed = computed(() => props.exercise.balls.find((ball) => ball.type === 'cue') || null)
const targetBallSeed = computed(() => props.exercise.balls.find((ball) => ball.type === 'target') || null)

const visibleTrajectories = computed(() => phase.value === 'idle' || phase.value === 'aiming')

const ballFill = (ball: Ball | PhysBall) => (ball.type === 'cue' ? '#f8fafc' : '#f43f5e')

const resetSim = () => {
  cancelAnimationFrame(rafId)
  cancelAnimationFrame(cueAnimId)
  rafId = 0
  lastTs = 0
  cueStickProgress.value = 0
  pocketedTarget.value = false
  aimPoint.value = null
  lastAimVector.value = null
  phase.value = 'idle'
  sim.value = createSimState(
    props.exercise.balls.map((ball) => ({
      id: ball.id,
      type: ball.type,
      label: ball.label,
      x: ball.x,
      y: ball.y
    }))
  )
}

watch(
  () => props.exercise.id,
  () => resetSim(),
  { immediate: true }
)

onBeforeUnmount(() => {
  cancelAnimationFrame(rafId)
  cancelAnimationFrame(cueAnimId)
})

const mapClientToSvg = (clientX: number, clientY: number): Point2D | null => {
  const svg = svgRef.value
  if (!svg) return null
  try {
    const pt = svg.createSVGPoint()
    pt.x = clientX
    pt.y = clientY
    const ctm = svg.getScreenCTM()
    if (!ctm) return null
    const res = pt.matrixTransform(ctm.inverse())
    return {
      x: Math.max(0, Math.min(100, res.x)),
      y: Math.max(0, Math.min(50, res.y))
    }
  } catch {
    return null
  }
}

const clampSpeed = (dragLen: number) => Math.min(58, Math.max(26, dragLen * 2.4))

const runPhysicsLoop = (ts: number) => {
  if (!sim.value) return
  if (!lastTs) lastTs = ts
  const dt = Math.min(0.032, (ts - lastTs) / 1000)
  lastTs = ts

  let next = sim.value
  const substeps = 3
  for (let i = 0; i < substeps; i += 1) {
    next = stepSimulation(next, dt / substeps)
  }
  sim.value = next

  const target = next.balls.find((ball) => ball.type === 'target')
  if (target && !target.active && !pocketedTarget.value) {
    pocketedTarget.value = true
    emit('targetPocketed')
  }

  if (isSimulationIdle(next)) {
    phase.value = 'idle'
    lastTs = 0
    emit('simulationEnd', { pocketedTarget: pocketedTarget.value })
    return
  }

  rafId = requestAnimationFrame(runPhysicsLoop)
}

const playCueStrikeAnim = (onHit: () => void) => {
  cancelAnimationFrame(cueAnimId)
  cueStickProgress.value = 0
  const start = performance.now()
  const duration = 180

  const tick = (now: number) => {
    const t = Math.min(1, (now - start) / duration)
    cueStickProgress.value = t < 0.65 ? t / 0.65 : 1 - (t - 0.65) / 0.35
    if (t < 1) {
      cueAnimId = requestAnimationFrame(tick)
    } else {
      cueStickProgress.value = 0
      onHit()
    }
  }

  cueAnimId = requestAnimationFrame(tick)
}

const fireStrike = (direction: Point2D, speed: number) => {
  if (!sim.value || !cueBallSeed.value || phase.value === 'running') return
  const cueId = cueBallSeed.value.id
  const dirLen = Math.hypot(direction.x, direction.y)
  if (dirLen < 1e-6) return
  lastAimVector.value = {
    dx: direction.x / dirLen,
    dy: direction.y / dirLen,
    power: speed
  }
  phase.value = 'running'
  aimPoint.value = null
  pocketedTarget.value = false
  lastTs = 0

  playCueStrikeAnim(() => {
    if (!sim.value) return
    strikeCueBall(sim.value, cueId, direction, speed)
    cancelAnimationFrame(rafId)
    rafId = requestAnimationFrame(runPhysicsLoop)
  })
}

const onPointerDown = (ev: PointerEvent) => {
  if (phase.value !== 'idle' || !cueBallSeed.value || !sim.value) return
  const cue = sim.value.balls.find((ball) => ball.id === cueBallSeed.value!.id)
  if (!cue?.active) return
  const point = mapClientToSvg(ev.clientX, ev.clientY)
  if (!point) return
  const dist = Math.hypot(point.x - cue.x, point.y - cue.y)
  if (dist > ballRadius * 3.5) return
  phase.value = 'aiming'
  aimPoint.value = point
  ;(ev.currentTarget as Element)?.setPointerCapture?.(ev.pointerId)
}

const onPointerMove = (ev: PointerEvent) => {
  if (phase.value !== 'aiming') return
  const point = mapClientToSvg(ev.clientX, ev.clientY)
  if (point) aimPoint.value = point
}

const onPointerUp = (ev: PointerEvent) => {
  if (phase.value !== 'aiming' || !sim.value || !cueBallSeed.value) return
  const cue = sim.value.balls.find((ball) => ball.id === cueBallSeed.value!.id)
  const point = mapClientToSvg(ev.clientX, ev.clientY)
  if (!cue || !point) {
    phase.value = 'idle'
    aimPoint.value = null
    return
  }

  const dir = directionBetween({ x: cue.x, y: cue.y }, point)
  const dragLen = Math.hypot(dir.x, dir.y)
  if (dragLen < 2.5) {
    phase.value = 'idle'
    aimPoint.value = null
    return
  }

  fireStrike(dir, clampSpeed(dragLen))
  ;(ev.currentTarget as Element)?.releasePointerCapture?.(ev.pointerId)
}

const idealStrike = () => {
  if (!cueBallSeed.value || !targetBallSeed.value || phase.value === 'running') return
  const dir = directionBetween(cueBallSeed.value, targetBallSeed.value)
  fireStrike(dir, 44)
}

const aimVector = computed(() => {
  if (!sim.value || !aimPoint.value || phase.value !== 'aiming') return null
  const cue = sim.value.balls.find((ball) => ball.type === 'cue')
  if (!cue) return null
  const dir = directionBetween({ x: cue.x, y: cue.y }, aimPoint.value)
  const len = Math.hypot(dir.x, dir.y)
  if (len < 1e-6) return null
  return {
    cx: cue.x,
    cy: cue.y,
    dx: dir.x / len,
    dy: dir.y / len,
    power: clampSpeed(len)
  }
})

const cueStickLine = computed(() => {
  if (!sim.value) return null
  const cue = sim.value.balls.find((ball) => ball.type === 'cue' && ball.active)
  if (!cue) return null

  const vec = phase.value === 'aiming' ? aimVector.value : lastAimVector.value
  if (!vec) return null

  if (phase.value === 'aiming' && aimVector.value) {
    const stickLen = 8 + aimVector.value.power * 0.22
    return {
      x1: cue.x - aimVector.value.dx * stickLen,
      y1: cue.y - aimVector.value.dy * stickLen,
      x2: cue.x - aimVector.value.dx * (stickLen * 0.25),
      y2: cue.y - aimVector.value.dy * (stickLen * 0.25),
      opacity: 0.95
    }
  }

  if (cueStickProgress.value > 0 && lastAimVector.value) {
    const pull = 7 * cueStickProgress.value
    return {
      x1: cue.x - lastAimVector.value.dx * (10 + pull),
      y1: cue.y - lastAimVector.value.dy * (10 + pull),
      x2: cue.x - lastAimVector.value.dx * 2.2,
      y2: cue.y - lastAimVector.value.dy * 2.2,
      opacity: 0.85
    }
  }

  return null
})
</script>

<template>
  <div class="card-surface p-4">
    <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
      <p class="text-xs uppercase tracking-[0.18em] text-cloth-accent">Физика · прототип</p>
      <div class="flex flex-wrap gap-2">
        <button type="button" class="btn-ghost text-xs" :disabled="phase === 'running'" @click="idealStrike">
          Идеальный удар
        </button>
        <button type="button" class="btn-ghost text-xs" :disabled="phase === 'running'" @click="resetSim">
          Сброс
        </button>
      </div>
    </div>

    <svg
      ref="svgRef"
      viewBox="0 0 100 50"
      class="w-full touch-none rounded-xl border border-white/10 bg-[#0e3026]"
      preserveAspectRatio="xMidYMid meet"
      :class="phase === 'aiming' ? 'cursor-crosshair' : phase === 'idle' ? 'cursor-pointer' : 'cursor-default'"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
    >
      <defs>
        <radialGradient id="clothGradientPhysics" cx="50%" cy="45%" r="65%">
          <stop offset="0%" stop-color="#1e6b58" />
          <stop offset="100%" stop-color="#0f3e32" />
        </radialGradient>
      </defs>

      <rect x="0" y="0" width="100" height="50" rx="2" fill="url(#clothGradientPhysics)" />

      <line x1="20" y1="0" x2="20" y2="50" stroke="#d1fae5" stroke-opacity="0.3" stroke-width="0.35" />
      <circle cx="75" cy="25" r="0.75" fill="#d1fae5" fill-opacity="0.6" />

      <g>
        <circle
          v-for="pocket in pockets"
          :key="`p-${pocket.x}-${pocket.y}`"
          :cx="pocket.x"
          :cy="pocket.y"
          r="2.3"
          fill="#0b1210"
        />
      </g>

      <g v-if="visibleTrajectories">
        <line
          v-for="(traj, idx) in exercise.trajectories"
          :key="`t-${idx}`"
          :x1="traj.from.x"
          :y1="traj.from.y"
          :x2="traj.to.x"
          :y2="traj.to.y"
          :stroke="traj.color"
          stroke-width="0.55"
          :stroke-dasharray="traj.style === 'dashed' ? '1.8 1.5' : undefined"
          stroke-linecap="round"
          opacity="0.55"
        />
      </g>

      <g v-if="aimVector && phase === 'aiming'">
        <line
          :x1="aimVector.cx"
          :y1="aimVector.cy"
          :x2="aimVector.cx + aimVector.dx * (4 + aimVector.power * 0.35)"
          :y2="aimVector.cy + aimVector.dy * (4 + aimVector.power * 0.35)"
          stroke="#fef08a"
          stroke-width="0.45"
          stroke-linecap="round"
          opacity="0.9"
        />
      </g>

      <line
        v-if="cueStickLine"
        :x1="cueStickLine.x1"
        :y1="cueStickLine.y1"
        :x2="cueStickLine.x2"
        :y2="cueStickLine.y2"
        stroke="#fde68a"
        stroke-width="0.55"
        stroke-linecap="round"
        :opacity="cueStickLine.opacity"
      />

      <g v-if="sim">
        <g v-for="ball in sim.balls.filter((item) => item.active)" :key="ball.id">
          <circle
            :cx="ball.x"
            :cy="ball.y"
            :r="ballRadius"
            :fill="ballFill(ball)"
            stroke="#ffffff"
            stroke-opacity="0.5"
            stroke-width="0.2"
          />
          <circle :cx="ball.x - 0.45" :cy="ball.y - 0.45" r="0.35" fill="#fff" opacity="0.55" />
          <text
            :x="ball.x"
            :y="ball.y + 0.45"
            text-anchor="middle"
            font-size="1.5"
            font-weight="700"
            :fill="ball.type === 'cue' ? '#111827' : '#fff'"
          >
            {{ ball.label }}
          </text>
        </g>
      </g>
    </svg>

    <p class="mt-3 text-xs text-cloth-muted">
      Потяните от битка в сторону удара (как кием). Длина жеста — сила. Или нажмите «Идеальный удар» для эталонной траектории.
    </p>
    <p v-if="pocketedTarget" class="mt-1 text-xs font-semibold text-emerald-300">Чужой шар в лузе.</p>

    <div class="mt-4 grid gap-4 md:grid-cols-[auto_1fr] md:items-center">
      <div class="panel-surface p-3">
        <p class="text-xs uppercase tracking-[0.18em] text-cloth-muted">Точка удара</p>
        <svg viewBox="0 0 100 100" class="mt-2 h-28 w-28">
          <circle cx="50" cy="50" r="45" fill="#e2e8f0" stroke="#94a3b8" stroke-width="2" />
          <line x1="50" y1="8" x2="50" y2="92" stroke="#64748b" stroke-width="1.2" stroke-dasharray="2 2" />
          <line x1="8" y1="50" x2="92" y2="50" stroke="#64748b" stroke-width="1.2" stroke-dasharray="2 2" />
          <circle
            :cx="50 + exercise.cue_hit_point.offset_x * 14"
            :cy="50 + exercise.cue_hit_point.offset_y * 14"
            r="5.4"
            fill="#ef4444"
          />
        </svg>
      </div>
      <div class="text-sm text-cloth-chalk/80">
        <p>{{ exercise.cue_hit_point.hint }}</p>
        <ul class="mt-3 space-y-1 text-xs text-cloth-muted">
          <li><span class="inline-block h-0.5 w-4 align-middle bg-white" /> белая — ход / прицел битка</li>
          <li><span class="inline-block h-0.5 w-4 align-middle bg-[#facc15]" /> жёлтая — путь чужого</li>
        </ul>
      </div>
    </div>
  </div>
</template>
