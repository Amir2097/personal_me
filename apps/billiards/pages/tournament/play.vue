<script setup lang="ts">
import { previousPlayerId } from '~/utils/scoring'
import type { Player } from '~/types/kolkhoz'

const store = useKolkhozStore()

onMounted(() => {
  if (!store.mode) store.setMode('tournament')
  if (!store.tournament.tables.length && store.activePlayers.length) {
    store.reseat()
  }
})

const playersAt = (playerIds: string[]): Player[] =>
  playerIds
    .map((id) => store.players.find((player) => player.id === id))
    .filter((player): player is Player => Boolean(player))

const activeIdsAt = (playerIds: string[]) =>
  playersAt(playerIds)
    .filter((player) => player.status === 'active')
    .map((player) => player.id)

const previousOf = (tablePlayerIds: string[], playerId: string) => {
  const prevId = previousPlayerId(activeIdsAt(tablePlayerIds), playerId)
  return store.players.find((player) => player.id === prevId) || null
}

const scoreAt = (tableId: string, playerIds: string[], scorerId: string) => {
  store.score(tableId, scorerId, 'standard', activeIdsAt(playerIds))
}

const nextRound = () => {
  store.advanceRound(store.tournament.currentRoundIndex + 1)
}

const orderLabel = (playerIds: string[]) =>
  activeIdsAt(playerIds)
    .map((id) => store.players.find((p) => p.id === id)?.name || id)
    .join(' → ')
</script>

<template>
  <div>
    <AppHeader />
    <RoundTimer />
    <main class="mx-auto max-w-6xl px-4 py-6">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p class="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-cloth-accent">
            <AppIcon name="trophy" size="sm" /> Турнир
          </p>
          <h2 class="mt-1 font-display text-2xl font-bold">Игровые столы</h2>
          <p v-if="store.currentRound" class="mt-1 text-sm text-cloth-muted">
            Тур {{ store.currentRound.number }} · тарифы
            C1={{ store.currentRound.tariffs[1] }} /
            C2={{ store.currentRound.tariffs[2] }} /
            C3={{ store.currentRound.tariffs[3] }}
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button type="button" class="btn-primary inline-flex items-center gap-1.5 text-sm" @click="store.startRoundTimer()">
            <AppIcon name="clock" size="sm" /> Таймер
          </button>
          <button
            type="button"
            class="btn-ghost text-sm"
            :disabled="store.tournament.currentRoundIndex >= store.tournament.rounds.length - 1"
            @click="nextRound"
          >
            След. тур
          </button>
          <button
            type="button"
            class="btn-ghost inline-flex items-center gap-1.5 text-sm"
            :disabled="!store.events.length"
            @click="store.undoLast()"
          >
            <AppIcon name="undo" size="sm" /> Undo
          </button>
          <NuxtLink to="/tournament" class="btn-ghost inline-flex items-center gap-1.5 text-sm">
            <AppIcon name="settings" size="sm" /> Настройки
          </NuxtLink>
          <NuxtLink to="/tv" class="btn-ghost inline-flex items-center gap-1.5 text-sm">
            <AppIcon name="tv" size="sm" /> TV
          </NuxtLink>
        </div>
      </div>

      <InfoCallout class="mt-5" title="Круг на столе" icon="chip">
        «+ Шар» забирает фишки только у предыдущего в порядке списка на этом столе.
        Сумма = тариф текущей категории того игрока. Третий игрок не затрагивается.
        Кнопка «След. тур» меняет тарифы и заново перемешивает игроков по столам.
      </InfoCallout>

      <div class="mt-6 grid gap-4 lg:grid-cols-2">
        <section v-for="table in store.tournament.tables" :key="table.id" class="card-surface p-4">
          <div class="flex items-start justify-between gap-2">
            <h3 class="flex items-center gap-2 font-display text-lg font-bold text-cloth-accent">
              <AppIcon name="ball" /> {{ table.label }}
            </h3>
          </div>
          <p class="mt-1 text-xs text-cloth-muted">Круг: {{ orderLabel(table.playerIds) || '—' }}</p>

          <div class="mt-3 space-y-3">
            <article
              v-for="(player, index) in playersAt(table.playerIds)"
              :key="player.id"
              class="rounded-xl border border-white/10 bg-black/20 p-3"
              :class="player.status === 'eliminated' ? 'opacity-40' : ''"
            >
              <div class="flex items-center justify-between gap-2">
                <div>
                  <p class="font-semibold">
                    <span class="mr-1 text-xs text-cloth-muted">#{{ index + 1 }}</span>
                    {{ player.name }}
                  </p>
                  <p class="text-xs text-cloth-muted">
                    Cat {{ player.category }}
                    <template v-if="player.status === 'active' && previousOf(table.playerIds, player.id)">
                      · бьёт
                      <span class="text-cloth-accent">{{ previousOf(table.playerIds, player.id)?.name }}</span>
                    </template>
                    <template v-else-if="player.status === 'eliminated'"> · выбыл</template>
                  </p>
                </div>
                <div class="text-right">
                  <p class="text-[10px] uppercase text-cloth-muted">фишки</p>
                  <p class="font-display text-2xl font-bold tabular-nums text-cloth-accent">{{ player.balance }}</p>
                </div>
              </div>
              <div v-if="player.status === 'active'" class="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  class="btn-primary inline-flex items-center gap-1 py-1.5 text-xs"
                  @click="scoreAt(table.id, table.playerIds, player.id)"
                >
                  <AppIcon name="ball" size="sm" /> + Шар
                </button>
                <button
                  type="button"
                  class="btn-ghost py-1.5 text-xs"
                  @click="store.dropout(table.id, player.id)"
                >
                  Выбыл
                </button>
              </div>
            </article>
          </div>
        </section>
      </div>

      <section class="card-surface mt-6 overflow-x-auto p-4">
        <div class="flex items-center gap-2">
          <AppIcon name="info" class="text-cloth-accent" />
          <h3 class="font-display text-lg font-bold">История</h3>
        </div>
        <p class="mt-1 text-xs text-cloth-muted">Кто забил и у кого списано.</p>
        <table class="mt-3 w-full min-w-[480px] text-left text-sm">
          <thead class="text-cloth-muted">
            <tr>
              <th class="py-2 pr-3">время</th>
              <th class="py-2 pr-3">забил</th>
              <th class="py-2 pr-3">у кого</th>
              <th class="py-2">перевод</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="event in [...store.events].reverse().slice(0, 25)"
              :key="event.id"
              class="border-t border-white/5"
            >
              <td class="py-2 pr-3 text-cloth-muted">{{ new Date(event.at).toLocaleTimeString('ru-RU') }}</td>
              <td class="py-2 pr-3 font-medium">
                {{ store.players.find((p) => p.id === event.scorerId)?.name || event.scorerId }}
              </td>
              <td class="py-2 pr-3 text-cloth-accent">
                {{ event.kind === 'dropout' ? 'выбывание' : event.note?.replace(/^vs\s+/, '') || '—' }}
              </td>
              <td class="py-2 text-xs">
                <span
                  v-for="(delta, pid) in event.deltas"
                  :key="pid"
                  class="mr-2"
                  :class="delta >= 0 ? 'text-emerald-300' : 'text-red-300'"
                >
                  {{ store.players.find((p) => p.id === pid)?.name }} {{ delta >= 0 ? '+' : '' }}{{ delta }}
                </span>
                <span v-if="!Object.keys(event.deltas).length" class="text-cloth-muted">—</span>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!store.events.length" class="mt-2 text-sm text-cloth-muted">Событий пока нет.</p>
      </section>

      <section class="card-surface mt-6 p-4">
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="trophy" class="text-cloth-accent" /> Лидерборд
        </h3>
        <ol class="mt-3 space-y-1 text-sm">
          <li
            v-for="(player, index) in store.leaderboard"
            :key="player.id"
            class="flex justify-between border-b border-white/5 py-1.5"
          >
            <span>{{ index + 1 }}. {{ player.name }} <span class="text-cloth-muted">C{{ player.category }}</span></span>
            <span class="tabular-nums font-semibold">{{ player.balance }}</span>
          </li>
        </ol>
      </section>
    </main>
  </div>
</template>
