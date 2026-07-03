<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { AdminUser, AdminUserStats } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'
import { useAuthStore } from '~/stores/auth'
import { USER_ROLES, roleLabel } from '~/constants/roles'

definePageMeta({
  middleware: 'admin'
})

const api = useApi()
const auth = useAuthStore()
const items = ref<AdminUser[]>([])
const stats = ref<AdminUserStats | null>(null)
const busy = ref(false)
const error = ref('')
const message = ref('')

const apiErrorMessage = (err: unknown, fallback: string) => {
  const detail = (err as { data?: { detail?: unknown } })?.data?.detail
  if (typeof detail === 'string') {
    return detail
  }
  return fallback
}

const isSelf = (item: AdminUser) => item.username === auth.username

const formatDate = (value: string | null) => {
  if (!value) return '—'
  return new Date(value).toLocaleString('ru-RU')
}

const load = async () => {
  busy.value = true
  error.value = ''
  try {
    ;[stats.value, items.value] = await Promise.all([api.getUserStats(), api.listUsers()])
  } catch {
    error.value = 'Не удалось загрузить пользователей.'
  } finally {
    busy.value = false
  }
}

const changeRole = async (item: AdminUser, role: string) => {
  if (role === item.role) return
  if (isSelf(item) && item.is_admin && role !== 'admin') {
    error.value = 'Нельзя снять права администратора у себя.'
    return
  }
  busy.value = true
  error.value = ''
  message.value = ''
  try {
    await api.updateUser(item.id, { role })
    message.value = `Роль ${item.username}: ${roleLabel(role)}.`
    await load()
  } catch (err) {
    error.value = apiErrorMessage(err, 'Не удалось изменить роль пользователя.')
  } finally {
    busy.value = false
  }
}

const toggleBan = async (item: AdminUser) => {
  if (isSelf(item)) {
    error.value = 'Нельзя заблокировать свой аккаунт.'
    return
  }
  busy.value = true
  error.value = ''
  message.value = ''
  try {
    await api.updateUser(item.id, { is_active: !item.is_active })
    message.value = item.is_active
      ? `Пользователь ${item.username} заблокирован.`
      : `Пользователь ${item.username} разблокирован.`
    await load()
  } catch (err) {
    error.value = apiErrorMessage(err, 'Не удалось изменить статус пользователя.')
  } finally {
    busy.value = false
  }
}

const revokeSessions = async (item: AdminUser) => {
  busy.value = true
  error.value = ''
  message.value = ''
  try {
    await api.revokeUserSessions(item.id)
    message.value = `Сессии ${item.username} отозваны.`
    await load()
  } catch {
    error.value = 'Не удалось отозвать сессии.'
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green md:py-8">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-5 md:gap-6">
      <HubIntro compact />
      <TerminalShell cwd="~/admin/users" session="terminal://dautovtech/admin/users" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p class="mb-1 text-xs uppercase tracking-[0.25em] text-terminal-gray">admin</p>
          <h1 class="mb-2 text-xl">Пользователи</h1>
          <p class="mb-4 text-terminal-gray">
            Список аккаунтов, роли, последний вход, блокировка и отзыв сессий.
          </p>

          <section class="mb-6 rounded-lg border border-terminal-gray/70 bg-black/30 p-4 text-xs text-terminal-gray">
            <h2 class="mb-2 text-sm text-terminal-green">Роли в системе</h2>
            <ul class="space-y-1">
              <li><span class="text-terminal-green">guest</span> — гость без входа.</li>
              <li><span class="text-terminal-green">user</span> — базовый зарегистрированный пользователь.</li>
              <li><span class="text-terminal-green">kent</span>, <span class="text-terminal-green">rodnulka</span>, <span class="text-terminal-green">customer</span> — тематические роли (пока те же права, что у user).</li>
              <li><span class="text-terminal-green">admin</span> — администратор платформы.</li>
            </ul>
            <p class="mt-2">Себе нельзя снять admin или заблокировать аккаунт.</p>
          </section>

          <p v-if="error" class="mb-4 text-red-400">{{ error }}</p>
          <p v-if="message" class="mb-4 text-cyan-300">{{ message }}</p>

          <section
            v-if="stats"
            class="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
          >
            <div class="rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
              <div class="text-xs uppercase text-terminal-gray">Всего</div>
              <div class="mt-1 text-2xl">{{ stats.total }}</div>
            </div>
            <div class="rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
              <div class="text-xs uppercase text-terminal-gray">Активных</div>
              <div class="mt-1 text-2xl text-terminal-green">{{ stats.active }}</div>
            </div>
            <div class="rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
              <div class="text-xs uppercase text-terminal-gray">Заблокировано</div>
              <div class="mt-1 text-2xl text-red-400">{{ stats.banned }}</div>
            </div>
            <div class="rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
              <div class="text-xs uppercase text-terminal-gray">Админов</div>
              <div class="mt-1 text-2xl text-cyan-300">{{ stats.admins }}</div>
            </div>
          </section>

          <section class="overflow-x-auto rounded-lg border border-terminal-gray/80">
            <table class="w-full min-w-[860px] text-left text-sm">
              <thead class="border-b border-terminal-gray/60 text-terminal-gray">
                <tr>
                  <th class="px-4 py-3">username</th>
                  <th class="px-4 py-3">email</th>
                  <th class="px-4 py-3">роль</th>
                  <th class="px-4 py-3">статус</th>
                  <th class="px-4 py-3">последний вход</th>
                  <th class="px-4 py-3">последняя сессия</th>
                  <th class="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in items"
                  :key="item.id"
                  class="border-b border-terminal-gray/40"
                  :class="isSelf(item) ? 'bg-terminal-green/5' : ''"
                >
                  <td class="px-4 py-3">
                    {{ item.username }}
                    <span v-if="isSelf(item)" class="ml-1 text-xs text-terminal-gray">(вы)</span>
                  </td>
                  <td class="px-4 py-3 text-terminal-gray">{{ item.email || '—' }}</td>
                  <td class="px-4 py-3">
                    <select
                      class="rounded border border-terminal-gray/60 bg-black/40 px-2 py-1 text-xs outline-none"
                      :value="item.role"
                      :disabled="busy || (isSelf(item) && item.is_admin)"
                      :title="isSelf(item) && item.is_admin ? 'Нельзя сменить свою роль admin' : ''"
                      @change="changeRole(item, ($event.target as HTMLSelectElement).value)"
                    >
                      <option v-for="role in USER_ROLES" :key="role.id" :value="role.id">
                        {{ role.label }}
                      </option>
                    </select>
                  </td>
                  <td class="px-4 py-3">
                    <span :class="item.is_active ? 'text-terminal-green' : 'text-red-400'">
                      {{ item.is_active ? 'active' : 'banned' }}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-terminal-gray">{{ formatDate(item.last_login_at) }}</td>
                  <td class="px-4 py-3 text-terminal-gray">{{ formatDate(item.last_session_at) }}</td>
                  <td class="px-4 py-3">
                    <div class="flex flex-wrap gap-2">
                      <button
                        class="rounded border border-terminal-gray/60 px-2 py-1 text-xs hover:bg-terminal-green/10 disabled:cursor-not-allowed disabled:opacity-40"
                        :disabled="busy || (isSelf(item) && item.is_active)"
                        :title="isSelf(item) && item.is_active ? 'Нельзя заблокировать себя' : ''"
                        @click="toggleBan(item)"
                      >
                        {{ item.is_active ? 'ban' : 'unban' }}
                      </button>
                      <button
                        class="rounded border border-terminal-gray/60 px-2 py-1 text-xs hover:bg-terminal-green/10"
                        :disabled="busy"
                        @click="revokeSessions(item)"
                      >
                        revoke
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </section>
        </div>
      </TerminalShell>
    </div>
  </main>
</template>
