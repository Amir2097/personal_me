<script setup lang="ts">
import { previousPlayerId } from '~/utils/scoring'
import type { Player } from '~/types/kolkhoz'
import { groupLabel } from '~/utils/labels'

const store = useKolkhozStore()
const sounds = useGameSounds()
const fineAmount = computed(() => store.fineDefaultAmount())

onMounted(() => {
  if (!store.mode) store.setMode('tournament')
  if (!store.tournament.tables.length && store.activePlayers.length) {
    store.reseat()
  }
})

const isOrganizer = computed(() => store.tournament.kind === 'organizer')

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

const onChipMarkupChange = (playerId: string, event: Event) => {
  const value = Number((event.target as HTMLInputElement).value)
  if (Number.isNaN(value)) return
  store.updatePlayer(playerId, { balance: value })
}

const reseatAndKeepTimer = () => {
  store.reseat()
}

const startTimer = () => {
  sounds.unlock()
  store.startRoundTimer()
}

const roundRateShort = computed(() => {
  const round = store.currentRound
  if (!round) return '—'
  return `${round.tariffs[1]}-${round.tariffs[2]}-${round.tariffs[3]}`
})

const roundMetaLabel = computed(() => (isOrganizer.value ? 'разметка' : 'тарифы'))

const potAt = (tableId: string) => store.potByTableId(tableId)

const potCursorName = (tableId: string) => {
  const pot = potAt(tableId)
  if (!pot) return ''
  return store.players.find((player) => player.id === pot.passCursorPlayerId)?.name || ''
}

const fineAt = (tableId: string, playerIds: string[], playerId: string) => {
  try {
    sounds.unlock()
    store.placeFine(tableId, playerId, activeIdsAt(playerIds))
  } catch (error) {
    window.alert(error instanceof Error ? error.message : 'Не удалось выписать штраф')
  }
}

const passMissAt = (tableId: string, playerId: string) => {
  try {
    sounds.unlock()
    const returned = store.passPotMiss(tableId, playerId)
    if (!returned) void sounds.play('miss')
  } catch (error) {
    window.alert(error instanceof Error ? error.message : 'Не удалось отметить мимо')
  }
}

const returnPotAt = (tableId: string) => {
  sounds.unlock()
  store.returnPot(tableId)
}
</script>

<template>
  <div>
    <RoundTimer />
    <main class="page-shell py-6">
      <div class="hero-strip flex flex-wrap items-start justify-between gap-3 rounded-2xl p-4 sm:p-5">
        <div class="min-w-[14rem]">
          <p class="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-cloth-accent">
            <AppIcon :name="isOrganizer ? 'clipboard' : 'trophy'" size="sm" />
            {{ isOrganizer ? 'Организатор' : 'Подробная игра' }}
          </p>
          <h2 class="mt-1 font-display text-2xl font-bold">
            {{ isOrganizer ? 'Пульт тура' : 'Игровые столы' }}
          </h2>
          <p v-if="store.currentRound" class="mt-1 text-sm text-cloth-muted">
            {{ store.currentRound.durationMinutes }} мин
          </p>
        </div>
        <div class="flex flex-wrap items-start justify-end gap-2">
          <div v-if="store.currentRound" class="round-badge rounded-xl px-3 py-2 text-right">
            <p class="text-sm font-semibold text-cloth-accent">Тур {{ store.currentRound.number }} · {{ roundRateShort }}</p>
            <p class="text-xs font-medium text-cloth-muted">{{ roundMetaLabel }}</p>
          </div>
          <button type="button" class="btn-primary btn-touch inline-flex items-center gap-1.5" @click="startTimer">
            <AppIcon name="clock" size="sm" /> Старт таймера
          </button>
          <button
            v-if="store.timerIsRunning"
            type="button"
            class="btn-ghost btn-touch inline-flex items-center gap-1.5"
            @click="store.pauseRoundTimer()"
          >
            <AppIcon name="pause" size="sm" /> Пауза
          </button>
          <button
            v-if="store.timerIsPaused"
            type="button"
            class="btn-ghost btn-touch inline-flex items-center gap-1.5"
            @click="store.resumeRoundTimer()"
          >
            <AppIcon name="play" size="sm" /> Продолжить время
          </button>
          <button
            v-if="isOrganizer"
            type="button"
            class="btn-ghost btn-touch inline-flex items-center gap-1.5"
            @click="reseatAndKeepTimer"
          >
            <AppIcon name="users" size="sm" /> Пересадить
          </button>
          <button
            type="button"
            class="btn-ghost btn-touch"
            :disabled="store.tournament.currentRoundIndex >= store.tournament.rounds.length - 1"
            @click="nextRound"
          >
            След. тур
          </button>
          <button
            v-if="!isOrganizer"
            type="button"
            class="btn-ghost btn-touch inline-flex items-center gap-1.5"
            :disabled="!store.events.length"
            @click="store.undoLast()"
          >
            <AppIcon name="undo" size="sm" /> Отмена
          </button>
          <NuxtLink to="/tournament" class="btn-ghost btn-touch inline-flex items-center gap-1.5">
            <AppIcon name="settings" size="sm" /> Настройки
          </NuxtLink>
          <NuxtLink to="/tv" class="btn-ghost btn-touch inline-flex items-center gap-1.5">
            <AppIcon name="tv" size="sm" /> Табло
          </NuxtLink>
        </div>
      </div>

      <InfoCallout v-if="!isOrganizer" class="mt-5" title="Круг на столе" icon="chip">
        «+ Шар» забирает фишки у предыдущего и общак, если он есть.
        «Штраф» кладёт в общак фишки по ставке <strong class="text-cloth-chalk">группы 1</strong>
        (макс. тариф тура), даже если оштрафован игрок другой группы.
        Дальше по кругу — «Мимо»; без забития общак вернётся сам.
      </InfoCallout>
      <InfoCallout v-else class="mt-5" title="Организаторский режим" icon="clipboard">
        Пауза → убрать/вернуть → «Пересадить» → продолжить таймер.
        Докупы и доны пишите на карточке игрока — банк и призовые пересчитаются сами.
      </InfoCallout>

      <BankPanel class="mt-5" />
      <SyncPanel class="mt-5" />
      <HistoryPanel class="mt-5" compact />

      <div class="tables-grid">
        <section v-for="table in store.tournament.tables" :key="table.id" class="table-board">
          <div class="flex flex-wrap items-baseline justify-between gap-2">
            <h3 class="flex items-center gap-1.5 font-display text-base font-bold text-cloth-accent">
              <AppIcon name="ball" size="sm" /> {{ table.label }}
              <span class="text-[10px] font-normal uppercase tracking-wide text-cloth-muted">
                № {{ table.number }}
              </span>
            </h3>
            <p class="max-w-[70%] truncate text-[10px] text-cloth-muted" :title="orderLabel(table.playerIds)">
              {{ isOrganizer ? 'Состав' : 'Круг' }}: {{ orderLabel(table.playerIds) || '—' }}
            </p>
          </div>

          <div
            v-if="!isOrganizer && potAt(table.id)"
            class="mt-2 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-2.5 py-1.5 text-xs"
          >
            <p>
              Общак
              <strong class="text-cloth-accent">{{ potAt(table.id)?.amount }}</strong>
              · ход
              <span class="text-cloth-accent">{{ potCursorName(table.id) }}</span>
            </p>
            <button type="button" class="btn-ghost btn-play" @click="returnPotAt(table.id)">
              Вернуть
            </button>
          </div>

          <div class="mt-2 space-y-1.5">
            <article
              v-for="(player, index) in playersAt(table.playerIds)"
              :key="player.id"
              class="player-chip player-chip--dense"
              :class="{
                'opacity-50': player.status === 'eliminated',
                'ring-1 ring-amber-400/60':
                  !isOrganizer && potAt(table.id)?.passCursorPlayerId === player.id
              }"
            >
              <PlayerAvatar :name="player.name" size="sm" />
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                  <p class="truncate text-sm font-semibold leading-tight">
                    <span class="mr-1 text-[10px] font-normal text-cloth-muted">#{{ index + 1 }}</span>
                    {{ player.name }}
                  </p>
                  <span class="text-[10px] text-cloth-muted">{{ groupLabel(player.category, true) }}</span>
                  <span
                    v-if="!isOrganizer && potAt(table.id)?.passCursorPlayerId === player.id"
                    class="text-[9px] uppercase tracking-wide text-amber-600"
                  >
                    ход
                  </span>
                  <span v-if="player.status === 'eliminated'" class="text-[10px] text-cloth-muted">вне игры</span>
                  <span
                    v-else-if="!isOrganizer && previousOf(table.playerIds, player.id)"
                    class="truncate text-[10px] text-cloth-muted"
                  >
                    → {{ previousOf(table.playerIds, player.id)?.name }}
                  </span>
                </div>

                <div class="mt-1 flex flex-wrap items-center gap-1">
                  <template v-if="!isOrganizer && player.status === 'active'">
                    <button
                      type="button"
                      class="btn-primary btn-play"
                      @click="scoreAt(table.id, table.playerIds, player.id)"
                    >
                      + Шар
                    </button>
                    <button
                      v-if="potAt(table.id)?.passCursorPlayerId === player.id"
                      type="button"
                      class="btn-ghost btn-play"
                      @click="passMissAt(table.id, player.id)"
                    >
                      Мимо
                    </button>
                    <button
                      type="button"
                      class="btn-ghost btn-play"
                      :title="`В общак ${fineAmount} фиш.`"
                      @click="fineAt(table.id, table.playerIds, player.id)"
                    >
                      Штраф {{ fineAmount }}
                    </button>
                    <button
                      type="button"
                      class="btn-ghost btn-play"
                      @click="store.dropout(table.id, player.id)"
                    >
                      Выбыл
                    </button>
                  </template>
                  <template v-else-if="isOrganizer">
                    <button
                      v-if="player.status === 'active'"
                      type="button"
                      class="btn-ghost btn-play"
                      @click="store.dropout(table.id, player.id)"
                    >
                      Убрать
                    </button>
                    <button
                      v-else
                      type="button"
                      class="btn-primary btn-play"
                      @click="store.reinstate(player.id)"
                    >
                      Вернуть
                    </button>
                  </template>
                </div>

                <PlayerBuyIn v-if="isOrganizer" :player-id="player.id" compact :history-limit="3" />
              </div>

              <div class="shrink-0 text-right">
                <p class="text-[9px] uppercase tracking-wide text-cloth-muted">
                  {{ isOrganizer ? 'фиш.' : 'фиш.' }}
                </p>
                <input
                  v-if="isOrganizer"
                  :value="player.balance"
                  type="number"
                  class="field-input mt-0.5 w-14 !px-1.5 !py-0.5 text-right font-display text-base font-bold tabular-nums text-cloth-accent"
                  @change="onChipMarkupChange(player.id, $event)"
                />
                <p v-else class="font-display text-xl font-bold leading-none tabular-nums text-cloth-accent">
                  {{ player.balance }}
                </p>
                <p v-if="isOrganizer" class="mt-0.5 text-[10px] text-cloth-muted">
                  {{ store.playerPaidAmount(player.id).toLocaleString('ru-RU') }} ₽
                </p>
              </div>
            </article>
          </div>
        </section>
      </div>

      <section v-if="isOrganizer && store.eliminatedPlayers.length" class="card-surface mt-5 p-3">
        <h3 class="flex items-center gap-2 font-display text-base font-bold">
          <AppIcon name="users" class="text-cloth-accent" size="sm" /> Вне текущего состава
        </h3>
        <ul class="mt-2 grid gap-1.5 sm:grid-cols-2 xl:grid-cols-3">
          <li
            v-for="player in store.eliminatedPlayers"
            :key="player.id"
            class="player-chip player-chip--dense !items-start"
          >
            <PlayerAvatar :name="player.name" size="sm" />
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center justify-between gap-1">
                <span class="truncate text-sm">{{ player.name }}</span>
                <button type="button" class="btn-ghost btn-play" @click="store.reinstate(player.id)">
                  вернуть
                </button>
              </div>
              <PlayerBuyIn :player-id="player.id" compact :history-limit="2" />
            </div>
          </li>
        </ul>
      </section>

      <section v-if="!isOrganizer" class="card-surface mt-6 overflow-x-auto p-4">
        <div class="flex items-center gap-2">
          <AppIcon name="info" class="text-cloth-accent" />
          <h3 class="font-display text-lg font-bold">История</h3>
        </div>
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
              class="border-t border-[color:var(--cloth-border)]"
            >
              <td class="py-2 pr-3 text-cloth-muted">{{ new Date(event.at).toLocaleTimeString('ru-RU') }}</td>
              <td class="py-2 pr-3 font-medium">
                {{ store.players.find((p) => p.id === event.scorerId)?.name || event.scorerId }}
              </td>
              <td class="py-2 pr-3 text-cloth-accent">
                <template v-if="event.kind === 'dropout'">выбывание</template>
                <template v-else-if="event.kind === 'fine_place'">штраф → общак</template>
                <template v-else-if="event.kind === 'fine_claim'">забрал общак</template>
                <template v-else-if="event.kind === 'fine_return'">возврат общака</template>
                <template v-else>{{ event.note?.replace(/^vs\s+/, '') || '—' }}</template>
              </td>
              <td class="py-2 text-xs">
                <span
                  v-for="(delta, pid) in event.deltas"
                  :key="pid"
                  class="mr-2"
                  :class="delta >= 0 ? 'text-emerald-600' : 'text-red-500'"
                >
                  {{ store.players.find((p) => p.id === pid)?.name }} {{ delta >= 0 ? '+' : '' }}{{ delta }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!store.events.length" class="mt-2 text-sm text-cloth-muted">Событий пока нет.</p>
      </section>

      <section class="card-surface mt-6 p-4">
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="trophy" class="text-cloth-accent" />
          {{ isOrganizer ? 'Список участников' : 'Лидерборд' }}
        </h3>
        <ol class="mt-3 space-y-2 text-sm">
          <li
            v-for="(player, index) in store.leaderboard"
            :key="player.id"
            class="flex items-center justify-between gap-3 border-b border-[color:var(--cloth-border)] py-2"
            :class="player.status === 'eliminated' ? 'opacity-40' : ''"
          >
            <span class="inline-flex min-w-0 items-center gap-2">
              <span class="w-5 text-cloth-muted">{{ index + 1 }}.</span>
              <PlayerAvatar :name="player.name" size="sm" />
              <span class="truncate">
                {{ player.name }}
                <span class="text-cloth-muted">{{ groupLabel(player.category, true) }}</span>
              </span>
            </span>
            <span class="tabular-nums font-semibold">
              {{ player.balance }}
              <span class="ml-2 text-xs font-normal text-cloth-muted">
                {{ store.playerPaidAmount(player.id).toLocaleString('ru-RU') }} ₽
              </span>
            </span>
          </li>
        </ol>
      </section>
    </main>
  </div>
</template>
