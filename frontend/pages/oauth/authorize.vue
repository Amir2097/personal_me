<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import LoginModal from '~/components/LoginModal.vue'
import { useApi } from '~/composables/useApi'
import { useAuthStore } from '~/stores/auth'

const route = useRoute()
const api = useApi()
const auth = useAuthStore()

const clientId = ref(String(route.query.client_id || ''))
const redirectUri = ref(String(route.query.redirect_uri || ''))
const scope = ref(String(route.query.scope || 'openid profile'))
const state = ref(String(route.query.state || ''))
const nonce = ref(String(route.query.nonce || ''))
const busy = ref(false)
const error = ref('')
const showLogin = ref(false)

onMounted(async () => {
  if (!clientId.value || !redirectUri.value) {
    error.value = 'Некорректные параметры OAuth.'
    return
  }
  const ok = await api.restoreSession()
  if (!ok) {
    showLogin.value = true
  }
})

const approve = async () => {
  busy.value = true
  error.value = ''
  try {
    const result = await $fetch<{ redirect_to: string }>('/api/v1/oidc/authorize/approve', {
      baseURL: import.meta.client ? '' : useRuntimeConfig().apiInternalUrl,
      method: 'POST',
      credentials: 'include',
      body: {
        client_id: clientId.value,
        redirect_uri: redirectUri.value,
        scope: scope.value,
        state: state.value,
        nonce: nonce.value
      }
    })
    window.location.href = result.redirect_to
  } catch {
    error.value = 'Не удалось подтвердить доступ.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-terminal-black px-4 text-terminal-green">
    <div class="w-full max-w-md rounded-xl border border-terminal-gray/80 bg-black/40 p-6 font-mono">
      <h1 class="mb-2 text-lg">Разрешить доступ?</h1>
      <p class="mb-4 text-sm text-terminal-gray">
        Приложение <span class="text-terminal-green">{{ clientId }}</span> запрашивает доступ к вашему аккаунту.
      </p>
      <p v-if="error" class="mb-4 text-sm text-red-400">{{ error }}</p>
      <div class="flex gap-3">
        <button
          class="flex-1 rounded border border-terminal-green/50 py-2 text-sm hover:bg-terminal-green/10"
          :disabled="busy || !auth.isAuthenticated"
          @click="approve"
        >
          Разрешить
        </button>
        <NuxtLink to="/" class="flex-1 rounded border border-terminal-gray/60 py-2 text-center text-sm text-terminal-gray">
          Отмена
        </NuxtLink>
      </div>
    </div>
    <LoginModal
      v-if="showLogin"
      @close="showLogin = false"
      @success="showLogin = false"
    />
  </main>
</template>
