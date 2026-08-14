<script setup lang="ts">
const route = useRoute()
const suknoAuth = useSuknoAuth()

const token = computed(() => String(route.query.token || ''))
const password = ref('')
const message = ref('')
const error = ref('')
const busy = ref(false)

const submit = async () => {
  error.value = ''
  busy.value = true
  try {
    await suknoAuth.confirmPasswordReset(token.value, password.value)
    message.value = 'Пароль обновлён.'
    await navigateTo('/auth/login')
  } catch {
    error.value = 'Не удалось сменить пароль.'
  } finally {
    busy.value = false
  }
}

useHead({ title: 'Новый пароль' })
</script>

<template>
  <div>
    <main class="page-shell py-10">
      <div class="card-surface mx-auto max-w-md p-6">
        <h1 class="font-display text-2xl font-bold">Новый пароль</h1>
        <form class="mt-5 space-y-3" @submit.prevent="submit">
          <label class="block text-xs text-cloth-muted">
            Новый пароль
            <input v-model="password" class="field-input mt-1 w-full" type="password" required minlength="8" />
          </label>
          <p v-if="message" class="text-sm text-cloth-accent">{{ message }}</p>
          <p v-if="error" class="text-sm text-amber-700">{{ error }}</p>
          <button type="submit" class="btn-primary w-full text-sm" :disabled="busy || !token">Сохранить</button>
        </form>
      </div>
    </main>
  </div>
</template>
