<script setup lang="ts">
import { cupFormatTitle, cupRaceLabel } from '~/utils/cupLabels'
import type { CupTournamentBundle } from '~/types/cup'

const props = defineProps<{
  compact?: boolean
}>()

const store = useCupStore()

const statusLabel = (item: CupTournamentBundle) => {
  if (item.tournament.status === 'completed') return 'завершён'
  if (item.tournament.status === 'setup') return 'настройка'
  return 'идёт'
}

const winnerOf = (item: CupTournamentBundle) => {
  if (!item.tournament.winnerId) return null
  return item.players.find((player) => player.id === item.tournament.winnerId)?.name || null
}

const switchTo = async (id: string) => {
  store.switchTournament(id)
  if (!props.compact) return
  await navigateTo('/cup/bracket')
}
</script>

<template>
  <div v-if="store.tournamentList.length > 1" class="cup-tournament-switcher">
    <p class="cup-tournament-switcher__label">
      {{ compact ? 'Турнир' : 'Параллельные турниры' }}
      <span v-if="store.runningTournamentCount > 1" class="text-cloth-accent">
        · {{ store.runningTournamentCount }} идут
      </span>
    </p>
    <div class="cup-tournament-switcher__list">
      <button
        v-for="item in store.tournamentList"
        :key="item.tournament.id"
        type="button"
        class="cup-tournament-switcher__item"
        :class="
          item.tournament.id === store.activeTournamentId
            ? 'cup-tournament-switcher__item--active'
            : ''
        "
        @click="switchTo(item.tournament.id)"
      >
        <span class="font-semibold text-cloth-chalk">{{ item.tournament.name || 'Без названия' }}</span>
        <span class="text-xs text-cloth-muted">
          {{ cupFormatTitle(item.tournament.format) }} · {{ cupRaceLabel(item.tournament.raceTo) }} ·
          {{ statusLabel(item) }}
          <template v-if="winnerOf(item)"> · {{ winnerOf(item) }}</template>
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.cup-tournament-switcher__label {
  margin: 0 0 0.5rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--cloth-muted) 90%, transparent);
}

.cup-tournament-switcher__list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.cup-tournament-switcher__item {
  display: flex;
  flex-direction: column;
  gap: 0.12rem;
  min-width: 10rem;
  max-width: 100%;
  padding: 0.55rem 0.7rem;
  text-align: left;
  border-radius: 0.75rem;
  border: 1px solid var(--cloth-border);
  background: var(--cloth-input);
  transition:
    border-color 0.15s ease,
    background-color 0.15s ease;
}

.cup-tournament-switcher__item:hover {
  border-color: color-mix(in srgb, var(--cloth-accent) 45%, transparent);
}

.cup-tournament-switcher__item--active {
  border-color: color-mix(in srgb, var(--cloth-accent) 70%, transparent);
  background: color-mix(in srgb, var(--cloth-accent) 12%, var(--cloth-input));
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--cloth-accent) 25%, transparent);
}
</style>
