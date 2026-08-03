<script setup lang="ts">
import type { Player, PlayerCategory } from '~/types/kolkhoz'

const store = useKolkhozStore()
const name = ref('')
const category = ref<PlayerCategory>(2)
const stack = ref(100)
const categories = [1, 2, 3] as const

onMounted(() => {
  if (!store.mode) store.setMode('tournament')
})

const add = () => {
  store.addPlayer({ name: name.value, category: category.value, startingStack: stack.value })
  name.value = ''
}

const playersAt = (tableId: string): Player[] => {
  const table = store.tournament.tables.find((item) => item.id === tableId)
  if (!table) return []
  return table.playerIds
    .map((id) => store.players.find((player) => player.id === id))
    .filter((player): player is Player => Boolean(player))
}

const setCategory = (playerId: string, cat: number) => {
  store.updatePlayer(playerId, { category: cat as PlayerCategory })
}

const onDurationChange = (index: number, event: Event) => {
  const value = Number((event.target as HTMLInputElement).value)
  store.updateRound(index, { durationMinutes: value })
}

const tariffValue = (roundIndex: number, cat: number) => {
  const round = store.tournament.rounds[roundIndex]
  if (!round) return 0
  return round.tariffs[cat as PlayerCategory] ?? 0
}

const onTariffChange = (index: number, cat: number, event: Event) => {
  const round = store.tournament.rounds[index]
  if (!round) return
  const value = Number((event.target as HTMLInputElement).value)
  store.updateRound(index, {
    tariffs: {
      ...round.tariffs,
      [cat as PlayerCategory]: value
    }
  })
}

const onTableCountChange = (event: Event) => {
  store.setTableCount(Number((event.target as HTMLInputElement).value))
}

const onMovePlayer = (playerId: string, event: Event) => {
  store.movePlayer(playerId, (event.target as HTMLSelectElement).value)
}

const startPlay = () => {
  if (!store.tournament.tables.length) store.reseat()
  navigateTo('/tournament/play')
}
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-6xl px-4 py-8">
      <p class="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-cloth-accent">
        <AppIcon name="trophy" size="sm" /> Турнир
      </p>
      <h2 class="mt-1 font-display text-2xl font-bold">Настройка</h2>

      <InfoCallout class="mt-5" title="Как работает выплата" icon="chip">
        На каждом столе порядок игроков в списке — круг сидения.
        Забил шар → фишки только у <strong class="text-cloth-chalk">предыдущего</strong> в круге.
        Сумма = тариф тура по категории того, у кого забирают (не у всех сразу).
      </InfoCallout>

      <section class="card-surface mt-6 p-4">
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="users" class="text-cloth-accent" /> Игроки
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">Категория влияет на тариф, когда у игрока забирают фишки.</p>

        <form class="mt-4 grid gap-3 sm:grid-cols-4" @submit.prevent="add">
          <input
            v-model="name"
            class="rounded-lg border border-white/15 bg-black/30 px-3 py-2 sm:col-span-2"
            placeholder="Имя"
            required
          />
          <select v-model.number="category" class="rounded-lg border border-white/15 bg-black/30 px-3 py-2">
            <option :value="1">Cat 1 (сильнее)</option>
            <option :value="2">Cat 2</option>
            <option :value="3">Cat 3</option>
          </select>
          <input
            v-model.number="stack"
            type="number"
            min="0"
            class="rounded-lg border border-white/15 bg-black/30 px-3 py-2"
            title="Стартовый стек"
          />
          <button type="submit" class="btn-primary sm:col-span-4 inline-flex items-center justify-center gap-2">
            <AppIcon name="users" size="sm" /> Добавить
          </button>
        </form>

        <ul class="mt-4 grid gap-2 sm:grid-cols-2">
          <li
            v-for="player in store.players"
            :key="player.id"
            class="flex items-center justify-between gap-2 rounded-xl border border-white/10 bg-black/20 px-4 py-3"
          >
            <div class="min-w-0">
              <p class="truncate font-semibold">{{ player.name }}</p>
              <p class="text-[10px] text-cloth-muted">{{ player.balance }} фишек</p>
              <div class="mt-1 flex gap-1">
                <button
                  v-for="cat in categories"
                  :key="cat"
                  type="button"
                  class="rounded px-2 py-0.5 text-xs"
                  :class="player.category === cat ? 'bg-cloth-accent text-cloth-deep' : 'border border-white/15'"
                  @click="setCategory(player.id, cat)"
                >
                  C{{ cat }}
                </button>
              </div>
            </div>
            <button type="button" class="btn-ghost py-1 text-xs" @click="store.removePlayer(player.id)">×</button>
          </li>
        </ul>
      </section>

      <section class="card-surface mt-6 p-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="flex items-center gap-2 font-display text-lg font-bold">
              <AppIcon name="clock" class="text-cloth-accent" /> Туры и тарифы
            </h3>
            <p class="mt-1 text-xs text-cloth-muted">
              Тариф Cat N — сколько забирают у игрока категории N при забитии шара.
            </p>
          </div>
          <button type="button" class="btn-ghost text-sm" @click="store.addRound()">+ тур</button>
        </div>
        <div class="mt-4 space-y-3">
          <div
            v-for="(round, index) in store.tournament.rounds"
            :key="round.number"
            class="rounded-xl border border-white/10 p-3"
            :class="index === store.tournament.currentRoundIndex ? 'border-cloth-accent/50 bg-cloth-accent/5' : ''"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <button type="button" class="text-left font-semibold" @click="store.advanceRound(index)">
                Тур {{ round.number }}
                <span v-if="index === store.tournament.currentRoundIndex" class="text-xs text-cloth-accent">· текущий</span>
              </button>
              <label class="text-xs text-cloth-muted">
                мин
                <input
                  :value="round.durationMinutes"
                  type="number"
                  min="1"
                  class="ml-2 w-16 rounded border border-white/15 bg-transparent px-2 py-1"
                  @change="onDurationChange(index, $event)"
                />
              </label>
            </div>
            <div class="mt-2 flex flex-wrap gap-3 text-sm">
              <label v-for="cat in categories" :key="cat" class="text-xs">
                Cat {{ cat }}
                <input
                  :value="tariffValue(index, cat)"
                  type="number"
                  min="0"
                  class="ml-1 w-14 rounded border border-white/15 bg-transparent px-2 py-1"
                  @change="onTariffChange(index, cat, $event)"
                />
              </label>
            </div>
          </div>
        </div>
      </section>

      <section class="card-surface mt-6 p-4">
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="ball" class="text-cloth-accent" /> Столы и рассадка
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">
          Порядок в списке стола = круг. Первый бьёт последнего, второй — первого и т.д.
        </p>
        <div class="mt-4 flex flex-wrap items-end gap-3">
          <label class="text-sm">
            Столов
            <input
              :value="store.tournament.tableCount"
              type="number"
              min="1"
              max="12"
              class="mt-1 w-24 rounded-lg border border-white/15 bg-black/30 px-3 py-2"
              @change="onTableCountChange"
            />
          </label>
          <button type="button" class="btn-primary" @click="store.reseat()">Сгенерировать рассадку</button>
        </div>

        <div v-if="store.tournament.tables.length" class="mt-4 grid gap-3 md:grid-cols-2">
          <div v-for="table in store.tournament.tables" :key="table.id" class="rounded-xl border border-white/10 p-3">
            <h4 class="font-semibold text-cloth-accent">{{ table.label }}</h4>
            <ul class="mt-2 space-y-1 text-sm">
              <li
                v-for="(player, index) in playersAt(table.id)"
                :key="player.id"
                class="flex items-center justify-between gap-2"
              >
                <span>
                  <span class="text-cloth-muted">#{{ index + 1 }}</span>
                  {{ player.name }}
                  <span class="text-cloth-muted">C{{ player.category }}</span>
                </span>
                <select
                  class="rounded border border-white/15 bg-black/40 px-2 py-1 text-xs"
                  :value="table.id"
                  @change="onMovePlayer(player.id, $event)"
                >
                  <option v-for="t in store.tournament.tables" :key="t.id" :value="t.id">{{ t.label }}</option>
                </select>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <div class="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          class="btn-primary inline-flex items-center gap-2"
          :disabled="store.activePlayers.length < 2"
          @click="startPlay"
        >
          <AppIcon name="play" size="sm" /> К игре
        </button>
        <NuxtLink to="/" class="btn-ghost">Назад</NuxtLink>
      </div>
    </main>
  </div>
</template>
