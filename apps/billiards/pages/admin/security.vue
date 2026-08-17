<script setup lang="ts">
const suknoAuth = useSuknoAuth()

const status = ref<Awaited<ReturnType<typeof suknoAuth.totpStatus>> | null>(null)
const setup = ref<Awaited<ReturnType<typeof suknoAuth.totpSetup>> | null>(null)
const enableCode = ref('')
const disablePassword = ref('')
const disableCode = ref('')
const message = ref('')
const error = ref('')
const busy = ref(false)

const refresh = async () => {
  error.value = ''
  try {
    status.value = await suknoAuth.totpStatus()
  } catch {
    error.value = 'Не удалось загрузить статус 2FA.'
  }
}

const startSetup = async () => {
  error.value = ''
  message.value = ''
  busy.value = true
  try {
    setup.value = await suknoAuth.totpSetup()
    message.value = 'Отсканируйте QR в Google Authenticator / Authy или введите секрет вручную.'
  } catch {
    error.value = '2FA доступна только операторам и администраторам.'
  } finally {
    busy.value = false
  }
}

const confirmEnable = async () => {
  error.value = ''
  busy.value = true
  try {
    status.value = await suknoAuth.totpEnable(enableCode.value.trim())
    setup.value = null
    enableCode.value = ''
    message.value = '2FA включена. При следующем входе потребуется код.'
  } catch {
    error.value = 'Неверный код подтверждения.'
  } finally {
    busy.value = false
  }
}

const confirmDisable = async () => {
  error.value = ''
  busy.value = true
  try {
    status.value = await suknoAuth.totpDisable(disablePassword.value, disableCode.value.trim())
    disablePassword.value = ''
    disableCode.value = ''
    message.value = '2FA отключена.'
  } catch {
    error.value = 'Не удалось отключить 2FA. Проверьте пароль и код.'
  } finally {
    busy.value = false
  }
}

onMounted(refresh)

useHead({ title: 'Безопасность · 2FA' })
</script>

<template>
  <AdminShell>
    <div class="card-surface mx-auto max-w-lg p-6">
      <h2 class="font-display text-xl font-bold">Двухфакторная аутентификация</h2>
      <p class="mt-2 text-sm text-cloth-muted">
        Для ролей <strong>operator</strong> и <strong>admin</strong>. При входе после пароля — код из приложения.
      </p>

      <p v-if="message" class="mt-4 text-sm text-cloth-accent">{{ message }}</p>
      <p v-if="error" class="mt-4 text-sm text-amber-700">{{ error }}</p>

      <div v-if="status && !status.eligible" class="mt-4 text-sm text-cloth-muted">
        Ваша роль не поддерживает 2FA. Обратитесь к администратору для повышения до operator.
      </div>

      <div v-else-if="status && status.enabled" class="mt-5 space-y-3">
        <p class="text-sm text-cloth-accent">2FA включена ✓</p>
        <label class="block text-xs text-cloth-muted">
          Пароль
          <input v-model="disablePassword" class="field-input mt-1 w-full" type="password" />
        </label>
        <label class="block text-xs text-cloth-muted">
          Текущий код 2FA
          <input v-model="disableCode" class="field-input mt-1 w-full" inputmode="numeric" maxlength="8" />
        </label>
        <button type="button" class="btn-ghost text-sm" :disabled="busy" @click="confirmDisable">
          Отключить 2FA
        </button>
      </div>

      <div v-else-if="setup" class="mt-5 space-y-3">
        <TotpQrCode :otpauth-url="setup.otpauth_url" />
        <p class="break-all font-mono text-xs text-cloth-muted">{{ setup.secret }}</p>
        <a
          :href="setup.otpauth_url"
          class="break-all text-xs text-cloth-accent underline"
          target="_blank"
          rel="noopener"
        >
          otpauth://… (открыть в приложении)
        </a>
        <label class="block text-xs text-cloth-muted">
          Код из приложения
          <input v-model="enableCode" class="field-input mt-1 w-full" inputmode="numeric" maxlength="8" />
        </label>
        <button type="button" class="btn-primary text-sm" :disabled="busy" @click="confirmEnable">
          Подтвердить и включить
        </button>
      </div>

      <div v-else-if="status" class="mt-5">
        <button type="button" class="btn-primary text-sm" :disabled="busy" @click="startSetup">
          Настроить 2FA
        </button>
      </div>
    </div>
  </AdminShell>
</template>
