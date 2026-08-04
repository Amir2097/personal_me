<script setup lang="ts">
import LoginModal from '~/components/LoginModal.vue'
import { useApi } from '~/composables/useApi'
import { useAuthStore } from '~/stores/auth'

const config = useRuntimeConfig()
const api = useApi()
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

useSiteSeo({
  title: 'Hobby',
  description: 'Хобби и подсервисы DAUTOVTECH: бильярд «Колхоз» и другие.',
  path: '/hobby'
})

const opening = ref(false)
const openError = ref('')
const showLogin = ref(false)
const sessionChecked = ref(false)

const isAuthenticated = computed(() => auth.isAuthenticated)

const syncSession = async () => {
  try {
    await api.restoreSession()
  } finally {
    sessionChecked.value = true
  }
}

onMounted(async () => {
  await syncSession()
  // Billiards bounced here with ?auth=required. If hub session is already OK,
  // clear the flag so it doesn't feel like an endless re-login loop.
  if (route.query.auth === 'required' && auth.isAuthenticated) {
    openError.value =
      'Сессия на хабе активна. Нажмите «открыть» ещё раз — Kolkhoz подхватит вход через SSO.'
    await clearAuthQuery()
  } else if (route.query.auth === 'required' && !auth.isAuthenticated) {
    showLogin.value = true
    openError.value = 'Для Kolkhoz Manager нужна авторизация.'
  }
})

watch(
  () => route.query.auth,
  (value) => {
    if (!sessionChecked.value) return
    if (value === 'required' && !auth.isAuthenticated) {
      showLogin.value = true
      openError.value = 'Для Kolkhoz Manager нужна авторизация.'
    }
  }
)

const clearAuthQuery = async () => {
  if (route.query.auth) {
    const nextQuery = { ...route.query }
    delete nextQuery.auth
    await router.replace({ path: '/hobby', query: nextQuery })
  }
}

const onLoginSuccess = async () => {
  showLogin.value = false
  openError.value = ''
  await clearAuthQuery()
  await syncSession()
}

const openBilliards = async () => {
  opening.value = true
  openError.value = ''
  try {
    if (!auth.isAuthenticated) {
      openError.value = 'Сначала войдите в аккаунт — раздел хобби открыт всем, а Kolkhoz только авторизованным.'
      showLogin.value = true
      return
    }

    const response = await api.executeCommand('go billiards')
    if (response.requires_auth) {
      openError.value = 'Сессия истекла. Войдите снова через login.'
      auth.logout()
      showLogin.value = true
      return
    }
    if (response.forbidden) {
      openError.value = 'Недостаточно прав для открытия Billiards.'
      return
    }
    const url = response.url || `${(config.public.siteUrl || '').replace(/\/$/, '')}/billiards/`
    window.open(url, '_blank', 'noopener,noreferrer')
  } catch (error) {
    openError.value = error instanceof Error ? error.message : 'Не удалось открыть Billiards.'
  } finally {
    opening.value = false
  }
}
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green md:py-8">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-5 md:gap-6">
      <HubIntro compact />
      <TerminalShell cwd="~/hobby" session="terminal://dautovtech/hobby" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">hobby</p>
          <h1 class="mt-2 text-xl">Хобби и подсервисы</h1>
          <p class="mt-2 max-w-2xl text-terminal-gray">
            Раздел {{ config.public.brandName || 'DAUTOVTECH' }} /hobby доступен без входа.
            Запуск подсервисов (Kolkhoz Manager) — только после авторизации.
          </p>

          <div
            v-if="sessionChecked && !isAuthenticated"
            class="mt-4 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-xs text-amber-100"
          >
            <p class="font-medium text-amber-200">Нужна авторизация для запуска</p>
            <p class="mt-1 text-amber-100/80">
              Страницу хобби можно смотреть свободно. Чтобы открыть Kolkhoz Manager, войдите в аккаунт
              (кнопка ниже или команда <code class="text-terminal-green">login</code> в терминале).
            </p>
            <button
              type="button"
              class="mt-3 rounded border border-amber-400/50 px-3 py-1.5 text-amber-100 transition hover:bg-amber-400/10"
              @click="showLogin = true"
            >
              Войти
            </button>
          </div>

          <div
            v-else-if="sessionChecked && isAuthenticated"
            class="mt-4 rounded-lg border border-terminal-green/30 bg-terminal-green/5 px-4 py-3 text-xs text-terminal-gray"
          >
            Сессия:
            <span class="text-terminal-green">{{ auth.displayLabel }}</span>
            — можно открыть Kolkhoz Manager.
          </div>

          <div class="mt-6 grid gap-4 md:grid-cols-2">
            <button
              type="button"
              class="block rounded-lg border border-terminal-gray/70 bg-black/30 p-5 text-left transition hover:border-terminal-green/50 hover:bg-terminal-green/5 disabled:opacity-60"
              :disabled="opening"
              @click="openBilliards"
            >
              <p class="text-xs uppercase tracking-widest text-amber-300">
                billiards · {{ isAuthenticated ? 'ready' : 'login required' }}
              </p>
              <h2 class="mt-2 text-lg text-terminal-green">Kolkhoz Manager</h2>
              <p class="mt-2 text-xs leading-relaxed text-terminal-gray">
                Русский бильярд «Колхоз»: быстрый стол с цветными шарами и турнир по турам
                с категориями, тарифами, рассадкой и TV-табло. Offline-first.
              </p>
              <p class="mt-4 text-xs text-cyan-300">
                <template v-if="opening">открываю через SSO…</template>
                <template v-else-if="!isAuthenticated">войти и открыть /billiards/ →</template>
                <template v-else>открыть /billiards/ →</template>
              </p>
              <p v-if="openError" class="mt-2 text-[11px] text-red-400">{{ openError }}</p>
              <p class="mt-2 text-[11px] text-terminal-gray">
                Если видите 502 — контейнер <code class="text-terminal-green">billiards</code> ещё стартует
                (<code class="text-terminal-green">docker compose logs -f billiards</code>).
              </p>
            </button>

            <div class="rounded-lg border border-dashed border-terminal-gray/50 bg-black/20 p-5 text-terminal-gray">
              <p class="text-xs uppercase tracking-widest">soon</p>
              <h2 class="mt-2 text-lg">Другие хобби</h2>
              <p class="mt-2 text-xs">Сюда можно добавлять следующие подсервисы платформы.</p>
            </div>
          </div>

          <section class="mt-6 rounded-lg border border-terminal-gray/60 bg-black/20 p-4 text-xs text-terminal-gray">
            <p>Терминал:</p>
            <pre class="mt-2 text-terminal-green">login
services
go billiards</pre>
          </section>
        </div>
      </TerminalShell>
    </div>

    <LoginModal
      v-if="showLogin"
      mode="login"
      @close="showLogin = false"
      @success="onLoginSuccess"
    />
  </main>
</template>
