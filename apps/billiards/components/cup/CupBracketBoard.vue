<script setup lang="ts">
import type { CupFormat, CupMatch, CupPlayer } from '~/types/cup'
import {
  BRACKET_CARD_W,
  buildBracketLayout,
  columnHeaders
} from '~/utils/cupBracketLayout'
import { matchStatusLabel } from '~/utils/cupLabels'
import { matchRoutingHint } from '~/utils/cupPlacement'

const props = withDefaults(
  defineProps<{
    matches: CupMatch[]
    players: CupPlayer[]
    raceTo: number
    format: CupFormat
    interactive?: boolean
    focusMatchId?: string | null
  }>(),
  {
    interactive: true,
    focusMatchId: null
  }
)

const emit = defineEmits<{
  open: [matchId: string]
}>()

const viewport = ref<HTMLElement | null>(null)
const panX = ref(0)
const panY = ref(0)
const dragging = ref(false)
const moved = ref(false)
const origin = ref({ x: 0, y: 0, panX: 0, panY: 0 })

const layout = computed(() => buildBracketLayout(props.matches, props.format))
const headers = computed(() => columnHeaders(layout.value))
const playerMap = computed(() => new Map(props.players.map((player) => [player.id, player.name])))

const nameOf = (id: string | null) => {
  if (!id) return '×'
  return playerMap.value.get(id) || '—'
}

const routingOf = (match: CupMatch) => matchRoutingHint(match, props.matches)

const scoreClass = (match: CupMatch, side: 'A' | 'B') => {
  if (match.status !== 'done' || !match.winnerId) return ''
  const id = side === 'A' ? match.playerAId : match.playerBId
  return id === match.winnerId ? 'bracket-board__score--win' : 'bracket-board__score--lose'
}

const clampPan = (x: number, y: number) => {
  const el = viewport.value
  if (!el) return { x, y }
  const viewW = el.clientWidth
  const viewH = el.clientHeight
  const { width, height } = layout.value
  const minX = Math.min(0, viewW - width)
  const minY = Math.min(0, viewH - height)
  return {
    x: Math.min(0, Math.max(minX, x)),
    y: Math.min(0, Math.max(minY, y))
  }
}

const applyPan = (x: number, y: number) => {
  const next = clampPan(x, y)
  panX.value = next.x
  panY.value = next.y
}

const onPointerDown = (event: PointerEvent) => {
  moved.value = false
  if ((event.target as HTMLElement).closest('[data-match-card]')) return
  dragging.value = true
  origin.value = { x: event.clientX, y: event.clientY, panX: panX.value, panY: panY.value }
  viewport.value?.setPointerCapture(event.pointerId)
}

const onPointerMove = (event: PointerEvent) => {
  if (!dragging.value) return
  const dx = event.clientX - origin.value.x
  const dy = event.clientY - origin.value.y
  if (Math.abs(dx) + Math.abs(dy) > 4) moved.value = true
  applyPan(origin.value.panX + dx, origin.value.panY + dy)
}

const onPointerUp = (event: PointerEvent) => {
  if (!dragging.value) return
  dragging.value = false
  try {
    viewport.value?.releasePointerCapture(event.pointerId)
  } catch {
    /* ignore */
  }
}

const openMatch = (match: CupMatch, event: MouseEvent) => {
  if (!props.interactive) {
    event.preventDefault()
    return
  }
  if (moved.value) {
    event.preventDefault()
    event.stopPropagation()
    return
  }
  emit('open', match.id)
}

const resetView = () => applyPan(0, 0)

watch(
  () => [layout.value.width, layout.value.height],
  () => applyPan(panX.value, panY.value)
)

onMounted(() => {
  applyPan(0, 0)
  window.addEventListener('resize', resetView)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resetView)
})
</script>

<template>
  <div class="bracket-board">
    <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
      <p class="text-sm text-cloth-muted">
        <template v-if="interactive">
          Перетаскивайте поле курсором · клик по встрече открывает пульт · до {{ raceTo }} партий
        </template>
        <template v-else>
          Общая сетка турнира · до {{ raceTo }} партий · обновляется вместе со счётом
        </template>
      </p>
      <button type="button" class="btn-ghost text-xs" @click="resetView">В начало</button>
    </div>

    <div
      ref="viewport"
      class="bracket-board__viewport"
      :class="dragging ? 'bracket-board__viewport--dragging' : ''"
      @pointerdown="onPointerDown"
      @pointermove="onPointerMove"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
    >
      <div
        class="bracket-board__canvas"
        :style="{
          width: `${layout.width}px`,
          height: `${layout.height}px`,
          transform: `translate(${panX}px, ${panY}px)`
        }"
      >
        <svg class="bracket-board__lines" :width="layout.width" :height="layout.height" aria-hidden="true">
          <path
            v-for="line in layout.connectors"
            :key="line.id"
            :d="line.path"
            fill="none"
            :class="line.kind === 'loser' ? 'bracket-board__line--loser' : 'bracket-board__line--winner'"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>

        <p
          v-if="layout.lowerBandY != null"
          class="bracket-board__band-label"
          :style="{ top: `${layout.upperBandY}px` }"
        >
          Верхняя сетка
        </p>
        <p
          v-if="layout.lowerBandY != null"
          class="bracket-board__band-label"
          :style="{ top: `${layout.lowerBandY - 8}px` }"
        >
          Нижняя сетка
        </p>

        <div
          v-for="header in headers"
          :key="`${header.x}-${header.label}`"
          class="bracket-board__col-header"
          :style="{ left: `${header.x}px`, top: `${header.y}px` }"
        >
          {{ header.label }}
        </div>

        <button
          v-for="node in layout.nodes"
          :key="node.match.id"
          type="button"
          data-match-card
          class="bracket-board__card"
          :class="{
            'bracket-board__card--live': node.match.status === 'live',
            'bracket-board__card--done': node.match.status === 'done',
            'bracket-board__card--final':
              node.match.roundKey === 'de-final' || node.match.roundKey === 'grand-final',
            'bracket-board__card--focus': focusMatchId === node.match.id
          }"
          :style="{ width: `${BRACKET_CARD_W}px`, left: `${node.x}px`, top: `${node.y}px` }"
          @click="openMatch(node.match, $event)"
        >
          <div class="bracket-board__meta">
            <span class="bracket-board__no">#{{ node.match.displayNo || '·' }}</span>
            <span>Стол {{ node.match.tableNo || '—' }}</span>
            <span>{{ matchStatusLabel(node.match.status) }}</span>
          </div>
          <div class="bracket-board__players">
            <p>
              <span class="bracket-board__name" :title="nameOf(node.match.playerAId)">{{
                nameOf(node.match.playerAId)
              }}</span>
              <span class="bracket-board__score" :class="scoreClass(node.match, 'A')">{{
                node.match.framesA
              }}</span>
            </p>
            <p>
              <span class="bracket-board__name" :title="nameOf(node.match.playerBId)">{{
                nameOf(node.match.playerBId)
              }}</span>
              <span class="bracket-board__score" :class="scoreClass(node.match, 'B')">{{
                node.match.framesB
              }}</span>
            </p>
          </div>
          <div v-if="routingOf(node.match)" class="bracket-board__footer">
            <span class="bracket-board__route">{{ routingOf(node.match) }}</span>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>
