<script setup lang="ts">
import { cupRaceLabel } from '~/utils/cupLabels'

const route = useRoute()
const store = useCupStore()
const sync = useCupSync()
const suknoAuth = useSuknoAuth()
const { canSyncRoom } = useGameAccess()

const matchId = computed(() => String(route.params.id || ''))
const eventBusy = ref(false)
const eventError = ref('')

const isHost = computed(() => sync.role.value === 'host')
const isFollower = computed(() => sync.role.value === 'follower')
const myLogin = computed(() => (suknoAuth.profile.value?.username || '').trim().toLowerCase())

const match = computed(() => store.matchById(matchId.value))
const playerA = computed(() => store.playerById(match.value?.playerAId ?? null))
const playerB = computed(() => store.playerById(match.value?.playerBId ?? null))
const nameA = computed(() => playerA.value?.name || '—')
const nameB = computed(() => playerB.value?.name || '—')

const linkedToPair = computed(() => {
  const login = myLogin.value
  if (!login) return false
  return (
    (playerA.value?.username || '').trim().toLowerCase() === login ||
    (playerB.value?.username || '').trim().toLowerCase() === login
  )
})

const matchOpen = computed(
  () => Boolean(match.value && match.value.status !== 'done' && match.value.playerAId && match.value.playerBId)
)

/** Operator on the host device scores locally (existing pulpit). */
const canScoreLocal = computed(() => matchOpen.value && (!sync.isLive.value || isHost.value))

/** Pair on a phone scores through the room API. */
const canScorePair = computed(
  () => matchOpen.value && isFollower.value && Boolean(sync.roomCode.value) && linkedToPair.value
)

const canClaimA = computed(
  () =>
    Boolean(match.value?.playerAId) &&
    suknoAuth.isAccountUser.value &&
    sync.roomCode.value &&
    !(playerA.value?.username || '').trim()
)

const canClaimB = computed(
  () =>
    Boolean(match.value?.playerBId) &&
    suknoAuth.isAccountUser.value &&
    sync.roomCode.value &&
    !(playerB.value?.username || '').trim()
)

const matchShareUrl = computed(() => {
  if (!import.meta.client || !sync.roomCode.value) return ''
  const url = new URL(window.location.href)
  url.searchParams.set('room', sync.roomCode.value)
  return url.toString()
})

onMounted(async () => {
  store.hydrate()
  sync.hydrateMeta()
  const room = typeof route.query.room === 'string' ? route.query.room : ''
  if (room && sync.role.value !== 'host') {
    await sync.joinRoom(room)
  }
  if (matchId.value) store.setActiveMatch(matchId.value)
  try {
    await suknoAuth.fetchMe()
  } catch {
    /* guest */
  }
})

let tickTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  tickTimer = setInterval(() => store.tickShotClock(), 250)
})
onBeforeUnmount(() => {
  if (tickTimer) clearInterval(tickTimer)
})

const clockLabel = computed(() => {
  const ms = store.shotClock.remainingMs
  const sec = Math.ceil(ms / 1000)
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
})

const runPairEvent = async (
  action: 'add_ball' | 'undo_ball' | 'award_frame' | 'complete',
  extra: { side?: 'A' | 'B'; winner_id?: string } = {}
) => {
  eventError.value = ''
  eventBusy.value = true
  try {
    await sync.postMatchEvent({
      match_id: matchId.value,
      action,
      ...extra
    })
  } catch (error: unknown) {
    eventError.value = error instanceof Error ? error.message : 'Не удалось отправить результат'
  } finally {
    eventBusy.value = false
  }
}

const claim = async (playerId: string) => {
  eventError.value = ''
  eventBusy.value = true
  try {
    await sync.claimPlayer(playerId)
  } catch (error: unknown) {
    eventError.value = error instanceof Error ? error.message : 'Не удалось привязать слот'
  } finally {
    eventBusy.value = false
  }
}

const copyMatchLink = async () => {
  if (!matchShareUrl.value) return
  try {
    await navigator.clipboard.writeText(matchShareUrl.value)
  } catch {
    /* ignore */
  }
}

const addBall = (side: 'A' | 'B') => {
  if (canScorePair.value) void runPairEvent('add_ball', { side })
  else store.addBall(matchId.value, side)
}

const undoBall = (side: 'A' | 'B') => {
  if (canScorePair.value) void runPairEvent('undo_ball', { side })
  else store.undoBall(matchId.value, side)
}

const awardFrame = (side: 'A' | 'B') => {
  if (canScorePair.value) void runPairEvent('award_frame', { side })
  else store.awardFrame(matchId.value, side)
}

const complete = (winnerId: string) => {
  if (canScorePair.value) void runPairEvent('complete', { winner_id: winnerId })
  else store.completeMatch(matchId.value, winnerId)
}

const scoringEnabled = computed(() => (canScoreLocal.value || canScorePair.value) && !eventBusy.value)
</script>

<template>
  <div>
    <main class="page-shell py-8">
      <div class="flex flex-wrap gap-2">
        <NuxtLink to="/cup/bracket" class="btn-ghost btn-touch">← Сетка</NuxtLink>
        <NuxtLink to="/cup/tv" class="btn-ghost btn-touch">Табло турнира</NuxtLink>
        <button
          v-if="matchShareUrl && isHost"
          type="button"
          class="btn-ghost btn-touch"
          @click="copyMatchLink"
        >
          Ссылка для пары
        </button>
      </div>

      <p v-if="isFollower && linkedToPair" class="mt-3 text-xs text-cloth-accent">
        Вы в паре этого матча — счёт уходит на табло сразу.
      </p>
      <p v-else-if="isFollower && suknoAuth.isAccountUser.value && matchOpen" class="mt-3 text-xs text-cloth-muted">
        Нажмите «Это я», чтобы привязать аккаунт к своему слоту и вносить результат.
      </p>
      <p v-else-if="isFollower && !suknoAuth.isAccountUser.value" class="mt-3 text-xs text-cloth-muted">
        Чтобы пара сама вносила счёт, войдите в аккаунт.
        <NuxtLink to="/auth/login" class="text-cloth-accent">Вход</NuxtLink>
      </p>
      <p v-if="eventError" class="mt-2 text-sm text-amber-700">{{ eventError }}</p>
      <p v-if="sync.syncError.value" class="mt-2 text-sm text-amber-700">{{ sync.syncError.value }}</p>

      <section v-if="!match" class="card-surface mt-4 p-5">
        <p class="text-sm text-cloth-muted">Матч не найден.</p>
      </section>

      <section v-else class="mt-4">
        <section class="hero-surface px-6 py-8 sm:px-8">
          <p class="section-eyebrow">
            {{ match.roundLabel }} · {{ store.tournament.name }}
          </p>
          <h1 class="mt-3 font-display text-4xl font-bold text-cloth-chalk sm:text-5xl">Пульт матча</h1>
          <p class="mt-2 text-sm text-cloth-chalk/75">
            {{ cupRaceLabel(store.tournament.raceTo) }} · шары текущей партии
          </p>
        </section>

        <div class="mt-6 grid gap-4 md:grid-cols-2">
          <div class="card-surface p-5">
            <p class="text-xs uppercase tracking-wider text-cloth-muted">Игрок A</p>
            <h2 class="mt-1 font-display text-2xl font-bold">{{ nameA }}</h2>
            <p v-if="playerA?.username" class="mt-1 text-[11px] text-cloth-muted">аккаунт {{ playerA.username }}</p>
            <p class="score-num mt-4 text-6xl font-bold text-gradient">{{ match.framesA }}</p>
            <p class="mt-1 text-sm text-cloth-muted">партии</p>
            <p class="mt-4 text-2xl font-bold">{{ match.ballsA }} <span class="text-sm font-normal text-cloth-muted">шаров</span></p>
            <div class="mt-4 flex flex-wrap gap-2">
              <button type="button" class="btn-primary btn-touch" :disabled="!scoringEnabled" @click="addBall('A')">
                + Шар
              </button>
              <button type="button" class="btn-ghost btn-touch" :disabled="!scoringEnabled" @click="undoBall('A')">
                − Шар
              </button>
              <button type="button" class="btn-ghost btn-touch" :disabled="!scoringEnabled" @click="awardFrame('A')">
                Партия A
              </button>
              <button
                v-if="canClaimA"
                type="button"
                class="btn-ghost btn-touch"
                :disabled="eventBusy"
                @click="claim(match.playerAId!)"
              >
                Это я
              </button>
            </div>
          </div>

          <div class="card-surface p-5">
            <p class="text-xs uppercase tracking-wider text-cloth-muted">Игрок B</p>
            <h2 class="mt-1 font-display text-2xl font-bold">{{ nameB }}</h2>
            <p v-if="playerB?.username" class="mt-1 text-[11px] text-cloth-muted">аккаунт {{ playerB.username }}</p>
            <p class="score-num mt-4 text-6xl font-bold text-gradient">{{ match.framesB }}</p>
            <p class="mt-1 text-sm text-cloth-muted">партии</p>
            <p class="mt-4 text-2xl font-bold">{{ match.ballsB }} <span class="text-sm font-normal text-cloth-muted">шаров</span></p>
            <div class="mt-4 flex flex-wrap gap-2">
              <button type="button" class="btn-primary btn-touch" :disabled="!scoringEnabled" @click="addBall('B')">
                + Шар
              </button>
              <button type="button" class="btn-ghost btn-touch" :disabled="!scoringEnabled" @click="undoBall('B')">
                − Шар
              </button>
              <button type="button" class="btn-ghost btn-touch" :disabled="!scoringEnabled" @click="awardFrame('B')">
                Партия B
              </button>
              <button
                v-if="canClaimB"
                type="button"
                class="btn-ghost btn-touch"
                :disabled="eventBusy"
                @click="claim(match.playerBId!)"
              >
                Это я
              </button>
            </div>
          </div>
        </div>

        <section v-if="store.hasShotClock" class="card-surface mt-5 p-5">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-wider text-cloth-muted">Таймер хода</p>
              <p
                class="score-num mt-1 text-4xl font-bold"
                :class="store.shotClock.remainingMs <= 5000 ? 'text-cloth-danger' : 'text-cloth-accent'"
              >
                {{ clockLabel }}
              </p>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-if="!store.shotClock.running"
                type="button"
                class="btn-primary btn-touch"
                :disabled="!canScoreLocal"
                @click="store.startShotClock()"
              >
                Старт
              </button>
              <button
                v-else
                type="button"
                class="btn-ghost btn-touch"
                :disabled="!canScoreLocal"
                @click="store.pauseShotClock()"
              >
                Пауза
              </button>
              <button type="button" class="btn-ghost btn-touch" :disabled="!canScoreLocal" @click="store.resetShotClock()">
                Сброс
              </button>
            </div>
          </div>
        </section>

        <p v-if="match.status === 'done'" class="mt-4 text-sm text-emerald-300">
          Матч завершён.
          Победитель: {{ store.playerById(match.winnerId)?.name || '—' }}
        </p>
        <div v-else-if="scoringEnabled" class="mt-4 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
          <button type="button" class="btn-ghost btn-touch w-full sm:w-auto" @click="complete(match.playerAId!)">
            Победа {{ nameA }}
          </button>
          <button type="button" class="btn-ghost btn-touch w-full sm:w-auto" @click="complete(match.playerBId!)">
            Победа {{ nameB }}
          </button>
        </div>
        <p v-else-if="isFollower && matchOpen && canSyncRoom" class="mt-4 text-xs text-cloth-muted">
          Вы смотрите трансляцию. Счёт с пульта оператора или из привязанной пары.
        </p>
      </section>
    </main>
  </div>
</template>
