<script setup lang="ts">
import { cupFormatTitle, cupRaceLabel, matchStatusLabel } from '~/utils/cupLabels'
import type { CupMatch } from '~/types/cup'

const store = useCupStore()
const sync = useCupSync()
const route = useRoute()

const joinCode = ref('')
const clockLabel = computed(() => {
  const sec = Math.ceil(store.shotClock.remainingMs / 1000)
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
})

const focusMatchId = computed(() => {
  const fromQuery = String(route.query.match || '')
  if (fromQuery) return fromQuery
  return store.activeMatchId
})

const liveMatches = computed(() =>
  store.matches.filter((match) => match.status === 'live' && match.playerAId && match.playerBId)
)

const readyMatches = computed(() =>
  store.matches.filter((match) => match.status === 'ready' && match.playerAId && match.playerBId)
)

const featuredMatch = computed(() => {
  const focused = store.matches.find((match) => match.id === focusMatchId.value)
  if (focused && (focused.status === 'live' || focused.status === 'ready')) return focused
  return liveMatches.value[0] || readyMatches.value[0] || null
})

const finishedMatches = computed(() =>
  store.matches
    .filter((match) => match.status === 'done' && match.winnerId)
    .slice()
    .sort((a, b) => (b.displayNo || 0) - (a.displayNo || 0))
    .slice(0, 8)
)

const doneCount = computed(() => store.matches.filter((match) => match.status === 'done').length)

const nameOf = (id: string | null) => store.playerById(id)?.name || '—'

const scoreLine = (match: CupMatch) => `${match.framesA} : ${match.framesB}`

onMounted(async () => {
  store.hydrate()
  sync.hydrateMeta()
  const q = String(route.query.room || '')
  if (q) {
    await sync.joinRoom(q)
  } else if (sync.role.value === 'follower' && sync.roomCode.value) {
    sync.startPolling()
  }

  if (!q && sync.role.value !== 'follower') {
    watch(
      () => store.$state,
      () => sync.schedulePush(),
      { deep: true }
    )
  }

  window.addEventListener('storage', onStorage)
})

let tick: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  tick = setInterval(() => store.tickShotClock(), 250)
})
onBeforeUnmount(() => {
  if (tick) clearInterval(tick)
  window.removeEventListener('storage', onStorage)
})

const ensureHostRoom = async () => {
  if (!sync.roomCode.value) await sync.createRoom()
  else await sync.pushNow()
}

const onStorage = (event: StorageEvent) => {
  if (event.key === 'dautovtech_cup_v1') store.hydrate()
}
</script>

<template>
  <div>
    <main class="page-shell page-shell--wide py-6">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex flex-wrap gap-2">
          <NuxtLink to="/cup/bracket" class="btn-ghost text-sm">← Турнир</NuxtLink>
          <NuxtLink to="/cup" class="btn-ghost text-sm">Список</NuxtLink>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <template v-if="sync.role.value === 'host' && sync.roomCode.value">
            <span class="rounded-lg border border-cloth-border bg-cloth-card px-3 py-1 text-sm text-cloth-chalk">
              Код: <span class="font-semibold text-cloth-accent">{{ sync.roomCode.value }}</span>
            </span>
            <button type="button" class="btn-ghost text-sm" @click="sync.closeRoom()">Закрыть комнату</button>
          </template>
          <button
            v-else-if="sync.role.value !== 'follower'"
            type="button"
            class="btn-primary text-sm"
            @click="ensureHostRoom"
          >
            Создать код для TV
          </button>
          <form
            v-if="sync.role.value !== 'host'"
            class="flex gap-2"
            @submit.prevent="sync.joinRoom(joinCode)"
          >
            <input v-model="joinCode" class="field-input w-28 text-sm" placeholder="Код" />
            <button type="submit" class="btn-ghost text-sm">Подключить</button>
          </form>
        </div>
      </div>

      <p v-if="sync.syncError.value" class="mt-3 text-sm text-red-600">
        {{ sync.syncError.value }}
      </p>

      <CupTournamentSwitcher compact class="mt-4" />

      <section class="hero-surface mt-5 px-6 py-9 sm:px-10 sm:py-11">
        <p class="section-eyebrow">Табло турнира</p>
        <h1 class="mt-3 font-display text-4xl font-bold text-cloth-chalk sm:text-5xl lg:text-6xl">
          {{ store.tournament.name || 'Турнир' }}
        </h1>
        <p class="mt-3 text-base text-cloth-muted">
          {{ cupFormatTitle(store.tournament.format) }} · {{ cupRaceLabel(store.tournament.raceTo) }}
          · сыграно {{ doneCount }} из {{ store.matches.length }}
        </p>
        <p v-if="store.winnerName" class="mt-2 font-semibold text-cloth-accent">
          Победитель: {{ store.winnerName }}
        </p>
      </section>

      <section v-if="featuredMatch" class="card-surface mt-5 p-5">
        <div class="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-wider text-cloth-muted">Сейчас на столе</p>
            <h2 class="mt-1 font-display text-xl font-bold text-cloth-chalk">
              #{{ featuredMatch.displayNo }} · {{ featuredMatch.roundLabel }}
            </h2>
          </div>
          <p class="text-sm text-cloth-muted">
            Стол {{ featuredMatch.tableNo || '—' }} · {{ matchStatusLabel(featuredMatch.status) }}
          </p>
        </div>

        <div class="mt-5 grid gap-4 md:grid-cols-[1fr_auto_1fr] md:items-center">
          <div>
            <p class="text-sm font-semibold text-cloth-chalk">{{ nameOf(featuredMatch.playerAId) }}</p>
            <p class="score-num mt-2 text-7xl font-bold text-gradient">{{ featuredMatch.framesA }}</p>
            <p class="mt-1 text-sm text-cloth-muted">шары: {{ featuredMatch.ballsA }}</p>
          </div>
          <div class="text-center">
            <p class="text-xs uppercase tracking-[0.22em] text-cloth-muted">против</p>
            <template v-if="store.hasShotClock && featuredMatch.status === 'live'">
              <p
                class="score-num mt-3 text-3xl font-bold"
                :class="store.shotClock.remainingMs <= 5000 ? 'text-cloth-danger' : 'text-cloth-accent'"
              >
                {{ clockLabel }}
              </p>
            </template>
          </div>
          <div class="md:text-right">
            <p class="text-sm font-semibold text-cloth-chalk">{{ nameOf(featuredMatch.playerBId) }}</p>
            <p class="score-num mt-2 text-7xl font-bold text-gradient">{{ featuredMatch.framesB }}</p>
            <p class="mt-1 text-sm text-cloth-muted">шары: {{ featuredMatch.ballsB }}</p>
          </div>
        </div>
      </section>

      <section v-else class="card-surface mt-5 p-5">
        <p class="text-sm text-cloth-muted">
          Сейчас нет живой встречи. Когда начнётся партия, счёт появится здесь, а сетка обновится сама.
        </p>
      </section>

      <section v-if="liveMatches.length + readyMatches.length > 1" class="mt-4 flex flex-wrap gap-2">
        <span
          v-for="match in [...liveMatches, ...readyMatches]"
          :key="match.id"
          class="panel-surface px-3 py-1.5 text-xs text-cloth-chalk"
          :class="match.id === featuredMatch?.id ? 'border-cloth-accent/60 bg-cloth-accent/10' : ''"
        >
          #{{ match.displayNo }} {{ nameOf(match.playerAId) }} {{ scoreLine(match) }}
          {{ nameOf(match.playerBId) }}
        </span>
      </section>

      <section v-if="store.matches.length" class="card-surface mt-5 p-3 sm:p-4">
        <CupBracketBoard
          :matches="store.matches"
          :players="store.players"
          :race-to="store.tournament.raceTo"
          :format="store.tournament.format"
          :interactive="false"
          :focus-match-id="featuredMatch?.id || focusMatchId"
        />
      </section>

      <section v-if="finishedMatches.length" class="card-surface mt-5 p-5">
        <h2 class="font-display text-lg font-bold text-cloth-chalk">Последние результаты</h2>
        <ul class="mt-3 grid gap-2 sm:grid-cols-2">
          <li
            v-for="match in finishedMatches"
            :key="match.id"
            class="panel-surface flex items-center justify-between gap-3 px-3 py-2 text-sm"
          >
            <span class="min-w-0 truncate text-cloth-chalk">
              #{{ match.displayNo }} · {{ nameOf(match.playerAId) }} — {{ nameOf(match.playerBId) }}
            </span>
            <span class="shrink-0 font-semibold text-cloth-accent">
              {{ scoreLine(match) }}
              · {{ nameOf(match.winnerId) }}
            </span>
          </li>
        </ul>
      </section>
    </main>
  </div>
</template>
