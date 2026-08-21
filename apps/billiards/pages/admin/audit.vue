<script setup lang="ts">
const { loadAudit } = useSuknoAdmin()

const entries = ref<Awaited<ReturnType<typeof loadAudit>>>([])
const error = ref('')
const busy = ref(false)

const actionLabel: Record<string, string> = {
  'admin.user.update': 'Пользователь',
  'site.settings.update': 'SEO / сайт',
  'admin.legacy_unlock': 'Ключ установки',
  'admin.totp.enable': '2FA включена',
  'admin.totp.disable': '2FA отключена'
}

const formatDetails = (details: Record<string, unknown>) => {
  const parts: string[] = []
  for (const [key, value] of Object.entries(details)) {
    if (value && typeof value === 'object' && 'from' in value && 'to' in value) {
      const change = value as { from: unknown; to: unknown }
      parts.push(`${key}: ${String(change.from)} → ${String(change.to)}`)
    } else {
      parts.push(`${key}: ${JSON.stringify(value)}`)
    }
  }
  return parts.join('; ') || '—'
}

const refresh = async () => {
  error.value = ''
  busy.value = true
  try {
    entries.value = await loadAudit(80)
  } catch {
    error.value = 'Не удалось загрузить журнал.'
  } finally {
    busy.value = false
  }
}

onMounted(refresh)

useHead({ title: 'Журнал действий' })
</script>

<template>
  <AdminShell>
    <div class="card-surface overflow-x-auto p-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="font-display text-xl font-bold">Журнал действий</h2>
          <p class="mt-1 text-sm text-cloth-muted">Кто менял роли, SEO и открывал legacy-доступ.</p>
        </div>
        <button type="button" class="btn-ghost btn-touch" :disabled="busy" @click="refresh">Обновить</button>
      </div>
      <p v-if="error" class="mt-3 text-sm text-amber-700">{{ error }}</p>
      <table class="mt-4 w-full min-w-[720px] text-left text-sm">
        <thead class="text-xs uppercase text-cloth-muted">
          <tr>
            <th class="py-2 pr-3">Когда</th>
            <th class="py-2 pr-3">Кто</th>
            <th class="py-2 pr-3">Действие</th>
            <th class="py-2 pr-3">Объект</th>
            <th class="py-2 pr-3">Детали</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in entries" :key="row.id" class="border-t border-cloth-border/60 align-top">
            <td class="py-3 pr-3 whitespace-nowrap text-xs text-cloth-muted">
              {{ new Date(row.created_at).toLocaleString('ru-RU') }}
            </td>
            <td class="py-3 pr-3 font-medium">{{ row.actor_username }}</td>
            <td class="py-3 pr-3">{{ actionLabel[row.action] || row.action }}</td>
            <td class="py-3 pr-3">{{ row.target || '—' }}</td>
            <td class="py-3 pr-3 text-xs text-cloth-muted">{{ formatDetails(row.details) }}</td>
          </tr>
        </tbody>
      </table>
      <p v-if="busy" class="mt-3 text-xs text-cloth-muted">Загрузка…</p>
      <p v-else-if="!entries.length" class="mt-3 text-sm text-cloth-muted">Записей пока нет.</p>
    </div>
  </AdminShell>
</template>
