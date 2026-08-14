<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    /** Compact strip for play pages (save only + link). */
    compact?: boolean
  }>(),
  { compact: false }
)

const history = useKolkhozHistory()
const { isSignedIn } = useHubAuth()
const titleDraft = ref('')
const message = ref('')

onMounted(() => {
  history.hydrateLastSaved()
  if (!props.compact) void history.refresh()
})

const save = async (asNew = false) => {
  message.value = ''
  const saved = await history.saveCurrent(titleDraft.value, { asNew })
  if (saved) {
    message.value = asNew
      ? `Новая запись: ${saved.title}`
      : `Обновлено: ${saved.title}`
    if (asNew) titleDraft.value = ''
  }
}

const restore = async (id: number) => {
  message.value = ''
  const ok = await history.loadGame(id)
  if (!ok) return
  message.value = 'Партия загружена в локальную сессию.'
  const href =
    useKolkhozStore().mode === 'casual'
      ? '/casual/play'
      : useKolkhozStore().mode === 'tournament'
        ? '/tournament/play'
        : '/'
  await navigateTo(href)
}

const remove = async (id: number) => {
  if (!import.meta.client) return
  if (!window.confirm('Удалить эту партию из истории?')) return
  await history.removeGame(id)
}
</script>

<template>
  <section class="card-surface p-4">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="clipboard" class="text-cloth-accent" /> История партий
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">
          Это <strong class="text-cloth-chalk">снимки по кнопке</strong>, не автозапись.
          В снимок попадает всё текущее состояние: туры, докупы, выбывшие, банк и призовые.
          После первого сохранения можно обновлять ту же запись по ходу турнира.
        </p>
        <p class="mt-2 text-xs text-cloth-accent">Сейчас в сессии: {{ history.sessionHint.value }}</p>
        <p v-if="!isSignedIn" class="mt-2 text-xs text-cloth-muted">
          Партия на этом устройстве уже пишется в браузер.
          Облачные снимки появятся, когда будет доступен API Цифрового Сукна.
        </p>
      </div>
    </div>

    <div class="mt-4 flex flex-wrap items-end gap-2">
      <label class="min-w-[12rem] flex-1 text-xs text-cloth-muted">
        Название (необязательно)
        <input
          v-model="titleDraft"
          class="field-input mt-1 w-full"
          maxlength="200"
          placeholder="Например: Пятница у Саши"
        />
      </label>
      <button
        type="button"
        class="btn-primary text-xs"
        :disabled="history.saving.value"
        @click="save(false)"
      >
        {{
          history.saving.value
            ? 'Сохраняю…'
            : history.lastSavedId.value
              ? 'Обновить запись'
              : 'Сохранить на сервер'
        }}
      </button>
      <button
        v-if="history.lastSavedId.value"
        type="button"
        class="btn-ghost text-xs"
        :disabled="history.saving.value"
        @click="save(true)"
      >
        Сохранить как новую
      </button>
      <button
        v-if="!compact"
        type="button"
        class="btn-ghost text-xs"
        :disabled="history.loading.value"
        @click="history.refresh()"
      >
        Обновить список
      </button>
    </div>

    <p v-if="history.lastSavedTitle.value" class="mt-2 text-[11px] text-cloth-muted">
      Активная запись истории:
      <span class="text-cloth-chalk">{{ history.lastSavedTitle.value }}</span>
    </p>
    <p v-if="message" class="mt-2 text-xs text-cloth-accent">{{ message }}</p>
    <p v-if="history.error.value" class="mt-2 text-xs text-red-500">{{ history.error.value }}</p>

    <ul v-if="!compact && history.games.value.length" class="mt-4 space-y-2">
      <li
        v-for="item in history.games.value"
        :key="item.id"
        class="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-[color:var(--cloth-border)] px-3 py-2 text-sm"
        :class="item.id === history.lastSavedId.value ? 'border-cloth-accent/50' : ''"
      >
        <div class="min-w-0">
          <p class="truncate font-semibold">
            {{ item.title }}
            <span
              v-if="item.id === history.lastSavedId.value"
              class="ml-1 text-[10px] font-bold uppercase tracking-wide text-cloth-accent"
            >
              текущая
            </span>
          </p>
          <p class="text-[11px] text-cloth-muted">
            {{ history.modeLabelRu(item) }}
            · игроков {{ item.player_count }}
            · событий {{ item.event_count }}
            · банк {{ item.bank_total.toLocaleString('ru-RU') }} ₽
            · {{ new Date(item.updated_at || item.created_at).toLocaleString('ru-RU') }}
          </p>
        </div>
        <div class="flex flex-wrap gap-1.5">
          <button type="button" class="btn-primary py-1 text-xs" @click="restore(item.id)">
            Открыть
          </button>
          <button type="button" class="btn-ghost py-1 text-xs text-red-500" @click="remove(item.id)">
            Удалить
          </button>
        </div>
      </li>
    </ul>
    <p
      v-else-if="!compact && !history.loading.value && !history.error.value"
      class="mt-4 text-xs text-cloth-muted"
    >
      Пока нет сохранённых партий. Сохраните после старта турнира и обновляйте запись по ходу туров.
    </p>
  </section>
</template>
