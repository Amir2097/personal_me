<script setup lang="ts">
import type { PlayerCategory } from '~/types/kolkhoz'

const store = useKolkhozStore()
const name = ref('')
const category = ref<PlayerCategory>(2)
const handicap = ref(1)
const stack = ref(100)

onMounted(() => {
  if (!store.mode) store.setMode('casual')
})

const add = () => {
  store.addPlayer({
    name: name.value,
    category: category.value,
    handicap: handicap.value,
    startingStack: stack.value
  })
  name.value = ''
}

const canPlay = computed(() => store.activePlayers.length >= 2 && store.activePlayers.length <= 5)

const onBaseUnitChange = (event: Event) => {
  store.setCasualBaseUnit(Number((event.target as HTMLInputElement).value))
}

const onBallLabelChange = (ballId: string, event: Event) => {
  store.updateBall(ballId, { label: (event.target as HTMLInputElement).value })
}

const onBallMultiplierChange = (ballId: string, event: Event) => {
  store.updateBall(ballId, { multiplier: Number((event.target as HTMLInputElement).value) })
}

const moveUp = (index: number) => {
  if (index <= 0) return
  const list = [...store.players]
  const tmp = list[index - 1]!
  list[index - 1] = list[index]!
  list[index] = tmp
  store.$patch({ players: list })
  store.persist()
}

const moveDown = (index: number) => {
  if (index >= store.players.length - 1) return
  const list = [...store.players]
  const tmp = list[index + 1]!
  list[index + 1] = list[index]!
  list[index] = tmp
  store.$patch({ players: list })
  store.persist()
}
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-4xl px-4 py-8">
      <p class="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-cloth-accent">
        <AppIcon name="settings" size="sm" /> Настройка
      </p>
      <h2 class="mt-1 font-display text-2xl font-bold">Быстрый стол</h2>

      <InfoCallout class="mt-5" title="Порядок игроков важен" icon="users">
        Добавляйте игроков по кругу сидения. Предыдущий в списке — тот, у кого забирают фишки при забитии.
        Можно менять порядок стрелками ↑ ↓ после добавления.
      </InfoCallout>

      <section class="card-surface mt-6 p-4">
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="users" class="text-cloth-accent" /> Игроки
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">2–5 человек. Фора — множитель выплаты предыдущего.</p>

        <form class="mt-4 grid gap-3 sm:grid-cols-2" @submit.prevent="add">
          <input
            v-model="name"
            class="rounded-lg border border-white/15 bg-black/30 px-3 py-2 outline-none focus:border-cloth-accent"
            placeholder="Имя игрока"
            required
          />
          <select v-model.number="category" class="rounded-lg border border-white/15 bg-black/30 px-3 py-2">
            <option :value="1">Категория 1 (сильнее)</option>
            <option :value="2">Категория 2</option>
            <option :value="3">Категория 3</option>
          </select>
          <label class="text-sm">
            Фора (коэф.)
            <input v-model.number="handicap" type="number" min="0.1" step="0.1" class="mt-1 w-full rounded-lg border border-white/15 bg-black/30 px-3 py-2" />
          </label>
          <label class="text-sm">
            Стартовый стек
            <input v-model.number="stack" type="number" min="0" class="mt-1 w-full rounded-lg border border-white/15 bg-black/30 px-3 py-2" />
          </label>
          <button type="submit" class="btn-primary sm:col-span-2">Добавить игрока</button>
        </form>

        <ul class="mt-4 space-y-2">
          <li
            v-for="(player, index) in store.players"
            :key="player.id"
            class="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-white/10 bg-black/20 px-4 py-3"
          >
            <div>
              <span class="text-xs text-cloth-muted">#{{ index + 1 }}</span>
              <span class="ml-2 font-semibold">{{ player.name }}</span>
              <span class="ml-2 text-xs text-cloth-muted">x{{ player.handicap }} · {{ player.balance }} фишек</span>
            </div>
            <div class="flex gap-1">
              <button type="button" class="btn-ghost px-2 py-1 text-xs" title="Выше в круге" @click="moveUp(index)">↑</button>
              <button type="button" class="btn-ghost px-2 py-1 text-xs" title="Ниже в круге" @click="moveDown(index)">↓</button>
              <button type="button" class="btn-ghost px-2 py-1 text-xs" @click="store.removePlayer(player.id)">удалить</button>
            </div>
          </li>
        </ul>
      </section>

      <section class="card-surface mt-6 p-4">
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="ball" class="text-cloth-accent" /> Шары и стоимость
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">
          Множитель шара умножается на базовую единицу и фору предыдущего игрока.
          Отрицательный множитель — штраф (вы платите предыдущему).
        </p>

        <label class="mt-4 block text-sm">
          Базовая единица (фишки за 1×)
          <input
            :value="store.casual.baseUnit"
            type="number"
            min="0.1"
            step="0.5"
            class="mt-1 w-32 rounded-lg border border-white/15 bg-black/30 px-3 py-2"
            @change="onBaseUnitChange"
          />
        </label>

        <ul class="mt-4 space-y-2">
          <li v-for="ball in store.casual.balls" :key="ball.id" class="flex flex-wrap items-center gap-2 text-sm">
            <span class="h-4 w-4 rounded-full border border-white/20" :style="{ background: ball.color }" />
            <input
              :value="ball.label"
              class="min-w-[8rem] flex-1 rounded border border-white/10 bg-transparent px-2 py-1"
              @change="onBallLabelChange(ball.id, $event)"
            />
            <input
              :value="ball.multiplier"
              type="number"
              step="0.5"
              class="w-20 rounded border border-white/10 bg-transparent px-2 py-1"
              @change="onBallMultiplierChange(ball.id, $event)"
            />
          </li>
        </ul>
        <button type="button" class="btn-ghost mt-3 text-sm" @click="store.addBall()">+ добавить шар</button>
      </section>

      <div class="mt-6 flex flex-wrap gap-3">
        <NuxtLink
          to="/casual/play"
          class="btn-primary inline-flex items-center gap-2"
          :class="{ 'pointer-events-none opacity-40': !canPlay }"
        >
          <AppIcon name="play" size="sm" /> К столу
        </NuxtLink>
        <NuxtLink to="/" class="btn-ghost">Назад</NuxtLink>
      </div>
      <p v-if="!canPlay" class="mt-2 text-xs text-amber-300">Нужно от 2 до 5 активных игроков.</p>
    </main>
  </div>
</template>
