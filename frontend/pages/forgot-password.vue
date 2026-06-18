<script setup lang="ts">
import { ref } from 'vue'
import { useApi } from '~/composables/useApi'

const api = useApi()
const login = ref('')
const busy = ref(false)
const error = ref('')
const success = ref('')
const showResetLink = ref(false)

const loadConfig = async () => {
  try {
    const config = await api.getAuthConfig()
    showResetLink.value = config.password_reset_via_email || config.expose_reset_token
  } catch {
    showResetLink.value = false
  }
}

void loadConfig()

const submit = async () => {
  if (!login.value.trim()) {
    error.value = 'Введите логин или email.'
    return
  }
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    const response = await api.requestPasswordReset(login.value.trim())
    success.value = response.message
    if (response.reset_token) {
      success.value += ` Токен: ${response.reset_token}`
    }
  } catch {
    error.value = 'Не удалось отправить запрос. Попробуйте позже.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-terminal-black px-4 text-terminal-green">
    <div class="w-full max-w-md rounded-xl border border-terminal-gray/80 bg-black/40 p-6 font-mono">
      <h1 class="mb-2 text-lg">Сброс пароля</h1>
      <p class="mb-4 text-xs text-terminal-gray">
        Введите логин или email. Если аккаунт существует, вы получите инструкции.
      </p>

      <form class="space-y-3" @submit.prevent="submit">
        <input
          v-model="login"
          type="text"
          autocomplete="username"
          placeholder="логин или email"
          class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
        />
        <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
        <p v-if="success" class="text-sm text-cyan-300">{{ success }}</p>
        <button
          type="submit"
          class="w-full rounded border border-terminal-green/50 py-2 text-sm hover:bg-terminal-green/10"
          :disabled="busy"
        >
          Отправить
        </button>
      </form>

      <NuxtLink to="/" class="mt-6 inline-block text-xs text-terminal-gray hover:text-terminal-green">
        ← назад к терминалу
      </NuxtLink>
    </div>
  </main>
</template>
