<script setup lang="ts">
const store = useKolkhozStore()
const bank = computed(() => store.tournament.bank)
const currency = computed(() => bank.value.currencyLabel || '₽')

const money = (value: number) => `${value.toLocaleString('ru-RU')} ${currency.value}`
</script>

<template>
  <section class="card-surface p-4">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="chip" class="text-cloth-accent" /> Банк и призовые
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">
          Считаем взносы и докупы. В призовые уходит
          {{ bank.prizePercent }}% банка.
        </p>
      </div>
    </div>

    <div class="mt-4 grid gap-3 sm:grid-cols-3">
      <div class="rounded-xl border border-[color:var(--cloth-border)] bg-[color:var(--cloth-input)] p-3">
        <p class="text-[10px] uppercase tracking-wider text-cloth-muted">Общий банк</p>
        <p class="mt-1 font-display text-2xl font-bold text-cloth-accent">{{ money(store.totalBank) }}</p>
        <p class="text-xs text-cloth-muted">{{ store.tournament.buyIns.length }} операций</p>
      </div>
      <div class="rounded-xl border border-cloth-accent/40 bg-cloth-accent/10 p-3">
        <p class="text-[10px] uppercase tracking-wider text-cloth-muted">Призовые ({{ bank.prizePercent }}%)</p>
        <p class="mt-1 font-display text-2xl font-bold text-cloth-accent">{{ money(store.prizePool) }}</p>
        <p class="text-xs text-cloth-muted">на выплату местам</p>
      </div>
      <div class="rounded-xl border border-[color:var(--cloth-border)] bg-[color:var(--cloth-input)] p-3">
        <p class="text-[10px] uppercase tracking-wider text-cloth-muted">Оргвзнос / остаток</p>
        <p class="mt-1 font-display text-2xl font-bold">{{ money(store.houseCut) }}</p>
        <p class="text-xs text-cloth-muted">{{ 100 - bank.prizePercent }}% банка</p>
      </div>
    </div>

    <div v-if="store.prizeBreakdown.length" class="mt-4">
      <p class="text-xs font-semibold uppercase tracking-wider text-cloth-muted">Распределение призовых</p>
      <ul class="mt-2 flex flex-wrap gap-2">
        <li
          v-for="row in store.prizeBreakdown"
          :key="row.place"
          class="rounded-lg border border-[color:var(--cloth-border)] px-3 py-2 text-sm"
        >
          <span class="text-cloth-muted">{{ row.place }} место</span>
          <span class="ml-2 font-semibold text-cloth-accent">{{ money(row.amount) }}</span>
          <span class="ml-1 text-xs text-cloth-muted">({{ row.percent }}%)</span>
        </li>
      </ul>
    </div>

    <slot />
  </section>
</template>
