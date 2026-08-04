<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    /** Compact strip for play pages (save only + link). */
    compact?: boolean
  }>(),
  { compact: false }
)

const history = useKolkhozHistory()
const titleDraft = ref('')
const message = ref('')

onMounted(() => {
  if (!props.compact) void history.refresh()
})

const save = async () => {
  message.value = ''
  const saved = await history.saveCurrent(titleDraft.value)
  if (saved) {
    message.value = `Сохранено: ${saved.title}`
    titleDraft.value = ''
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
          Снимки на сервере под вашим аккаунтом хаба — можно восстановить на любом устройстве.
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
      <button type="button" class="btn-primary text-xs" :disabled="history.saving.value" @click="save">
        {{ history.saving.value ? 'Сохраняю…' : 'Сохранить на сервер' }}
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

    <p v-if="message" class="mt-2 text-xs text-cloth-accent">{{ message }}</p>
    <p v-if="history.error.value" class="mt-2 text-xs text-red-500">{{ history.error.value }}</p>

    <ul v-if="!compact && history.games.value.length" class="mt-4 space-y-2">
      <li
        v-for="item in history.games.value"
        :key="item.id"
        class="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-[color:var(--cloth-border)] px-3 py-2 text-sm"
      >
        <div class="min-w-0">
          <p class="truncate font-semibold">{{ item.title }}</p>
          <p class="text-[11px] text-cloth-muted">
            {{ history.modeLabelRu(item) }}
            · игроков {{ item.player_count }}
            · событий {{ item.event_count }}
            · банк {{ item.bank_total.toLocaleString('ru-RU') }} ₽
            · {{ new Date(item.created_at).toLocaleString('ru-RU') }}
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
      Пока нет сохранённых партий.
    </p>
  </section>
</template>
