<script setup lang="ts">
const { loadUsers, updateUser } = useSuknoAdmin()

const users = ref<Awaited<ReturnType<typeof loadUsers>>>([])
const error = ref('')
const busy = ref(false)

const roleOptions = [
  { value: 'player', label: 'Игрок' },
  { value: 'operator', label: 'Оператор' },
  { value: 'admin', label: 'Администратор' }
]

const refresh = async () => {
  error.value = ''
  busy.value = true
  try {
    users.value = await loadUsers()
  } catch {
    error.value = 'Не удалось загрузить пользователей.'
  } finally {
    busy.value = false
  }
}

const patchUser = async (username: string, payload: { role?: string; is_active?: boolean; display_name?: string }) => {
  error.value = ''
  try {
    await updateUser(username, payload)
    await refresh()
  } catch {
    error.value = `Не удалось обновить ${username}.`
  }
}

onMounted(refresh)

useHead({ title: 'Пользователи' })
</script>

<template>
  <AdminShell>
    <div class="card-surface overflow-x-auto p-4">
      <h2 class="font-display text-xl font-bold">Пользователи</h2>
      <p class="mt-1 text-sm text-cloth-muted">Роли: игрок, оператор зала, администратор.</p>
      <p v-if="error" class="mt-3 text-sm text-amber-700">{{ error }}</p>
      <table class="mt-4 w-full min-w-[640px] text-left text-sm">
        <thead class="text-xs uppercase text-cloth-muted">
          <tr>
            <th class="py-2 pr-3">Логин</th>
            <th class="py-2 pr-3">Email</th>
            <th class="py-2 pr-3">Роль</th>
            <th class="py-2 pr-3">Статус</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.username" class="border-t border-cloth-border/60">
            <td class="py-3 pr-3 font-medium">{{ user.username }}</td>
            <td class="py-3 pr-3">
              {{ user.email }}
              <span v-if="!user.email_verified" class="text-xs text-amber-700"> · не подтверждён</span>
            </td>
            <td class="py-3 pr-3">
              <select
                class="field-input py-1 text-xs"
                :value="user.role"
                @change="patchUser(user.username, { role: ($event.target as HTMLSelectElement).value })"
              >
                <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
              </select>
            </td>
            <td class="py-3 pr-3">
              <label class="inline-flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  :checked="user.is_active"
                  @change="patchUser(user.username, { is_active: ($event.target as HTMLInputElement).checked })"
                />
                активен
              </label>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="busy" class="mt-3 text-xs text-cloth-muted">Загрузка…</p>
    </div>
  </AdminShell>
</template>
