<script setup lang="ts">
const store = useKolkhozStore()

const currency = computed(() => store.casual.currencyLabel || '₽')
const endedAt = computed(() => store.casual.sessionEndedAt)

const transfers = computed(() => store.casualDebtTransfers)

const playerName = (id: string) => store.players.find((player) => player.id === id)?.name || id

const partiesPlayed = computed(
  () => store.events.filter((event) => event.kind === 'party_settle').length
)
</script>

<template>
  <section class="card-surface border-cloth-accent/40 p-5">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="text-xs uppercase tracking-[0.18em] text-cloth-accent">Итог встречи</p>
        <h3 class="mt-1 font-display text-2xl font-bold">Встреча завершена</h3>
        <p v-if="endedAt" class="mt-1 text-sm text-cloth-muted">
          {{ new Date(endedAt).toLocaleString('ru-RU') }} · партий: {{ partiesPlayed }}
        </p>
      </div>
      <button type="button" class="btn-primary text-sm" @click="store.resetCasualMeeting()">
        Новая встреча
      </button>
    </div>

    <div class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <article
        v-for="player in store.players"
        :key="player.id"
        class="rounded-xl border border-[color:var(--cloth-border)] bg-[color:var(--cloth-input)] px-4 py-3"
      >
        <p class="font-semibold">{{ player.name }}</p>
        <p
          class="mt-1 font-display text-2xl font-bold tabular-nums"
          :class="player.balance >= 0 ? 'text-emerald-300' : 'text-red-300'"
        >
          {{ player.balance >= 0 ? '+' : '' }}{{ player.balance.toLocaleString('ru-RU') }} {{ currency }}
        </p>
        <p class="mt-1 text-xs text-cloth-muted">
          <template v-if="player.balance > 0">в плюсе — ему должны</template>
          <template v-else-if="player.balance < 0">в минусе — он должен</template>
          <template v-else>в ноль</template>
        </p>
      </article>
    </div>

    <div class="mt-6">
      <h4 class="font-display text-lg font-bold">Кто кому платит</h4>
      <ul v-if="transfers.length" class="mt-3 space-y-2">
        <li
          v-for="(transfer, index) in transfers"
          :key="`${transfer.fromId}-${transfer.toId}-${index}`"
          class="rounded-lg border border-[color:var(--cloth-border)] px-3 py-2 text-sm"
        >
          <span class="font-medium text-red-300">{{ playerName(transfer.fromId) }}</span>
          →
          <span class="font-medium text-emerald-300">{{ playerName(transfer.toId) }}</span>
          :
          <strong class="text-cloth-chalk">{{ transfer.amount.toLocaleString('ru-RU') }} {{ currency }}</strong>
        </li>
      </ul>
      <p v-else class="mt-2 text-sm text-cloth-muted">Все сошлись в ноль — переводов не требуется.</p>
    </div>
  </section>
</template>
