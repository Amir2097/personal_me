<script setup lang="ts">
import { useApi } from '~/composables/useApi'
import { useAuthStore } from '~/stores/auth'

definePageMeta({
  middleware: 'auth'
})

const api = useApi()
const auth = useAuthStore()
const { label: fxLabel, setPreset } = useTerminalFx()
const { cursorEnabled, soundEnabled, faviconAlerts } = useTerminalPreferences()
const fxPresets = ['minimal', 'retro', 'hacker', 'off'] as const
const email = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const busy = ref(false)
const message = ref('')
const error = ref('')

useSiteSeo({
  title: 'Profile',
  description: 'Профиль пользователя personal_me',
  path: '/profile'
})

onMounted(async () => {
  try {
    const profile = await api.me()
    auth.setSession(profile.username, profile.is_admin)
    email.value = profile.email || ''
  } catch {
    await navigateTo('/')
  }
})

const saveEmail = async () => {
  busy.value = true
  error.value = ''
  message.value = ''
  try {
    const profile = await api.updateProfile(email.value.trim() || null)
    email.value = profile.email || ''
    message.value = 'Email обновлён.'
  } catch {
    error.value = 'Не удалось обновить email.'
  } finally {
    busy.value = false
  }
}

const savePassword = async () => {
  if (!currentPassword.value || !newPassword.value) {
    error.value = 'Заполните оба поля пароля.'
    return
  }
  busy.value = true
  error.value = ''
  message.value = ''
  try {
    await api.changePassword(currentPassword.value, newPassword.value)
    auth.logout()
    message.value = 'Пароль изменён. Войдите снова.'
    currentPassword.value = ''
    newPassword.value = ''
  } catch {
    error.value = 'Смена пароля не удалась.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green md:py-8">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-5 md:gap-6">
      <HubIntro compact />
      <TerminalShell cwd="~/profile" session="terminal://personal_me/profile" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">profile</p>
          <h1 class="mt-2 text-xl">{{ auth.username }}</h1>
          <p v-if="auth.isAdmin" class="mt-1 text-xs text-amber-300">role: admin</p>

          <section class="mt-6 max-w-md space-y-3 rounded-lg border border-terminal-gray/70 bg-black/30 p-4">
            <h2 class="text-terminal-gray">Email</h2>
            <input
              v-model="email"
              type="email"
              placeholder="email@example.com"
              class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
            />
            <button
              class="rounded border border-terminal-green/50 px-4 py-2 hover:bg-terminal-green/10"
              :disabled="busy"
              @click="saveEmail"
            >
              Сохранить email
            </button>
          </section>

          <section class="mt-6 max-w-md space-y-3 rounded-lg border border-terminal-gray/70 bg-black/30 p-4">
            <h2 class="text-terminal-gray">Оформление терминала</h2>
            <label class="flex items-center gap-2 text-sm">
              <input v-model="cursorEnabled" type="checkbox" class="accent-terminal-green" />
              Блок-курсор
            </label>
            <label class="flex items-center gap-2 text-sm">
              <input v-model="soundEnabled" type="checkbox" class="accent-terminal-green" />
              Звук клавиш
            </label>
            <label class="flex items-center gap-2 text-sm">
              <input v-model="faviconAlerts" type="checkbox" class="accent-terminal-green" />
              Мигание favicon при ошибках
            </label>
            <div class="flex flex-wrap gap-2 pt-1">
              <button
                v-for="preset in fxPresets"
                :key="preset"
                class="rounded border border-terminal-gray/60 px-3 py-1 text-xs hover:bg-terminal-green/10"
                @click="setPreset(preset)"
              >
                fx {{ preset }}
              </button>
            </div>
            <p class="text-xs text-terminal-gray">Текущие эффекты: {{ fxLabel || 'off' }}</p>
          </section>

          <section class="mt-6 max-w-md space-y-3 rounded-lg border border-terminal-gray/70 bg-black/30 p-4">
            <h2 class="text-terminal-gray">Смена пароля</h2>
            <input
              v-model="currentPassword"
              type="password"
              placeholder="текущий пароль"
              class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
            />
            <input
              v-model="newPassword"
              type="password"
              placeholder="новый пароль"
              class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
            />
            <button
              class="rounded border border-terminal-green/50 px-4 py-2 hover:bg-terminal-green/10"
              :disabled="busy"
              @click="savePassword"
            >
              Сменить пароль
            </button>
          </section>

          <p v-if="message" class="mt-4 text-cyan-300">{{ message }}</p>
          <p v-if="error" class="mt-4 text-red-400">{{ error }}</p>
        </div>
      </TerminalShell>
    </div>
  </main>
</template>
