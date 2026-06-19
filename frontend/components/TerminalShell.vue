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
  () => props.session || `terminal://personal_me${props.cwd === '~' ? '/session' : props.cwd.replace('~', '')}`
)

const authLabel = computed(() =>
  auth.isAuthenticated ? auth.username || 'user' : 'guest'
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
  return props.tall ? 'min-h-[70vh]' : 'h-[calc(100vh-15rem)] min-h-[480px] max-h-[820px]'
})
</script>

<template>
  <section
    class="relative mx-auto flex w-full max-w-6xl overflow-hidden rounded-xl border border-terminal-gray/90 bg-terminal-black/95 font-mono shadow-2xl shadow-black/40"
    :class="shellHeightClass"
  >
    <button
      type="button"
      class="absolute left-3 top-3 z-20 rounded border border-terminal-gray/70 px-2 py-1 text-[11px] text-terminal-gray md:hidden"
      @click="sidebarOpen = !sidebarOpen"
    >
      ☰ menu
    </button>

    <aside
      class="absolute inset-y-0 left-0 z-10 w-56 shrink-0 border-r border-terminal-gray/80 bg-black/95 p-4 transition-transform md:static md:block md:translate-x-0 md:bg-black/25"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
    >
      <div class="mb-4 text-[11px] uppercase tracking-widest text-terminal-gray">Рабочая область</div>
      <ul class="space-y-2 text-xs" :class="themeStyles.muted">
        <li>cwd: {{ cwd }}</li>
        <li>режим: {{ cwd === '~' ? 'interactive' : 'view' }}</li>
        <li>auth: {{ auth.isAuthenticated ? 'авторизован' : 'гость' }}</li>
        <li v-if="auth.isAdmin">role: admin</li>
      </ul>

      <nav class="mt-4 space-y-1 text-xs">
        <NuxtLink to="/" class="block underline decoration-dotted underline-offset-2" :class="navLinkClass('/')">
          ~ / терминал
        </NuxtLink>
        <NuxtLink to="/projects" :class="navLinkClass('/projects')" @click="sidebarOpen = false">
          ~/projects
        </NuxtLink>
        <NuxtLink to="/about" :class="navLinkClass('/about')" @click="sidebarOpen = false">
          ~/about
        </NuxtLink>
        <NuxtLink to="/resume" :class="navLinkClass('/resume')" @click="sidebarOpen = false">
          ~/resume
        </NuxtLink>
        <template v-if="auth.isAuthenticated">
          <NuxtLink to="/profile" :class="navLinkClass('/profile')" @click="sidebarOpen = false">
            ~/profile
          </NuxtLink>
        </template>
          <NuxtLink to="/contact" :class="navLinkClass('/contact')" @click="sidebarOpen = false">
            ~/contact
          </NuxtLink>
          <template v-if="auth.isAdmin">
          <NuxtLink
            to="/admin/integrations"
            :class="navLinkClass('/admin/integrations')"
            @click="sidebarOpen = false"
          >
            ~/admin/integrations
          </NuxtLink>
          <NuxtLink to="/admin/projects" :class="navLinkClass('/admin/projects')" @click="sidebarOpen = false">
            ~/admin/projects
          </NuxtLink>
          <NuxtLink
            to="/admin/oidc-clients"
            :class="navLinkClass('/admin/oidc-clients')"
            @click="sidebarOpen = false"
          >
            ~/admin/oidc-clients
          </NuxtLink>
          <NuxtLink to="/admin/contacts" :class="navLinkClass('/admin/contacts')" @click="sidebarOpen = false">
            ~/admin/contacts
          </NuxtLink>
          <NuxtLink to="/admin/seo" :class="navLinkClass('/admin/seo')" @click="sidebarOpen = false">
            ~/admin/seo
          </NuxtLink>
          <NuxtLink to="/admin/users" :class="navLinkClass('/admin/users')" @click="sidebarOpen = false">
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
      <header class="terminal-title-bar flex items-center justify-between border-b border-terminal-gray/80 px-4 py-3">
        <div class="flex min-w-0 items-center gap-2">
          <span class="h-3 w-3 shrink-0 rounded-full bg-red-500/90" />
          <span class="h-3 w-3 shrink-0 rounded-full bg-yellow-500/90" />
          <span class="h-3 w-3 shrink-0 rounded-full bg-green-500/90" />
          <span class="ml-3 truncate text-xs" :class="themeStyles.muted">{{ sessionLabel }}</span>
        </div>
        <div class="shrink-0 text-xs text-terminal-gray">с {{ startedAtLabel || '—' }}</div>
      </header>

      <div v-if="$slots.toolbar" class="border-b px-4 py-2" :class="themeStyles.border">
        <slot name="toolbar" />
      </div>

      <div class="flex min-h-0 flex-1 flex-col">
        <slot />
      </div>

      <footer
        class="flex flex-wrap items-center justify-between gap-2 border-t px-4 py-2 text-[11px]"
        :class="[themeStyles.border, themeStyles.muted]"
      >
        <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
          <BrandStamp variant="micro" class="hidden sm:inline-flex" />
          <span>{{ authLabel }}@personal-me</span>
          <span>theme:{{ themeLabel }}</span>
          <span>cwd:{{ cwd }}</span>
          <slot name="status" />
        </div>
        <div class="flex items-center gap-3">
          <slot name="status-actions" />
          <NuxtLink to="/legal/privacy" class="text-terminal-gray hover:text-terminal-green">privacy</NuxtLink>
          <NuxtLink to="/legal/terms" class="text-terminal-gray hover:text-terminal-green">terms</NuxtLink>
          <BrandStamp variant="micro" />
          <NuxtLink to="/" class="text-terminal-gray hover:text-terminal-green">cd ~</NuxtLink>
        </div>
      </footer>
    </div>
  </section>
</template>
