<script setup lang="ts">
const route = useRoute()
const suknoAuth = useSuknoAuth()
const { hubEnabled, loginViaHub } = useHubAuth()

const loginName = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)
const configReady = ref(false)

onMounted(async () => {
  try {
    await suknoAuth.loadConfig()
  } finally {
    configReady.value = true
  }
})

const submit = async () => {
  error.value = ''
  busy.value = true
  try {
    const result = await suknoAuth.login(loginName.value.trim(), password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    if (result.requires_totp && result.challenge_token) {
      await navigateTo({
        path: '/auth/totp',
        query: { challenge: result.challenge_token, redirect }
      })
      return
    }
    await navigateTo(redirect)
  } catch {
    error.value = 'Неверный логин или пароль, либо email ещё не подтверждён.'
  } finally {
    busy.value = false
  }
}

useHead({ title: 'Вход' })
</script>

<template>
  <div>
    <main class="page-shell py-10">
      <div class="card-surface mx-auto max-w-md p-6">
        <h1 class="font-display text-2xl font-bold">Вход</h1>
        <p class="mt-2 text-sm text-cloth-muted">Аккаунт Цифрового Сукна.</p>
        <form class="mt-5 space-y-3" @submit.prevent="submit">
          <label class="block text-xs text-cloth-muted">
            Логин или email
            <input v-model="loginName" class="field-input mt-1 w-full" required />
          </label>
          <label class="block text-xs text-cloth-muted">
            Пароль
            <input v-model="password" class="field-input mt-1 w-full" type="password" required />
          </label>
          <p v-if="error" class="text-sm text-amber-700">{{ error }}</p>
          <button type="submit" class="btn-primary w-full text-sm" :disabled="busy">
            {{ busy ? '…' : 'Войти' }}
          </button>
        </form>

        <div v-if="hubEnabled" class="mt-4 space-y-2">
          <p class="text-center text-xs text-cloth-muted">или</p>
          <button type="button" class="btn-ghost w-full text-sm" @click="loginViaHub">
            Войти через DAUTOVTECH
          </button>
          <p class="text-center text-[11px] text-cloth-muted">
            Связать сессию с аккаунтом на портале разработчика.
          </p>
        </div>

        <p class="mt-3 text-center text-sm">
          <NuxtLink to="/auth/forgot-password" class="text-cloth-accent">Забыли пароль?</NuxtLink>
        </p>
        <p v-if="configReady && suknoAuth.registrationAllowed.value" class="mt-2 text-center text-sm text-cloth-muted">
          Нет аккаунта?
          <NuxtLink to="/auth/register" class="text-cloth-accent">Регистрация</NuxtLink>
        </p>
      </div>
    </main>
  </div>
</template>
