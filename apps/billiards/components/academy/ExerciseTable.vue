<script setup lang="ts">
import type { Ball, Exercise, Point2D } from '~/types/academy'

const props = defineProps<{
  exercise: Exercise
  /**
   * Actual cue-ball stop point selected by trainee (for auto-check).
   * Same coordinate system as SVG: x in [0..100], y in [0..50].
   */
  cueStopPoint?: Point2D | null
  interactiveCueStop?: boolean
}>()

const emit = defineEmits<{
  (e: 'cueStopSelected', point: Point2D): void
}>()

const svgRef = ref<SVGSVGElement | null>(null)

const pockets = [
  { x: 0, y: 0 },
  { x: 50, y: 0 },
  { x: 100, y: 0 },
  { x: 0, y: 50 },
  { x: 50, y: 50 },
  { x: 100, y: 50 }
]

/** Same SVG radius for cue, target and ghost balls. */
const ballRadius = 1.6

const cueIndicatorX = computed(() => 50 + props.exercise.cue_hit_point.offset_x * 14)
const cueIndicatorY = computed(() => 50 + props.exercise.cue_hit_point.offset_y * 14)

const ghost = computed(() => props.exercise.ghost_ball || null)
const expectedCueStop = computed(() => props.exercise.expected_cue_stop || null)

const ballFill = (ball: Ball) => {
  if (ball.type === 'cue') return '#f8fafc'
  return '#f43f5e'
}

const mapClientToSvg = (clientX: number, clientY: number): Point2D | null => {
  const svg = svgRef.value
  if (!svg) return null
  try {
    const pt = svg.createSVGPoint()
    pt.x = clientX
    pt.y = clientY
    const ctm = svg.getScreenCTM()
    if (!ctm) return null
    const inv = ctm.inverse()
    const res = pt.matrixTransform(inv)
    return {
      x: Math.max(0, Math.min(100, res.x)),
      y: Math.max(0, Math.min(50, res.y))
    }
  } catch {
    return null
  }
}

const onSvgClick = (ev: MouseEvent) => {
  if (!props.interactiveCueStop) return
  if (ev.button !== 0) return
  const point = mapClientToSvg(ev.clientX, ev.clientY)
  if (!point) return
  emit('cueStopSelected', point)
}
</script>

<template>
  <div class="card-surface p-4">
    <svg
      ref="svgRef"
      viewBox="0 0 100 50"
      class="w-full rounded-xl border border-white/10 bg-[#0e3026]"
      preserveAspectRatio="xMidYMid meet"
      :class="interactiveCueStop ? 'cursor-crosshair' : undefined"
      @click="onSvgClick"
    >
      <defs>
        <radialGradient id="clothGradient" cx="50%" cy="45%" r="65%">
          <stop offset="0%" stop-color="#1e6b58" />
          <stop offset="100%" stop-color="#0f3e32" />
        </radialGradient>
      </defs>

      <rect x="0" y="0" width="100" height="50" rx="2" fill="url(#clothGradient)" />

      <!-- Home line + pyramid spot -->
      <line x1="20" y1="0" x2="20" y2="50" stroke="#d1fae5" stroke-opacity="0.3" stroke-width="0.35" />
      <circle cx="75" cy="25" r="0.75" fill="#d1fae5" fill-opacity="0.6" />

      <!-- Pockets -->
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

      <!-- Trajectories -->
      <g>
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
          opacity="0.95"
        />
      </g>

      <!-- Expected cue stop point -->
      <g v-if="expectedCueStop">
        <circle
          :cx="expectedCueStop.x"
          :cy="expectedCueStop.y"
          r="2.6"
          fill="none"
          stroke="#34d399"
          stroke-width="0.45"
          stroke-dasharray="1.6 1.4"
        />
      </g>

      <!-- Actual trainee cue stop point -->
      <g v-if="cueStopPoint">
        <circle :cx="cueStopPoint.x" :cy="cueStopPoint.y" r="2.1" fill="#ef4444" fill-opacity="0.9" />
        <circle :cx="cueStopPoint.x" :cy="cueStopPoint.y" r="3" fill="none" stroke="#ef4444" stroke-width="0.4" />
      </g>

      <!-- Ghost ball -->
      <g v-if="ghost">
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

      <!-- Real balls (no shadows) -->
      <g>
        <g v-for="ball in exercise.balls" :key="ball.id">
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

    <div class="mt-4 grid gap-4 md:grid-cols-[auto_1fr] md:items-center">
      <div class="panel-surface p-3">
        <p class="text-xs uppercase tracking-[0.18em] text-cloth-muted">Точка удара</p>
        <svg viewBox="0 0 100 100" class="mt-2 h-28 w-28">
          <circle cx="50" cy="50" r="45" fill="#e2e8f0" stroke="#94a3b8" stroke-width="2" />
          <line x1="50" y1="8" x2="50" y2="92" stroke="#64748b" stroke-width="1.2" stroke-dasharray="2 2" />
          <line x1="8" y1="50" x2="92" y2="50" stroke="#64748b" stroke-width="1.2" stroke-dasharray="2 2" />
          <circle :cx="cueIndicatorX" :cy="cueIndicatorY" r="5.4" fill="#ef4444" />
        </svg>
      </div>

      <div class="text-sm text-cloth-chalk/80">
        <p>{{ exercise.cue_hit_point.hint }}</p>
        <p v-if="ghost" class="mt-2 text-xs text-cloth-muted">
          Фантом ({{ ghost.label || 'Ф' }}) — точка контакта при резке (виден полупрозрачно).
        </p>
        <ul class="mt-3 space-y-1 text-xs text-cloth-muted">
          <li><span class="inline-block h-0.5 w-4 align-middle bg-white" /> белая — ход / прицел битка</li>
          <li><span class="inline-block h-0.5 w-4 align-middle bg-[#facc15]" /> жёлтая — путь чужого</li>
          <li><span class="inline-block h-0.5 w-4 align-middle bg-[#38bdf8]" /> синяя — путь битка после удара (свояк / выход)</li>
        </ul>
      </div>
    </div>
  </div>
</template>
