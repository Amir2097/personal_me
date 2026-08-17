<script setup lang="ts">
import { groupLabel, modeLabel, tournamentKindLabel } from '~/utils/labels'
import { createEmptyState } from '~/types/kolkhoz'

definePageMeta({ layout: 'bare' })

const store = useKolkhozStore()
const config = useRuntimeConfig()
const route = useRoute()
const { hydrateTheme } = useClothTheme()
const sync = useKolkhozSync()
const { appHref } = useAppBase()

useHead({
  title: 'Табло · Колхоз'
})

const sounds = useGameSounds()
const remainingLabel = ref('--:--')
const timerStatus = ref<'idle' | 'running' | 'paused'>('idle')
const roomInput = ref('')
const joinBusy = ref(false)
const showSwitchForm = ref(false)
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
    remainingLabel.value = '--:--'
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
    if (ok) {
      showSwitchForm.value = false
      tick()
    }
  } finally {
    joinBusy.value = false
  }
}

const disconnectBoard = () => {
  sync.leaveRoom()
  roomInput.value = ''
  showSwitchForm.value = true
  tick()
}

onMounted(async () => {
  hydrateTheme()
  tick()
  timer = setInterval(tick, 250)
  window.addEventListener('storage', onStorage)

  const q = typeof route.query.room === 'string' ? route.query.room : ''
  if (q) {
    roomInput.value = q
    await connectRoom(q)
    return
  }

  // Rejoin saved follower room only if it still exists on the server.
  const resumed = await sync.resumeFollowerIfPossible()
  if (!resumed) {
    // Do NOT hydrate old localStorage game — that looked like a “ghost” sync.
    // Start with an empty board until a live code is entered.
    Object.assign(store, createEmptyState())
    showSwitchForm.value = true
  }
  tick()
})

const loadLocalPreview = () => {
  store.hydrate()
  showSwitchForm.value = true
  tick()
}

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
const isRemoteFollower = computed(() => sync.role.value === 'follower' && sync.isLive.value)
const needsRoomCode = computed(
  () =>
    !isRemoteFollower.value ||
    showSwitchForm.value ||
    sync.roomStatus.value === 'ended' ||
    sync.roomStatus.value === 'idle'
)

const joinQrUrl = computed(() => {
  const code = (sync.roomCode.value || roomInput.value || '').trim().toUpperCase()
  if (code.length < 4) return ''
  if (!import.meta.client) return ''
  return appHref('tv', { room: code })
})

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
  <div class="min-h-screen px-4 py-4 text-cloth-chalk sm:px-6 sm:py-5 lg:px-8">
    <header class="tv-topbar rounded-2xl px-3 py-2.5 sm:px-4 sm:py-3">
      <div class="tv-topbar__row">
        <div class="tv-topbar__brand">
          <p class="tv-topbar__eyebrow">
            <AppIcon name="tv" size="sm" />
            {{ config.public.brandName }} · табло
          </p>
          <h1 class="tv-topbar__title">Колхоз · табло</h1>
          <p class="tv-topbar__sub">
            {{ modeText }}
            <template v-if="store.mode === 'tournament' && store.currentRound">
              · Тур {{ store.currentRound.number }}
            </template>
            <template v-if="sync.roomCode.value">
              · <span class="font-semibold text-cloth-accent">{{ sync.roomCode.value }}</span>
            </template>
          </p>
        </div>

        <div class="tv-topbar__room">
          <template v-if="needsRoomCode">
            <div class="tv-topbar__room-row">
              <label class="tv-topbar__room-label">
                Код комнаты
                <input
                  v-model="roomInput"
                  class="field-input"
                  maxlength="8"
                  placeholder="ABC123"
                  autocomplete="off"
                  @keyup.enter="connectRoom(roomInput)"
                />
              </label>
              <button
                type="button"
                class="btn-primary text-sm"
                :disabled="joinBusy"
                @click="connectRoom(roomInput)"
              >
                {{ joinBusy ? '…' : 'Подключить' }}
              </button>
              <button
                v-if="!isRemoteFollower"
                type="button"
                class="btn-ghost text-xs"
                @click="loadLocalPreview"
              >
                Локально
              </button>
            </div>
            <p v-if="sync.syncError.value" class="mt-1.5 text-xs text-red-500">{{ sync.syncError.value }}</p>
            <p v-if="sync.roomStatus.value === 'ended'" class="tv-topbar__alert">
              {{ sync.endedMessage.value || 'Встреча завершена.' }} Введите новый код.
            </p>
            <RoomQrCode
              v-if="joinQrUrl"
              class="mt-3"
              :url="joinQrUrl"
              label="Отсканируйте на TV или телефоне"
              :size="140"
            />
          </template>
          <template v-else-if="isRemoteFollower">
            <div class="tv-topbar__room-row">
              <p class="tv-topbar__status">
                Онлайн ·
                <span class="text-cloth-accent">{{ sync.roomCode.value }}</span>
                · № {{ sync.revision.value }}
              </p>
              <button type="button" class="btn-ghost text-xs" @click="showSwitchForm = true">
                Сменить
              </button>
              <button type="button" class="btn-ghost text-xs" @click="disconnectBoard">
                Отключить
              </button>
            </div>
          </template>
        </div>

        <div class="tv-topbar__timer">
          <div class="tv-topbar__timer-copy">
            <p class="tv-topbar__timer-label">
              <template v-if="timerStatus === 'paused'">пауза</template>
              <template v-else-if="timerStatus === 'running'">идёт</template>
              <template v-else>таймер</template>
            </p>
            <p class="tv-topbar__time">{{ remainingLabel }}</p>
          </div>
          <div v-if="canControlTimer && !isRemoteFollower" class="tv-topbar__timer-actions">
            <button
              v-if="timerStatus === 'idle'"
              type="button"
              class="btn-primary"
              @click="startTimer"
            >
              Старт
            </button>
            <button
              v-if="timerStatus === 'running'"
              type="button"
              class="btn-ghost"
              @click="pauseTimer"
            >
              Пауза
            </button>
            <button
              v-if="timerStatus === 'paused'"
              type="button"
              class="btn-primary"
              @click="resumeTimer"
            >
              Далее
            </button>
            <button
              v-if="timerStatus !== 'idle'"
              type="button"
              class="btn-ghost"
              @click="stopTimer"
            >
              Стоп
            </button>
            <button type="button" class="btn-ghost" @click="toggleMute">
              {{ store.tournament.timerMuted ? 'Звук' : 'Тише' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="store.mode === 'tournament'" class="tv-topbar__meta">
        <div v-if="store.currentRound" class="tv-topbar__chip tv-topbar__chip--accent">
          Ставки {{ roundRateShort }}
          <span class="text-cloth-muted">· 1-2-3</span>
        </div>
        <div class="tv-topbar__chip">
          Банк <strong>{{ store.totalBank.toLocaleString('ru-RU') }} ₽</strong>
        </div>
        <div class="tv-topbar__chip">
          Приз {{ store.tournament.bank.prizePercent }}%
          <strong>{{ store.prizePool.toLocaleString('ru-RU') }} ₽</strong>
        </div>
        <div class="tv-topbar__chip">
          Остаток <strong>{{ store.houseCut.toLocaleString('ru-RU') }} ₽</strong>
        </div>
      </div>
    </header>

    <div class="mt-5 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
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
            v-for="(player, index) in store.activePlayers"
            :key="player.id"
            class="card-surface rounded-3xl p-5"
          >
            <div class="flex items-center gap-3">
              <PlayerAvatar :name="player.name" />
              <div>
                <p class="text-xl font-bold">{{ player.name }}</p>
                <p v-if="index === 0" class="text-xs text-cloth-accent">разбив</p>
              </div>
            </div>
            <p class="mt-2 text-sm text-cloth-muted">
              пирамида: {{ store.casual.party ? (store.casual.party.rackPointsByPlayer[player.id] || 0) : 0 }} очк.
            </p>
            <p class="mt-1 font-display text-4xl tabular-nums text-cloth-accent">
              {{ player.balance.toLocaleString('ru-RU') }} {{ store.casual.currencyLabel }}
            </p>
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
          Табло подписано на комнату ведущего. Когда ведущий нажмёт «Завершить встречу», код
          перестанет действовать — здесь появится поле для нового кода.
        </template>
        <template v-else>
          Введите код комнаты с пульта. Локальный просмотр без кода показывает только данные
          этого браузера (не чужую встречу).
        </template>
      </p>
    </footer>
  </div>
</template>
