<script setup lang="ts">
import ExerciseTable from '~/components/academy/ExerciseTable.vue'
import exercisesRaw from '~/data/exercises.json'
import type { Exercise } from '~/types/academy'

const route = useRoute()
const academy = useAcademyStore()
const sync = useAcademySync()

const exercises = exercisesRaw as Exercise[]
const exercise = computed(() => exercises.find((item) => item.id === String(route.params.id)) || null)

const made = ref(0)
const attempts = ref(1)
const saving = ref(false)
const saveHint = ref('')

onMounted(async () => {
  academy.hydrate()
  await sync.pullAndMerge()
})

watch(
  exercise,
  (value) => {
    if (!value) return
    const saved = academy.byExercise(value.id)
    made.value = saved?.made ?? 0
    attempts.value = saved?.attempts ?? value.target_reps
  },
  { immediate: true }
)

const saveResult = async () => {
  if (!exercise.value) return
  saving.value = true
  saveHint.value = ''
  try {
    academy.recordResult(exercise.value.id, made.value, attempts.value)
    const pushed = await sync.pushOne(exercise.value.id)
    saveHint.value = pushed
      ? 'Сохранено локально и в аккаунте хаба.'
      : 'Сохранено на этом устройстве. Войдите, чтобы синхронизировать.'
  } finally {
    saving.value = false
  }
}

const successRate = computed(() => {
  if (attempts.value <= 0) return 0
  return Math.round((Math.max(0, made.value) / Math.max(1, attempts.value)) * 100)
})

const updatedAt = computed(() => {
  if (!exercise.value) return ''
  const entry = academy.byExercise(exercise.value.id)
  if (!entry) return ''
  return new Date(entry.updatedAt).toLocaleString('ru-RU')
})
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-6xl px-4 py-6">
      <NuxtLink to="/academy" class="btn-ghost text-sm">← К каталогу</NuxtLink>

      <section v-if="exercise" class="mt-4">
        <div class="card-surface p-5">
          <p class="text-xs uppercase tracking-[0.2em] text-cloth-accent">
            Уровень {{ exercise.level }} · {{ exercise.level_label }} · {{ exercise.category }}
          </p>
          <h1 class="mt-2 font-display text-3xl font-bold">{{ exercise.title }}</h1>
          <p class="mt-3 text-sm text-cloth-muted">{{ exercise.description }}</p>
        </div>

        <ExerciseTable :exercise="exercise" class="mt-5" />

        <div class="mt-5 grid gap-5 lg:grid-cols-[1fr_320px]">
          <section class="card-surface p-4">
            <h2 class="font-display text-xl font-bold">Инструкция</h2>
            <ol class="mt-3 list-decimal space-y-2 pl-5 text-sm text-cloth-chalk/85">
              <li v-for="(step, index) in exercise.instructions" :key="`step-${index}`">{{ step }}</li>
            </ol>
          </section>

          <section class="card-surface p-4">
            <h2 class="font-display text-xl font-bold">Результат тренировки</h2>
            <p class="mt-1 text-xs text-cloth-muted">
              Цель упражнения: {{ exercise.target_reps }} попыток
            </p>
            <p class="mt-1 text-xs text-cloth-muted">
              <template v-if="sync.isSignedIn">Прогресс синхронизируется с аккаунтом хаба.</template>
              <template v-else>Без входа результат хранится только на этом устройстве.</template>
            </p>

            <label class="mt-4 block text-sm">
              Забито
              <input v-model.number="made" type="number" min="0" class="field-input mt-1 w-full" />
            </label>

            <label class="mt-3 block text-sm">
              Из попыток
              <input v-model.number="attempts" type="number" min="1" class="field-input mt-1 w-full" />
            </label>

            <div class="mt-3 rounded-lg border border-white/10 px-3 py-2 text-sm">
              Точность: <strong class="text-cloth-accent">{{ successRate }}%</strong>
            </div>

            <button
              type="button"
              class="btn-primary mt-4 w-full"
              :disabled="saving"
              @click="saveResult"
            >
              {{ saving ? 'Сохранение…' : 'Сохранить результат' }}
            </button>
            <p v-if="saveHint" class="mt-2 text-xs text-cloth-muted">{{ saveHint }}</p>
            <p v-if="sync.syncError" class="mt-2 text-xs text-amber-300">{{ sync.syncError }}</p>
            <p v-if="updatedAt" class="mt-2 text-xs text-cloth-muted">Обновлено: {{ updatedAt }}</p>
          </section>
        </div>
      </section>

      <section v-else class="card-surface mt-4 p-5">
        <h2 class="font-display text-xl font-bold">Упражнение не найдено</h2>
        <p class="mt-2 text-sm text-cloth-muted">Проверьте ссылку или откройте карточку заново из каталога.</p>
      </section>
    </main>
  </div>
</template>
