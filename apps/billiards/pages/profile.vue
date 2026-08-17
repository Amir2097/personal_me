<script setup lang="ts">
const suknoAuth = useSuknoAuth()
const route = useRoute()

const form = reactive({
  display_name: '',
  bio: '',
  location: '',
  telegram: ''
})
const email = ref('')
const username = ref('')
const role = ref('')
const emailVerified = ref(false)
const createdAt = ref<string | null>(null)
const lastLoginAt = ref<string | null>(null)
const avatarUrl = ref('')
const totpStatus = ref<Awaited<ReturnType<typeof suknoAuth.totpStatus>> | null>(null)
const totpSetupData = ref<Awaited<ReturnType<typeof suknoAuth.totpSetup>> | null>(null)
const enableCode = ref('')
const disablePassword = ref('')
const disableCode = ref('')
const totpBusy = ref(false)

const currentPassword = ref('')
const newPassword = ref('')
const newPasswordConfirm = ref('')

const busyProfile = ref(false)
const busyPassword = ref(false)
const message = ref('')
const error = ref('')

import { roleLabel as formatRoleLabel } from '~/utils/suknoRoles'

const roleLabel = computed(() => formatRoleLabel(role.value))

const formatDate = (value: string | null) => {
  if (!value) return '—'
  return new Date(value).toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const applyProfile = (profile: Awaited<ReturnType<typeof suknoAuth.loadProfile>>) => {
  username.value = profile.username
  email.value = profile.email
  role.value = profile.role
  emailVerified.value = profile.email_verified
  form.display_name = profile.display_name || ''
  form.bio = profile.bio || ''
  form.location = profile.location || ''
  form.telegram = profile.telegram || ''
  avatarUrl.value = suknoAuth.mediaUrl(profile.avatar_url)
  createdAt.value = profile.created_at ?? null
  lastLoginAt.value = profile.last_login_at ?? null
}

const refreshTotp = async () => {
  try {
    totpStatus.value = await suknoAuth.totpStatus()
  } catch {
    totpStatus.value = null
  }
}

const startTotpSetup = async () => {
  totpBusy.value = true
  error.value = ''
  try {
    totpSetupData.value = await suknoAuth.totpSetup()
    message.value = 'Введите секрет в приложении-аутентификаторе и подтвердите кодом.'
  } catch {
    error.value = '2FA доступна только операторам и администраторам.'
  } finally {
    totpBusy.value = false
  }
}

const confirmTotpEnable = async () => {
  totpBusy.value = true
  error.value = ''
  try {
    totpStatus.value = await suknoAuth.totpEnable(enableCode.value.trim())
    totpSetupData.value = null
    enableCode.value = ''
    message.value = '2FA включена. При следующем входе потребуется код.'
  } catch {
    error.value = 'Неверный код подтверждения.'
  } finally {
    totpBusy.value = false
  }
}

const confirmTotpDisable = async () => {
  totpBusy.value = true
  error.value = ''
  try {
    totpStatus.value = await suknoAuth.totpDisable(disablePassword.value, disableCode.value.trim())
    disablePassword.value = ''
    disableCode.value = ''
    message.value = '2FA отключена.'
  } catch {
    error.value = 'Не удалось отключить 2FA. Проверьте пароль и код.'
  } finally {
    totpBusy.value = false
  }
}

onMounted(async () => {
  try {
    await suknoAuth.fetchMe()
  } catch {
    /* guest */
  }
  if (!suknoAuth.isAccountUser.value) {
    await navigateTo({ path: '/auth/login', query: { redirect: route.fullPath } })
    return
  }
  try {
    applyProfile(await suknoAuth.loadProfile())
    await refreshTotp()
  } catch {
    error.value = 'Не удалось загрузить профиль.'
  }
})

const onAvatarUpdated = (url: string) => {
  avatarUrl.value = suknoAuth.mediaUrl(url)
  message.value = url ? 'Аватар обновлён.' : 'Аватар удалён.'
  error.value = ''
}

const saveProfile = async () => {
  busyProfile.value = true
  error.value = ''
  message.value = ''
  try {
    applyProfile(
      await suknoAuth.updateProfile({
        display_name: form.display_name.trim(),
        bio: form.bio.trim(),
        location: form.location.trim(),
        telegram: form.telegram.trim().replace(/^@/, '')
      })
    )
    message.value = 'Профиль сохранён.'
  } catch {
    error.value = 'Не удалось сохранить профиль.'
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
    await suknoAuth.changePassword(currentPassword.value, newPassword.value)
    await suknoAuth.logout()
    await navigateTo('/auth/login')
  } catch {
    error.value = 'Смена пароля не удалась. Проверьте текущий пароль.'
  } finally {
    busyPassword.value = false
  }
}

useHead({ title: 'Профиль' })
</script>

<template>
  <main class="page-shell py-8 sm:py-10">
    <p class="section-eyebrow">аккаунт</p>
    <h1 class="mt-2 font-display text-3xl font-bold">Личный кабинет</h1>
    <p class="mt-2 max-w-2xl text-sm text-cloth-muted">
      Имя, фото и контакты, которые видят в сервисе. Логин и email меняются только через поддержку зала.
    </p>

    <p v-if="message" class="mt-4 text-sm text-cloth-accent">{{ message }}</p>
    <p v-if="error" class="mt-4 text-sm text-amber-700">{{ error }}</p>

    <section class="card-surface mt-6 flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
      <PlayerAvatar :name="form.display_name || username" :src="avatarUrl" size="xl" />
      <div class="min-w-0 flex-1">
        <h2 class="truncate font-display text-xl font-bold">{{ form.display_name || username }}</h2>
        <p class="mt-1 text-sm text-cloth-muted">@{{ username }} · {{ roleLabel }}</p>
        <p class="mt-1 text-xs text-cloth-muted">
          {{ email }}
          <span v-if="emailVerified"> · email подтверждён</span>
        </p>
        <p class="mt-2 text-xs text-cloth-muted">
          Создан: {{ formatDate(createdAt) }} · вход: {{ formatDate(lastLoginAt) }}
        </p>
      </div>
    </section>

    <div class="mt-6 grid gap-5 lg:grid-cols-2">
      <form class="card-surface space-y-4 p-5" @submit.prevent="saveProfile">
        <h2 class="font-display text-lg font-bold">Публичный профиль</h2>
        <AvatarUpload
          :username="username"
          :display-name="form.display_name"
          :avatar-url="avatarUrl"
          :disabled="busyProfile"
          @updated="onAvatarUpdated"
        />
        <label class="block text-xs text-cloth-muted">
          Отображаемое имя
          <input v-model="form.display_name" class="field-input mt-1 w-full" maxlength="64" placeholder="Как вас представлять" />
        </label>
        <label class="block text-xs text-cloth-muted">
          О себе
          <textarea v-model="form.bio" class="field-input mt-1 w-full" rows="3" maxlength="280" placeholder="Клуб, разряд, любимый формат" />
        </label>
        <label class="block text-xs text-cloth-muted">
          Город
          <input v-model="form.location" class="field-input mt-1 w-full" maxlength="128" placeholder="Казань" />
        </label>
        <label class="block text-xs text-cloth-muted">
          Telegram
          <input v-model="form.telegram" class="field-input mt-1 w-full" maxlength="64" placeholder="username без @" />
        </label>
        <button type="submit" class="btn-primary text-sm" :disabled="busyProfile">
          {{ busyProfile ? 'Сохранение…' : 'Сохранить профиль' }}
        </button>
      </form>

      <div class="space-y-5">
        <form class="card-surface space-y-3 p-5" @submit.prevent="savePassword">
          <h2 class="font-display text-lg font-bold">Пароль</h2>
          <p class="text-xs text-cloth-muted">После смены пароля нужно войти заново.</p>
          <label class="block text-xs text-cloth-muted">
            Текущий пароль
            <input v-model="currentPassword" class="field-input mt-1 w-full" type="password" autocomplete="current-password" />
          </label>
          <label class="block text-xs text-cloth-muted">
            Новый пароль
            <input v-model="newPassword" class="field-input mt-1 w-full" type="password" minlength="8" autocomplete="new-password" />
          </label>
          <label class="block text-xs text-cloth-muted">
            Ещё раз
            <input v-model="newPasswordConfirm" class="field-input mt-1 w-full" type="password" minlength="8" autocomplete="new-password" />
          </label>
          <button type="submit" class="btn-ghost text-sm" :disabled="busyPassword">
            {{ busyPassword ? '…' : 'Сменить пароль' }}
          </button>
        </form>

        <section class="card-surface space-y-3 p-5">
          <h2 class="font-display text-lg font-bold">Двухфакторный вход</h2>
          <p class="text-sm text-cloth-muted">
            Для operator и admin: после пароля — код из Google Authenticator, Authy или аналога.
          </p>
          <div v-if="totpStatus && !totpStatus.eligible" class="text-sm text-cloth-muted">
            Для вашей роли дополнительный код не требуется.
          </div>
          <div v-else-if="totpStatus?.enabled" class="space-y-3">
            <p class="text-sm text-cloth-accent">2FA включена</p>
            <label class="block text-xs text-cloth-muted">
              Пароль
              <input v-model="disablePassword" class="field-input mt-1 w-full" type="password" />
            </label>
            <label class="block text-xs text-cloth-muted">
              Текущий код
              <input v-model="disableCode" class="field-input mt-1 w-full" inputmode="numeric" maxlength="8" />
            </label>
            <button type="button" class="btn-ghost text-sm" :disabled="totpBusy" @click="confirmTotpDisable">
              Отключить 2FA
            </button>
          </div>
          <div v-else-if="totpSetupData" class="space-y-3">
            <TotpQrCode :otpauth-url="totpSetupData.otpauth_url" />
            <p class="break-all font-mono text-xs text-cloth-muted">{{ totpSetupData.secret }}</p>
            <a :href="totpSetupData.otpauth_url" class="break-all text-xs text-cloth-accent underline" target="_blank" rel="noopener">
              Открыть в приложении
            </a>
            <label class="block text-xs text-cloth-muted">
              Код из приложения
              <input v-model="enableCode" class="field-input mt-1 w-full" inputmode="numeric" maxlength="8" />
            </label>
            <button type="button" class="btn-primary text-sm" :disabled="totpBusy" @click="confirmTotpEnable">
              Подтвердить и включить
            </button>
          </div>
          <button
            v-else-if="totpStatus?.eligible"
            type="button"
            class="btn-primary text-sm"
            :disabled="totpBusy"
            @click="startTotpSetup"
          >
            Настроить 2FA
          </button>
          <NuxtLink v-if="suknoAuth.isAdmin.value" to="/admin" class="btn-ghost inline-flex text-sm">Админка</NuxtLink>
        </section>
      </div>
    </div>
  </main>
</template>
