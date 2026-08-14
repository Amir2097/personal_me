<script setup lang="ts">
const route = useRoute()
const suknoAuth = useSuknoAuth()

const challenge = computed(() => String(route.query.challenge || ''))
const code = ref('')
const error = ref('')
const busy = ref(false)

const submit = async () => {
  error.value = ''
  busy.value = true
  try {
    await suknoAuth.verifyTotp(challenge.value, code.value.trim())
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await navigateTo(redirect)
  } catch {
    error.value = 'Неверный код или истёкший challenge. Войдите снова.'
  } finally {
    busy.value = false
  }
}

useHead({ title: 'Код 2FA' })
</script>

<template>
  <div>
    <main class="page-shell py-10">
      <div class="card-surface mx-auto max-w-md p-6">
        <h1 class="font-display text-2xl font-bold">Двухфакторная аутентификация</h1>
        <p class="mt-2 text-sm text-cloth-muted">Введите 6-значный код из приложения-аутентификатора.</p>
        <form class="mt-5 space-y-3" @submit.prevent="submit">
          <label class="block text-xs text-cloth-muted">
            Код
            <input
              v-model="code"
              class="field-input mt-1 w-full tracking-[0.3em]"
              inputmode="numeric"
              autocomplete="one-time-code"
              maxlength="8"
              required
            />
          </label>
          <p v-if="error" class="text-sm text-amber-700">{{ error }}</p>
          <button type="submit" class="btn-primary w-full text-sm" :disabled="busy || !challenge">
            {{ busy ? '…' : 'Подтвердить' }}
          </button>
        </form>
        <p class="mt-4 text-center text-sm">
          <NuxtLink to="/auth/login" class="text-cloth-accent">← Назад ко входу</NuxtLink>
        </p>
      </div>
    </main>
  </div>
</template>
