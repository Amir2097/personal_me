<script setup lang="ts">
import type { CasualBallPartyRole, CasualPenaltyMode } from '~/types/kolkhoz'
import { canRemoveCasualBall } from '~/types/kolkhoz'
import { hasOpenPartyActivity } from '~/utils/casual'
import { penaltyModeLabel } from '~/utils/casualPenalties'

const store = useKolkhozStore()
const name = ref('')
const handicap = ref(0)
const stakePrice = ref<number | ''>('')

onMounted(() => {
  if (!store.mode) store.setMode('casual')
})

const partyHasActivity = computed(() =>
  Boolean(store.casual.party && hasOpenPartyActivity(store.casual.party))
)

const canDeleteBall = (ballId: string) =>
  canRemoveCasualBall(store.casual.balls, ballId, { partyHasActivity: partyHasActivity.value })

const add = () => {
  store.addPlayer({
    name: name.value,
    handicap: handicap.value,
    stakePrice: stakePrice.value === '' ? undefined : Number(stakePrice.value)
  })
  name.value = ''
  stakePrice.value = ''
}

const canPlay = computed(() => store.activePlayers.length >= 2 && store.activePlayers.length <= 5)

const onBallPriceChange = (event: Event) => {
  store.setCasualBallPrice(Number((event.target as HTMLInputElement).value))
}

const onBallLabelChange = (ballId: string, event: Event) => {
  store.updateBall(ballId, { label: (event.target as HTMLInputElement).value })
}

const onBallPriceFieldChange = (ballId: string, event: Event) => {
  store.updateBall(ballId, { price: Number((event.target as HTMLInputElement).value) })
}

const onBallRoleChange = (ballId: string, event: Event) => {
  store.updateBall(ballId, {
    partyRole: (event.target as HTMLSelectElement).value as CasualBallPartyRole
  })
}

const penaltyModes: { id: CasualPenaltyMode; title: string; text: string }[] = [
  {
    id: 'pay_all',
    title: 'Платит всем за столом',
    text: 'Провинившийся отдаёт фиксированную сумму каждому оппоненту. При личной ставке сильный игрок платит больше.'
  },
  {
    id: 'ball_from_home',
    title: 'Шар из дома',
    text: 'Игрок выставляет один забитый шар на стол (или копит долг, если ещё ничего не забил). Баланс ₽ не меняется.'
  },
  {
    id: 'pass_advantage',
    title: 'Переход хода + свободный удар',
    text: 'Без денег: следующий по кругу получает свободный удар (ball-in-hand). Отмечается на столе.'
  }
]

const selectPenaltyMode = (mode: CasualPenaltyMode) => {
  store.setCasualPenalties({ mode })
}

const togglePersonalStake = (event: Event) => {
  store.setCasualPenalties({ usePersonalStake: (event.target as HTMLInputElement).checked })
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
    <main class="page-shell page-shell--narrow py-8">
      <p class="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-cloth-accent">
        <AppIcon name="settings" size="sm" /> Настройка
      </p>
      <h2 class="mt-1 font-display text-2xl font-bold">Быстрый стол</h2>

      <InfoCallout class="mt-5" title="Порядок игроков важен" icon="users">
        Добавляйте игроков по кругу сидения. Первый в списке разбивает пирамиду.
        После каждой партии очередь сдвигается: второй становится разбивающим.
        Фора — целое число шаров, которое прибавляется к результату игрока при закрытии партии.
      </InfoCallout>

      <section class="card-surface mt-6 p-4">
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="users" class="text-cloth-accent" /> Игроки
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">2–5 человек. Группы и фишки не нужны.</p>

        <form class="mt-4 grid gap-3 sm:grid-cols-[1fr_auto_auto_auto]" @submit.prevent="add">
          <input
            v-model="name"
            class="field-input outline-none focus:border-cloth-accent"
            placeholder="Имя игрока"
            required
          />
          <label class="text-sm">
            Фора (+шар.)
            <input
              v-model.number="handicap"
              type="number"
              min="0"
              step="1"
              class="field-input mt-1 w-24"
            />
          </label>
          <label class="text-sm">
            Ставка ₽
            <input
              v-model.number="stakePrice"
              type="number"
              min="1"
              step="10"
              class="field-input mt-1 w-24"
              :placeholder="String(store.casual.ballPrice)"
            />
          </label>
          <button type="submit" class="btn-primary self-end">Добавить</button>
        </form>

        <ul class="mt-4 space-y-2">
          <li v-for="(player, index) in store.players" :key="player.id" class="player-chip">
            <PlayerAvatar :name="player.name" />
            <div class="min-w-0 flex-1">
              <p class="font-semibold">
                <span class="text-xs text-cloth-muted">#{{ index + 1 }}</span>
                {{ player.name }}
                <span v-if="index === 0" class="ml-1 text-[10px] uppercase text-cloth-accent">разбив</span>
              </p>
              <p class="text-xs text-cloth-muted">
                <template v-if="player.handicap > 0">фора +{{ player.handicap }} шар.</template>
                <template v-else>без форы</template>
                · ставка {{ (player.stakePrice || store.casual.ballPrice).toLocaleString('ru-RU') }} ₽
              </p>
            </div>
            <div class="flex gap-1">
              <button type="button" class="btn-ghost btn-play" @click="moveUp(index)">↑</button>
              <button type="button" class="btn-ghost btn-play" @click="moveDown(index)">↓</button>
              <button type="button" class="btn-ghost btn-play" @click="store.removePlayer(player.id)">
                удалить
              </button>
            </div>
          </li>
        </ul>
      </section>

      <section class="card-surface mt-6 p-4">
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="ball" class="text-cloth-accent" /> Шары и цены
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">
          Базовая ставка стола и цена каждого шара. Цветные можно удалить, если играете без них —
          «Обычный» остаётся для пирамиды из 16. Для каждого цвета выберите:
          <strong class="text-cloth-chalk">в пирамиду (16)</strong> — занимает слот раскладки;
          <strong class="text-cloth-chalk">дополнительно</strong> — сверх 16, не двигает счётчик пирамиды.
        </p>

        <label class="mt-4 block text-sm">
          Базовая ставка стола (₽ за обычный шар)
          <input
            :value="store.casual.ballPrice"
            type="number"
            min="1"
            step="10"
            class="field-input mt-1 w-36"
            @change="onBallPriceChange"
          />
        </label>

        <ul class="mt-4 space-y-2">
          <li v-for="ball in store.casual.balls" :key="ball.id" class="flex flex-wrap items-center gap-2 text-sm">
            <span class="h-4 w-4 rounded-full border border-white/20" :style="{ background: ball.color }" />
            <input
              :value="ball.label"
              class="field-input min-w-[8rem] flex-1 !px-2"
              @change="onBallLabelChange(ball.id, $event)"
            />
            <input
              :value="ball.price"
              type="number"
              step="10"
              class="field-input w-24 !px-2"
              @change="onBallPriceFieldChange(ball.id, $event)"
            />
            <span class="text-xs text-cloth-muted">₽</span>
            <select
              :value="ball.partyRole"
              class="field-input !px-2 text-sm"
              :disabled="ball.id === 'standard'"
              @change="onBallRoleChange(ball.id, $event)"
            >
              <option value="rack">в пирамиду (16)</option>
              <option value="extra">дополнительно</option>
            </select>
            <button
              v-if="canDeleteBall(ball.id)"
              type="button"
              class="btn-ghost btn-play text-red-300 hover:border-red-400/40"
              @click="store.removeBall(ball.id)"
            >
              удалить
            </button>
          </li>
        </ul>
        <button type="button" class="btn-ghost mt-3 text-sm" @click="store.addBall()">+ добавить шар</button>
      </section>

      <section class="card-surface mt-6 p-4">
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="chip" class="text-cloth-accent" /> Штрафы (фолы)
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">
          Выберите до начала игры. На столе кнопка «Фол» у провинившегося игрока.
          Сейчас: <strong class="text-cloth-chalk">{{ penaltyModeLabel(store.casual.penalties.mode) }}</strong>
        </p>

        <div class="mt-4 grid gap-3">
          <button
            v-for="mode in penaltyModes"
            :key="mode.id"
            type="button"
            class="panel-surface p-4 text-left transition"
            :class="
              store.casual.penalties.mode === mode.id
                ? 'border-cloth-accent bg-cloth-accent/10 ring-1 ring-cloth-accent/50'
                : 'hover:border-cloth-accent/40'
            "
            @click="selectPenaltyMode(mode.id)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="font-semibold text-cloth-chalk">{{ mode.title }}</p>
                <p class="mt-1 text-xs text-cloth-muted">{{ mode.text }}</p>
              </div>
              <span
                class="mt-0.5 inline-flex h-6 w-6 items-center justify-center rounded-full border"
                :class="
                  store.casual.penalties.mode === mode.id
                    ? 'border-cloth-accent bg-cloth-accent/20'
                    : 'border-white/15 bg-transparent'
                "
                aria-hidden="true"
              >
                <span
                  v-if="store.casual.penalties.mode === mode.id"
                  class="h-2.5 w-2.5 rounded-full bg-cloth-accent"
                />
              </span>
            </div>
          </button>
        </div>

        <label
          v-if="store.casual.penalties.mode === 'pay_all'"
          class="mt-4 flex items-center gap-2 text-sm"
        >
          <input
            type="checkbox"
            :checked="store.casual.penalties.usePersonalStake"
            @change="togglePersonalStake"
          />
          Личная ставка провинившегося (сильный игрок платит больше)
        </label>
      </section>

      <div class="mt-6 flex flex-wrap gap-3">
        <NuxtLink
          to="/casual/play"
          class="btn-primary inline-flex items-center gap-2"
          :class="{ 'pointer-events-none opacity-40': !canPlay }"
        >
          <AppIcon name="play" size="sm" /> К столу
        </NuxtLink>
        <NuxtLink to="/kolkhoz" class="btn-ghost">Назад</NuxtLink>
      </div>
      <p v-if="!canPlay" class="mt-2 text-xs text-amber-300">Нужно от 2 до 5 активных игроков.</p>
    </main>
  </div>
</template>
