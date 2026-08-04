<script setup lang="ts">
import { previousPlayerId } from '~/utils/scoring'

const store = useKolkhozStore()

onMounted(() => {
  if (!store.mode) store.setMode('casual')
})

const tableIds = computed(() => store.activePlayers.map((player) => player.id))

const previousOf = (playerId: string) => {
  const prevId = previousPlayerId(tableIds.value, playerId)
  return store.players.find((player) => player.id === prevId) || null
}

const score = (playerId: string, ballId: string) => {
  store.score(store.casualTableId, playerId, ballId, tableIds.value)
}

const netDelta = (playerId: string) =>
  store.events.reduce((sum, event) => sum + (event.deltas[playerId] || 0), 0)

const orderLabel = computed(() =>
  store.activePlayers.map((player) => player.name).join(' → ')
)
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-6xl px-4 py-6">
      <div class="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p class="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-cloth-accent">
            <AppIcon name="cue" size="sm" /> Быстрый стол
          </p>
          <h2 class="mt-1 font-display text-2xl font-bold">Игровой стол</h2>
        </div>
        <div class="flex flex-wrap gap-2">
          <button type="button" class="btn-ghost inline-flex items-center gap-1.5 text-sm" :disabled="!store.events.length" @click="store.undoLast()">
            <AppIcon name="undo" size="sm" /> Отмена
          </button>
          <NuxtLink to="/casual" class="btn-ghost inline-flex items-center gap-1.5 text-sm">
            <AppIcon name="settings" size="sm" /> Настройки
          </NuxtLink>
          <NuxtLink to="/tv" class="btn-ghost inline-flex items-center gap-1.5 text-sm">
            <AppIcon name="tv" size="sm" /> Табло
          </NuxtLink>
        </div>
      </div>

      <SyncPanel class="mt-5" />
      <HistoryPanel class="mt-5" compact />

      <InfoCallout class="mt-5" title="Как считаются фишки" icon="chip">
        Игроки идут по кругу в порядке добавления:
        <span class="text-cloth-chalk">{{ orderLabel || '—' }}</span>.
        Когда игрок забивает шар, фишки списываются
        <strong class="text-cloth-chalk">только у предыдущего</strong>
        в круге (не у всех сразу). Сумма = базовая единица × коэффициент шара × фора предыдущего.
      </InfoCallout>

      <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <article
          v-for="(player, index) in store.activePlayers"
          :key="player.id"
          class="card-surface relative overflow-hidden p-4 transition hover:border-cloth-accent/40"
        >
          <div class="absolute right-3 top-3 rounded-full bg-cloth-felt/80 px-2 py-0.5 text-[10px] uppercase tracking-wider text-cloth-muted">
            #{{ index + 1 }}
          </div>
          <div class="flex items-start justify-between gap-2 pr-10">
            <div class="flex items-start gap-3">
              <PlayerAvatar :name="player.name" />
              <div>
                <h3 class="font-display text-xl font-bold">
                  {{ player.name }}
                </h3>
                <p class="mt-1 text-xs text-cloth-muted">
                  фора x{{ player.handicap }}
                  <template v-if="previousOf(player.id)">
                    · бьёт <span class="text-cloth-accent">{{ previousOf(player.id)?.name }}</span>
                  </template>
                </p>
              </div>
            </div>
            <div class="text-right">
              <p class="text-[10px] uppercase text-cloth-muted">фишки</p>
              <p class="font-display text-3xl font-bold tabular-nums text-cloth-accent">{{ player.balance }}</p>
            </div>
          </div>
          <p class="mt-1 text-xs text-cloth-muted">
            Δ сессии:
            <span :class="netDelta(player.id) >= 0 ? 'text-emerald-300' : 'text-red-300'">
              {{ netDelta(player.id) >= 0 ? '+' : '' }}{{ netDelta(player.id) }}
            </span>
          </p>

          <p class="mt-4 text-[11px] font-medium uppercase tracking-wide text-cloth-muted">Забил шар</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <button
              v-for="ball in store.casual.balls"
              :key="ball.id"
              type="button"
              class="inline-flex items-center gap-1.5 rounded-lg border border-white/15 px-3 py-2 text-xs font-semibold transition hover:border-cloth-accent hover:bg-cloth-accent/10"
              :style="{ boxShadow: `inset 0 -3px 0 ${ball.color}` }"
              @click="score(player.id, ball.id)"
            >
              <span class="h-2.5 w-2.5 rounded-full" :style="{ background: ball.color }" />
              {{ ball.label }}
              <span class="text-cloth-muted">({{ ball.multiplier }}x)</span>
            </button>
          </div>
        </article>
      </div>

      <section class="card-surface mt-6 overflow-x-auto p-4">
        <div class="flex items-center gap-2">
          <AppIcon name="info" class="text-cloth-accent" />
          <h3 class="font-display text-lg font-bold">История взаимозачёта</h3>
        </div>
        <p class="mt-1 text-xs text-cloth-muted">Кто забил, у кого списано, какой шар и сколько фишек.</p>
        <table class="mt-3 w-full min-w-[520px] text-left text-sm">
          <thead class="text-cloth-muted">
            <tr>
              <th class="py-2 pr-3">время</th>
              <th class="py-2 pr-3">забил</th>
              <th class="py-2 pr-3">у кого</th>
              <th class="py-2 pr-3">шар</th>
              <th class="py-2">перевод</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="event in [...store.events].reverse().slice(0, 30)" :key="event.id" class="border-t border-white/5">
              <td class="py-2 pr-3 text-cloth-muted">{{ new Date(event.at).toLocaleTimeString('ru-RU') }}</td>
              <td class="py-2 pr-3 font-medium">{{ store.players.find((p) => p.id === event.scorerId)?.name || event.scorerId }}</td>
              <td class="py-2 pr-3 text-cloth-accent">{{ event.note?.replace(/^vs\s+/, '') || '—' }}</td>
              <td class="py-2 pr-3">{{ store.casual.balls.find((b) => b.id === event.ballId)?.label || event.ballId }}</td>
              <td class="py-2 text-xs">
                <span v-for="(delta, pid) in event.deltas" :key="pid" class="mr-2" :class="delta >= 0 ? 'text-emerald-300' : 'text-red-300'">
                  {{ store.players.find((p) => p.id === pid)?.name }} {{ delta >= 0 ? '+' : '' }}{{ delta }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!store.events.length" class="mt-2 text-sm text-cloth-muted">Событий пока нет — нажмите шар на карточке игрока.</p>
      </section>
    </main>
  </div>
</template>
