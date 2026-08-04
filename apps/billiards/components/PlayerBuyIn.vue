<script setup lang="ts">
import type { BuyInKind } from '~/types/kolkhoz'
import { buyInKindLabel, buyInsForPlayer } from '~/utils/bank'

const props = withDefaults(
  defineProps<{
    playerId: string
    /** How many history rows to show. */
    historyLimit?: number
  }>(),
  { historyLimit: 5 }
)

const store = useKolkhozStore()
const bank = computed(() => store.tournament.bank)
const currency = computed(() => bank.value.currencyLabel || '₽')

const formOpen = ref(false)
const kind = ref<BuyInKind>('rebuy')
const money = ref(bank.value.rebuyPreset.money)
const chips = ref(bank.value.rebuyPreset.chips)

const paid = computed(() => store.playerPaidAmount(props.playerId))
const history = computed(() =>
  buyInsForPlayer(store.tournament.buyIns, props.playerId).slice().reverse()
)

const presetFor = (next: BuyInKind) => {
  if (next === 'addon') return bank.value.addonPreset
  // entry and rebuy share the same practical meaning in UI — use rebuy preset.
  return bank.value.rebuyPreset
}

/** Open editor with preset defaults — user can change money/chips before saving. */
const openForm = (next: BuyInKind) => {
  kind.value = next
  const preset = presetFor(next)
  money.value = preset.money
  chips.value = preset.chips
  formOpen.value = true
}

const submit = () => {
  store.recordBuyIn({
    playerId: props.playerId,
    kind: kind.value,
    money: money.value,
    chips: chips.value,
    note: buyInKindLabel(kind.value)
  })
  formOpen.value = false
}
</script>

<template>
  <div class="mt-2 space-y-2">
    <p class="text-xs text-cloth-muted">
      Внёс:
      <span class="font-semibold text-cloth-accent">{{ paid.toLocaleString('ru-RU') }} {{ currency }}</span>
    </p>
    <div class="flex flex-wrap gap-1.5">
      <button type="button" class="btn-ghost py-1 text-[11px]" @click="openForm('rebuy')">
        + Докуп
      </button>
      <button type="button" class="btn-ghost py-1 text-[11px]" @click="openForm('addon')">
        + Дон
      </button>
    </div>

    <div v-if="formOpen" class="rounded-lg border border-[color:var(--cloth-border)] bg-[color:var(--cloth-input)] p-2">
      <p class="text-[11px] font-semibold text-cloth-accent">{{ buyInKindLabel(kind) }}</p>
      <p class="mt-0.5 text-[10px] text-cloth-muted">
        Значения из пресета — поменяйте сумму или фишки перед записью.
      </p>
      <div class="mt-2 grid grid-cols-2 gap-2">
        <label class="text-[11px] text-cloth-muted">
          Сумма, {{ currency }}
          <input v-model.number="money" type="number" min="0" class="field-input mt-0.5 w-full py-1" />
        </label>
        <label class="text-[11px] text-cloth-muted">
          Фишки
          <input v-model.number="chips" type="number" min="0" class="field-input mt-0.5 w-full py-1" />
        </label>
      </div>
      <div class="mt-2 flex gap-2">
        <button type="button" class="btn-primary flex-1 py-1 text-xs" @click="submit">Записать</button>
        <button type="button" class="btn-ghost py-1 text-xs" @click="formOpen = false">Отмена</button>
      </div>
    </div>

    <ul v-if="history.length" class="space-y-1 text-[11px] text-cloth-muted">
      <li
        v-for="item in history.slice(0, historyLimit)"
        :key="item.id"
        class="flex items-start gap-2"
      >
        <span class="min-w-0 flex-1">
          {{ buyInKindLabel(item.kind) }} · {{ item.money }} {{ currency }} / {{ item.chips }} фиш.
          <span v-if="item.roundNumber">· тур {{ item.roundNumber }}</span>
        </span>
        <button
          type="button"
          class="shrink-0 px-1 text-red-500 hover:underline"
          title="Удалить запись"
          @click="store.removeBuyIn(item.id)"
        >
          ×
        </button>
      </li>
    </ul>
  </div>
</template>
