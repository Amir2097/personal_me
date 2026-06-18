<script setup lang="ts">
import { ref } from 'vue'
import { useApi } from '~/composables/useApi'
import { useAuthStore } from '~/stores/auth'

const props = defineProps<{
  mode?: 'login' | 'register'
}>()

const emit = defineEmits<{
  close: []
  success: []
}>()

const api = useApi()
const auth = useAuthStore()
const mode = ref<'login' | 'register'>(props.mode ?? 'login')
const username = ref('')
const email = ref('')
const password = ref('')
const busy = ref(false)
const error = ref('')
const allowRegistration = ref(false)
const showForgotPassword = ref(false)

const loadConfig = async () => {
  try {
    const config = await api.getAuthConfig()
    allowRegistration.value = config.allow_registration
    showForgotPassword.value = config.password_reset_via_email || config.expose_reset_token
  } catch {
    allowRegistration.value = false
  }
}

void loadConfig()

const submit = async () => {
  if (!username.value || !password.value) {
    error.value = 'Заполните логин и пароль.'
    return
  }
  busy.value = true
  error.value = ''
  try {
    const response =
      mode.value === 'login'
        ? await api.login(username.value, password.value)
        : await api.register(username.value, password.value, email.value || undefined)
    auth.setSession(response.username || username.value, response.is_admin ?? false)
    emit('success')
    emit('close')
  } catch {
    error.value =
      mode.value === 'login'
        ? 'Ошибка авторизации.'
        : 'Регистрация не удалась. Возможно, она отключена или логин занят.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
    <div class="w-full max-w-md rounded-xl border border-terminal-gray/80 bg-terminal-black p-6 font-mono text-terminal-green shadow-2xl">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg">{{ mode === 'login' ? 'Вход' : 'Регистрация' }}</h2>
        <button class="text-terminal-gray hover:text-terminal-green" @click="emit('close')">✕</button>
      </div>

      <p class="mb-4 text-xs text-terminal-gray">
        Пароль не вводится в терминал — только через эту форму.
      </p>

      <form class="space-y-3" @submit.prevent="submit">
        <input
          v-model="username"
          type="text"
          autocomplete="username"
          placeholder="логин"
          class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
        />
        <input
          v-if="mode === 'register'"
          v-model="email"
          type="email"
          autocomplete="email"
          placeholder="email (для сброса пароля)"
          class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
        />
        <input
          v-model="password"
          type="password"
          :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
          placeholder="пароль"
          class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
        />
        <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
        <button
          type="submit"
          class="w-full rounded border border-terminal-green/50 py-2 text-sm hover:bg-terminal-green/10"
          :disabled="busy"
        >
          {{ mode === 'login' ? 'Войти' : 'Зарегистрироваться' }}
        </button>
      </form>

      <div v-if="mode === 'login' && showForgotPassword" class="mt-3 text-center text-xs">
        <NuxtLink to="/forgot-password" class="text-terminal-gray underline hover:text-terminal-green" @click="emit('close')">
          забыли пароль?
        </NuxtLink>
      </div>

      <div v-if="allowRegistration" class="mt-4 text-center text-xs text-terminal-gray">
        <button
          v-if="mode === 'login'"
          class="underline hover:text-terminal-green"
          @click="mode = 'register'"
        >
          создать аккаунт
        </button>
        <button
          v-else
          class="underline hover:text-terminal-green"
          @click="mode = 'login'"
        >
          уже есть аккаунт
        </button>
      </div>
    </div>
  </div>
</template>
