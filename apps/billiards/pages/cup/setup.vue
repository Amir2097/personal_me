<script setup lang="ts">
import type { CupFormat } from '~/types/cup'
import { cupUid, nextPowerOfTwo } from '~/types/cup'
import { CUP_DE_MAX_PLAYERS, CUP_SE_MAX_PLAYERS } from '~/utils/cupLabels'
import { uniqueCupName } from '~/utils/cupNames'

type DraftPlayer = { id: string; name: string }

const store = useCupStore()
const history = useCupHistory()

const name = ref('Кубок клуба')
const format = ref<CupFormat>('se')
const raceTo = ref(5)
const clockEnabled = ref(false)
const shotClockSec = ref(45)
const shuffle = ref(false)
const error = ref('')
const nameHint = ref('')
const draftName = ref('')
const players = ref<DraftPlayer[]>([])

const maxPlayers = computed(() => (format.value === 'de' ? CUP_DE_MAX_PLAYERS : CUP_SE_MAX_PLAYERS))
const minPlayers = computed(() => (format.value === 'de' ? 3 : 2))
const playerCount = computed(() => players.value.length)
const bracketSize = computed(() =>
  playerCount.value ? nextPowerOfTwo(Math.max(playerCount.value, format.value === 'de' ? 4 : 2)) : 0
)
const byeCount = computed(() => (bracketSize.value ? bracketSize.value - playerCount.value : 0))

const takenNames = computed(() => {
  const active = store.tournamentList.map((item) => item.tournament.name)
  const archived = history.items.value.map((item) => item.title)
  return [...active, ...archived]
})

const suggestedName = computed(() => uniqueCupName(name.value, takenNames.value))
const nameIsTaken = computed(() => {
  const trimmed = name.value.trim()
  if (!trimmed) return false
  return suggestedName.value.toLowerCase() !== trimmed.toLowerCase()
})

onMounted(async () => {
  store.hydrate()
  await history.refresh()
  name.value = uniqueCupName('Кубок клуба', takenNames.value)
})

const addPlayer = () => {
  error.value = ''
  const value = draftName.value.trim()
  if (!value) return
  if (playerCount.value >= maxPlayers.value) {
    error.value = `Максимум ${maxPlayers.value} игроков`
    return
  }
  const exists = players.value.some((player) => player.name.toLowerCase() === value.toLowerCase())
  if (exists) {
    error.value = 'Такой игрок уже в списке'
    return
  }
  players.value.push({ id: cupUid('p'), name: value })
  draftName.value = ''
}

const removePlayer = (id: string) => {
  players.value = players.value.filter((player) => player.id !== id)
}

const movePlayer = (index: number, delta: number) => {
  const next = index + delta
  if (next < 0 || next >= players.value.length) return
  const copy = [...players.value]
  const [row] = copy.splice(index, 1)
  copy.splice(next, 0, row)
  players.value = copy
}

const start = async () => {
  error.value = ''
  nameHint.value = ''
  try {
    const finalName = uniqueCupName(name.value, takenNames.value)
    if (finalName !== name.value.trim()) {
      name.value = finalName
      nameHint.value = `Название уже было занято — сохранено как «${finalName}».`
    }
    store.configureSetup({
      name: finalName,
      format: format.value,
      raceTo: raceTo.value,
      shotClockSec: clockEnabled.value ? Math.max(10, shotClockSec.value || 45) : 0,
      playerNames: players.value.map((player) => player.name),
      shuffle: shuffle.value
    })
    await navigateTo('/cup/bracket')
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Не удалось создать турнир'
  }
}
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-6xl px-4 py-8">
      <NuxtLink to="/cup" class="btn-ghost text-sm">← К турниру</NuxtLink>

      <section class="hero-surface mt-4 rounded-2xl px-5 py-5 sm:px-6">
        <h1 class="font-display text-3xl font-bold text-cloth-chalk">Новый турнир</h1>
        <p class="mt-2 max-w-4xl text-sm leading-relaxed text-cloth-chalk/75">
          Форы нет. Если игроков не хватает до 4 / 8 / 16 / 32, свободные места получают
          <strong class="text-cloth-chalk">проход без игры</strong> в следующий раунд.
        </p>
      </section>

      <section class="card-surface mt-6 space-y-5 p-5 sm:p-6">
        <label class="block text-sm">
          <span class="text-cloth-chalk">Название</span>
          <input v-model="name" class="field-input mt-1 w-full" type="text" maxlength="80" />
          <span v-if="nameIsTaken" class="mt-1 block text-xs text-cloth-accent">
            Такое имя уже есть. Будет создано как «{{ suggestedName }}».
          </span>
          <span v-else class="mt-1 block text-xs text-cloth-muted">
            Имя должно быть уникальным среди активных и сохранённых турниров.
          </span>
        </label>

        <div class="grid gap-3 md:grid-cols-2">
          <button
            type="button"
            class="mode-option panel-surface p-4"
            :class="format === 'se' ? 'mode-option--active' : ''"
            @click="format = 'se'"
          >
            <p class="font-semibold text-cloth-chalk">Олимпийская система</p>
            <p class="mt-1 text-xs leading-relaxed text-cloth-muted">
              Одно поражение — выбывание. От 2 до {{ CUP_SE_MAX_PLAYERS }} игроков
              (50 человек → сетка на 64 с пропусками тура).
            </p>
          </button>
          <button
            type="button"
            class="mode-option panel-surface p-4"
            :class="format === 'de' ? 'mode-option--active' : ''"
            @click="format = 'de'"
          >
            <p class="font-semibold text-cloth-chalk">До двух поражений</p>
            <p class="mt-1 text-xs leading-relaxed text-cloth-muted">
              Проигравший идёт в нижнюю сетку и выбывает только со второго поражения.
              От 3 до {{ CUP_DE_MAX_PLAYERS }} игроков. Сетка по числу участников (на 4 — две встречи первого тура, без четвертьфиналов).
            </p>
          </button>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <label class="block text-sm">
            <span class="text-cloth-chalk">Сколько партий нужно выиграть</span>
            <input v-model.number="raceTo" class="field-input mt-1 w-full" type="number" min="1" max="20" />
            <span class="mt-1 block text-xs text-cloth-muted">
              Матч идёт до {{ raceTo }} {{ raceTo === 1 ? 'выигранной партии' : 'выигранных партий' }}.
            </span>
          </label>
          <div class="text-sm">
            <label class="flex items-center gap-2 text-cloth-chalk">
              <input v-model="clockEnabled" type="checkbox" class="rounded border-cloth-border" />
              Ограничивать время удара
            </label>
            <input
              v-if="clockEnabled"
              v-model.number="shotClockSec"
              class="field-input mt-2 w-full"
              type="number"
              min="10"
              max="180"
            />
            <span class="mt-1 block text-xs text-cloth-muted">
              Необязательно. Без галочки игра идёт без таймера.
            </span>
          </div>
        </div>

        <div>
          <h3 class="flex items-center gap-2 font-display text-lg font-bold text-cloth-chalk">
            <AppIcon name="users" class="text-cloth-accent" /> Участники
          </h3>
          <p class="mt-1 text-sm text-cloth-muted">
            Добавляйте по одному — как за стойкой. Порядок в списке это посев (#1 играет с последним).
          </p>

          <form class="mt-4 flex flex-col gap-2 sm:flex-row" @submit.prevent="addPlayer">
            <input
              v-model="draftName"
              class="field-input flex-1"
              type="text"
              maxlength="40"
              placeholder="Имя игрока"
              autocomplete="off"
            />
            <button type="submit" class="btn-primary inline-flex items-center justify-center gap-2">
              <AppIcon name="user" size="sm" /> Добавить
            </button>
          </form>

          <p class="mt-2 text-xs text-cloth-muted">
            Сейчас: {{ playerCount }} / {{ maxPlayers }}
            <template v-if="playerCount">
              · сетка на {{ bracketSize }}
              <template v-if="byeCount"> · {{ byeCount }} без игры</template>
              <template v-else> · без пропусков</template>
            </template>
            · минимум {{ minPlayers }}
          </p>

          <ul v-if="players.length" class="mt-4 grid gap-2 sm:grid-cols-2">
            <li v-for="(player, index) in players" :key="player.id" class="player-chip">
              <PlayerAvatar :name="player.name" />
              <div class="min-w-0 flex-1">
                <p class="truncate font-semibold text-cloth-chalk">{{ player.name }}</p>
                <p class="text-[11px] text-cloth-muted">посев #{{ index + 1 }}</p>
              </div>
              <div class="flex shrink-0 gap-1">
                <button
                  type="button"
                  class="btn-ghost px-2 py-1 text-xs"
                  :disabled="index === 0"
                  @click="movePlayer(index, -1)"
                >
                  ↑
                </button>
                <button
                  type="button"
                  class="btn-ghost px-2 py-1 text-xs"
                  :disabled="index === players.length - 1"
                  @click="movePlayer(index, 1)"
                >
                  ↓
                </button>
                <button type="button" class="btn-ghost px-2 py-1 text-xs" @click="removePlayer(player.id)">
                  ×
                </button>
              </div>
            </li>
          </ul>

          <div
            v-else
            class="mt-4 rounded-xl border border-dashed border-cloth-border px-4 py-6 text-center text-sm text-cloth-muted"
          >
            Пока никого нет. Введите имя и нажмите «Добавить» или Enter.
          </div>
        </div>

        <label class="flex items-center gap-2 text-sm text-cloth-chalk">
          <input v-model="shuffle" type="checkbox" class="rounded border-cloth-border" />
          Случайный посев
        </label>

        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
        <p v-if="nameHint" class="text-sm text-cloth-accent">{{ nameHint }}</p>

        <button type="button" class="btn-primary w-full sm:w-auto" @click="start">Создать сетку</button>
      </section>
    </main>
  </div>
</template>
