<script setup lang="ts">
import exercisesRaw from '~/data/exercises.json'
import type { Exercise, ExerciseCategory, ExerciseLevel } from '~/types/academy'

const exercises = exercisesRaw as Exercise[]
const academy = useAcademyStore()

const levelFilter = ref<ExerciseLevel | 0>(0)
const categoryFilter = ref<ExerciseCategory | 'all'>('all')
const search = ref('')
const sortBy = ref<'level_asc' | 'level_desc' | 'title' | 'progress_desc'>('level_asc')

onMounted(() => {
  academy.hydrate()
})

const categories = computed(() => ['all', ...new Set(exercises.map((item) => item.category))] as Array<ExerciseCategory | 'all'>)

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  const list = exercises.filter((item) => {
    const levelOk = levelFilter.value === 0 || item.level === levelFilter.value
    const catOk = categoryFilter.value === 'all' || item.category === categoryFilter.value
    const textOk =
      !q ||
      item.title.toLowerCase().includes(q) ||
      item.description.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q)
    return levelOk && catOk && textOk
  })

  const withProgress = (item: Exercise) => {
    const log = academy.byExercise(item.id)
    if (!log || log.attempts <= 0) return 0
    return Math.round((Math.max(0, log.made) / Math.max(1, log.attempts)) * 100)
  }

  if (sortBy.value === 'title') {
    return [...list].sort((a, b) => a.title.localeCompare(b.title, 'ru'))
  }
  if (sortBy.value === 'level_desc') {
    return [...list].sort((a, b) => b.level - a.level || a.title.localeCompare(b.title, 'ru'))
  }
  if (sortBy.value === 'progress_desc') {
    return [...list].sort((a, b) => withProgress(b) - withProgress(a) || a.level - b.level)
  }
  return [...list].sort((a, b) => a.level - b.level || a.title.localeCompare(b.title, 'ru'))
})

const levelLabel = (value: number) => {
  if (value === 1) return 'Новичок'
  if (value === 2) return 'Любитель'
  if (value === 3) return 'Продвинутый'
  return 'Профи'
}

const levelBadgeClass = (value: number) => {
  if (value === 1) return 'bg-emerald-500/15 text-emerald-200'
  if (value === 2) return 'bg-sky-500/15 text-sky-200'
  if (value === 3) return 'bg-amber-500/15 text-amber-200'
  return 'bg-fuchsia-500/15 text-fuchsia-200'
}

const categoryDotClass = (category: ExerciseCategory) => {
  if (category === 'чужие') return 'bg-red-400'
  if (category === 'свояки') return 'bg-cyan-400'
  if (category === 'выход') return 'bg-violet-400'
  if (category === 'отыгрыш') return 'bg-amber-400'
  if (category === 'контроль') return 'bg-lime-400'
  if (category === 'дуплеты') return 'bg-orange-400'
  if (category === 'особые') return 'bg-pink-400'
  if (category === 'серии') return 'bg-indigo-400'
  return 'bg-slate-400'
}

const progressFor = (exerciseId: string) => {
  const log = academy.byExercise(exerciseId)
  if (!log || log.attempts <= 0) return null
  const rate = Math.round((Math.max(0, log.made) / Math.max(1, log.attempts)) * 100)
  return { ...log, rate }
}
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-6xl px-4 py-6">
      <section class="hero-surface rounded-2xl p-5">
        <p class="text-xs uppercase tracking-[0.2em] text-cloth-accent">Академия</p>
        <h2 class="mt-2 font-display text-3xl font-bold text-cloth-chalk">Тренажер русского бильярда</h2>
        <p class="mt-2 max-w-3xl text-sm text-cloth-chalk/80">
          Каталог упражнений с визуальными схемами, точкой удара и фиксацией результата по попыткам.
        </p>
      </section>

      <section class="card-surface mt-6 p-4">
        <h3 class="font-display text-lg font-bold">Фильтры</h3>
        <div class="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <label class="text-sm sm:col-span-2 lg:col-span-1">
            Поиск
            <input
              v-model.trim="search"
              class="field-input mt-1 w-full"
              placeholder="Название, описание, категория"
            />
          </label>
          <label class="text-sm">
            Уровень
            <select v-model.number="levelFilter" class="field-input mt-1 w-full">
              <option :value="0">Все уровни</option>
              <option :value="1">1 — Новичок</option>
              <option :value="2">2 — Любитель</option>
              <option :value="3">3 — Продвинутый</option>
              <option :value="4">4 — Профи</option>
            </select>
          </label>
          <label class="text-sm">
            Категория
            <select v-model="categoryFilter" class="field-input mt-1 w-full">
              <option value="all">Все категории</option>
              <option v-for="cat in categories.filter((c) => c !== 'all')" :key="cat" :value="cat">
                {{ cat }}
              </option>
            </select>
          </label>
          <label class="text-sm">
            Сортировка
            <select v-model="sortBy" class="field-input mt-1 w-full">
              <option value="level_asc">Сначала проще (уровень ↑)</option>
              <option value="level_desc">Сначала сложнее (уровень ↓)</option>
              <option value="title">По названию (А-Я)</option>
              <option value="progress_desc">По прогрессу (лучшие сверху)</option>
            </select>
          </label>
        </div>

        <div class="mt-4 flex flex-wrap gap-2 text-xs">
          <span class="rounded-full bg-emerald-500/15 px-2 py-1 text-emerald-200">Ур. 1 — Новичок</span>
          <span class="rounded-full bg-sky-500/15 px-2 py-1 text-sky-200">Ур. 2 — Любитель</span>
          <span class="rounded-full bg-amber-500/15 px-2 py-1 text-amber-200">Ур. 3 — Продвинутый</span>
          <span class="rounded-full bg-fuchsia-500/15 px-2 py-1 text-fuchsia-200">Ур. 4 — Профи</span>
        </div>
        <div class="mt-2 flex flex-wrap gap-3 text-xs text-cloth-muted">
          <span class="inline-flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-full bg-red-400" /> чужие</span>
          <span class="inline-flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-full bg-cyan-400" /> свояки</span>
          <span class="inline-flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-full bg-violet-400" /> выход</span>
          <span class="inline-flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-full bg-amber-400" /> отыгрыш</span>
          <span class="inline-flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-full bg-lime-400" /> контроль</span>
          <span class="inline-flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-full bg-orange-400" /> дуплеты</span>
          <span class="inline-flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-full bg-pink-400" /> особые</span>
          <span class="inline-flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-full bg-indigo-400" /> серии</span>
        </div>
      </section>

      <section class="mt-6 grid gap-4 md:grid-cols-2">
        <article v-for="exercise in filtered" :key="exercise.id" class="card-surface p-4">
          <div class="flex flex-wrap items-center gap-2 text-xs">
            <span class="rounded-full px-2 py-0.5" :class="levelBadgeClass(exercise.level)">
              {{ exercise.level }} — {{ levelLabel(exercise.level) }}
            </span>
            <span class="inline-flex items-center gap-1 text-cloth-muted">
              <span class="h-2.5 w-2.5 rounded-full" :class="categoryDotClass(exercise.category)" />
              {{ exercise.category }}
            </span>
          </div>
          <h3 class="mt-1 font-display text-xl font-bold">{{ exercise.title }}</h3>
          <p class="mt-2 text-sm text-cloth-muted">{{ exercise.description }}</p>
          <div v-if="progressFor(exercise.id)" class="mt-3 rounded-lg border border-white/10 px-3 py-2 text-xs text-cloth-muted">
            Прогресс:
            <strong class="text-cloth-accent">
              {{ progressFor(exercise.id)?.made }}/{{ progressFor(exercise.id)?.attempts }}
              ({{ progressFor(exercise.id)?.rate }}%)
            </strong>
          </div>
          <div class="mt-4 flex items-center justify-between">
            <span class="text-xs text-cloth-muted">Попыток: {{ exercise.target_reps }}</span>
            <NuxtLink :to="`/academy/${exercise.id}`" class="btn-primary text-sm">Открыть</NuxtLink>
          </div>
        </article>
      </section>

      <p v-if="!filtered.length" class="mt-5 text-sm text-cloth-muted">
        По выбранным фильтрам ничего не найдено.
      </p>
    </main>
  </div>
</template>
