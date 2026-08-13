<script setup lang="ts">
import { cupRaceLabel } from '~/utils/cupLabels'

const route = useRoute()
const store = useCupStore()
const sync = useCupSync()

const matchId = computed(() => String(route.params.id || ''))
const tvLink = computed(() => sync.tvUrl.value)

onMounted(() => {
  store.hydrate()
  sync.hydrateMeta()
  if (matchId.value) store.setActiveMatch(matchId.value)
})

const ensureHostRoom = async () => {
  if (!sync.roomCode.value) await sync.createRoom()
  else await sync.pushNow()
}

let tickTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  tickTimer = setInterval(() => store.tickShotClock(), 250)
})
onBeforeUnmount(() => {
  if (tickTimer) clearInterval(tickTimer)
})

const match = computed(() => store.matchById(matchId.value))
const nameA = computed(() => store.playerById(match.value?.playerAId ?? null)?.name || '—')
const nameB = computed(() => store.playerById(match.value?.playerBId ?? null)?.name || '—')

const clockLabel = computed(() => {
  const ms = store.shotClock.remainingMs
  const sec = Math.ceil(ms / 1000)
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
})

const canScore = computed(
  () => Boolean(match.value && match.value.status !== 'done' && match.value.playerAId && match.value.playerBId)
)
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-6xl px-4 py-8">
      <div class="flex flex-wrap gap-2">
        <NuxtLink to="/cup/bracket" class="btn-ghost text-sm">← Сетка</NuxtLink>
        <NuxtLink to="/cup/tv" class="btn-ghost text-sm">Табло турнира</NuxtLink>
        <button
          v-if="sync.role.value !== 'follower'"
          type="button"
          class="btn-ghost text-sm"
          @click="ensureHostRoom"
        >
          {{ sync.roomCode.value ? `Код TV: ${sync.roomCode.value}` : 'Создать код TV' }}
        </button>
        <a
          v-if="tvLink"
          :href="tvLink"
          target="_blank"
          rel="noopener"
          class="btn-ghost text-sm"
        >
          Открыть TV по коду
        </a>
      </div>
      <p v-if="sync.syncError.value" class="mt-2 text-sm text-amber-300">{{ sync.syncError.value }}</p>

      <section v-if="!match" class="card-surface mt-4 p-5">
        <p class="text-sm text-cloth-muted">Матч не найден.</p>
      </section>

      <section v-else class="mt-4">
        <section class="hero-surface rounded-2xl px-5 py-5">
          <p class="text-xs uppercase tracking-[0.2em] text-cloth-accent">
            {{ match.roundLabel }} · {{ store.tournament.name }}
          </p>
          <h1 class="mt-2 font-display text-3xl font-bold text-cloth-chalk">Пульт матча</h1>
          <p class="mt-1 text-sm text-cloth-chalk/75">
            {{ cupRaceLabel(store.tournament.raceTo) }} · шары текущей партии
          </p>
        </section>

        <div class="mt-6 grid gap-4 md:grid-cols-2">
          <div class="card-surface p-5">
            <p class="text-xs uppercase tracking-wider text-cloth-muted">Игрок A</p>
            <h2 class="mt-1 font-display text-2xl font-bold">{{ nameA }}</h2>
            <p class="mt-4 text-4xl font-extrabold text-cloth-accent">{{ match.framesA }}</p>
            <p class="mt-1 text-sm text-cloth-muted">партии</p>
            <p class="mt-4 text-2xl font-bold">{{ match.ballsA }} <span class="text-sm font-normal text-cloth-muted">шаров</span></p>
            <div class="mt-4 flex flex-wrap gap-2">
              <button type="button" class="btn-primary text-sm" :disabled="!canScore" @click="store.addBall(match.id, 'A')">
                + Шар
              </button>
              <button type="button" class="btn-ghost text-sm" :disabled="!canScore" @click="store.undoBall(match.id, 'A')">
                − Шар
              </button>
              <button type="button" class="btn-ghost text-sm" :disabled="!canScore" @click="store.awardFrame(match.id, 'A')">
                Партия A
              </button>
            </div>
          </div>

          <div class="card-surface p-5">
            <p class="text-xs uppercase tracking-wider text-cloth-muted">Игрок B</p>
            <h2 class="mt-1 font-display text-2xl font-bold">{{ nameB }}</h2>
            <p class="mt-4 text-4xl font-extrabold text-cloth-accent">{{ match.framesB }}</p>
            <p class="mt-1 text-sm text-cloth-muted">партии</p>
            <p class="mt-4 text-2xl font-bold">{{ match.ballsB }} <span class="text-sm font-normal text-cloth-muted">шаров</span></p>
            <div class="mt-4 flex flex-wrap gap-2">
              <button type="button" class="btn-primary text-sm" :disabled="!canScore" @click="store.addBall(match.id, 'B')">
                + Шар
              </button>
              <button type="button" class="btn-ghost text-sm" :disabled="!canScore" @click="store.undoBall(match.id, 'B')">
                − Шар
              </button>
              <button type="button" class="btn-ghost text-sm" :disabled="!canScore" @click="store.awardFrame(match.id, 'B')">
                Партия B
              </button>
            </div>
          </div>
        </div>

        <section v-if="store.hasShotClock" class="card-surface mt-5 p-5">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-wider text-cloth-muted">Таймер хода</p>
              <p class="mt-1 font-display text-4xl font-bold" :class="store.shotClock.remainingMs <= 5000 ? 'text-red-300' : ''">
                {{ clockLabel }}
              </p>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-if="!store.shotClock.running"
                type="button"
                class="btn-primary text-sm"
                :disabled="!canScore"
                @click="store.startShotClock()"
              >
                Старт
              </button>
              <button
                v-else
                type="button"
                class="btn-ghost text-sm"
                @click="store.pauseShotClock()"
              >
                Пауза
              </button>
              <button type="button" class="btn-ghost text-sm" @click="store.resetShotClock()">Сброс</button>
            </div>
          </div>
        </section>

        <p v-if="match.status === 'done'" class="mt-4 text-sm text-emerald-300">
          Матч завершён.
          Победитель: {{ store.playerById(match.winnerId)?.name || '—' }}
        </p>
        <div v-else-if="canScore" class="mt-4 flex flex-wrap gap-2">
          <button type="button" class="btn-ghost text-sm" @click="store.completeMatch(match.id, match.playerAId!)">
            Победа {{ nameA }}
          </button>
          <button type="button" class="btn-ghost text-sm" @click="store.completeMatch(match.id, match.playerBId!)">
            Победа {{ nameB }}
          </button>
        </div>
      </section>
    </main>
  </div>
</template>
