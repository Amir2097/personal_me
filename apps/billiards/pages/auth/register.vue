<script setup lang="ts">
const suknoAuth = useSuknoAuth()

const username = ref('')
const email = ref('')
const password = ref('')
const acceptTerms = ref(false)
const error = ref('')
const info = ref('')
const busy = ref(false)
const devToken = ref('')
const configReady = ref(false)

const registrationAllowed = computed(() => suknoAuth.registrationAllowed.value)

onMounted(async () => {
  try {
    await suknoAuth.loadConfig()
  } finally {
    configReady.value = true
  }
})

const submit = async () => {
  error.value = ''
  info.value = ''
  devToken.value = ''
  busy.value = true
  try {
    const result = await suknoAuth.register({
      username: username.value.trim(),
      email: email.value.trim(),
      password: password.value,
      accept_terms: acceptTerms.value
    })
    if (result.verification_required) {
      info.value = result.message
      if (result.verification_token) devToken.value = result.verification_token
      return
    }
    await navigateTo('/')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Не удалось зарегистрироваться.'
  } finally {
    busy.value = false
  }
}

useHead({ title: 'Регистрация' })
</script>

<template>
  <div>
    <main class="page-shell py-10">
      <div class="card-surface mx-auto max-w-md p-6">
        <h1 class="font-display text-2xl font-bold">Регистрация</h1>

        <div v-if="!configReady" class="mt-4 text-sm text-cloth-muted">Загрузка…</div>

        <div v-else-if="!registrationAllowed" class="mt-4 space-y-3">
          <p class="text-sm text-cloth-muted">
            Регистрация новых аккаунтов закрыта администратором зала. Попросите оператора создать
            аккаунт или войдите, если он уже есть.
          </p>
          <NuxtLink to="/auth/login" class="btn-primary inline-block text-sm">Перейти ко входу</NuxtLink>
        </div>

        <template v-else>
          <p class="mt-2 text-sm text-cloth-muted">Аккаунт Цифрового Сукна с подтверждением email.</p>
          <form class="mt-5 space-y-3" @submit.prevent="submit">
            <label class="block text-xs text-cloth-muted">
              Логин
              <input v-model="username" class="field-input mt-1 w-full" required minlength="3" />
            </label>
            <label class="block text-xs text-cloth-muted">
              Email
              <input v-model="email" class="field-input mt-1 w-full" type="email" required />
            </label>
            <label class="block text-xs text-cloth-muted">
              Пароль
              <input v-model="password" class="field-input mt-1 w-full" type="password" required minlength="8" />
            </label>
            <label class="flex items-start gap-2 text-xs text-cloth-muted">
              <input v-model="acceptTerms" type="checkbox" class="mt-1" required />
              <span>
                Согласен с
                <NuxtLink to="/legal/privacy" class="text-cloth-accent">политикой конфиденциальности</NuxtLink>
                и
                <NuxtLink to="/legal/terms" class="text-cloth-accent">пользовательским соглашением</NuxtLink>.
              </span>
            </label>
            <p v-if="error" class="text-sm text-amber-700">{{ error }}</p>
            <p v-if="info" class="text-sm text-cloth-accent">{{ info }}</p>
            <p v-if="devToken" class="break-all font-mono text-xs text-cloth-muted">
              Dev-токен: {{ devToken }}
            </p>
            <button type="submit" class="btn-primary w-full text-sm" :disabled="busy">
              {{ busy ? '…' : 'Создать аккаунт' }}
            </button>
          </form>
          <p class="mt-4 text-center text-sm text-cloth-muted">
            Уже есть аккаунт?
            <NuxtLink to="/auth/login" class="text-cloth-accent">Войти</NuxtLink>
          </p>
        </template>
      </div>
    </main>
  </div>
</template>
