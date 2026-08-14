<script setup lang="ts">
const suknoAuth = useSuknoAuth()

const login = ref('')
const message = ref('')
const devToken = ref('')
const error = ref('')
const busy = ref(false)

const submit = async () => {
  error.value = ''
  message.value = ''
  devToken.value = ''
  busy.value = true
  try {
    const result = await suknoAuth.requestPasswordReset(login.value.trim())
    message.value = result.message
    if (result.reset_token) devToken.value = result.reset_token
  } catch {
    error.value = 'Не удалось отправить запрос.'
  } finally {
    busy.value = false
  }
}

useHead({ title: 'Сброс пароля' })
</script>

<template>
  <div>
    <main class="page-shell py-10">
      <div class="card-surface mx-auto max-w-md p-6">
        <h1 class="font-display text-2xl font-bold">Сброс пароля</h1>
        <form class="mt-5 space-y-3" @submit.prevent="submit">
          <label class="block text-xs text-cloth-muted">
            Логин или email
            <input v-model="login" class="field-input mt-1 w-full" required />
          </label>
          <p v-if="message" class="text-sm text-cloth-accent">{{ message }}</p>
          <p v-if="devToken" class="break-all font-mono text-xs text-cloth-muted">Dev-токен: {{ devToken }}</p>
          <p v-if="error" class="text-sm text-amber-700">{{ error }}</p>
          <button type="submit" class="btn-primary w-full text-sm" :disabled="busy">Отправить</button>
        </form>
      </div>
    </main>
  </div>
</template>
