<script setup lang="ts">
import { groupLabel, modeLabel, tournamentKindLabel } from '~/utils/labels'

const store = useKolkhozStore()
const config = useRuntimeConfig()
const route = useRoute()
const { hydrateTheme } = useClothTheme()
const sync = useKolkhozSync()

useHead({
  title: 'Табло · Колхоз'
})

const sounds = useGameSounds()
const remainingLabel = ref('—:—')
const timerStatus = ref<'idle' | 'running' | 'paused'>('idle')
const roomInput = ref('')
const joinBusy = ref(false)
let timer: ReturnType<typeof setInterval> | null = null
const hasBeeped = ref(false)

const formatMs = (ms: number) => {
  const total = Math.max(0, Math.floor(ms / 1000))
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
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
    hasBeeped.value = false
    return
  }
  timerStatus.value = 'running'
  const left = Math.max(0, new Date(ends).getTime() - Date.now())
  remainingLabel.value = formatMs(left)
  if (left <= 0) {
    if (!hasBeeped.value) {
      hasBeeped.value = true
      void sounds.play('timer')
    }
    store.clearRoundTimer()
    timerStatus.value = 'idle'
    remainingLabel.value = '00:00'
  }
}

const onStorage = (event: StorageEvent) => {
  // Same-browser tabs fallback when remote room is not used.
  if (sync.role.value === 'follower') return
  if (event.key === 'dautovtech_kolkhoz_v1') {
    store.hydrate()
    tick()
  }
}

const connectRoom = async (code: string) => {
  joinBusy.value = true
  try {
    const ok = await sync.joinRoom(code)
    if (ok) tick()
  } finally {
    joinBusy.value = false
  }
}

onMounted(async () => {
  hydrateTheme()
  sync.hydrateMeta()
  store.hydrate()
  tick()
  timer = setInterval(tick, 250)
  window.addEventListener('storage', onStorage)

  const q = typeof route.query.room === 'string' ? route.query.room : ''
  if (q) {
    roomInput.value = q
    await connectRoom(q)
  } else if (sync.role.value === 'follower' && sync.roomCode.value) {
    sync.startPolling()
  }
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  window.removeEventListener('storage', onStorage)
  sync.stopPolling()
})

watch(
  () => store.updatedAt,
  () => tick()
)

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
const isRemoteFollower = computed(() => sync.role.value === 'follower')

const roundRateShort = computed(() => {
  const round = store.currentRound
  if (!round) return '—'
  return `${round.tariffs[1]}-${round.tariffs[2]}-${round.tariffs[3]}`
})

const startTimer = () => {
  sounds.unlock()
  hasBeeped.value = false
  store.startRoundTimer()
  tick()
}

const pauseTimer = () => {
  store.pauseRoundTimer()
  tick()
}

const resumeTimer = () => {
  sounds.unlock()
  store.resumeRoundTimer()
  tick()
}

const stopTimer = () => {
  store.clearRoundTimer()
  hasBeeped.value = false
  tick()
}

const toggleMute = () => {
  sounds.unlock()
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
          <template v-if="sync.roomCode.value">
            · комната <span class="text-cloth-accent">{{ sync.roomCode.value }}</span>
          </template>
        </p>

        <div
          v-if="!isRemoteFollower && !sync.roomCode.value"
          class="mt-4 flex max-w-md flex-wrap items-end gap-2 rounded-xl border border-[color:var(--cloth-border)] bg-[color:var(--cloth-card)] p-3"
        >
          <label class="min-w-[10rem] flex-1 text-xs text-cloth-muted">
            Код комнаты с телефона
            <input
              v-model="roomInput"
              class="field-input mt-1 w-full uppercase tracking-widest"
              maxlength="8"
              placeholder="ABC123"
              @keyup.enter="connectRoom(roomInput)"
            />
          </label>
          <button
            type="button"
            class="btn-primary text-sm"
            :disabled="joinBusy"
            @click="connectRoom(roomInput)"
          >
            Подключить
          </button>
          <p v-if="sync.syncError.value" class="w-full text-xs text-red-500">{{ sync.syncError.value }}</p>
        </div>
        <p v-else-if="isRemoteFollower" class="mt-3 text-sm text-cloth-accent">
          Онлайн-синк · обновление ~1 с · rev {{ sync.revision.value }}
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

        <div v-if="canControlTimer && !isRemoteFollower" class="tv-timer-controls">
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
            <p
              v-if="store.potByTableId(table.id)"
              class="mt-3 rounded-xl border border-amber-400/40 bg-amber-500/15 px-3 py-2 text-lg"
            >
              Общак:
              <strong class="font-display text-2xl text-cloth-accent">
                {{ store.potByTableId(table.id)?.amount }}
              </strong>
              фиш.
              <span class="mt-0.5 block text-sm text-cloth-muted">
                ход круга:
                {{
                  store.players.find((p) => p.id === store.potByTableId(table.id)?.passCursorPlayerId)?.name || '—'
                }}
              </span>
            </p>
            <ul class="mt-3 space-y-2">
              <li
                v-for="player in playersAt(table.playerIds)"
                :key="player.id"
                class="flex items-center justify-between text-lg"
                :class="{
                  'opacity-40 line-through': player.status === 'eliminated',
                  'rounded-lg bg-amber-500/10 px-2':
                    store.potByTableId(table.id)?.passCursorPlayerId === player.id
                }"
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
          v-if="store.mode === 'tournament'"
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
        <template v-if="isRemoteFollower">
          Табло подписано на комнату хоста. Счёт и столы обновляются автоматически.
        </template>
        <template v-else>
          Локальный режим: изменения видны во вкладках этого браузера. Для другого устройства
          откройте синк на пульте и введите код здесь.
        </template>
      </p>
    </footer>
  </div>
</template>
