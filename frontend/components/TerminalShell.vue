<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'
import { useTerminalTheme } from '~/composables/useTerminalTheme'

const props = withDefaults(
  defineProps<{
    cwd?: string
    session?: string
    tall?: boolean
    heightClass?: string
  }>(),
  {
    cwd: '~',
    session: '',
    tall: false,
    heightClass: ''
  }
)

const auth = useAuthStore()
const { theme, themeLabel, themeStyles } = useTerminalTheme()
const route = useRoute()
const startedAtLabel = ref('')
const sidebarOpen = ref(false)

onMounted(() => {
  startedAtLabel.value = new Date().toLocaleTimeString('ru-RU')
})

const sessionLabel = computed(
  () => props.session || `terminal://dautovtech${props.cwd === '~' ? '/session' : props.cwd.replace('~', '')}`
)

const authLabel = computed(() =>
  auth.isAuthenticated ? auth.displayLabel || auth.username || 'user' : 'guest'
)

const isActivePath = (path: string) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path === path || route.path.startsWith(`${path}/`)
}

const navLinkClass = (path: string) => {
  const active = isActivePath(path)
  return [
    'terminal-interactive block',
    active ? 'text-cyan-300 terminal-nav-active' : 'text-terminal-gray hover:text-terminal-green'
  ]
}

const shellHeightClass = computed(() => {
  if (props.heightClass) {
    return props.heightClass
  }
  return props.tall
    ? 'min-h-[60vh] sm:min-h-[70vh]'
    : 'h-[calc(100dvh-11rem)] min-h-[380px] max-h-[820px] sm:h-[calc(100vh-15rem)] sm:min-h-[480px]'
})

const closeSidebar = () => {
  sidebarOpen.value = false
}
</script>

<template>
  <section
    class="relative mx-auto flex w-full max-w-6xl overflow-hidden rounded-xl border border-terminal-gray/90 bg-terminal-black/95 font-mono shadow-2xl shadow-black/40"
    :class="shellHeightClass"
  >
    <button
      v-if="sidebarOpen"
      type="button"
      class="fixed inset-0 z-[15] bg-black/70 md:hidden"
      aria-label="Закрыть меню"
      @click="closeSidebar"
    />

    <aside
      class="absolute inset-y-0 left-0 z-20 w-[min(16rem,85vw)] shrink-0 overflow-y-auto border-r border-terminal-gray/80 bg-black/95 p-4 transition-transform md:static md:z-auto md:block md:w-56 md:translate-x-0 md:bg-black/25"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
    >
      <div class="mb-4 text-[11px] uppercase tracking-widest text-terminal-gray">Рабочая область</div>
      <ul class="space-y-2 text-xs" :class="themeStyles.muted">
        <li>cwd: {{ cwd }}</li>
        <li>режим: {{ cwd === '~' ? 'interactive' : 'view' }}</li>
        <li>auth: {{ auth.isAuthenticated ? 'авторизован' : 'гость' }}</li>
        <li v-if="auth.isAuthenticated">role: {{ auth.role }}</li>
      </ul>

      <div v-if="auth.isAuthenticated" class="mt-4 flex items-center gap-2 rounded border border-terminal-gray/60 bg-black/40 p-2">
        <UserAvatar
          :username="auth.username"
          :display-name="auth.displayName"
          :avatar-url="auth.avatarUrl"
          size="sm"
        />
        <div class="min-w-0 text-xs">
          <div class="truncate text-terminal-green">{{ auth.displayLabel }}</div>
          <div class="truncate text-terminal-gray">@{{ auth.username }}</div>
        </div>
      </div>

      <nav class="mt-4 space-y-1 text-xs">
        <NuxtLink to="/" class="block underline decoration-dotted underline-offset-2" :class="navLinkClass('/')" @click="closeSidebar">
          ~ / терминал
        </NuxtLink>
        <NuxtLink to="/projects" :class="navLinkClass('/projects')" @click="closeSidebar">
          ~/projects
        </NuxtLink>
        <NuxtLink to="/about" :class="navLinkClass('/about')" @click="closeSidebar">
          ~/about
        </NuxtLink>
        <NuxtLink to="/resume" :class="navLinkClass('/resume')" @click="closeSidebar">
          ~/resume
        </NuxtLink>
        <template v-if="auth.isAuthenticated">
          <NuxtLink to="/profile" :class="navLinkClass('/profile')" @click="closeSidebar">
            ~/profile
          </NuxtLink>
        </template>
        <NuxtLink to="/contact" :class="navLinkClass('/contact')" @click="closeSidebar">
          ~/contact
        </NuxtLink>
        <template v-if="auth.isAdmin">
          <NuxtLink
            to="/admin/integrations"
            :class="navLinkClass('/admin/integrations')"
            @click="closeSidebar"
          >
            ~/admin/integrations
          </NuxtLink>
          <NuxtLink to="/admin/projects" :class="navLinkClass('/admin/projects')" @click="closeSidebar">
            ~/admin/projects
          </NuxtLink>
          <NuxtLink
            to="/admin/oidc-clients"
            :class="navLinkClass('/admin/oidc-clients')"
            @click="closeSidebar"
          >
            ~/admin/oidc-clients
          </NuxtLink>
          <NuxtLink to="/admin/contacts" :class="navLinkClass('/admin/contacts')" @click="closeSidebar">
            ~/admin/contacts
          </NuxtLink>
          <NuxtLink to="/admin/seo" :class="navLinkClass('/admin/seo')" @click="closeSidebar">
            ~/admin/seo
          </NuxtLink>
          <NuxtLink to="/admin/users" :class="navLinkClass('/admin/users')" @click="closeSidebar">
            ~/admin/users
          </NuxtLink>
        </template>
      </nav>

      <div class="mt-6 text-[11px] uppercase tracking-widest text-terminal-gray">Подсказки</div>
      <ul class="mt-2 space-y-1 text-xs" :class="themeStyles.muted">
        <li>help · clear</li>
        <li>login · logout</li>
        <li>projects · go &lt;svc&gt;</li>
        <li>theme auto|green|amber|blue</li>
        <li>fx preset retro|hacker</li>
      </ul>
    </aside>

    <div class="flex min-w-0 flex-1 flex-col">
      <header class="terminal-title-bar flex items-center justify-between gap-2 border-b border-terminal-gray/80 px-3 py-2.5 sm:px-4 sm:py-3">
        <div class="flex min-w-0 flex-1 items-center gap-2">
          <button
            type="button"
            class="shrink-0 rounded border border-terminal-gray/70 px-2 py-1 text-[11px] text-terminal-gray hover:text-terminal-green md:hidden"
            aria-label="Открыть меню"
            @click="sidebarOpen = !sidebarOpen"
          >
            ☰
          </button>
          <span class="hidden h-3 w-3 shrink-0 rounded-full bg-red-500/90 sm:inline-block" />
          <span class="hidden h-3 w-3 shrink-0 rounded-full bg-yellow-500/90 sm:inline-block" />
          <span class="hidden h-3 w-3 shrink-0 rounded-full bg-green-500/90 sm:inline-block" />
          <span class="min-w-0 truncate text-[11px] sm:ml-1 sm:text-xs" :class="themeStyles.muted">{{ sessionLabel }}</span>
        </div>
        <div class="shrink-0 text-[10px] text-terminal-gray sm:text-xs">с {{ startedAtLabel || '—' }}</div>
      </header>

      <div v-if="$slots.toolbar" class="border-b px-3 py-2 sm:px-4" :class="themeStyles.border">
        <slot name="toolbar" />
      </div>

      <div class="flex min-h-0 flex-1 flex-col">
        <slot />
      </div>

      <footer
        class="flex flex-col gap-2 border-t px-3 py-2 text-[10px] sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:px-4 sm:text-[11px]"
        :class="[themeStyles.border, themeStyles.muted]"
      >
        <div class="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1 sm:gap-x-3">
          <BrandStamp variant="micro" class="hidden sm:inline-flex" />
          <span v-if="auth.isAuthenticated" class="inline-flex min-w-0 items-center gap-1.5">
            <UserAvatar
              :username="auth.username"
              :display-name="auth.displayName"
              :avatar-url="auth.avatarUrl"
              size="xs"
            />
            <span class="truncate">{{ authLabel }}@dautovtech</span>
          </span>
          <span v-else class="truncate">{{ authLabel }}@dautovtech</span>
          <span class="hidden sm:inline">theme:{{ themeLabel }}</span>
          <span class="hidden md:inline">cwd:{{ cwd }}</span>
          <slot name="status" />
        </div>
        <div class="flex flex-wrap items-center gap-2 sm:gap-3">
          <slot name="status-actions" />
          <NuxtLink to="/legal/privacy" class="text-terminal-gray hover:text-terminal-green">privacy</NuxtLink>
          <NuxtLink to="/legal/terms" class="text-terminal-gray hover:text-terminal-green">terms</NuxtLink>
          <BrandStamp variant="micro" class="sm:hidden" />
          <NuxtLink to="/" class="text-terminal-gray hover:text-terminal-green">cd ~</NuxtLink>
        </div>
      </footer>
    </div>
  </section>
</template>
