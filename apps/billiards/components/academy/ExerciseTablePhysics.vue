<script setup lang="ts">
import type { Ball, Exercise } from '~/types/academy'
import {
  createSimState,
  DEMO_TABLE,
  directionBetween,
  isSimulationIdle,
  stepSimulation,
  strikeCueBall,
  type PhysBall,
  type SimState
} from '~/utils/billiardPhysics'
import { idealAimPoint, idealStrikeSpeed } from '~/utils/physicsAim'

const props = defineProps<{
  exercise: Exercise
}>()

const sim = ref<SimState | null>(null)
const phase = ref<'idle' | 'running'>('idle')
const lastAimVector = ref<{ dx: number; dy: number } | null>(null)
const cueStickProgress = ref(0)

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
let holdUntilTs = 0
const HOLD_AFTER_MS = 1100
/** Playback slower than realtime so the object ball rolls in calmly. */
const DEMO_TIME_SCALE = 0.48

const cancelRaf = (id: number) => {
  if (!import.meta.client || !id) return
  cancelAnimationFrame(id)
}

const cueBallSeed = computed(() => props.exercise.balls.find((ball) => ball.type === 'cue') || null)
const aimPoint = computed(() => idealAimPoint(props.exercise))
const ghost = computed(() => props.exercise.ghost_ball || null)
const showReplayButton = computed(() => phase.value === 'idle')
const visibleTrajectories = computed(() => phase.value === 'idle')
const pocketedBalls = computed(() => sim.value?.balls.filter((ball) => !ball.active) || [])

const ballFill = (ball: Ball | PhysBall) => (ball.type === 'cue' ? '#f8fafc' : '#f43f5e')

const resetSim = () => {
  cancelRaf(rafId)
  cancelRaf(cueAnimId)
  rafId = 0
  lastTs = 0
  holdUntilTs = 0
  cueStickProgress.value = 0
  lastAimVector.value = null
  phase.value = 'idle'
  sim.value = createSimState(
    props.exercise.balls.map((ball) => ({
      id: ball.id,
      type: ball.type,
      label: ball.label,
      x: ball.x,
      y: ball.y
    })),
    DEMO_TABLE
  )
}

watch(
  () => props.exercise.id,
  () => resetSim(),
  { immediate: true }
)

onBeforeUnmount(() => {
  cancelRaf(rafId)
  cancelRaf(cueAnimId)
})

const runPhysicsLoop = (ts: number) => {
  if (!sim.value) return

  if (holdUntilTs > 0) {
    if (ts >= holdUntilTs) {
      holdUntilTs = 0
      resetSim()
      return
    }
    rafId = requestAnimationFrame(runPhysicsLoop)
    return
  }

  if (!lastTs) lastTs = ts
  const dt = Math.min(0.032, (ts - lastTs) / 1000) * DEMO_TIME_SCALE
  lastTs = ts

  let next = sim.value
  const substeps = 4
  for (let i = 0; i < substeps; i += 1) {
    next = stepSimulation(next, dt / substeps, DEMO_TABLE)
  }
  sim.value = next

  if (isSimulationIdle(next, DEMO_TABLE)) {
    lastTs = 0
    // Keep the final frame (incl. pocketed balls) visible, then restore diagram.
    holdUntilTs = ts + HOLD_AFTER_MS
    rafId = requestAnimationFrame(runPhysicsLoop)
    return
  }

  rafId = requestAnimationFrame(runPhysicsLoop)
}

const playCueStrikeAnim = (onHit: () => void) => {
  if (!import.meta.client) return
  cancelRaf(cueAnimId)
  cueStickProgress.value = 0
  const start = performance.now()
  const duration = 280

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

const playExerciseAnimation = () => {
  if (!import.meta.client) return
  if (!sim.value || !cueBallSeed.value || !aimPoint.value || phase.value === 'running') return

  const cueId = cueBallSeed.value.id
  const direction = directionBetween(cueBallSeed.value, aimPoint.value)
  const dirLen = Math.hypot(direction.x, direction.y)
  if (dirLen < 1e-6) return

  lastAimVector.value = {
    dx: direction.x / dirLen,
    dy: direction.y / dirLen
  }
  phase.value = 'running'
  lastTs = 0

  const speed = idealStrikeSpeed(props.exercise)
  playCueStrikeAnim(() => {
    if (!sim.value) return
    strikeCueBall(sim.value, cueId, direction, speed)
    cancelRaf(rafId)
    rafId = requestAnimationFrame(runPhysicsLoop)
  })
}

const cueStickLine = computed(() => {
  if (!sim.value || cueStickProgress.value <= 0 || !lastAimVector.value) return null
  const cue = sim.value.balls.find((ball) => ball.type === 'cue' && ball.active)
  if (!cue) return null

  const pull = 7 * cueStickProgress.value
  return {
    x1: cue.x - lastAimVector.value.dx * (10 + pull),
    y1: cue.y - lastAimVector.value.dy * (10 + pull),
    x2: cue.x - lastAimVector.value.dx * 2.2,
    y2: cue.y - lastAimVector.value.dy * 2.2
  }
})
</script>

<template>
  <div class="card-surface p-4">
    <div class="relative overflow-hidden rounded-xl">
      <svg
        viewBox="0 0 100 50"
        class="w-full rounded-xl border border-white/10 bg-[#0e3026]"
        preserveAspectRatio="xMidYMid meet"
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

        <DiagramAnnotations
          v-if="visibleTrajectories && exercise.annotations?.length"
          :annotations="exercise.annotations"
        />

        <g v-if="visibleTrajectories && ghost">
          <circle
            :cx="ghost.x"
            :cy="ghost.y"
            :r="ballRadius"
            fill="#f8fafc"
            fill-opacity="0.35"
            stroke="#f8fafc"
            stroke-opacity="0.95"
            stroke-width="0.35"
            stroke-dasharray="1.1 0.8"
          />
          <text
            :x="ghost.x"
            :y="ghost.y + 0.5"
            text-anchor="middle"
            font-size="1.5"
            font-weight="700"
            fill="#f8fafc"
            fill-opacity="0.9"
          >
            {{ ghost.label || 'Ф' }}
          </text>
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
          opacity="0.85"
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
          <!-- Keep pocketed balls visible in the pocket until the hold ends. -->
          <g v-for="ball in pocketedBalls" :key="`pocketed-${ball.id}`">
            <circle
              :cx="ball.x"
              :cy="ball.y"
              :r="ballRadius * 0.72"
              :fill="ballFill(ball)"
              opacity="0.75"
            />
          </g>
        </g>
      </svg>

      <button
        v-if="showReplayButton"
        type="button"
        class="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/25 bg-black/35 px-4 py-2 text-sm font-semibold text-white/90 shadow-lg backdrop-blur-sm transition hover:border-white/40 hover:bg-black/45 hover:text-white"
        @click="playExerciseAnimation"
      >
        Анимация упражнения
      </button>
    </div>

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
        <p class="mt-2 text-xs text-cloth-muted">
          Нажмите «Анимация упражнения», чтобы посмотреть эталонный удар. Результат тренировки отмечайте вручную справа.
        </p>
        <p v-if="ghost" class="mt-2 text-xs text-cloth-muted">
          Фантом ({{ ghost.label || 'Ф' }}) — точка контакта при резке.
        </p>
        <ul class="mt-3 space-y-1 text-xs text-cloth-muted">
          <li><span class="inline-block h-0.5 w-4 align-middle bg-white" /> белая — ход / прицел битка</li>
          <li><span class="inline-block h-0.5 w-4 align-middle bg-[#facc15]" /> жёлтая — путь чужого</li>
          <li><span class="inline-block h-0.5 w-4 align-middle bg-[#38bdf8]" /> синяя — путь битка после удара</li>
          <li v-if="exercise.annotations?.length">
            <span class="inline-block h-0.5 w-4 align-middle bg-[#fde68a]" /> жёлтая пунктирная — размер / зазор до борта
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
