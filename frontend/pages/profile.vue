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

const form = reactive({
  display_name: '',
  avatar_url: '',
  email: '',
  bio: '',
  location: '',
  website: '',
  telegram: '',
  github: ''
})

const createdAt = ref<string | null>(null)
const lastLoginAt = ref<string | null>(null)
const currentPassword = ref('')
const newPassword = ref('')
const newPasswordConfirm = ref('')
const busyProfile = ref(false)
const busyPassword = ref(false)
const message = ref('')
const error = ref('')

useSiteSeo({
  title: 'Profile',
  description: 'Личный кабинет DAUTOVTECH',
  path: '/profile'
})

const formatDate = (value: string | null | undefined) => {
  if (!value) return '—'
  return new Date(value).toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const applyProfile = (profile: Awaited<ReturnType<typeof api.me>>) => {
  auth.setProfile(profile)
  form.display_name = profile.display_name || ''
  form.avatar_url = profile.avatar_url || ''
  form.email = profile.email || ''
  form.bio = profile.bio || ''
  form.location = profile.location || ''
  form.website = profile.website || ''
  form.telegram = profile.telegram || ''
  form.github = profile.github || ''
  createdAt.value = profile.created_at ?? null
  lastLoginAt.value = profile.last_login_at ?? null
}

onMounted(async () => {
  try {
    applyProfile(await api.me())
  } catch {
    await navigateTo('/')
  }
})

const onAvatarUpdated = (avatarUrl: string) => {
  form.avatar_url = avatarUrl
  auth.setProfile({
    username: auth.username,
    is_admin: auth.isAdmin,
    display_name: form.display_name,
    avatar_url: avatarUrl,
    email: form.email
  })
  message.value = avatarUrl ? 'Аватар обновлён.' : 'Аватар удалён.'
  error.value = ''
}

const apiErrorMessage = (err: unknown, fallback: string) => {
  const detail = (err as { data?: { detail?: unknown } })?.data?.detail
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === 'object' && item && 'msg' in item ? String(item.msg) : ''))
      .filter(Boolean)
      .join('; ')
  }
  return fallback
}

const saveProfile = async () => {
  busyProfile.value = true
  error.value = ''
  message.value = ''
  try {
    const profile = await api.updateProfile({
      display_name: form.display_name.trim(),
      avatar_url: form.avatar_url.trim(),
      email: form.email.trim() || null,
      bio: form.bio.trim(),
      location: form.location.trim(),
      website: form.website.trim(),
      telegram: form.telegram.trim(),
      github: form.github.trim()
    })
    applyProfile(profile)
    message.value = 'Профиль сохранён.'
  } catch (err) {
    error.value = apiErrorMessage(err, 'Не удалось сохранить профиль.')
  } finally {
    busyProfile.value = false
  }
}

const savePassword = async () => {
  if (!currentPassword.value || !newPassword.value || !newPasswordConfirm.value) {
    error.value = 'Заполните все поля пароля.'
    return
  }
  if (newPassword.value !== newPasswordConfirm.value) {
    error.value = 'Новый пароль и подтверждение не совпадают.'
    return
  }
  if (newPassword.value.length < 8) {
    error.value = 'Новый пароль должен быть не короче 8 символов.'
    return
  }
  busyPassword.value = true
  error.value = ''
  message.value = ''
  try {
    await api.changePassword(currentPassword.value, newPassword.value, newPasswordConfirm.value)
    auth.logout()
    message.value = 'Пароль изменён. Войдите снова.'
    currentPassword.value = ''
    newPassword.value = ''
    newPasswordConfirm.value = ''
  } catch (err) {
    error.value = apiErrorMessage(err, 'Смена пароля не удалась. Проверьте текущий пароль.')
  } finally {
    busyPassword.value = false
  }
}
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green md:py-8">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-5 md:gap-6">
      <HubIntro compact />
      <TerminalShell cwd="~/profile" session="terminal://dautovtech/profile" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">личный кабинет</p>

          <section
            class="mt-4 flex flex-col gap-4 rounded-lg border border-terminal-gray/70 bg-black/30 p-4 sm:flex-row sm:items-center"
          >
            <UserAvatar
              :username="auth.username"
              :display-name="form.display_name"
              :avatar-url="form.avatar_url"
              size="lg"
            />
            <div class="min-w-0 flex-1">
              <h1 class="truncate text-xl">{{ auth.displayLabel }}</h1>
              <p class="mt-1 text-terminal-gray">@{{ auth.username }}</p>
              <p v-if="auth.isAdmin" class="mt-1 text-xs text-amber-300">role: admin</p>
              <p v-else-if="auth.isAuthenticated" class="mt-1 text-xs text-terminal-gray">role: {{ auth.role }} ({{ auth.roleLabel }})</p>
              <div class="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-terminal-gray">
                <span>создан: {{ formatDate(createdAt) }}</span>
                <span>вход: {{ formatDate(lastLoginAt) }}</span>
              </div>
            </div>
          </section>

          <form @submit.prevent="saveProfile">
          <div class="mt-6 grid gap-6 lg:grid-cols-2">
            <section class="space-y-4 rounded-lg border border-terminal-gray/70 bg-black/30 p-4">
              <h2 class="text-terminal-gray">Публичный профиль</h2>
              <p class="text-xs text-terminal-gray">
                Ник и аватар отображаются в терминале и навигации.
              </p>

              <AvatarUpload
                :username="auth.username"
                :display-name="form.display_name"
                :avatar-url="form.avatar_url"
                :disabled="busyProfile"
                @updated="onAvatarUpdated"
              />

              <label class="block space-y-1">
                <span class="text-xs text-terminal-gray">Отображаемое имя</span>
                <input
                  v-model="form.display_name"
                  type="text"
                  maxlength="64"
                  placeholder="Как вас показывать"
                  class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none focus:border-terminal-green/50"
                />
              </label>

              <details class="text-xs text-terminal-gray">
                <summary class="cursor-pointer hover:text-terminal-green">Или укажите URL картинки</summary>
                <label class="mt-2 block space-y-1">
                  <span class="text-terminal-gray">Внешняя ссылка на аватар</span>
                  <input
                    v-model="form.avatar_url"
                    type="text"
                    maxlength="512"
                    placeholder="https://... или /api/v1/uploads/..."
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none focus:border-terminal-green/50"
                  />
                </label>
              </details>

              <label class="block space-y-1">
                <span class="text-xs text-terminal-gray">О себе</span>
                <textarea
                  v-model="form.bio"
                  rows="3"
                  maxlength="500"
                  placeholder="Коротко о вас"
                  class="w-full resize-y rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none focus:border-terminal-green/50"
                />
              </label>

              <label class="block space-y-1">
                <span class="text-xs text-terminal-gray">Локация</span>
                <input
                  v-model="form.location"
                  type="text"
                  maxlength="128"
                  placeholder="Город, страна"
                  class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none focus:border-terminal-green/50"
                />
              </label>

              <button
                type="submit"
                class="rounded border border-terminal-green/50 px-4 py-2 hover:bg-terminal-green/10 disabled:opacity-50"
                :disabled="busyProfile"
              >
                Сохранить профиль
              </button>
            </section>

            <div class="space-y-6">
              <section class="space-y-4 rounded-lg border border-terminal-gray/70 bg-black/30 p-4">
                <h2 class="text-terminal-gray">Контакты и ссылки</h2>

                <label class="block space-y-1">
                  <span class="text-xs text-terminal-gray">Email</span>
                  <input
                    v-model="form.email"
                    type="email"
                    placeholder="email@example.com"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none focus:border-terminal-green/50"
                  />
                </label>

                <label class="block space-y-1">
                  <span class="text-xs text-terminal-gray">Сайт</span>
                  <input
                    v-model="form.website"
                    type="text"
                    maxlength="256"
                    placeholder="https://yoursite.dev"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none focus:border-terminal-green/50"
                  />
                </label>

                <label class="block space-y-1">
                  <span class="text-xs text-terminal-gray">Telegram</span>
                  <input
                    v-model="form.telegram"
                    type="text"
                    maxlength="128"
                    placeholder="@username"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none focus:border-terminal-green/50"
                  />
                </label>

                <label class="block space-y-1">
                  <span class="text-xs text-terminal-gray">GitHub</span>
                  <input
                    v-model="form.github"
                    type="text"
                    maxlength="256"
                    placeholder="username или полный URL"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none focus:border-terminal-green/50"
                  />
                </label>

                <button
                  type="submit"
                  class="rounded border border-terminal-green/50 px-4 py-2 hover:bg-terminal-green/10 disabled:opacity-50"
                  :disabled="busyProfile"
                >
                  Сохранить контакты
                </button>
              </section>

              <section class="space-y-3 rounded-lg border border-terminal-gray/70 bg-black/30 p-4">
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
            </div>
          </div>
          </form>

          <form class="mt-6 max-w-lg space-y-3 rounded-lg border border-terminal-gray/70 bg-black/30 p-4" @submit.prevent="savePassword">
            <h2 class="text-terminal-gray">Безопасность</h2>
            <p class="text-xs text-terminal-gray">После смены пароля потребуется повторный вход.</p>

            <label class="block space-y-1">
              <span class="text-xs text-terminal-gray">Текущий пароль</span>
              <PasswordInput v-model="currentPassword" autocomplete="current-password" placeholder="текущий пароль" />
            </label>

            <label class="block space-y-1">
              <span class="text-xs text-terminal-gray">Новый пароль</span>
              <PasswordInput v-model="newPassword" autocomplete="new-password" placeholder="новый пароль (мин. 8)" />
            </label>

            <label class="block space-y-1">
              <span class="text-xs text-terminal-gray">Подтверждение нового пароля</span>
              <PasswordInput
                v-model="newPasswordConfirm"
                autocomplete="new-password"
                placeholder="повторите новый пароль"
              />
            </label>

            <button
              type="submit"
              class="rounded border border-terminal-green/50 px-4 py-2 hover:bg-terminal-green/10 disabled:opacity-50"
              :disabled="busyPassword"
            >
              Сменить пароль
            </button>
          </form>

          <p v-if="message" class="mt-4 text-cyan-300">{{ message }}</p>
          <p v-if="error" class="mt-4 text-red-400">{{ error }}</p>
        </div>
      </TerminalShell>
    </div>
  </main>
</template>
