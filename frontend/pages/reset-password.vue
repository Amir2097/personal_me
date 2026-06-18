<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApi } from '~/composables/useApi'

const route = useRoute()
const router = useRouter()
const api = useApi()

const token = ref('')
const password = ref('')
const confirm = ref('')
const busy = ref(false)
const error = ref('')
const success = ref(false)

onMounted(() => {
  token.value = String(route.query.token || '')
  if (!token.value) {
    error.value = 'Ссылка недействительна: отсутствует токен.'
  }
})

const submit = async () => {
  if (!token.value) {
    return
  }
  if (password.value.length < 8) {
    error.value = 'Пароль должен быть не короче 8 символов.'
    return
  }
  if (password.value !== confirm.value) {
    error.value = 'Пароли не совпадают.'
    return
  }
  busy.value = true
  error.value = ''
  try {
    await api.confirmPasswordReset(token.value, password.value)
    success.value = true
    setTimeout(() => router.push('/'), 2000)
  } catch {
    error.value = 'Токен недействителен или истёк.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-terminal-black px-4 text-terminal-green">
    <div class="w-full max-w-md rounded-xl border border-terminal-gray/80 bg-black/40 p-6 font-mono">
      <h1 class="mb-2 text-lg">Новый пароль</h1>

      <p v-if="success" class="text-sm text-cyan-300">
        Пароль обновлён. Перенаправление на терминал…
      </p>

      <form v-else class="space-y-3" @submit.prevent="submit">
        <input
          v-model="password"
          type="password"
          autocomplete="new-password"
          placeholder="новый пароль"
          class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
        />
        <input
          v-model="confirm"
          type="password"
          autocomplete="new-password"
          placeholder="повторите пароль"
          class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
        />
        <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
        <button
          type="submit"
          class="w-full rounded border border-terminal-green/50 py-2 text-sm hover:bg-terminal-green/10"
          :disabled="busy || !token"
        >
          Сохранить
        </button>
      </form>

      <NuxtLink to="/" class="mt-6 inline-block text-xs text-terminal-gray hover:text-terminal-green">
        ← терминал
      </NuxtLink>
    </div>
  </main>
</template>
