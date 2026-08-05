<script setup lang="ts">
import type { TournamentKind } from '~/types/kolkhoz'
import { downloadKolkhozExcel } from '~/utils/exportExcel'

const store = useKolkhozStore()
const config = useRuntimeConfig()
const importError = ref('')
const { username } = useHubAuth()
const clientReady = ref(false)

onMounted(() => {
  clientReady.value = true
})

const startCasual = () => {
  store.setMode('casual')
  navigateTo('/casual')
}

const startTournament = (kind: TournamentKind) => {
  store.setTournamentKind(kind)
  navigateTo('/tournament')
}

const downloadSave = () => {
  downloadKolkhozExcel(store.$state)
}

const onImportFile = async (event: Event) => {
  importError.value = ''
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  try {
    store.importJson(await file.text())
  } catch {
    importError.value = 'Не удалось импортировать JSON-сессию.'
  }
}

const modeLabel = computed(() => {
  if (store.mode === 'casual') return 'Быстрый стол'
  if (store.mode === 'tournament') {
    return store.tournament.kind === 'organizer' ? 'Турнир · организаторская' : 'Турнир · подробная игра'
  }
  return '—'
})

const continueHref = computed(() => {
  if (store.mode === 'casual') return '/casual/play'
  if (store.mode === 'tournament') return '/tournament/play'
  return null
})
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-6xl px-4 py-8 sm:py-12">
      <section class="hero-surface max-w-3xl rounded-2xl px-5 py-4 sm:px-6 sm:py-5">
        <p class="flex items-center gap-2 text-sm text-cloth-muted">
          <AppIcon name="cue" class="text-cloth-accent" />
          Подсервис {{ config.public.brandName }}
        </p>
        <h2 class="mt-2 font-display text-3xl font-extrabold tracking-tight text-cloth-chalk sm:text-5xl">
          Колхоз на зелёном сукне
        </h2>
        <p class="mt-4 max-w-2xl text-base leading-relaxed text-cloth-chalk/75">
          Быстрый стол или турнир. В подробной игре — скоринг шаров, банк и призовые;
          в организаторской — рассадка, туры, таймер и банк без пошагового скоринга.
        </p>
        <ClientOnly>
          <p v-if="clientReady && username" class="mt-3 inline-flex items-center gap-2 text-sm text-cloth-accent">
            <AppIcon name="user" size="sm" />
            Вы вошли как <strong class="text-cloth-chalk">{{ username }}</strong>
          </p>
        </ClientOnly>
      </section>

      <InfoCallout class="mt-6 max-w-3xl" title="Правило выплат (подробная игра)" icon="chip">
        Порядок сидения = круг. Игрок забирает фишки только у предыдущего.
        Взносы и докупы копятся в банке; призовые — процент от банка.
        В организаторском режиме фишки — справочная разметка тура, без кнопок «+ Шар».
      </InfoCallout>

      <div class="mt-10 grid gap-5 md:grid-cols-2">
        <button
          type="button"
          class="card-surface group p-6 text-left transition hover:border-cloth-accent/50 hover:bg-cloth-accent/5"
          @click="startCasual"
        >
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-cloth-accent/15 text-cloth-accent">
            <AppIcon name="ball" size="lg" />
          </div>
          <p class="mt-4 text-xs uppercase tracking-[0.2em] text-cloth-accent">Режим Б</p>
          <h3 class="mt-2 font-display text-2xl font-bold">Быстрый стол</h3>
          <p class="mt-3 text-sm text-cloth-chalk/70">
            2–5 человек, фора, цена шара. Партии по 15 шаров (последний ×2), расчёт от среднего.
          </p>
          <span class="mt-6 inline-flex items-center gap-1 text-sm font-semibold text-cloth-accent group-hover:underline">
            Начать <AppIcon name="arrow" size="sm" />
          </span>
        </button>

        <div class="card-surface p-6">
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-cloth-accent/15 text-cloth-accent">
            <AppIcon name="trophy" size="lg" />
          </div>
          <p class="mt-4 text-xs uppercase tracking-[0.2em] text-cloth-accent">Режим А</p>
          <h3 class="mt-2 font-display text-2xl font-bold">Турнир по турам</h3>
          <p class="mt-3 text-sm text-cloth-chalk/70">
            Выберите формат: полный учёт фишек или пульт организатора.
          </p>

          <div class="mt-5 grid gap-3">
            <button
              type="button"
              class="panel-surface p-4 text-left transition hover:border-cloth-accent/50"
              @click="startTournament('detailed')"
            >
              <p class="flex items-center gap-2 font-semibold text-cloth-chalk">
                <AppIcon name="chip" class="text-cloth-accent" /> Подробная игра
              </p>
              <p class="mt-1 text-xs text-cloth-muted">
                Тарифы, «+ Шар», банк, взносы/докупы и призовые.
              </p>
            </button>
            <button
              type="button"
              class="panel-surface p-4 text-left transition hover:border-cloth-accent/50"
              @click="startTournament('organizer')"
            >
              <p class="flex items-center gap-2 font-semibold text-cloth-chalk">
                <AppIcon name="clipboard" class="text-cloth-accent" /> Организаторская
              </p>
              <p class="mt-1 text-xs text-cloth-muted">
                Игроки, столы, туры, таймер, банк. Фишки — разметка тура.
              </p>
            </button>
          </div>
        </div>
      </div>

      <section class="card-surface mt-6 p-6">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-cloth-accent">Академия</p>
            <h3 class="mt-1 font-display text-2xl font-bold">Тренажёр русского бильярда</h3>
            <p class="mt-2 text-sm text-cloth-chalk/75">
              Интерактивные упражнения с SVG-схемами стола, траекториями и фиксацией результатов.
            </p>
          </div>
          <NuxtLink to="/academy" class="btn-primary inline-flex items-center gap-2 text-sm">
            <AppIcon name="play" size="sm" /> Открыть академию
          </NuxtLink>
        </div>
      </section>

      <section class="card-surface mt-8 p-5">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="flex items-center gap-2 font-display text-lg font-bold">
              <AppIcon name="chip" class="text-cloth-accent" /> Сохранённая сессия
            </h3>
            <p class="mt-1 text-sm text-cloth-muted">
              {{ modeLabel }} · игроков: {{ store.players.length }} · событий: {{ store.events.length }}
            </p>
            <p class="mt-1 text-xs text-cloth-muted">
              Excel — таблица с листами игроков, столов, туров и событий.
              Импорт JSON — полное восстановление сессии.
            </p>
            <p v-if="importError" class="mt-1 text-xs text-red-300">{{ importError }}</p>
          </div>
          <div class="flex flex-wrap gap-2">
            <NuxtLink v-if="continueHref" :to="continueHref" class="btn-primary text-sm">Продолжить</NuxtLink>
            <NuxtLink to="/tv" class="btn-ghost inline-flex items-center gap-1 text-sm">
              <AppIcon name="tv" size="sm" /> Табло
            </NuxtLink>
            <button type="button" class="btn-ghost text-sm" @click="downloadSave">Excel</button>
            <label class="btn-ghost cursor-pointer text-sm">
              Импорт JSON
              <input type="file" accept="application/json,.json" class="hidden" @change="onImportFile" />
            </label>
            <button type="button" class="btn-ghost text-sm" @click="store.resetAll()">Сбросить</button>
          </div>
        </div>
      </section>

      <HistoryPanel class="mt-5" />
    </main>
  </div>
</template>
