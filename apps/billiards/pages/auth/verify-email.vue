<script setup lang="ts">
const route = useRoute()
const suknoAuth = useSuknoAuth()

const token = computed(() => String(route.query.token || ''))
const status = ref<'idle' | 'ok' | 'error'>('idle')
const message = ref('')

onMounted(async () => {
  if (!token.value) {
    status.value = 'error'
    message.value = 'Токен не передан.'
    return
  }
  try {
    await suknoAuth.verifyEmail(token.value)
    status.value = 'ok'
    message.value = 'Email подтверждён. Теперь можно войти.'
  } catch {
    status.value = 'error'
    message.value = 'Ссылка недействительна или истекла.'
  }
})

useHead({ title: 'Подтверждение email' })
</script>

<template>
  <div>
    <main class="page-shell py-10">
      <div class="card-surface mx-auto max-w-md p-6 text-center">
        <h1 class="font-display text-2xl font-bold">Подтверждение email</h1>
        <p class="mt-4 text-sm" :class="status === 'ok' ? 'text-cloth-accent' : 'text-cloth-muted'">
          {{ message || 'Проверяем…' }}
        </p>
        <NuxtLink v-if="status === 'ok'" to="/auth/login" class="btn-primary mt-6 inline-block text-sm">
          Войти
        </NuxtLink>
        <NuxtLink v-else-if="status === 'error'" to="/auth/register" class="btn-ghost mt-6 inline-block text-sm">
          К регистрации
        </NuxtLink>
      </div>
    </main>
  </div>
</template>
