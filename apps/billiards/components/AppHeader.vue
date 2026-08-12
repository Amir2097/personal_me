<script setup lang="ts">
const config = useRuntimeConfig()
const store = useKolkhozStore()
const { username, ready } = useHubAuth()
const { theme, toggleTheme, hydrateTheme } = useClothTheme()
const sounds = useGameSounds()

const hubHref = computed(() => config.public.hubUrl || '/')
const profileHref = computed(() => `${String(hubHref.value).replace(/\/$/, '')}/profile`)

// Auth/theme from browser only — keep SSR markup stable to avoid hydration mismatch.
const clientReady = ref(false)

onMounted(() => {
  hydrateTheme()
  clientReady.value = true
})
</script>

<template>
  <header class="app-header">
    <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4">
      <div class="flex items-center gap-3">
        <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-cloth-accent/15 text-cloth-accent">
          <AppIcon name="cue" size="lg" />
        </span>
        <div>
          <p class="text-xs uppercase tracking-[0.28em] text-cloth-muted">{{ config.public.brandName }} · хобби</p>
          <NuxtLink to="/" class="font-display text-xl font-bold text-cloth-chalk sm:text-2xl hover:text-cloth-accent">
            Бильярд
          </NuxtLink>
        </div>
      </div>
      <nav class="flex flex-wrap items-center gap-2 text-sm">
        <ClientOnly>
          <a
            v-if="clientReady && ready && username"
            :href="profileHref"
            class="inline-flex items-center gap-2 rounded-xl border border-cloth-accent/35 bg-cloth-accent/10 px-3 py-1.5 text-xs text-cloth-chalk transition hover:border-cloth-accent hover:bg-cloth-accent/20"
            title="Профиль на хабе"
          >
            <PlayerAvatar :name="username" size="sm" />
            <span class="min-w-0">
              <span class="block text-[10px] uppercase tracking-wider text-cloth-muted">профиль</span>
              <span class="block max-w-[9rem] truncate font-semibold text-cloth-accent">{{ username }}</span>
            </span>
          </a>
          <span
            v-else-if="clientReady && ready"
            class="rounded-md border border-amber-400/30 px-2 py-1 text-[11px] text-amber-700"
          >
            не авторизован
          </span>
          <button
            type="button"
            class="btn-ghost inline-flex items-center gap-1 py-1.5 text-xs"
            :title="store.tournament.timerMuted ? 'Включить звуки' : 'Выключить звуки'"
            @click="store.setTimerMuted(!store.tournament.timerMuted); sounds.unlock()"
          >
            <AppIcon :name="store.tournament.timerMuted ? 'volume-off' : 'volume'" size="sm" />
            {{ store.tournament.timerMuted ? 'Звук выкл' : 'Звук' }}
          </button>
          <button
            type="button"
            class="btn-ghost inline-flex items-center gap-1 py-1.5 text-xs"
            :title="theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'"
            @click="toggleTheme"
          >
            <AppIcon :name="theme === 'dark' ? 'sun' : 'moon'" size="sm" />
            {{ theme === 'dark' ? 'Светлая' : 'Тёмная' }}
          </button>
        </ClientOnly>
        <NuxtLink to="/" class="btn-ghost inline-flex items-center gap-1 py-1.5 text-xs">
          <AppIcon name="cue" size="sm" /> Главная
        </NuxtLink>
        <NuxtLink to="/kolkhoz" class="btn-ghost inline-flex items-center gap-1 py-1.5 text-xs">
          <AppIcon name="chip" size="sm" /> Колхоз
        </NuxtLink>
        <NuxtLink to="/academy" class="btn-ghost inline-flex items-center gap-1 py-1.5 text-xs">
          <AppIcon name="ball" size="sm" /> Академия
        </NuxtLink>
        <NuxtLink to="/tv" class="btn-ghost inline-flex items-center gap-1 py-1.5 text-xs">
          <AppIcon name="tv" size="sm" /> Табло
        </NuxtLink>
        <a :href="hubHref" class="btn-ghost py-1.5 text-xs">← Хаб</a>
        <button
          type="button"
          class="btn-ghost inline-flex items-center gap-1 py-1.5 text-xs"
          :disabled="!store.events.length"
          @click="store.undoLast()"
        >
          <AppIcon name="undo" size="sm" /> Отмена
        </button>
      </nav>
    </div>
  </header>
</template>
