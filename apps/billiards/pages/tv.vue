<script setup lang="ts">
const store = useKolkhozStore()
const config = useRuntimeConfig()

useHead({
  title: 'TV · Kolkhoz'
})

const remainingLabel = ref('--:--')
let timer: ReturnType<typeof setInterval> | null = null

const tick = () => {
  const ends = store.tournament.roundEndsAt
  if (!ends) {
    remainingLabel.value = '—:—'
    return
  }
  const left = Math.max(0, Math.floor((new Date(ends).getTime() - Date.now()) / 1000))
  const m = Math.floor(left / 60)
  const s = left % 60
  remainingLabel.value = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

onMounted(() => {
  store.hydrate()
  tick()
  timer = setInterval(tick, 500)
  window.addEventListener('storage', onStorage)
})

const onStorage = (event: StorageEvent) => {
  if (event.key === 'dautovtech_kolkhoz_v1') {
    store.hydrate()
    tick()
  }
}

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  window.removeEventListener('storage', onStorage)
})

const playersAt = (playerIds: string[]) =>
  playerIds
    .map((id) => store.players.find((player) => player.id === id))
    .filter((player): player is NonNullable<typeof player> => Boolean(player))
</script>

<template>
  <div class="min-h-screen bg-cloth-deep px-4 py-6 text-cloth-chalk sm:px-8">
    <header class="flex flex-wrap items-end justify-between gap-4 border-b border-white/10 pb-6">
      <div>
        <p class="flex items-center gap-2 text-sm uppercase tracking-[0.35em] text-cloth-muted">
          <AppIcon name="tv" class="text-cloth-accent" /> {{ config.public.brandName }} TV
        </p>
        <h1 class="mt-2 font-display text-4xl font-extrabold sm:text-6xl">Колхоз · табло</h1>
        <p class="mt-2 text-lg text-cloth-muted">
          Режим: {{ store.mode || '—' }}
          <template v-if="store.mode === 'tournament' && store.currentRound">
            · Тур {{ store.currentRound.number }}
          </template>
        </p>
      </div>
      <div class="text-right">
        <p class="flex items-center justify-end gap-2 text-sm uppercase tracking-widest text-cloth-muted">
          <AppIcon name="clock" size="sm" /> таймер
        </p>
        <p class="font-display text-5xl font-bold tabular-nums text-cloth-accent sm:text-7xl">{{ remainingLabel }}</p>
      </div>
    </header>

    <div class="mt-8 grid gap-8 xl:grid-cols-[1.2fr_0.8fr]">
      <section>
        <h2 class="flex items-center gap-2 font-display text-2xl font-bold">
          <AppIcon name="ball" class="text-cloth-accent" /> Столы
        </h2>
        <div v-if="store.mode === 'tournament'" class="mt-4 grid gap-4 md:grid-cols-2">
          <article v-for="table in store.tournament.tables" :key="table.id" class="rounded-3xl border border-white/10 bg-black/25 p-5">
            <h3 class="text-xl font-bold text-cloth-accent">{{ table.label }}</h3>
            <ul class="mt-3 space-y-2">
              <li
                v-for="player in playersAt(table.playerIds)"
                :key="player.id"
                class="flex items-center justify-between text-lg"
                :class="player.status === 'eliminated' ? 'opacity-40 line-through' : ''"
              >
                <span>{{ player.name }} <span class="text-cloth-muted">C{{ player.category }}</span></span>
                <span class="font-display text-2xl tabular-nums">{{ player.balance }}</span>
              </li>
            </ul>
          </article>
          <p v-if="!store.tournament.tables.length" class="text-cloth-muted">Рассадка ещё не задана.</p>
        </div>
        <div v-else class="mt-4 grid gap-3 sm:grid-cols-2">
          <article v-for="player in store.activePlayers" :key="player.id" class="rounded-3xl border border-white/10 bg-black/25 p-5">
            <p class="text-xl font-bold">{{ player.name }}</p>
            <p class="mt-2 font-display text-4xl tabular-nums text-cloth-accent">{{ player.balance }}</p>
          </article>
        </div>
      </section>

      <section class="space-y-6">
        <div class="rounded-3xl border border-white/10 bg-black/25 p-5">
          <h2 class="flex items-center gap-2 font-display text-2xl font-bold">
            <AppIcon name="trophy" class="text-cloth-accent" /> Лидерборд
          </h2>
          <ol class="mt-4 space-y-3">
            <li
              v-for="(player, index) in store.leaderboard"
              :key="player.id"
              class="flex items-center justify-between gap-3 border-b border-white/5 pb-2 text-xl"
            >
              <span>
                <span class="text-cloth-accent">{{ index + 1 }}.</span>
                {{ player.name }}
              </span>
              <span class="font-display text-3xl tabular-nums">{{ player.balance }}</span>
            </li>
          </ol>
        </div>

        <div class="rounded-3xl border border-white/10 bg-black/25 p-5">
          <h2 class="font-display text-2xl font-bold">Выбывшие</h2>
          <ul class="mt-3 space-y-2 text-lg text-cloth-muted">
            <li v-for="player in store.eliminatedPlayers" :key="player.id">
              {{ player.name }} · {{ player.balance }}
            </li>
            <li v-if="!store.eliminatedPlayers.length">Пока никого</li>
          </ul>
        </div>
      </section>
    </div>

    <footer class="mt-10 flex flex-wrap gap-4 text-sm text-cloth-muted">
      <NuxtLink to="/" class="hover:text-cloth-accent">← управление</NuxtLink>
      <span>только чтение · обновление из localStorage этой вкладки</span>
    </footer>
  </div>
</template>
