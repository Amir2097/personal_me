<script setup lang="ts">
import type { Player, PlayerCategory, TournamentKind } from '~/types/kolkhoz'
import { groupHint, groupLabel, statusLabel } from '~/utils/labels'

const store = useKolkhozStore()
const name = ref('')
const category = ref<PlayerCategory>(2)
const stack = ref(20)
const entryMoney = ref(500)
const categories = [1, 2, 3] as const

onMounted(() => {
  if (!store.mode) store.setMode('tournament')
  store.ensureTables()
  syncEntryDefaults()
})

const isOrganizer = computed(() => store.tournament.kind === 'organizer')

const syncEntryDefaults = () => {
  const bank = store.tournament.bank
  stack.value = bank.rebuyPreset.chips
  entryMoney.value = bank.rebuyPreset.money
}

const setKind = (kind: TournamentKind) => {
  store.setTournamentKind(kind)
  syncEntryDefaults()
}

const add = () => {
  store.addPlayer({
    name: name.value,
    category: category.value,
    entryChips: stack.value,
    entryMoney: entryMoney.value
  })
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

const onTableNumberChange = (tableId: string, event: Event) => {
  store.setTableNumber(tableId, Number((event.target as HTMLInputElement).value))
}

const startPlay = () => {
  store.ensureTables()
  if (!store.tournament.tables.some((t) => t.playerIds.length) && store.activePlayers.length >= 2) {
    store.reseat()
  }
  navigateTo('/tournament/play')
}
</script>

<template>
  <div>
    <main class="page-shell py-8">
      <p class="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-cloth-accent">
        <AppIcon name="trophy" size="sm" /> Турнир
      </p>
      <h2 class="mt-1 font-display text-2xl font-bold">Настройка</h2>

      <section class="mt-5 grid gap-3 sm:grid-cols-2">
        <button
          type="button"
          class="panel-surface mode-option p-4"
          :class="{ 'mode-option--active': !isOrganizer }"
          @click="setKind('detailed')"
        >
          <p class="flex items-center gap-2 font-semibold">
            <AppIcon name="chip" class="text-cloth-accent" /> Подробная игра
          </p>
          <p class="mt-1 text-xs text-cloth-muted">Скоринг шаров, банк, взносы и призовые.</p>
          <span v-if="!isOrganizer" class="mode-option__badge">Выбрано</span>
        </button>
        <button
          type="button"
          class="panel-surface mode-option p-4"
          :class="{ 'mode-option--active': isOrganizer }"
          @click="setKind('organizer')"
        >
          <p class="flex items-center gap-2 font-semibold">
            <AppIcon name="clipboard" class="text-cloth-accent" /> Организаторская
          </p>
          <p class="mt-1 text-xs text-cloth-muted">Рассадка, туры, таймер, банк — без кнопок шаров.</p>
          <span v-if="isOrganizer" class="mode-option__badge">Выбрано</span>
        </button>
      </section>

      <InfoCallout v-if="!isOrganizer" class="mt-5" title="Как работает выплата" icon="chip">
        На каждом столе порядок игроков в списке — круг сидения.
        Забил шар → фишки только у <strong class="text-cloth-chalk">предыдущего</strong> в круге.
        Сумма = тариф тура по группе того, у кого забирают.
        Взносы и докупы идут в банк; призовые — процент от банка (обычно 80%).
      </InfoCallout>
      <InfoCallout v-else class="mt-5" title="Пульт организатора" icon="clipboard">
        Соберите игроков и столы, задайте длительность туров. При добавлении игрока сразу
        учитывается взнос в банк. Докупы и доны можно писать на пульте. Призовые — обычно 80% банка.
      </InfoCallout>

      <section class="mt-6">
        <BankPanel>
          <div class="mt-5 grid gap-3 border-t border-[color:var(--cloth-border)] pt-4 sm:grid-cols-2 lg:grid-cols-3">
            <label class="text-xs text-cloth-muted">
              % призовых
              <input
                :value="store.tournament.bank.prizePercent"
                type="number"
                min="0"
                max="100"
                class="field-input mt-1 w-full"
                @change="store.updateBank({ prizePercent: Number(($event.target as HTMLInputElement).value) })"
              />
            </label>
            <label class="text-xs text-cloth-muted">
              Докуп: ₽ / фишки
              <span class="mt-1 flex gap-1">
                <input
                  :value="store.tournament.bank.rebuyPreset.money"
                  type="number"
                  min="0"
                  class="field-input w-full"
                  @change="store.updateBank({ rebuyPreset: { money: Number(($event.target as HTMLInputElement).value), chips: store.tournament.bank.rebuyPreset.chips } }); syncEntryDefaults()"
                />
                <input
                  :value="store.tournament.bank.rebuyPreset.chips"
                  type="number"
                  min="0"
                  class="field-input w-full"
                  @change="store.updateBank({ rebuyPreset: { money: store.tournament.bank.rebuyPreset.money, chips: Number(($event.target as HTMLInputElement).value) } }); syncEntryDefaults()"
                />
              </span>
            </label>
            <label class="text-xs text-cloth-muted">
              Дон: ₽ / фишки
              <span class="mt-1 flex gap-1">
                <input
                  :value="store.tournament.bank.addonPreset.money"
                  type="number"
                  min="0"
                  class="field-input w-full"
                  @change="store.updateBank({ addonPreset: { money: Number(($event.target as HTMLInputElement).value), chips: store.tournament.bank.addonPreset.chips } })"
                />
                <input
                  :value="store.tournament.bank.addonPreset.chips"
                  type="number"
                  min="0"
                  class="field-input w-full"
                  @change="store.updateBank({ addonPreset: { money: store.tournament.bank.addonPreset.money, chips: Number(($event.target as HTMLInputElement).value) } })"
                />
              </span>
            </label>
          </div>
          <div class="mt-3 flex flex-wrap gap-3">
            <label
              v-for="place in store.tournament.bank.prizePlaces"
              :key="place.place"
              class="text-xs text-cloth-muted"
            >
              {{ place.place }} место, %
              <input
                :value="place.percent"
                type="number"
                min="0"
                max="100"
                class="field-input mt-1 w-20"
                @change="store.setPrizePlace(place.place, Number(($event.target as HTMLInputElement).value))"
              />
            </label>
          </div>
        </BankPanel>
      </section>

      <section class="card-surface mt-6 p-4">
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="users" class="text-cloth-accent" /> Игроки
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">
          {{
            isOrganizer
              ? 'Группа и фишки — для разметки тура. Докупы и доны можно писать прямо здесь.'
              : 'Группа влияет на тариф при забитии. Докупы и доны идут в банк.'
          }}
        </p>

        <form class="mt-4 grid gap-3 sm:grid-cols-4" @submit.prevent="add">
          <input v-model="name" class="field-input sm:col-span-2" placeholder="Имя" required />
          <select v-model.number="category" class="field-input">
            <option :value="1">Группа 1 (сильнее)</option>
            <option :value="2">Группа 2</option>
            <option :value="3">Группа 3</option>
          </select>
          <input
            v-model.number="stack"
            type="number"
            min="0"
            class="field-input"
            title="Фишки за взнос"
            placeholder="Фишки"
          />
          <input
            v-model.number="entryMoney"
            type="number"
            min="0"
            class="field-input sm:col-span-2"
            placeholder="Докуп, ₽"
            title="Стартовый докуп в банк"
          />
          <button
            type="submit"
            class="btn-primary inline-flex items-center justify-center gap-2 sm:col-span-2"
          >
            <AppIcon name="users" size="sm" /> Добавить
          </button>
        </form>

        <ul class="mt-4 grid gap-2 sm:grid-cols-2">
          <li
            v-for="player in store.players"
            :key="player.id"
            class="player-chip !items-start"
          >
            <PlayerAvatar :name="player.name" />
            <div class="min-w-0 flex-1">
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <p class="truncate font-semibold">{{ player.name }}</p>
                  <p class="text-[10px] text-cloth-muted">
                    {{ player.balance }} фишек · {{ statusLabel(player.status) }}
                    · внёс {{ store.playerPaidAmount(player.id).toLocaleString('ru-RU') }} ₽
                  </p>
                </div>
                <button type="button" class="btn-ghost btn-play shrink-0" @click="store.removePlayer(player.id)">
                  ×
                </button>
              </div>
              <div class="mt-1 flex flex-wrap gap-1">
                <button
                  v-for="cat in categories"
                  :key="cat"
                  type="button"
                  class="btn-chip"
                  :class="
                    player.category === cat
                      ? 'btn-chip--active'
                      : ''
                  "
                  :title="groupHint(cat)"
                  @click="setCategory(player.id, cat)"
                >
                  {{ groupLabel(cat, true) }}
                </button>
              </div>
              <PlayerBuyIn :player-id="player.id" />
            </div>
          </li>
        </ul>
      </section>

      <section class="card-surface mt-6 p-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="flex items-center gap-2 font-display text-lg font-bold">
              <AppIcon name="clock" class="text-cloth-accent" /> Туры и
              {{ isOrganizer ? 'разметка фишек' : 'тарифы' }}
            </h3>
            <p class="mt-1 text-xs text-cloth-muted">
              {{
                isOrganizer
                  ? 'Группа N — ориентир фишек/ставки для этой группы на туре.'
                  : 'Тариф группы N — сколько забирают у игрока этой группы при забитии.'
              }}
            </p>
          </div>
          <button type="button" class="btn-ghost text-sm" @click="store.addRound()">+ тур</button>
        </div>
        <div class="mt-4 space-y-3">
          <div
            v-for="(round, index) in store.tournament.rounds"
            :key="round.number"
            class="rounded-xl border border-[color:var(--cloth-border)] p-3"
            :class="index === store.tournament.currentRoundIndex ? 'border-cloth-accent/50 bg-cloth-accent/5' : ''"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <button type="button" class="text-left font-semibold" @click="store.setCurrentRound(index)">
                Тур {{ round.number }}
                <span v-if="index === store.tournament.currentRoundIndex" class="text-xs text-cloth-accent">· текущий</span>
              </button>
              <label class="text-xs text-cloth-muted">
                мин
                <input
                  :value="round.durationMinutes"
                  type="number"
                  min="1"
                  class="field-input ml-2 w-16 py-1"
                  @change="onDurationChange(index, $event)"
                />
              </label>
            </div>
            <div class="mt-2 flex flex-wrap gap-3 text-sm">
              <label v-for="cat in categories" :key="cat" class="text-xs">
                {{ groupLabel(cat, true) }}
                <input
                  :value="tariffValue(index, cat)"
                  type="number"
                  min="0"
                  class="field-input ml-1 w-14 py-1"
                  @change="onTariffChange(index, cat, $event)"
                />
              </label>
            </div>
          </div>
        </div>
      </section>

      <section class="card-surface mt-6 p-4">
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="ball" class="text-cloth-accent" /> Столы и жеребьёвка
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">
          Сначала задайте <strong class="text-cloth-chalk">сколько столов</strong> и их
          <strong class="text-cloth-chalk">номера в зале</strong> (№3, №7…). Потом нажмите «Рассадить игроков».
        </p>

        <div class="mt-4 flex flex-wrap items-end gap-3">
          <label class="text-sm">
            Кол-во столов
            <input
              :value="store.tournament.tableCount"
              type="number"
              min="1"
              max="12"
              class="field-input mt-1 w-24"
              @change="onTableCountChange"
            />
          </label>
          <button
            type="button"
            class="btn-primary"
            :disabled="store.activePlayers.length < 2"
            @click="store.reseat()"
          >
            Рассадить игроков
          </button>
        </div>

        <div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="(table, slot) in store.tournament.tables"
            :key="table.id"
            class="rounded-xl border border-[color:var(--cloth-border)] bg-[color:var(--cloth-input)] p-3"
          >
            <p class="text-[10px] uppercase tracking-wider text-cloth-muted">Слот {{ slot + 1 }}</p>
            <label class="mt-1 block text-sm font-semibold text-cloth-accent">
              № стола в зале
              <input
                :value="table.number"
                type="number"
                min="1"
                max="99"
                class="field-input mt-1 w-full"
                @change="onTableNumberChange(table.id, $event)"
              />
            </label>
            <p class="mt-2 text-xs text-cloth-muted">Будет: {{ table.label }}</p>
          </div>
        </div>

        <div
          v-if="store.tournament.tables.some((t) => t.playerIds.length)"
          class="mt-5 grid gap-3 md:grid-cols-2"
        >
          <div
            v-for="table in store.tournament.tables"
            :key="`seat-${table.id}`"
            class="rounded-xl border border-[color:var(--cloth-border)] p-3"
          >
            <h4 class="font-semibold text-cloth-accent">{{ table.label }}</h4>
            <ul class="mt-2 space-y-2 text-sm">
              <li
                v-for="(player, index) in playersAt(table.id)"
                :key="player.id"
                class="flex items-center justify-between gap-2"
              >
                <span class="inline-flex min-w-0 items-center gap-2">
                  <PlayerAvatar :name="player.name" size="sm" />
                  <span class="truncate">
                    <span class="text-cloth-muted">#{{ index + 1 }}</span>
                    {{ player.name }}
                    <span class="text-cloth-muted">{{ groupLabel(player.category, true) }}</span>
                  </span>
                </span>
                <select
                  class="field-input min-w-[7rem] !px-2 text-sm"
                  :value="table.id"
                  @change="onMovePlayer(player.id, $event)"
                >
                  <option v-for="t in store.tournament.tables" :key="t.id" :value="t.id">{{ t.label }}</option>
                </select>
              </li>
              <li v-if="!playersAt(table.id).length" class="text-xs text-cloth-muted">Пока пусто — нажмите «Рассадить игроков»</li>
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
          <AppIcon name="play" size="sm" />
          {{ isOrganizer ? 'К пульту' : 'К игре' }}
        </button>
        <NuxtLink to="/kolkhoz" class="btn-ghost">Назад</NuxtLink>
      </div>
    </main>
  </div>
</template>
