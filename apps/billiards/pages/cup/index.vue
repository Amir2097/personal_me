<script setup lang="ts">
import { cupFormatHint, cupFormatTitle, cupRaceLabel } from '~/utils/cupLabels'
import type { CupTournamentBundle } from '~/types/cup'

const store = useCupStore()
const history = useCupHistory()
const saveHint = ref('')
const saveHints = ref<Record<string, string>>({})

onMounted(() => {
  store.hydrate()
})

const statusLabel = (item: CupTournamentBundle) => {
  if (item.tournament.status === 'completed') return 'завершён'
  if (item.tournament.status === 'setup') return 'настройка'
  return 'идёт'
}

const winnerOf = (item: CupTournamentBundle) => {
  if (!item.tournament.winnerId) return null
  return item.players.find((player) => player.id === item.tournament.winnerId)?.name || null
}

const isActive = (id: string) => store.activeTournamentId === id

const openTournament = async (id: string) => {
  store.switchTournament(id)
  await navigateTo('/cup/bracket')
}

const saveTournament = async (item: CupTournamentBundle) => {
  const id = item.tournament.id
  saveHints.value[id] = ''
  store.switchTournament(id)
  await history.saveSnapshot(store.exportSnapshot())
  saveHints.value[id] = history.error.value || 'Сохранено в историю.'
}

const removeTournament = (item: CupTournamentBundle) => {
  const name = item.tournament.name || 'турнир'
  const ok = window.confirm(`Удалить «${name}» из списка активных?`)
  if (!ok) return
  store.removeTournament(item.tournament.id)
}
</script>

<template>
  <div>
    <main class="page-shell py-8">
      <NuxtLink to="/" class="btn-ghost text-sm">← На главную</NuxtLink>

      <section class="hero-surface mt-4 px-6 py-9 sm:px-10 sm:py-12">
        <p class="section-eyebrow">
          <AppIcon name="trophy" class="text-cloth-accent" />
          Классические сетки
        </p>
        <h2 class="mt-4 font-display text-4xl font-bold text-cloth-chalk sm:text-5xl lg:text-6xl">
          Турнир
        </h2>
        <p class="mt-4 max-w-3xl text-base leading-relaxed text-cloth-chalk/75">
          Несколько турниров могут идти параллельно — переключайтесь между сетками без потери прогресса.
          Олимпийская система или до двух поражений, пульт матча и табло для стола.
        </p>
      </section>

      <div class="mt-8 grid gap-5 lg:grid-cols-2">
        <NuxtLink
          to="/cup/setup"
          class="card-surface group block p-6 transition hover:border-cloth-accent/50 hover:bg-cloth-accent/5"
        >
          <p class="text-xs uppercase tracking-[0.2em] text-cloth-accent">Новый</p>
          <h3 class="mt-2 font-display text-2xl font-bold text-cloth-chalk">Создать турнир</h3>
          <p class="mt-3 text-sm text-cloth-chalk/70">
            Добавить ещё одну сетку — текущие турниры сохранятся в списке.
          </p>
          <span class="mt-6 inline-flex items-center gap-1 text-sm font-semibold text-cloth-accent group-hover:underline">
            Настроить <AppIcon name="arrow" size="sm" />
          </span>
        </NuxtLink>

        <div class="card-surface p-6">
          <p class="text-xs uppercase tracking-[0.2em] text-cloth-accent">Сводка</p>
          <h3 class="mt-2 font-display text-2xl font-bold text-cloth-chalk">
            {{ store.tournamentList.length ? store.tournamentList.length : 'Нет' }}
            {{ store.tournamentList.length === 1 ? 'турнир' : 'турниров' }}
          </h3>
          <p class="mt-2 text-sm text-cloth-muted">
            <template v-if="store.runningTournamentCount">
              {{ store.runningTournamentCount }} идут сейчас
            </template>
            <template v-else-if="store.tournamentList.length">Все завершены</template>
            <template v-else>Создайте первый турнир</template>
          </p>
          <NuxtLink to="/cup/history" class="btn-ghost mt-4 inline-flex text-sm">История</NuxtLink>
        </div>
      </div>

      <section v-if="store.tournamentList.length" class="card-surface mt-6 p-5 sm:p-6">
        <h3 class="font-display text-xl font-bold text-cloth-chalk">Активные турниры</h3>
        <p class="mt-1 text-sm text-cloth-muted">Выберите сетку для работы или удалите завершённую.</p>

        <ul class="mt-4 space-y-3">
          <li
            v-for="item in store.tournamentList"
            :key="item.tournament.id"
            class="panel-surface p-4"
            :class="isActive(item.tournament.id) ? 'ring-1 ring-cloth-accent/40' : ''"
          >
            <div class="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <h4 class="font-display text-lg font-bold text-cloth-chalk">
                    {{ item.tournament.name || 'Без названия' }}
                  </h4>
                  <span
                    v-if="isActive(item.tournament.id)"
                    class="rounded-full bg-cloth-accent/15 px-2 py-0.5 text-xs font-semibold text-cloth-accent"
                  >
                    выбран
                  </span>
                </div>
                <p class="mt-1 text-sm text-cloth-muted">
                  {{ cupFormatTitle(item.tournament.format) }} · {{ cupRaceLabel(item.tournament.raceTo) }} ·
                  {{ statusLabel(item) }} · {{ item.players.length }} игроков
                </p>
                <p class="mt-1 text-xs text-cloth-muted">{{ cupFormatHint(item.tournament.format) }}</p>
                <p v-if="winnerOf(item)" class="mt-1 text-sm text-cloth-accent">
                  Победитель: {{ winnerOf(item) }}
                </p>
              </div>

              <div class="flex flex-wrap gap-2">
                <button type="button" class="btn-primary text-sm" @click="openTournament(item.tournament.id)">
                  {{ isActive(item.tournament.id) ? 'Сетка' : 'Открыть' }}
                </button>
                <button
                  type="button"
                  class="btn-ghost text-sm"
                  :disabled="history.saving.value"
                  @click="saveTournament(item)"
                >
                  В историю
                </button>
                <button type="button" class="btn-ghost text-sm" @click="removeTournament(item)">
                  Удалить
                </button>
              </div>
            </div>
            <p v-if="saveHints[item.tournament.id]" class="mt-2 text-xs text-cloth-muted">
              {{ saveHints[item.tournament.id] }}
            </p>
          </li>
        </ul>
      </section>

      <section v-else class="card-surface mt-6 p-5">
        <h3 class="font-display text-lg font-bold text-cloth-chalk">Пока нет турниров</h3>
        <p class="mt-2 text-sm text-cloth-muted">Создайте первый или откройте сохранённый из истории.</p>
        <NuxtLink to="/cup/setup" class="btn-primary mt-4 inline-flex text-sm">Создать турнир</NuxtLink>
      </section>
    </main>
  </div>
</template>
