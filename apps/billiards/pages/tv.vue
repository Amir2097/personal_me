<script setup lang="ts">
import { groupLabel, modeLabel, tournamentKindLabel } from '~/utils/labels'

const store = useKolkhozStore()
const config = useRuntimeConfig()
const { hydrateTheme } = useClothTheme()

useHead({
  title: 'Табло · Колхоз'
})

const remainingLabel = ref('—:—')
const timerStatus = ref<'idle' | 'running' | 'paused'>('idle')
let timer: ReturnType<typeof setInterval> | null = null
let audioCtx: AudioContext | null = null

const formatMs = (ms: number) => {
  const total = Math.max(0, Math.floor(ms / 1000))
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

const ensureAudio = async () => {
  if (typeof window === 'undefined') return null
  if (!audioCtx) audioCtx = new AudioContext()
  if (audioCtx.state === 'suspended') {
    try {
      await audioCtx.resume()
    } catch {
      /* ignore */
    }
  }
  return audioCtx
}

const tick = () => {
  if (store.timerIsPaused) {
    timerStatus.value = 'paused'
    remainingLabel.value = formatMs(store.tournament.timerPausedRemainingMs || 0)
    return
  }
  const ends = store.tournament.roundEndsAt
  if (!ends) {
    timerStatus.value = 'idle'
    remainingLabel.value = '—:—'
    return
  }
  timerStatus.value = 'running'
  const left = Math.max(0, new Date(ends).getTime() - Date.now())
  remainingLabel.value = formatMs(left)
  if (left <= 0) {
    store.clearRoundTimer()
    timerStatus.value = 'idle'
    remainingLabel.value = '00:00'
  }
}

const onStorage = (event: StorageEvent) => {
  if (event.key === 'dautovtech_kolkhoz_v1') {
    store.hydrate()
    tick()
  }
}

onMounted(() => {
  hydrateTheme()
  store.hydrate()
  tick()
  timer = setInterval(tick, 250)
  window.addEventListener('storage', onStorage)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  window.removeEventListener('storage', onStorage)
})

const playersAt = (playerIds: string[]) =>
  playerIds
    .map((id) => store.players.find((player) => player.id === id))
    .filter((player): player is NonNullable<typeof player> => Boolean(player))

const modeText = computed(() => {
  if (store.mode === 'tournament') {
    return `${modeLabel(store.mode)} · ${tournamentKindLabel(store.tournament.kind)}`
  }
  return modeLabel(store.mode)
})

const backHref = computed(() => {
  if (store.mode === 'tournament') return '/tournament/play'
  if (store.mode === 'casual') return '/casual/play'
  return '/'
})

const backLabel = computed(() => {
  if (store.mode === 'tournament') {
    return store.tournament.kind === 'organizer' ? 'К пульту тура' : 'К игровым столам'
  }
  if (store.mode === 'casual') return 'К быстрому столу'
  return 'К режимам'
})

const canControlTimer = computed(() => store.mode === 'tournament' && Boolean(store.currentRound))

const roundRateShort = computed(() => {
  const round = store.currentRound
  if (!round) return '—'
  return `${round.tariffs[1]}-${round.tariffs[2]}-${round.tariffs[3]}`
})

const startTimer = () => {
  void ensureAudio()
  store.startRoundTimer()
  tick()
}

const pauseTimer = () => {
  store.pauseRoundTimer()
  tick()
}

const resumeTimer = () => {
  void ensureAudio()
  store.resumeRoundTimer()
  tick()
}

const stopTimer = () => {
  store.clearRoundTimer()
  tick()
}

const toggleMute = () => {
  void ensureAudio()
  store.setTimerMuted(!store.tournament.timerMuted)
}
</script>

<template>
  <div class="min-h-screen px-4 py-6 text-cloth-chalk sm:px-8">
    <header class="flex flex-wrap items-end justify-between gap-4 border-b border-[color:var(--cloth-border)] pb-6">
      <div class="tv-hero-panel rounded-2xl p-4 sm:p-5">
        <p class="flex items-center gap-2 text-sm uppercase tracking-[0.35em] text-cloth-muted">
          <AppIcon name="tv" class="text-cloth-accent" /> {{ config.public.brandName }} · табло
        </p>
        <h1 class="mt-2 font-display text-4xl font-extrabold sm:text-6xl">Колхоз · табло</h1>
        <p class="mt-2 text-lg text-cloth-muted">
          {{ modeText }}
          <template v-if="store.mode === 'tournament' && store.currentRound">
            · Тур {{ store.currentRound.number }}
          </template>
        </p>
        <div v-if="store.mode === 'tournament'" class="mt-3 grid gap-2 sm:max-w-3xl sm:grid-cols-2">
          <div
            v-if="store.currentRound"
            class="rounded-xl border border-cloth-accent/35 bg-cloth-accent/10 px-3 py-2 text-sm"
          >
            <p class="font-semibold text-cloth-accent">Ставки тура: {{ roundRateShort }}</p>
            <p class="text-xs text-cloth-muted">формат групп 1-2-3</p>
          </div>
          <div
            v-if="store.tournament.kind === 'organizer'"
            class="rounded-xl border border-[color:var(--cloth-border)] bg-[color:var(--cloth-card)] px-3 py-2 text-sm"
          >
            <p>
              Банк: <strong class="text-cloth-accent">{{ store.totalBank.toLocaleString('ru-RU') }} ₽</strong>
            </p>
            <p>
              Призовые ({{ store.tournament.bank.prizePercent }}%):
              <strong class="text-cloth-accent">{{ store.prizePool.toLocaleString('ru-RU') }} ₽</strong>
            </p>
            <p>Остаток: <strong>{{ store.houseCut.toLocaleString('ru-RU') }} ₽</strong></p>
          </div>
        </div>
      </div>
      <div class="tv-hero-panel min-w-[14rem] rounded-2xl p-4 text-right sm:p-5">
        <p class="flex items-center justify-end gap-2 text-sm uppercase tracking-widest text-cloth-muted">
          <AppIcon name="clock" size="sm" />
          <template v-if="timerStatus === 'paused'">на паузе</template>
          <template v-else-if="timerStatus === 'running'">идёт</template>
          <template v-else>таймер</template>
        </p>
        <p class="font-display text-5xl font-bold tabular-nums text-cloth-accent sm:text-7xl">{{ remainingLabel }}</p>

        <div v-if="canControlTimer" class="tv-timer-controls">
          <button
            v-if="timerStatus === 'idle'"
            type="button"
            class="btn-primary inline-flex items-center gap-1.5 text-sm"
            @click="startTimer"
          >
            <AppIcon name="clock" size="sm" /> Старт
          </button>
          <button
            v-if="timerStatus === 'running'"
            type="button"
            class="btn-ghost inline-flex items-center gap-1.5 text-sm"
            @click="pauseTimer"
          >
            <AppIcon name="pause" size="sm" /> Пауза
          </button>
          <button
            v-if="timerStatus === 'paused'"
            type="button"
            class="btn-primary inline-flex items-center gap-1.5 text-sm"
            @click="resumeTimer"
          >
            <AppIcon name="play" size="sm" /> Продолжить
          </button>
          <button
            v-if="timerStatus !== 'idle'"
            type="button"
            class="btn-ghost text-sm"
            @click="stopTimer"
          >
            Стоп
          </button>
          <button type="button" class="btn-ghost text-sm" @click="toggleMute">
            {{ store.tournament.timerMuted ? 'Вкл. звук' : 'Без звука' }}
          </button>
        </div>
      </div>
    </header>

    <div class="mt-8 grid gap-8 xl:grid-cols-[1.2fr_0.8fr]">
      <section>
        <h2 class="flex items-center gap-2 font-display text-2xl font-bold">
          <AppIcon name="ball" class="text-cloth-accent" /> Столы
        </h2>
        <div v-if="store.mode === 'tournament'" class="mt-4 grid gap-4 md:grid-cols-2">
          <article
            v-for="table in store.tournament.tables"
            :key="table.id"
            class="card-surface rounded-3xl p-5"
          >
            <h3 class="font-display text-2xl font-bold text-cloth-accent">{{ table.label }}</h3>
            <p class="mt-1 text-xs uppercase tracking-wider text-cloth-muted">номер в зале · {{ table.number }}</p>
            <ul class="mt-3 space-y-2">
              <li
                v-for="player in playersAt(table.playerIds)"
                :key="player.id"
                class="flex items-center justify-between text-lg"
                :class="player.status === 'eliminated' ? 'opacity-40 line-through' : ''"
              >
                <span class="inline-flex items-center gap-2">
                  <PlayerAvatar :name="player.name" size="sm" />
                  {{ player.name }}
                  <span class="text-cloth-muted">{{ groupLabel(player.category, true) }}</span>
                </span>
                <span class="font-display text-2xl tabular-nums">{{ player.balance }}</span>
              </li>
            </ul>
          </article>
          <p v-if="!store.tournament.tables.length" class="text-cloth-muted">Рассадка ещё не задана.</p>
        </div>
        <div v-else class="mt-4 grid gap-3 sm:grid-cols-2">
          <article
            v-for="player in store.activePlayers"
            :key="player.id"
            class="card-surface rounded-3xl p-5"
          >
            <div class="flex items-center gap-3">
              <PlayerAvatar :name="player.name" />
              <p class="text-xl font-bold">{{ player.name }}</p>
            </div>
            <p class="mt-2 font-display text-4xl tabular-nums text-cloth-accent">{{ player.balance }}</p>
          </article>
        </div>
      </section>

      <section class="space-y-6">
        <div class="card-surface rounded-3xl p-5">
          <h2 class="flex items-center gap-2 font-display text-2xl font-bold">
            <AppIcon name="trophy" class="text-cloth-accent" /> Лидерборд
          </h2>
          <ol class="mt-4 space-y-3">
            <li
              v-for="(player, index) in store.leaderboard"
              :key="player.id"
              class="flex items-center justify-between gap-3 border-b border-[color:var(--cloth-border)] pb-2 text-xl"
            >
              <span class="inline-flex items-center gap-2">
                <span class="text-cloth-accent">{{ index + 1 }}.</span>
                <PlayerAvatar :name="player.name" size="sm" />
                {{ player.name }}
              </span>
              <span class="font-display text-3xl tabular-nums">{{ player.balance }}</span>
            </li>
          </ol>
        </div>

        <div
          v-if="store.mode === 'tournament' && store.tournament.kind === 'organizer'"
          class="card-surface rounded-3xl p-5"
        >
          <h2 class="flex items-center gap-2 font-display text-2xl font-bold">
            <AppIcon name="chip" class="text-cloth-accent" /> Призовые места
          </h2>
          <ul class="mt-4 space-y-2 text-lg">
            <li
              v-for="row in store.prizeBreakdown"
              :key="row.place"
              class="flex items-center justify-between border-b border-[color:var(--cloth-border)] pb-2"
            >
              <span>{{ row.place }} место ({{ row.percent }}%)</span>
              <span class="font-display text-2xl tabular-nums text-cloth-accent">
                {{ row.amount.toLocaleString('ru-RU') }} ₽
              </span>
            </li>
          </ul>
        </div>

        <div class="card-surface rounded-3xl p-5">
          <h2 class="font-display text-2xl font-bold">Вне игры</h2>
          <ul class="mt-3 space-y-2 text-lg text-cloth-muted">
            <li v-for="player in store.eliminatedPlayers" :key="player.id">
              {{ player.name }} · {{ player.balance }}
            </li>
            <li v-if="!store.eliminatedPlayers.length">Пока никого</li>
          </ul>
        </div>
      </section>
    </div>

    <footer class="tv-footer">
      <NuxtLink
        :to="backHref"
        class="btn-primary inline-flex w-fit items-center gap-2 px-5 py-2.5 text-sm shadow-md"
      >
        <AppIcon name="arrow" size="sm" class="rotate-180" />
        {{ backLabel }}
      </NuxtLink>
      <p class="max-w-md text-sm text-cloth-muted">
        Табло можно использовать для управления таймером. Изменения сохраняются локально и подхватываются
        другими вкладками этого браузера.
      </p>
    </footer>
  </div>
</template>
