<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    /** kolkhoz = /tv; cup = /cup/tv */
    variant?: 'kolkhoz' | 'cup'
  }>(),
  { variant: 'kolkhoz' }
)

const kolkhoz = useKolkhozSync()
const cup = useCupSync()
const sync = computed(() => (props.variant === 'cup' ? cup : kolkhoz))

const { ready } = useHubAuth()
const { canSyncRoom, syncDeniedMessage } = useGameAccess()

const joinInput = ref('')
const busy = ref(false)

const tvPath = computed(() => (props.variant === 'cup' ? '/cup/tv' : '/tv'))
const hostLabel = computed(() =>
  props.variant === 'cup' ? 'Я веду турнир' : 'Я веду партию'
)
const hostHint = computed(() =>
  props.variant === 'cup'
    ? 'Создать код и отправлять сетку и матчи на табло.'
    : 'Создать код и отправлять изменения с этого устройства на табло.'
)

onMounted(() => {
  sync.value.hydrateMeta()
})

const startHost = async () => {
  busy.value = true
  try {
    await sync.value.createRoom()
  } finally {
    busy.value = false
  }
}

const joinAsTv = async () => {
  busy.value = true
  try {
    const ok = await sync.value.joinRoom(joinInput.value)
    if (ok) {
      await navigateTo({
        path: tvPath.value,
        query: { room: sync.value.roomCode.value || undefined }
      })
    }
  } finally {
    busy.value = false
  }
}

const copyCode = async () => {
  if (!sync.value.roomCode.value || !import.meta.client) return
  try {
    await navigator.clipboard.writeText(sync.value.roomCode.value)
  } catch {
    /* ignore */
  }
}

const copyTvLink = async () => {
  if (!sync.value.tvUrl.value) return
  try {
    await navigator.clipboard.writeText(sync.value.tvUrl.value)
  } catch {
    /* ignore */
  }
}
</script>

<template>
  <section class="card-surface p-4">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 class="flex items-center gap-2 font-display text-lg font-bold">
          <AppIcon name="tv" class="text-cloth-accent" /> Общий экран · телефон и табло
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">
          Ведущий отправляет состояние на сервер. Зрители открывают код или ссылку табло — без входа,
          только просмотр. Обновление примерно раз в секунду.
        </p>
      </div>
    </div>

    <div v-if="sync.role.value === 'host' && sync.roomCode.value" class="mt-4 space-y-3">
      <div class="flex flex-wrap items-start gap-4">
        <div class="min-w-[12rem] flex-1 rounded-xl border border-cloth-accent/40 bg-cloth-accent/10 px-4 py-3">
          <p class="text-[10px] uppercase tracking-wider text-cloth-muted">Код комнаты</p>
          <p class="mt-1 font-display text-3xl font-bold tracking-[0.2em] text-cloth-accent">
            {{ sync.roomCode.value }}
          </p>
          <p class="mt-1 text-xs text-cloth-muted">
            обновление № {{ sync.revision.value }}
            <span v-if="sync.lastPushedAt">
              · отправлено {{ new Date(sync.lastPushedAt).toLocaleTimeString('ru-RU') }}
            </span>
          </p>
        </div>
        <RoomQrCode
          v-if="sync.tvUrl.value"
          :url="sync.tvUrl.value"
          label="QR для табло"
          :size="160"
        />
      </div>
      <div class="flex flex-wrap gap-2">
        <button type="button" class="btn-ghost text-xs" @click="copyCode">Копировать код</button>
        <button type="button" class="btn-ghost text-xs" @click="copyTvLink">Копировать ссылку табло</button>
        <NuxtLink
          :to="{ path: tvPath, query: { room: sync.roomCode.value } }"
          class="btn-primary text-xs"
          target="_blank"
        >
          Открыть табло
        </NuxtLink>
        <button type="button" class="btn-ghost text-xs" @click="sync.closeRoom()">Завершить трансляцию</button>
      </div>
    </div>

    <div v-else-if="sync.role.value === 'follower' && sync.roomCode.value" class="mt-4 space-y-2">
      <p class="text-sm">
        Подключено как табло к комнате
        <strong class="text-cloth-accent">{{ sync.roomCode.value }}</strong>
        (обновление № {{ sync.revision.value }})
      </p>
      <button type="button" class="btn-ghost text-xs" @click="sync.leaveRoom()">Отключиться</button>
    </div>

    <div v-else class="mt-4 grid gap-3 sm:grid-cols-2">
      <div class="rounded-xl border border-[color:var(--cloth-border)] p-3">
        <p class="text-sm font-semibold">{{ hostLabel }}</p>
        <p class="mt-1 text-xs text-cloth-muted">{{ hostHint }}</p>
        <button
          type="button"
          class="btn-primary mt-3 text-xs"
          :disabled="busy || (ready && !sync.username.value) || !canSyncRoom"
          @click="startHost"
        >
          {{ busy ? '…' : 'Создать комнату' }}
        </button>
        <p v-if="!canSyncRoom" class="mt-2 text-[11px] text-amber-700">
          {{ syncDeniedMessage }}
        </p>
        <p v-else-if="ready && !sync.username.value" class="mt-2 text-[11px] text-amber-700">
          Нет связи с API Цифрового Сукна.
        </p>
      </div>
      <div class="rounded-xl border border-[color:var(--cloth-border)] p-3">
        <p class="text-sm font-semibold">Я табло / зритель</p>
        <p class="mt-1 text-xs text-cloth-muted">
          Введите код с телефона ведущего — можно с телефона гостя, планшета или TV.
        </p>
        <div class="mt-3 flex gap-2">
          <input
            v-model="joinInput"
            class="field-input flex-1 uppercase tracking-widest"
            maxlength="8"
            placeholder="Код"
            @keyup.enter="joinAsTv"
          />
          <button type="button" class="btn-ghost text-xs" :disabled="busy" @click="joinAsTv">
            Подключить
          </button>
        </div>
      </div>
    </div>

    <p v-if="sync.endedMessage && sync.roomStatus.value !== 'live'" class="mt-3 text-xs text-amber-700">
      {{ sync.endedMessage }}
    </p>
    <p v-if="sync.syncError.value" class="mt-3 text-xs text-red-500">{{ sync.syncError.value }}</p>
  </section>
</template>
