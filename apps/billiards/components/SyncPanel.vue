<script setup lang="ts">
const sync = useKolkhozSync()
const { ready } = useHubAuth()

const joinInput = ref('')
const busy = ref(false)

onMounted(() => {
  sync.hydrateMeta()
})

const startHost = async () => {
  busy.value = true
  try {
    await sync.createRoom()
  } finally {
    busy.value = false
  }
}

const joinAsTv = async () => {
  busy.value = true
  try {
    const ok = await sync.joinRoom(joinInput.value)
    if (ok) await navigateTo({ path: '/tv', query: { room: sync.roomCode.value || undefined } })
  } finally {
    busy.value = false
  }
}

const copyCode = async () => {
  if (!sync.roomCode.value || !import.meta.client) return
  try {
    await navigator.clipboard.writeText(sync.roomCode.value)
  } catch {
    /* ignore */
  }
}

const copyTvLink = async () => {
  if (!sync.tvUrl.value) return
  try {
    await navigator.clipboard.writeText(sync.tvUrl.value)
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
          <AppIcon name="tv" class="text-cloth-accent" /> Синк · телефон ↔ TV
        </h3>
        <p class="mt-1 text-xs text-cloth-muted">
          Хост пушит партию на сервер. Табло на другом устройстве открывает код и обновляется ~раз в секунду.
        </p>
      </div>
    </div>

    <div v-if="sync.role.value === 'host' && sync.roomCode.value" class="mt-4 space-y-3">
      <div class="rounded-xl border border-cloth-accent/40 bg-cloth-accent/10 px-4 py-3">
        <p class="text-[10px] uppercase tracking-wider text-cloth-muted">Код комнаты</p>
        <p class="mt-1 font-display text-3xl font-bold tracking-[0.2em] text-cloth-accent">
          {{ sync.roomCode.value }}
        </p>
        <p class="mt-1 text-xs text-cloth-muted">
          rev {{ sync.revision.value }}
          <span v-if="sync.lastPushedAt.value">
            · пуш {{ new Date(sync.lastPushedAt.value).toLocaleTimeString('ru-RU') }}
          </span>
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button type="button" class="btn-ghost text-xs" @click="copyCode">Копировать код</button>
        <button type="button" class="btn-ghost text-xs" @click="copyTvLink">Копировать ссылку TV</button>
        <NuxtLink
          :to="{ path: '/tv', query: { room: sync.roomCode.value } }"
          class="btn-primary text-xs"
          target="_blank"
        >
          Открыть табло
        </NuxtLink>
        <button type="button" class="btn-ghost text-xs" @click="sync.clearRoom()">Стоп синк</button>
      </div>
    </div>

    <div v-else-if="sync.role.value === 'follower' && sync.roomCode.value" class="mt-4 space-y-2">
      <p class="text-sm">
        Подключено как табло к комнате
        <strong class="text-cloth-accent">{{ sync.roomCode.value }}</strong>
        (rev {{ sync.revision.value }})
      </p>
      <button type="button" class="btn-ghost text-xs" @click="sync.clearRoom()">Отключиться</button>
    </div>

    <div v-else class="mt-4 grid gap-3 sm:grid-cols-2">
      <div class="rounded-xl border border-[color:var(--cloth-border)] p-3">
        <p class="text-sm font-semibold">Я веду партию</p>
        <p class="mt-1 text-xs text-cloth-muted">Создать код и пушить изменения с этого устройства.</p>
        <button
          type="button"
          class="btn-primary mt-3 text-xs"
          :disabled="busy || (ready && !sync.username.value)"
          @click="startHost"
        >
          {{ busy ? '…' : 'Открыть синк' }}
        </button>
        <p v-if="ready && !sync.username.value" class="mt-2 text-[11px] text-amber-700">
          Сначала войдите через хаб (SSO).
        </p>
      </div>
      <div class="rounded-xl border border-[color:var(--cloth-border)] p-3">
        <p class="text-sm font-semibold">Я табло / зритель</p>
        <p class="mt-1 text-xs text-cloth-muted">Введите код с телефона хоста.</p>
        <div class="mt-3 flex gap-2">
          <input
            v-model="joinInput"
            class="field-input flex-1 uppercase tracking-widest"
            maxlength="8"
            placeholder="Код"
            @keyup.enter="joinAsTv"
          />
          <button type="button" class="btn-ghost text-xs" :disabled="busy" @click="joinAsTv">
            Войти
          </button>
        </div>
      </div>
    </div>

    <p v-if="sync.syncError.value" class="mt-3 text-xs text-red-500">{{ sync.syncError.value }}</p>
  </section>
</template>
