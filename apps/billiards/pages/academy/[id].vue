<script setup lang="ts">
import ExerciseTable from '~/components/academy/ExerciseTable.vue'
import ExerciseTablePhysics from '~/components/academy/ExerciseTablePhysics.vue'
import exercisesRaw from '~/data/exercises.json'
import type { Exercise, Point2D } from '~/types/academy'

const route = useRoute()
const academy = useAcademyStore()
const sync = useAcademySync()

const exercises = exercisesRaw as Exercise[]
const exercise = computed(() => exercises.find((item) => item.id === String(route.params.id)) || null)

const made = ref(0)
const attempts = ref(0)
const actualCueStop = ref<Point2D | null>(null)
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
    attempts.value = saved?.attempts ?? 0
  },
  { immediate: true }
)

const expectedCueStop = computed(() => exercise.value?.expected_cue_stop || null)
const cueStopTolerance = computed(() => exercise.value?.cue_stop_tolerance ?? 2)

const distToExpected = computed(() => {
  if (!expectedCueStop.value || !actualCueStop.value) return null
  const dx = actualCueStop.value.x - expectedCueStop.value.x
  const dy = actualCueStop.value.y - expectedCueStop.value.y
  return Math.hypot(dx, dy)
})

const isHit = computed(() => {
  if (!expectedCueStop.value || !actualCueStop.value) return false
  const d = distToExpected.value
  return d != null && d <= cueStopTolerance.value
})

const saveResult = async () => {
  if (!exercise.value) return
  saving.value = true
  saveHint.value = ''
  try {
    academy.recordResult(exercise.value.id, made.value, attempts.value)
    const pushed = await sync.pushOne(exercise.value.id)
    saveHint.value = pushed
      ? 'Сохранено локально и в облаке.'
      : 'Сохранено на этом устройстве. Облако сейчас недоступно.'
  } finally {
    saving.value = false
  }
}

const successRate = computed(() => {
  if (attempts.value <= 0) return 0
  return Math.round((Math.max(0, made.value) / Math.max(1, attempts.value)) * 100)
})

const addAttempt = async (mode: 'auto' | 'hit' | 'miss') => {
  if (!exercise.value) return
  if (mode === 'auto') {
    if (!expectedCueStop.value) return
    if (!actualCueStop.value) return
  }

  const hitNow =
    mode === 'hit'
      ? true
      : mode === 'miss'
        ? false
        : expectedCueStop.value
          ? isHit.value
          : false

  attempts.value += 1
  if (hitNow) made.value += 1

  actualCueStop.value = null
  await saveResult()
}

const updatedAt = computed(() => {
  if (!exercise.value) return ''
  const entry = academy.byExercise(exercise.value.id)
  if (!entry) return ''
  return new Date(entry.updatedAt).toLocaleString('ru-RU')
})

</script>

<template>
  <div>
    <main class="page-shell py-6">
      <NuxtLink to="/academy" class="btn-ghost text-sm">← К каталогу</NuxtLink>
      <NuxtLink to="/" class="btn-ghost ml-2 text-sm">Главная</NuxtLink>

      <section v-if="exercise" class="mt-4">
        <div class="card-surface p-5">
          <p class="text-xs uppercase tracking-[0.2em] text-cloth-accent">
            Уровень {{ exercise.level }} · {{ exercise.level_label }} · {{ exercise.category }}
          </p>
          <h1 class="mt-2 font-display text-3xl font-bold">{{ exercise.title }}</h1>
          <p class="mt-3 text-sm text-cloth-muted">{{ exercise.description }}</p>
        </div>

        <ExerciseTablePhysics
          v-if="exercise.physics_demo"
          :exercise="exercise"
          class="mt-5"
        />
        <ExerciseTable
          v-else
          :exercise="exercise"
          class="mt-5"
          :interactiveCueStop="Boolean(exercise.expected_cue_stop)"
          :cueStopPoint="actualCueStop"
          @cueStopSelected="actualCueStop = $event"
        />

        <div class="mt-5 grid gap-5 lg:grid-cols-[1fr_320px]">
          <section class="card-surface p-4">
            <h2 class="font-display text-xl font-bold">Инструкция</h2>
            <ol class="mt-3 list-decimal space-y-2 pl-5 text-sm text-cloth-chalk/85">
              <li v-for="(step, index) in exercise.instructions" :key="`step-${index}`">{{ step }}</li>
            </ol>
          </section>

          <section class="card-surface p-4">
            <h2 class="font-display text-xl font-bold">Результат тренировки</h2>
            <p class="mt-1 text-xs text-cloth-muted">Цель упражнения: {{ exercise.target_reps }} попыток</p>
            <p class="mt-1 text-xs text-cloth-muted">
              <template v-if="sync.isSignedIn">Прогресс синхронизируется с облаком.</template>
              <template v-else>Без API результат хранится только на этом устройстве.</template>
            </p>

            <div class="mt-4 rounded-lg border border-white/10 px-3 py-2 text-sm">
              Забито: <strong class="text-cloth-accent">{{ made }}</strong> / {{ attempts }} попыток
            </div>

            <div class="mt-2 rounded-lg border border-white/10 px-3 py-2 text-sm">
              Точность: <strong class="text-cloth-accent">{{ successRate }}%</strong>
            </div>

            <div v-if="expectedCueStop" class="mt-4 rounded-lg border border-white/10 p-3 text-sm">
              <p class="text-xs text-cloth-muted">Клапштос / остановка: кликните точку остановки битка на схеме.</p>
              <p class="mt-2 text-xs text-cloth-muted">
                Ожидание: (<strong class="text-cloth-accent">{{ expectedCueStop.x.toFixed(1) }}</strong>,
                <strong class="text-cloth-accent">{{ expectedCueStop.y.toFixed(1) }}</strong>) · допуск
                <strong class="text-cloth-accent">{{ cueStopTolerance.toFixed(1) }}</strong>
              </p>
              <p v-if="distToExpected != null" class="mt-1 text-xs text-cloth-muted">
                Фактическое отклонение: <strong class="text-cloth-accent">{{ distToExpected.toFixed(2) }}</strong> →
                <span :class="isHit ? 'text-emerald-300' : 'text-red-300'">
                  {{ isHit ? 'зачёт' : 'мимо' }}
                </span>
              </p>

              <div class="mt-3 grid gap-2">
                <button
                  type="button"
                  class="btn-primary w-full"
                  :disabled="saving || !actualCueStop || !isHit"
                  @click="addAttempt('auto')"
                >
                  Зафиксировать попытку (авто: за зачёт)
                </button>
                <div class="grid grid-cols-2 gap-2">
                  <button type="button" class="btn-ghost w-full" :disabled="saving" @click="addAttempt('hit')">
                    Как забито
                  </button>
                  <button type="button" class="btn-ghost w-full" :disabled="saving" @click="addAttempt('miss')">
                    Как мимо
                  </button>
                </div>
              </div>
            </div>

            <div v-else class="mt-4 grid grid-cols-2 gap-2">
              <button type="button" class="btn-ghost w-full" :disabled="saving" @click="addAttempt('miss')">
                Мимо
              </button>
              <button type="button" class="btn-primary w-full" :disabled="saving" @click="addAttempt('hit')">
                Забито
              </button>
            </div>

            <p v-if="saveHint" class="mt-3 text-xs text-cloth-muted">{{ saveHint }}</p>
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
