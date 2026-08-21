<script setup lang="ts">
import { cupFormatTitle, cupRaceLabel, matchStatusLabel } from '~/utils/cupLabels'
import { downloadCupExcel } from '~/utils/exportCupExcel'

const store = useCupStore()
const history = useCupHistory()
const sync = useCupSync()
const saveHint = ref('')

onMounted(() => store.hydrate())

const playableMatches = computed(() =>
  store.matches.filter(
    (match) =>
      (match.status === 'ready' || match.status === 'live') &&
      match.playerAId &&
      match.playerBId
  )
)

const playerName = (id: string | null) => store.playerById(id)?.name || '—'

const saveHistory = async () => {
  saveHint.value = ''
  if (!store.tournament.id) return
  await history.saveSnapshot(store.exportSnapshot())
  saveHint.value = history.error.value || 'Сохранено в историю.'
}

const openMatch = async (id: string) => {
  store.setActiveMatch(id)
  await navigateTo({
    path: `/cup/match/${id}`,
    query: sync.roomCode.value ? { room: sync.roomCode.value } : {}
  })
}

const exportExcel = () => {
  downloadCupExcel(store.exportSnapshot())
}
</script>

<template>
  <div>
    <main class="page-shell page-shell--wide py-6">
      <div class="flex flex-wrap items-center gap-2">
        <NuxtLink to="/cup" class="btn-ghost btn-touch">← Турнир</NuxtLink>
        <NuxtLink to="/cup/tv" class="btn-ghost btn-touch">Табло</NuxtLink>
        <NuxtLink to="/cup/history" class="btn-ghost btn-touch">История</NuxtLink>
        <button type="button" class="btn-ghost btn-touch" :disabled="history.saving.value" @click="saveHistory">
          Сохранить в историю
        </button>
        <button type="button" class="btn-ghost btn-touch" @click="exportExcel">Excel</button>
      </div>
      <p v-if="saveHint" class="mt-2 text-sm text-cloth-chalk">{{ saveHint }}</p>

      <CupTournamentSwitcher compact class="mt-4" />

      <SyncPanel variant="cup" class="mt-4" />

      <section class="hero-surface mt-4 rounded-2xl px-5 py-4 sm:px-6">
        <div class="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 class="font-display text-3xl font-bold text-cloth-chalk">
              {{ store.tournament.name || 'Сетка' }}
            </h1>
            <p class="mt-2 text-sm text-cloth-chalk/75">
              {{ cupFormatTitle(store.tournament.format) }}
              · {{ cupRaceLabel(store.tournament.raceTo) }}
              <span v-if="store.hasShotClock"> · таймер {{ store.tournament.shotClockSec }} сек</span>
              <span v-if="store.winnerName"> · победитель: {{ store.winnerName }}</span>
            </p>
          </div>
          <p class="text-xs text-cloth-muted">Игроков: {{ store.players.length }} · матчей: {{ store.matches.length }}</p>
        </div>
      </section>

      <section v-if="!store.matches.length" class="card-surface mt-6 p-5">
        <p class="text-sm text-cloth-muted">Сетка ещё не создана.</p>
        <NuxtLink to="/cup/setup" class="btn-primary mt-4 inline-flex text-sm">Создать турнир</NuxtLink>
      </section>

      <section v-else class="card-surface mt-5 p-3 sm:p-4">
        <div v-if="playableMatches.length" class="mb-3 flex flex-wrap gap-2">
          <button
            v-for="match in playableMatches"
            :key="match.id"
            type="button"
            class="btn-ghost btn-touch max-w-full text-left"
            @click="openMatch(match.id)"
          >
            #{{ match.displayNo }} · {{ playerName(match.playerAId) }} — {{ playerName(match.playerBId) }}
            · {{ matchStatusLabel(match.status) }}
          </button>
        </div>
        <CupBracketBoard
          :matches="store.matches"
          :players="store.players"
          :race-to="store.tournament.raceTo"
          :format="store.tournament.format"
          @open="openMatch"
        />
      </section>
    </main>
  </div>
</template>
