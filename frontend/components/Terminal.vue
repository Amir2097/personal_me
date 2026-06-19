<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import type { Project } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'
import { useTerminalAliases } from '~/composables/useTerminalAliases'
import { useTerminalLogs } from '~/composables/useTerminalLogs'
import { useLocale } from '~/composables/useLocale'
import type { TerminalFxFlag, TerminalFxPreset } from '~/composables/useTerminalFx'
import type { TerminalTheme } from '~/composables/useTerminalTheme'

interface TerminalLine {
  type: 'input' | 'output' | 'error' | 'system'
  value: string
  timestamp: string
}

const EXTENDED_BOOT = [
  'POST ok — personal_me hub',
  'loading kernel modules... ok',
  'mount /dev/portfolio... ok',
  'starting integration daemon... ok',
  'auth subsystem ready',
  'network stack up',
  'session ready — type help for commands'
]

const api = useApi()
const auth = useAuthStore()
const config = useRuntimeConfig()
const { theme, themeLabel, themeStyles } = useTerminalTheme()
const { label: fxLabel, setPreset, toggleFlag } = useTerminalFx()
const { soundEnabled } = useTerminalPreferences()
const { notify: faviconNotify } = useTerminalFavicon()
const { show: showMatrix } = useTerminalMatrix()
const { logs, pushLog } = useTerminalLogs()
const { resolveAlias, setAlias, removeAlias, listAliases } = useTerminalAliases()
const { locale, setLocale } = useLocale()
const integrationKeys = ref<string[]>([])
const contactKeys = ref<string[]>([])
const command = ref('')
const lines = ref<TerminalLine[]>([])
const history = ref<string[]>([])
const historyIndex = ref(-1)
const busy = ref(false)
const terminalEl = ref<HTMLElement | null>(null)
const terminalLines = computed<TerminalLine[]>(() => lines.value)
const prompt = computed(() =>
  auth.isAuthenticated
    ? `${auth.username || 'user'}@personal-me:~$`
    : 'guest@personal-me:~$'
)
const activeTab = ref<'terminal' | 'projects' | 'logs'>('terminal')
const portfolioProjects = ref<Project[]>([])
const featuredProjects = ref<Project[]>([])
const portfolioLoading = ref(false)
const showAuthModal = ref(false)
const authModalMode = ref<'login' | 'register'>('login')

const nowStamp = () => new Date().toLocaleTimeString('ru-RU')

const bootSequence = (): TerminalLine[] => [
  { type: 'system', value: 'POST ok — personal_me hub', timestamp: nowStamp() },
  { type: 'system', value: `welcome, ${config.public.ownerName} developer hub`, timestamp: nowStamp() },
  { type: 'system', value: 'работодателям: projects · пользователям: services · help', timestamp: nowStamp() },
  { type: 'system', value: "session ready — type 'help' for commands", timestamp: nowStamp() }
]

const addLine = (type: TerminalLine['type'], value: string) => {
  lines.value.push({
    type,
    value,
    timestamp: nowStamp()
  })
  if (type === 'error') {
    faviconNotify('error')
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (terminalEl.value) {
    terminalEl.value.scrollTop = terminalEl.value.scrollHeight
  }
}

const loadPortfolio = async () => {
  portfolioLoading.value = true
  try {
    const [all, featured] = await Promise.all([
      api.listProjects(false),
      api.listFeaturedProjects()
    ])
    portfolioProjects.value = all
    featuredProjects.value = featured
  } catch {
    portfolioProjects.value = []
    featuredProjects.value = []
  } finally {
    portfolioLoading.value = false
  }
}

const BASE_COMMANDS = [
  'help',
  'man',
  'about',
  'contact',
  'status',
  'clear',
  'projects',
  'project',
  'services',
  'go',
  'login',
  'register',
  'logout',
  'profile',
  'whoami',
  'pwd',
  'session',
  'theme',
  'fx',
  'lang',
  'alias'
]

const completeInput = (input: string): string | null => {
  const trimmed = input.trimStart()
  if (!trimmed) return null
  const parts = trimmed.split(/\s+/)
  const head = parts[0]?.toLowerCase() ?? ''
  const tail = parts.slice(1).join(' ')
  if (parts.length === 1) {
    const matches = BASE_COMMANDS.filter((item) => item.startsWith(head))
    if (matches.length === 1 && matches[0] !== head) {
      return matches[0]
    }
    return null
  }
  if (head === 'go' && parts.length === 2) {
    const partial = parts[1].toLowerCase()
    const matches = integrationKeys.value.filter((key) => key.startsWith(partial))
    if (matches.length === 1 && matches[0] !== partial) {
      return `go ${matches[0]}`
    }
  }
  if (head === 'contact' && parts.length === 2) {
    const partial = parts[1].toLowerCase()
    const matches = contactKeys.value.filter((key) => key.startsWith(partial))
    if (matches.length === 1 && matches[0] !== partial) {
      return `contact ${matches[0]}`
    }
  }
  if (head === 'theme' && parts.length === 2) {
    const themes = ['green', 'amber', 'blue']
    const partial = parts[1].toLowerCase()
    const matches = themes.filter((item) => item.startsWith(partial))
    if (matches.length === 1) {
      return `theme ${matches[0]}`
    }
  }
  if (head === 'lang' && parts.length === 2) {
    const langs = ['ru', 'en']
    const partial = parts[1].toLowerCase()
    const matches = langs.filter((item) => item.startsWith(partial))
    if (matches.length === 1) {
      return `lang ${matches[0]}`
    }
  }
  if (head === 'project' && parts.length === 2) {
    const partial = parts[1].toLowerCase()
    const slugs = portfolioProjects.value.map((item) => item.slug)
    const matches = slugs.filter((slug) => slug.startsWith(partial))
    if (matches.length === 1) {
      return `project ${matches[0]}`
    }
  }
  if (tail) {
    return null
  }
  return null
}

const terminalCommandErrorMessage = (error: unknown) => {
  const status = (error as { statusCode?: number }).statusCode
  if (status === 401 || status === 403) {
    return 'Для этой команды нужно войти в систему. Используйте login.'
  }
  if (status === 429) {
    return 'Слишком много попыток. Подождите минуту и повторите.'
  }
  return 'Такой команды нет или она сейчас недоступна. Введите help для списка.'
}

const maybeShowServicesHint = (command: string) => {
  if (typeof window === 'undefined') return
  if (!command.startsWith('services') && !command.startsWith('go')) return
  if (localStorage.getItem('services_hint_shown')) return
  localStorage.setItem('services_hint_shown', '1')
  addLine(
    'system',
    'Подсказка: go <service> откроет интеграцию в новой вкладке. SSO подставится автоматически.'
  )
}

const execute = async () => {
  const raw = resolveAlias(command.value.trim())
  if (!raw || busy.value) return

  addLine('input', raw)
  pushLog('cmd', raw)
  history.value.push(raw)
  historyIndex.value = history.value.length
  command.value = ''

  maybeShowServicesHint(raw)

  if (raw === 'matrix') {
    showMatrix()
    addLine('system', 'Wake up, Neo...')
    await scrollToBottom()
    return
  }

  if (raw === 'sudo' || raw.startsWith('sudo ')) {
    addLine('error', 'Nice try. Недостаточно прав (и так задумано).')
    await scrollToBottom()
    return
  }

  if (raw === 'vim' || raw.startsWith('vim ')) {
    addLine('output', 'Vim: :wq — выход. (или просто закройте вкладку)')
    await scrollToBottom()
    return
  }

  if (raw === 'profile') {
    if (!auth.isAuthenticated) {
      addLine('error', 'Требуется авторизация.')
    } else {
      addLine('output', `Профиль: ${auth.username}. Откройте /profile для email и пароля.`)
    }
    await scrollToBottom()
    return
  }

  if (raw.startsWith('lang ')) {
    const selected = raw.split(' ')[1] as 'ru' | 'en' | undefined
    if (!selected || (selected !== 'ru' && selected !== 'en')) {
      addLine('error', 'Использование: lang <ru|en>')
    } else {
      setLocale(selected)
      addLine('system', `Язык: ${selected}`)
    }
    await scrollToBottom()
    return
  }

  if (raw.startsWith('alias ')) {
    const body = raw.slice('alias '.length).trim()
    if (!body) {
      const items = listAliases()
      addLine('output', items.length ? items.join('\n') : 'Алиасы не заданы.')
    } else if (body.startsWith('-d ')) {
      removeAlias(body.slice(3).trim())
      addLine('system', 'Алиас удалён.')
    } else {
      const eq = body.indexOf('=')
      if (eq === -1) {
        addLine('error', 'Использование: alias name=command  |  alias -d name')
      } else {
        setAlias(body.slice(0, eq).trim(), body.slice(eq + 1).trim())
        addLine('system', 'Алиас сохранён.')
      }
    }
    await scrollToBottom()
    return
  }

  if (raw === 'logout') {
    if (!auth.isAuthenticated) {
      addLine('error', 'Вы не авторизованы.')
      await scrollToBottom()
      return
    }
    try {
      busy.value = true
      await api.logout()
      auth.logout()
      addLine('output', 'Выход выполнен успешно.')
      pushLog('auth', 'logout')
    } catch {
      addLine('error', 'Не удалось выполнить logout.')
    } finally {
      busy.value = false
      await scrollToBottom()
    }
    return
  }

  if (raw === 'whoami') {
    addLine('output', auth.isAuthenticated ? auth.username || 'user' : 'guest')
    await scrollToBottom()
    return
  }

  if (raw === 'pwd') {
    addLine('output', '~/personal_me')
    await scrollToBottom()
    return
  }

  if (raw === 'session') {
    addLine(
      'system',
      `auth=${auth.isAuthenticated ? 'авторизован' : 'гость'}; admin=${auth.isAdmin}; history=${history.value.length}; theme=${themeLabel.value}; fx=${fxLabel.value}`
    )
    await scrollToBottom()
    return
  }

  if (raw.startsWith('theme ')) {
    const selected = raw.split(' ')[1] as TerminalTheme | undefined
    if (!selected || !['green', 'amber', 'blue', 'auto'].includes(selected)) {
      addLine('error', 'Использование: theme <auto|green|amber|blue>')
    } else {
      theme.value = selected
      await nextTick()
      addLine('system', `Тема: ${themeLabel.value}.`)
    }
    await scrollToBottom()
    return
  }

  if (raw.startsWith('fx ')) {
    const parts = raw.split(/\s+/)
    const action = parts[1]
    if (action === 'off') {
      setPreset('off')
      addLine('system', 'Эффекты отключены.')
    } else if (action === 'preset' && parts[2]) {
      const preset = parts[2] as TerminalFxPreset
      if (!['minimal', 'retro', 'hacker', 'off'].includes(preset)) {
        addLine('error', 'Использование: fx preset <minimal|retro|hacker|off>')
      } else {
        setPreset(preset)
        addLine('system', `FX preset: ${preset} (${fxLabel.value}).`)
      }
    } else if (action === 'toggle' && parts[2]) {
      const flag = parts[2] as TerminalFxFlag
      if (!['scanlines', 'glow', 'vignette', 'grain'].includes(flag)) {
        addLine('error', 'Использование: fx toggle <scanlines|glow|vignette|grain>')
      } else {
        toggleFlag(flag)
        addLine('system', `FX: ${fxLabel.value}`)
      }
    } else {
      addLine(
        'error',
        'Использование: fx off | fx preset <minimal|retro|hacker> | fx toggle <flag>'
      )
    }
    await scrollToBottom()
    return
  }

  if (raw === 'fx') {
    addLine(
      'system',
      `fx: ${fxLabel.value} · preset: minimal|retro|hacker · toggle: scanlines|glow|vignette|grain`
    )
    await scrollToBottom()
    return
  }

  if (raw === 'login' || raw.startsWith('login ')) {
    if (raw !== 'login') {
      addLine('system', 'Пароль в терминал не вводится. Открываю форму входа...')
    }
    authModalMode.value = 'login'
    showAuthModal.value = true
    await scrollToBottom()
    return
  }

  if (raw === 'register' || raw.startsWith('register ')) {
    if (raw !== 'register') {
      addLine('system', 'Регистрация только через форму (без пароля в истории команд).')
    }
    authModalMode.value = 'register'
    showAuthModal.value = true
    await scrollToBottom()
    return
  }

  if (raw.startsWith('reset-request ')) {
    const username = raw.split(' ')[1]
    if (!username) {
      addLine('error', 'Использование: reset-request <логин>')
      await scrollToBottom()
      return
    }
    try {
      busy.value = true
      const response = await api.requestPasswordReset(username)
      addLine('output', response.message)
      if (response.reset_token) {
        addLine('system', `Токен сброса: ${response.reset_token}`)
        addLine('system', `Срок действия: ${response.expires_in_minutes} мин.`)
      }
    } catch {
      addLine('error', 'Не удалось запросить сброс пароля.')
    } finally {
      busy.value = false
      await scrollToBottom()
    }
    return
  }

  if (raw.startsWith('reset-password ')) {
    const parts = raw.split(' ')
    const token = parts[1]
    const newPassword = parts[2]
    if (!token || !newPassword) {
      addLine('error', 'Использование: reset-password <токен> <новый_пароль>')
      await scrollToBottom()
      return
    }
    try {
      busy.value = true
      await api.confirmPasswordReset(token, newPassword)
      auth.logout()
      addLine('output', 'Пароль успешно сброшен. Выполните login с новым паролем.')
    } catch {
      addLine('error', 'Сброс пароля не удался. Проверьте токен и срок действия.')
    } finally {
      busy.value = false
      await scrollToBottom()
    }
    return
  }

  if (raw.startsWith('password ')) {
    if (!auth.isAuthenticated) {
      addLine('error', 'Требуется авторизация.')
      await scrollToBottom()
      return
    }
    const parts = raw.split(' ')
    const currentPassword = parts[1]
    const newPassword = parts[2]
    if (!currentPassword || !newPassword) {
      addLine('error', 'Использование: password <текущий_пароль> <новый_пароль>')
      await scrollToBottom()
      return
    }
    try {
      busy.value = true
      await api.changePassword(currentPassword, newPassword)
      auth.logout()
      addLine('output', 'Пароль изменён. Войдите снова через login.')
    } catch {
      addLine('error', 'Смена пароля не удалась. Проверьте текущий пароль.')
    } finally {
      busy.value = false
      await scrollToBottom()
    }
    return
  }

  try {
    busy.value = true
    const response = await api.executeCommand(raw)
    if (response.output === '__CLEAR__') {
      lines.value = [
        {
          type: 'system',
          value: 'Экран терминала очищен.',
          timestamp: nowStamp()
        }
      ]
    } else {
      const lineType = response.requires_auth || response.forbidden ? 'error' : 'output'
      addLine(lineType, response.output)
      if (response.action === 'open_url' && response.url && typeof window !== 'undefined') {
        window.open(response.url, '_blank', 'noopener,noreferrer')
        pushLog('info', `open ${response.url}`)
      }
    }
  } catch (error) {
    addLine('error', terminalCommandErrorMessage(error))
  } finally {
    busy.value = false
    await scrollToBottom()
  }
}

const onKeydown = (event: KeyboardEvent) => {
  if (
    soundEnabled.value &&
    event.key.length === 1 &&
    !event.ctrlKey &&
    !event.metaKey &&
    !event.altKey
  ) {
    playTerminalKeySound()
  }
  if (event.key === 'Tab') {
    event.preventDefault()
    const completed = completeInput(command.value)
    if (completed) {
      command.value = completed
    }
    return
  }
  if (event.key === 'ArrowUp') {
    event.preventDefault()
    if (history.value.length === 0) return
    historyIndex.value = Math.max(0, historyIndex.value - 1)
    command.value = history.value[historyIndex.value] ?? ''
  } else if (event.key === 'ArrowDown') {
    event.preventDefault()
    if (history.value.length === 0) return
    historyIndex.value = Math.min(history.value.length, historyIndex.value + 1)
    command.value = history.value[historyIndex.value] ?? ''
    if (historyIndex.value === history.value.length) {
      command.value = ''
    }
  }
}

const getLineTimestamp = (line: unknown): string =>
  typeof line === 'object' && line !== null && 'timestamp' in line
    ? String((line as { timestamp: string }).timestamp)
    : ''

const getLineType = (line: unknown): TerminalLine['type'] =>
  typeof line === 'object' && line !== null && 'type' in line
    ? ((line as { type: TerminalLine['type'] }).type ?? 'output')
    : 'output'

const getLineValue = (line: unknown): string =>
  typeof line === 'object' && line !== null && 'value' in line
    ? String((line as { value: string }).value)
    : ''

onMounted(async () => {
  if (typeof window !== 'undefined' && !localStorage.getItem('terminal_boot_seen')) {
    lines.value = []
    for (const line of EXTENDED_BOOT) {
      await new Promise((resolve) => setTimeout(resolve, 75))
      addLine('system', line)
    }
    localStorage.setItem('terminal_boot_seen', '1')
  } else {
    lines.value = bootSequence()
  }

  if (typeof window === 'undefined') return
  const savedHistory = localStorage.getItem('terminal_history')

  if (savedHistory) {
    try {
      history.value = JSON.parse(savedHistory) as string[]
      historyIndex.value = history.value.length
    } catch {
      history.value = []
    }
  }
  if (auth.isAuthenticated) {
    await api.restoreSession()
  } else {
    auth.markInitialized()
  }
  try {
    const integrations = await api.listIntegrations()
    integrationKeys.value = integrations.map((item) => item.key)
  } catch {
    integrationKeys.value = []
  }
  try {
    const contacts = await api.listContacts()
    contactKeys.value = contacts.map((item) => item.key)
  } catch {
    contactKeys.value = []
  }
  await loadPortfolio()
})

watch(
  history,
  (nextHistory) => {
    if (typeof window === 'undefined') return
    localStorage.setItem('terminal_history', JSON.stringify(nextHistory.slice(-50)))
  },
  { deep: true }
)

const onAuthSuccess = async () => {
  addLine('output', 'Сессия обновлена.')
  pushLog('auth', `login ${auth.username}`)
  try {
    const about = await api.getAbout()
    if (about.motd) {
      addLine('system', about.motd)
    }
  } catch {
    /* ignore */
  }
}
</script>

<template>
  <TerminalShell cwd="~" session="terminal://personal_me/session">
    <template #toolbar>
      <div class="flex items-center gap-2 text-xs">
        <button
          class="rounded px-2 py-1"
          :class="activeTab === 'terminal' ? [themeStyles.output, 'bg-white/10'] : 'text-terminal-gray'"
          @click="activeTab = 'terminal'"
        >
          терминал
        </button>
        <button
          class="rounded px-2 py-1"
          :class="activeTab === 'projects' ? [themeStyles.output, 'bg-white/10'] : 'text-terminal-gray'"
          @click="activeTab = 'projects'; loadPortfolio()"
        >
          проекты
        </button>
        <button
          class="rounded px-2 py-1"
          :class="activeTab === 'logs' ? [themeStyles.output, 'bg-white/10'] : 'text-terminal-gray'"
          @click="activeTab = 'logs'"
        >
          логи
        </button>
      </div>
    </template>

    <div class="flex min-h-0 flex-1 flex-col">
      <div v-if="activeTab === 'terminal'" ref="terminalEl" class="terminal-scroll min-h-0 flex-1 overflow-y-auto p-5">
        <div v-for="(line, idx) in terminalLines" :key="idx" class="mb-2 grid grid-cols-[76px_1fr] gap-3 whitespace-pre-wrap text-sm">
          <span class="text-terminal-gray">{{ getLineTimestamp(line) }}</span>
          <span v-if="getLineType(line) === 'input'" :class="themeStyles.input">
            {{ prompt }} {{ getLineValue(line) }}
          </span>
          <span v-else-if="getLineType(line) === 'error'" class="text-red-400">{{ getLineValue(line) }}</span>
          <span v-else-if="getLineType(line) === 'system'" :class="themeStyles.system">{{ getLineValue(line) }}</span>
          <span v-else :class="themeStyles.output">{{ getLineValue(line) }}</span>
        </div>
      </div>
      <div v-else-if="activeTab === 'projects'" class="min-h-0 flex-1 overflow-y-auto p-5 text-sm" :class="themeStyles.output">
        <div class="mb-4 flex items-center justify-between">
          <p>portfolio://projects</p>
          <NuxtLink to="/projects" class="text-xs text-cyan-300 hover:underline">открыть веб</NuxtLink>
        </div>
        <p v-if="portfolioLoading" class="text-terminal-gray">Загрузка...</p>
        <template v-else>
          <div v-if="featuredProjects.length" class="mb-6">
            <p class="mb-2 text-amber-300">★ Featured</p>
            <ul class="space-y-3">
              <li v-for="item in featuredProjects" :key="`f-${item.id}`">
                <NuxtLink :to="`/projects/${item.slug}`" class="text-cyan-300 hover:underline">
                  {{ item.title }}
                </NuxtLink>
                <p class="text-terminal-gray">{{ item.summary }}</p>
              </li>
            </ul>
          </div>
          <ul class="space-y-3">
            <li v-for="item in portfolioProjects" :key="item.id">
              <NuxtLink :to="`/projects/${item.slug}`" class="text-cyan-300 hover:underline">
                {{ item.title }}
              </NuxtLink>
              <span v-if="item.featured" class="ml-1 text-amber-300">★</span>
              <p class="text-terminal-gray">{{ item.summary }}</p>
            </li>
          </ul>
        </template>
      </div>
      <div v-else class="min-h-0 flex-1 overflow-y-auto p-5 text-sm" :class="themeStyles.output">
        <p class="mb-2">log://session</p>
        <ul class="space-y-1">
          <li v-for="(entry, idx) in logs" :key="idx" class="text-terminal-gray">
            [{{ entry.ts }}] {{ entry.level }}: {{ entry.message }}
          </li>
        </ul>
        <p v-if="!logs.length" class="text-terminal-gray">Событий пока нет.</p>
      </div>

      <form class="border-t px-5 py-4" :class="themeStyles.border" @submit.prevent="execute">
        <div class="flex items-center gap-2 text-sm">
          <span :class="themeStyles.input">{{ prompt }}</span>
          <input
            v-model="command"
            type="text"
            class="w-full border-none bg-transparent outline-none"
            :class="themeStyles.input"
            :disabled="busy"
            autocomplete="off"
            @keydown="onKeydown"
          />
          <span :class="themeStyles.caret" />
        </div>
      </form>
    </div>

    <template #status>
      <span>hist:{{ history.length }}</span>
    </template>
    <template #status-actions>
      <span class="text-terminal-gray">Ctrl+L → clear</span>
    </template>
  </TerminalShell>

  <LoginModal
    v-if="showAuthModal"
    :mode="authModalMode"
    @close="showAuthModal = false"
    @success="onAuthSuccess"
  />
</template>
