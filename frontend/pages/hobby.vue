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
    openError.value = 'Сессия на хабе активна. Нажмите «открыть» — Kolkhoz подхватит вход через SSO.'
    await clearAuthQuery()
  } else if (route.query.auth === 'required' && !auth.isAuthenticated) {
    showLogin.value = true
    openError.value = 'Для облачного синка Kolkhoz войдите в хаб. Сам сервис уже открывается без входа.'
  }
})

watch(
  () => route.query.auth,
  (value) => {
    if (!sessionChecked.value) return
    if (value === 'required' && !auth.isAuthenticated) {
      showLogin.value = true
      openError.value = 'Для облачного синка Kolkhoz войдите в хаб. Сам сервис уже открывается без входа.'
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

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

/** Wait until Nuxt billiards answers (avoid burning SSO codes on nginx boot page). */
const waitForBilliardsReady = async () => {
  const maxAttempts = 36 // ~3 minutes
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    openError.value = `Жду готовности Kolkhoz… (${attempt}/${maxAttempts})`
    try {
      const response = await fetch('/billiards/', {
        method: 'GET',
        cache: 'no-store',
        redirect: 'manual'
      })
      const starting =
        response.headers.get('x-service-starting') === '1' ||
        response.status === 502 ||
        response.status === 503 ||
        response.status === 504
      if (starting) {
        await sleep(5000)
        continue
      }
      // Any other HTTP response means Nuxt is listening (200, 302, opaque redirect, etc.).
      return true
    } catch {
      await sleep(5000)
    }
  }
  return false
}

const openBilliards = async () => {
  opening.value = true
  openError.value = ''
  try {
    if (!auth.isAuthenticated) {
      const ready = await waitForBilliardsReady()
      if (!ready) {
        openError.value =
          'Бильярд ещё не поднялся. Проверьте `docker compose logs -f billiards` и попробуйте снова через минуту.'
        return
      }
      window.open('/billiards/', '_blank', 'noopener,noreferrer')
      return
    }

    const ready = await waitForBilliardsReady()
    if (!ready) {
      openError.value =
        'Kolkhoz ещё не поднялся. Проверьте `docker compose logs -f billiards` и попробуйте снова через минуту.'
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
    openError.value = ''
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
            Бильярд открывается сразу: игра, сетка и табло локальные. Вход нужен только чтобы
            подтянуть облачный синк через SSO.
          </p>

          <div
            v-if="sessionChecked && !isAuthenticated"
            class="mt-4 rounded-lg border border-terminal-green/30 bg-terminal-green/5 px-4 py-3 text-xs text-terminal-gray"
          >
            <p class="font-medium text-terminal-green">Можно открыть без входа</p>
            <p class="mt-1">
              Kolkhoz Manager работает как отдельный сервис. Если войти в хаб, откроется тот же
              адрес с SSO — синк табло и история на сервере.
            </p>
            <button
              type="button"
              class="mt-3 rounded border border-terminal-green/50 px-3 py-1.5 text-terminal-green transition hover:bg-terminal-green/10"
              @click="showLogin = true"
            >
              Войти для облака
            </button>
          </div>

          <div
            v-else-if="sessionChecked && isAuthenticated"
            class="mt-4 rounded-lg border border-terminal-green/30 bg-terminal-green/5 px-4 py-3 text-xs text-terminal-gray"
          >
            Сессия:
            <span class="text-terminal-green">{{ auth.displayLabel }}</span>
            — облачный синк через SSO доступен.
          </div>

          <div class="mt-6 grid gap-4 md:grid-cols-2">
            <button
              type="button"
              class="block rounded-lg border border-terminal-gray/70 bg-black/30 p-5 text-left transition hover:border-terminal-green/50 hover:bg-terminal-green/5 disabled:opacity-60"
              :disabled="opening"
              @click="openBilliards"
            >
              <p class="text-xs uppercase tracking-widest text-amber-300">
                billiards · {{ isAuthenticated ? 'sso' : 'standalone' }}
              </p>
              <h2 class="mt-2 text-lg text-terminal-green">Kolkhoz Manager</h2>
              <p class="mt-2 text-xs leading-relaxed text-terminal-gray">
                Русский бильярд: быстрый стол, турнир по турам, олимпийская сетка и TV-табло.
                Открывается без входа; хаб остаётся необязательным облаком.
              </p>
              <p class="mt-4 text-xs text-cyan-300">
                <template v-if="opening">открываю…</template>
                <template v-else-if="!isAuthenticated">открыть /billiards/ →</template>
                <template v-else>открыть через SSO →</template>
              </p>
              <p v-if="openError" class="mt-2 text-[11px] text-red-400">{{ openError }}</p>
              <p class="mt-2 text-[11px] text-terminal-gray">
                Перед SSO кнопка ждёт, пока Nuxt на <code class="text-terminal-green">:3010</code> ответит —
                иначе nginx отдаёт 502, пока идёт <code class="text-terminal-green">npm install</code>.
                Логи: <code class="text-terminal-green">docker compose logs -f billiards</code>.
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
