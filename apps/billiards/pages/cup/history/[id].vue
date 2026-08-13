<script setup lang="ts">
import { matchesByRound } from '~/utils/cupBracket'
import type { CupState } from '~/types/cup'
import { createEmptyCupState } from '~/types/cup'
import { cupFormatTitle, cupRaceLabel, slotName } from '~/utils/cupLabels'

const route = useRoute()
const history = useCupHistory()
const store = useCupStore()

const snapshot = ref<CupState>(createEmptyCupState())
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  loading.value = true
  const idParam = route.params.id
  const id = Array.isArray(idParam) ? idParam[0] : idParam
  const numeric = typeof id === 'string' && /^\d+$/.test(id) ? Number(id) : id
  const state = await history.loadDetail(numeric as string | number)
  if (!state || !state.tournament.id) {
    error.value = 'Турнир не найден'
  } else {
    snapshot.value = state
  }
  loading.value = false
})

const nameOf = (id: string | null) =>
  slotName(id, snapshot.value.players.find((player) => player.id === id)?.name)

const rounds = computed(() => matchesByRound(snapshot.value.matches))

const restoreToActive = async () => {
  store.applyRemoteState(snapshot.value)
  store.persistNow()
  await navigateTo('/cup/bracket')
}
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-6xl px-4 py-8">
      <NuxtLink to="/cup/history" class="btn-ghost text-sm">← История</NuxtLink>

      <p v-if="loading" class="mt-6 text-sm text-cloth-chalk">Загрузка…</p>
      <p v-else-if="error" class="card-surface mt-6 p-5 text-sm text-red-300">{{ error }}</p>

      <template v-else>
        <section class="hero-surface mt-4 flex flex-wrap items-start justify-between gap-3 rounded-2xl px-5 py-5">
          <div>
            <h1 class="font-display text-3xl font-bold text-cloth-chalk">{{ snapshot.tournament.name }}</h1>
            <p class="mt-2 text-sm text-cloth-chalk/75">
              {{ cupFormatTitle(snapshot.tournament.format) }}
              · {{ cupRaceLabel(snapshot.tournament.raceTo) }}
            </p>
            <p v-if="snapshot.tournament.winnerId" class="mt-1 text-sm text-emerald-300">
              Победитель: {{ nameOf(snapshot.tournament.winnerId) }}
            </p>
          </div>
          <button type="button" class="btn-primary text-sm" @click="restoreToActive">
            Добавить в активные
          </button>
        </section>

        <section class="card-surface mt-6 p-5 sm:p-6">
          <h2 class="font-display text-xl font-bold text-cloth-chalk">Участники</h2>
          <ul class="mt-3 grid gap-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            <li v-for="player in snapshot.players" :key="player.id" class="panel-surface px-3 py-2 text-sm">
              #{{ player.seed }} {{ player.name }}
            </li>
          </ul>
        </section>

        <section class="card-surface mt-6 p-5 sm:p-6">
          <h2 class="font-display text-xl font-bold text-cloth-chalk">Сетка (архив)</h2>
          <div class="mt-4 flex gap-4 overflow-x-auto pb-3">
            <div v-for="round in rounds" :key="round.roundKey" class="min-w-[220px] flex-1">
              <p class="round-chip mb-3">{{ round.label }}</p>
              <div class="space-y-3">
                <div v-for="match in round.matches" :key="match.id" class="panel-surface p-3 text-sm">
                  <p class="flex justify-between gap-2 text-cloth-chalk">
                    <span>{{ nameOf(match.playerAId) }}</span><span>{{ match.framesA }}</span>
                  </p>
                  <p class="mt-1 flex justify-between gap-2 text-cloth-chalk">
                    <span>{{ nameOf(match.playerBId) }}</span><span>{{ match.framesB }}</span>
                  </p>
                  <p v-if="match.winnerId" class="mt-2 text-xs text-emerald-300">
                    Победитель: {{ nameOf(match.winnerId) }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>
