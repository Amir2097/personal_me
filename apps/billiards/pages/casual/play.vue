<script setup lang="ts">
import {
  CASUAL_PARTY_BALL_COUNT,
  CASUAL_PARTY_TARGET_POINTS,
  casualHandicapBalls,
  isLastBall,
  isRackComplete,
  nextBallIndex,
  playerExtraPoints,
  playerRackPoints
} from '~/utils/casual'
import { penaltyModeLabel } from '~/utils/casualPenalties'
import { previousPlayerId } from '~/utils/scoring'

const store = useKolkhozStore()

onMounted(() => {
  if (!store.mode) store.setMode('casual')
})

const tableIds = computed(() => store.activePlayers.map((player) => player.id))

const party = computed(() => store.casual.party)
const rackTotal = computed(() => store.casualRackTotal)
const partyTotal = computed(() => store.casualPartyTotal)
const nextBall = computed(() => (party.value ? nextBallIndex(party.value) : 1))
const nextBallDouble = computed(() => isLastBall(nextBall.value))
const rackComplete = computed(() => (party.value ? isRackComplete(party.value) : false))
const targetNorm = computed(() => store.casualPartyNorm)
const currency = computed(() => store.casual.currencyLabel || '₽')
const sessionEnded = computed(() => store.casualSessionEnded)
const endBusy = ref(false)

const previousOf = (playerId: string) => {
  const prevId = previousPlayerId(tableIds.value, playerId)
  return store.players.find((player) => player.id === prevId) || null
}

const potBall = (playerId: string, ballId: string) => {
  store.potCasualBall(playerId, ballId, tableIds.value)
}

const applyFoul = (playerId: string) => {
  store.applyCasualFoul(playerId, tableIds.value)
}

const ballDebt = (playerId: string) => party.value?.ballDebtByPlayer?.[playerId] || 0

const settleParty = () => {
  if (!party.value || partyTotal.value <= 0) return
  store.settleCasualParty(tableIds.value)
}

const endSession = async () => {
  if (sessionEnded.value) return
  const openParty = party.value && partyTotal.value > 0
  const ok = openParty
    ? window.confirm('Закрыть текущую партию и завершить всю встречу с итоговым расчётом?')
    : window.confirm('Завершить встречу и показать итог — кто кому сколько должен?')
  if (!ok) return
  endBusy.value = true
  try {
    store.endCasualSession(tableIds.value)
  } finally {
    endBusy.value = false
  }
}

const orderLabel = computed(() =>
  store.activePlayers.map((player, index) => (index === 0 ? `${player.name} (разбив)` : player.name)).join(' → ')
)

const formatMoney = (value: number) =>
  `${value >= 0 ? '+' : ''}${value.toLocaleString('ru-RU')} ${currency.value}`

const ballLabel = (ballId: string) =>
  store.casual.balls.find((ball) => ball.id === ballId)?.label || ballId

const formatPoints = (value: number) => value.toFixed(1).replace(/\.0$/, '')
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
        <div v-if="!sessionEnded" class="flex flex-wrap gap-2">
          <button
            type="button"
            class="btn-ghost inline-flex items-center gap-1.5 text-sm"
            :disabled="!store.events.length"
            @click="store.undoLast()"
          >
            <AppIcon name="undo" size="sm" /> Отмена
          </button>
          <NuxtLink to="/casual" class="btn-ghost inline-flex items-center gap-1.5 text-sm">
            <AppIcon name="settings" size="sm" /> Настройки
          </NuxtLink>
          <NuxtLink to="/tv" class="btn-ghost inline-flex items-center gap-1.5 text-sm">
            <AppIcon name="tv" size="sm" /> Табло
          </NuxtLink>
          <button
            type="button"
            class="btn-primary inline-flex items-center gap-1.5 text-sm"
            :disabled="endBusy"
            @click="endSession"
          >
            <AppIcon name="trophy" size="sm" /> Завершить встречу
          </button>
        </div>
      </div>

      <CasualSessionSummary v-if="sessionEnded" class="mt-5" />

      <template v-else>
        <SyncPanel class="mt-5" />
        <HistoryPanel class="mt-5" compact />

        <section class="card-surface mt-5 p-4">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.18em] text-cloth-muted">
                Партия {{ party?.number || 1 }} · база {{ store.casual.ballPrice }} {{ currency }}
              </p>
              <p class="mt-1 text-xs text-cloth-muted">
                Штрафы: {{ penaltyModeLabel(store.casual.penalties.mode) }}
              </p>
              <p class="mt-1 text-sm text-cloth-chalk">
                Круг:
                <span class="text-cloth-accent">{{ orderLabel || '—' }}</span>
              </p>
            </div>
            <div class="text-right">
              <p class="text-xs text-cloth-muted">пирамида (16)</p>
              <p class="font-display text-3xl font-bold tabular-nums text-cloth-accent">
                {{ formatPoints(rackTotal) }} / {{ CASUAL_PARTY_TARGET_POINTS }}
              </p>
              <p v-if="partyTotal > rackTotal" class="mt-1 text-xs text-cloth-muted">
                + доп. шары: {{ formatPoints(partyTotal - rackTotal) }}
              </p>
            </div>
          </div>

          <div class="mt-3 h-2 overflow-hidden rounded-full bg-[color:var(--cloth-input)]">
            <div
              class="h-full rounded-full bg-cloth-accent transition-all"
              :style="{ width: `${Math.min(100, (rackTotal / CASUAL_PARTY_TARGET_POINTS) * 100)}%` }"
            />
          </div>

          <p class="mt-3 text-sm text-cloth-muted">
            <template v-if="!party || party.ballIndex === 0">
              Выберите шар на карточке игрока. «В пирамиду» — в зачёт 16; «доп.» — сверх пирамиды.
            </template>
            <template v-else-if="rackComplete">
              Пирамида набрана (16). Можно добивать доп. шары или закрыть партию.
            </template>
            <template v-else>
              Следующий слот пирамиды: {{ nextBall }} / {{ CASUAL_PARTY_BALL_COUNT }}
              <span v-if="nextBallDouble" class="font-semibold text-cloth-accent"> (×2)</span>.
            </template>
          </p>

          <div
            v-if="party && (party.ballsOnTable || party.freeShotForPlayerId || Object.keys(party.ballDebtByPlayer || {}).length)"
            class="mt-3 flex flex-wrap gap-2 text-xs"
          >
            <span
              v-if="party.ballsOnTable"
              class="rounded-full bg-amber-500/15 px-2 py-1 text-amber-200"
            >
              На столе: {{ party.ballsOnTable }} шар.
            </span>
            <span
              v-for="player in store.activePlayers.filter((p) => ballDebt(p.id) > 0)"
              :key="`debt-${player.id}`"
              class="rounded-full bg-red-500/15 px-2 py-1 text-red-200"
            >
              {{ player.name }}: долг {{ ballDebt(player.id) }} шар.
            </span>
            <span
              v-if="party.freeShotForPlayerId"
              class="rounded-full bg-emerald-500/15 px-2 py-1 text-emerald-200"
            >
              Свободный удар:
              {{ store.players.find((p) => p.id === party.freeShotForPlayerId)?.name }}
            </span>
          </div>

          <button
            type="button"
            class="btn-primary mt-4 text-sm"
            :disabled="partyTotal <= 0"
            @click="settleParty"
          >
            Закрыть партию и начать новую
          </button>
        </section>

        <InfoCallout class="mt-5" title="Расчёт" icon="chip">
          Пирамида = 16 очков (последний физический ×2). Доп. шары не двигают пирамиду, но входят в
          итог партии. Фора — целые шары при закрытии. «Завершить встречу» — общий итог сессии и
          список переводов между игроками.
        </InfoCallout>

        <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <article
            v-for="(player, index) in store.activePlayers"
            :key="player.id"
            class="card-surface relative overflow-hidden p-4 transition hover:border-cloth-accent/40"
          >
            <div
              class="absolute right-3 top-3 rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wider"
              :class="index === 0 ? 'bg-cloth-accent/20 text-cloth-accent' : 'bg-cloth-felt/80 text-cloth-muted'"
            >
              {{ index === 0 ? 'разбив' : `#${index + 1}` }}
            </div>

            <div class="flex items-start gap-3 pr-16">
              <PlayerAvatar :name="player.name" />
              <div class="min-w-0">
                <h3 class="font-display text-xl font-bold">{{ player.name }}</h3>
                <p class="mt-1 text-xs text-cloth-muted">
                  <template v-if="casualHandicapBalls(player) > 0">
                    фора +{{ casualHandicapBalls(player) }} шар.
                  </template>
                  <template v-else>без форы</template>
                  <template v-if="previousOf(player.id)">
                    · бьёт <span class="text-cloth-accent">{{ previousOf(player.id)?.name }}</span>
                  </template>
                </p>
              </div>
            </div>

            <div class="mt-4 grid grid-cols-3 gap-2 text-center text-xs">
              <div class="rounded-lg border border-[color:var(--cloth-border)] px-2 py-2">
                <p class="text-cloth-muted">пирамида</p>
                <p class="font-display text-xl font-bold tabular-nums text-cloth-accent">
                  {{ formatPoints(party ? playerRackPoints(party, player.id) : 0) }}
                </p>
              </div>
              <div class="rounded-lg border border-[color:var(--cloth-border)] px-2 py-2">
                <p class="text-cloth-muted">с форой</p>
                <p class="font-display text-xl font-bold tabular-nums text-cloth-chalk">
                  {{ formatPoints(party ? store.casualEffectiveScore(player.id) : casualHandicapBalls(player)) }}
                </p>
              </div>
              <div class="rounded-lg border border-[color:var(--cloth-border)] px-2 py-2">
                <p class="text-cloth-muted">прогноз</p>
                <p
                  class="font-display text-lg font-bold tabular-nums"
                  :class="store.casualProjected(player.id) >= 0 ? 'text-emerald-300' : 'text-red-300'"
                >
                  {{ formatMoney(store.casualProjected(player.id)) }}
                </p>
              </div>
            </div>

            <p v-if="party && playerExtraPoints(party, player.id) > 0" class="mt-2 text-xs text-cloth-muted">
              доп. шары: +{{ formatPoints(playerExtraPoints(party, player.id)) }}
            </p>

            <p v-if="party?.freeShotForPlayerId === player.id" class="mt-2 text-xs font-semibold text-emerald-300">
              Свободный удар (ball-in-hand)
            </p>
            <p v-if="ballDebt(player.id) > 0" class="mt-1 text-xs text-red-300">
              Долг: выставить {{ ballDebt(player.id) }} шар. после забитого
            </p>

            <p class="mt-3 text-[11px] font-medium uppercase tracking-wide text-cloth-muted">Забил шар</p>
            <div class="mt-2 flex flex-wrap gap-2">
              <button
                v-for="ball in store.casual.balls"
                :key="ball.id"
                type="button"
                class="inline-flex items-center gap-1.5 rounded-lg border border-white/15 px-3 py-2 text-xs font-semibold transition hover:border-cloth-accent hover:bg-cloth-accent/10 disabled:opacity-40"
                :style="{ boxShadow: `inset 0 -3px 0 ${ball.color}` }"
                :disabled="ball.partyRole === 'rack' && rackComplete"
                @click="potBall(player.id, ball.id)"
              >
                <span class="h-2.5 w-2.5 rounded-full" :style="{ background: ball.color }" />
                {{ ball.label }}
                <span class="text-cloth-muted">{{ ball.price }} ₽</span>
                <span
                  v-if="ball.partyRole === 'extra'"
                  class="rounded bg-cloth-accent/15 px-1 text-[9px] uppercase text-cloth-accent"
                >
                  доп
                </span>
              </button>
            </div>

            <button
              type="button"
              class="btn-ghost mt-3 w-full border border-red-500/30 text-xs text-red-300 hover:border-red-400 hover:bg-red-500/10"
              @click="applyFoul(player.id)"
            >
              Фол
            </button>

            <p class="mt-2 text-xs text-cloth-muted">
              Сессия:
              <strong class="text-cloth-chalk">
                {{ player.balance.toLocaleString('ru-RU') }} {{ currency }}
              </strong>
            </p>
          </article>
        </div>

        <section class="card-surface mt-6 overflow-x-auto p-4">
          <div class="flex items-center gap-2">
            <AppIcon name="info" class="text-cloth-accent" />
            <h3 class="font-display text-lg font-bold">История</h3>
          </div>
          <table class="mt-3 w-full min-w-[520px] text-left text-sm">
            <thead class="text-cloth-muted">
              <tr>
                <th class="py-2 pr-3">время</th>
                <th class="py-2 pr-3">событие</th>
                <th class="py-2 pr-3">игрок</th>
                <th class="py-2">детали</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="event in [...store.events].reverse().slice(0, 40)"
                :key="event.id"
                class="border-t border-white/5"
              >
                <td class="py-2 pr-3 text-cloth-muted">{{ new Date(event.at).toLocaleTimeString('ru-RU') }}</td>
                <td class="py-2 pr-3">
                  {{
                    event.kind === 'party_settle'
                      ? 'закрытие партии'
                      : event.kind === 'session_end'
                        ? 'конец встречи'
                        : event.kind === 'casual_foul'
                          ? 'фол'
                          : ballLabel(event.ballId)
                  }}
                </td>
                <td class="py-2 pr-3 font-medium">
                  {{ store.players.find((p) => p.id === event.scorerId)?.name || event.scorerId }}
                </td>
                <td class="py-2 text-xs">
                  <template v-if="event.kind === 'party_settle' || event.kind === 'session_end'">
                    <span
                      v-for="(delta, pid) in event.deltas"
                      :key="pid"
                      class="mr-2"
                      :class="delta >= 0 ? 'text-emerald-300' : 'text-red-300'"
                    >
                      {{ store.players.find((p) => p.id === pid)?.name }}
                      {{ delta >= 0 ? '+' : '' }}{{ delta }} {{ currency }}
                    </span>
                    <span v-if="event.kind === 'session_end' && !Object.keys(event.deltas).length">
                      {{ event.note }}
                    </span>
                  </template>
                  <template v-else>{{ event.note || '—' }}</template>
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      </template>
    </main>
  </div>
</template>
