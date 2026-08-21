<script setup lang="ts">
const config = useRuntimeConfig()
const suknoAuth = useSuknoAuth()
const { theme, toggleTheme, hydrateTheme } = useClothTheme()
const route = useRoute()

const brandName = computed(() => String(config.public.brandName || 'Цифровое Сукно'))
const clientReady = ref(false)
const menuOpen = ref(false)

const accountLabel = computed(() => {
  const me = suknoAuth.profile.value
  if (me?.source === 'account') return me.display_name || me.username
  return ''
})

const avatarSrc = computed(() => suknoAuth.mediaUrl(suknoAuth.profile.value?.avatar_url))

const navItems = [
  { to: '/kolkhoz', label: 'Колхоз', icon: 'chip' as const },
  { to: '/cup', label: 'Турнир', icon: 'trophy' as const },
  { to: '/academy', label: 'Академия', icon: 'ball' as const }
]

const isActive = (path: string) => {
  const current = route.path
  if (path === '/') return current === '/'
  return current === path || current.startsWith(`${path}/`)
}

const closeMenu = () => {
  menuOpen.value = false
}

const onDocClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement | null
  if (target?.closest('[data-account-menu]')) return
  menuOpen.value = false
}

onMounted(async () => {
  hydrateTheme()
  clientReady.value = true
  document.addEventListener('click', onDocClick)
  try {
    await suknoAuth.fetchMe()
  } catch {
    /* device / guest */
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
})

const logout = async () => {
  closeMenu()
  await suknoAuth.logout()
  await navigateTo('/')
}
</script>

<template>
  <header class="app-header">
    <div class="page-shell flex items-center justify-between gap-4 py-3">
      <NuxtLink to="/" class="shrink-0 no-underline" :title="brandName">
        <BrandLogo compact class="brand-logo" />
      </NuxtLink>

      <nav class="hidden items-center gap-1 md:flex" aria-label="Основное меню">
        <NuxtLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="header-nav-link"
          :class="isActive(item.to) ? 'header-nav-link--active' : ''"
        >
          <AppIcon :name="item.icon" size="sm" />
          {{ item.label }}
        </NuxtLink>
      </nav>

      <div class="flex items-center gap-2">
        <button
          type="button"
          class="header-icon-btn"
          :title="theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'"
          :aria-label="theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'"
          @click="toggleTheme"
        >
          <AppIcon :name="theme === 'dark' ? 'sun' : 'moon'" size="sm" />
        </button>

        <ClientOnly>
          <template v-if="clientReady && suknoAuth.isAccountUser.value">
            <div class="relative" data-account-menu>
              <button
                type="button"
                class="inline-flex items-center gap-2 rounded-full border border-transparent py-1 pl-1 pr-2.5 text-sm text-cloth-chalk transition hover:bg-cloth-accent/10"
                :aria-expanded="menuOpen"
                @click="menuOpen = !menuOpen"
              >
                <PlayerAvatar :name="accountLabel || ''" :src="avatarSrc" size="sm" />
                <span class="hidden max-w-[9rem] truncate font-medium sm:inline">{{ accountLabel }}</span>
              </button>
              <div
                v-if="menuOpen"
                class="absolute right-0 z-40 mt-2 w-48 overflow-hidden rounded-2xl bg-[color:var(--cloth-card-solid)] py-1 shadow-soft ring-1 ring-[color:var(--hairline)]"
              >
                <NuxtLink to="/profile" class="header-menu-item" @click="closeMenu">Профиль</NuxtLink>
                <NuxtLink v-if="suknoAuth.isAdmin.value" to="/admin" class="header-menu-item" @click="closeMenu">
                  Админка
                </NuxtLink>
                <button type="button" class="header-menu-item w-full text-left" @click="logout">Выйти</button>
              </div>
            </div>
          </template>
          <NuxtLink v-else-if="clientReady" to="/auth/login" class="btn-ghost btn-touch px-3">Войти</NuxtLink>
        </ClientOnly>
      </div>
    </div>

    <nav class="page-shell flex gap-1 overflow-x-auto pb-3 md:hidden" aria-label="Разделы">
      <NuxtLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="header-nav-link shrink-0"
        :class="isActive(item.to) ? 'header-nav-link--active' : ''"
      >
        {{ item.label }}
      </NuxtLink>
    </nav>
  </header>
</template>
