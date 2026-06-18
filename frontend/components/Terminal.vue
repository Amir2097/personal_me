<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import type { Project } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'
import { useAuthStore } from '~/stores/auth'

interface TerminalLine {
  type: 'input' | 'output' | 'error' | 'system'
  value: string
  timestamp: string
}

type TerminalTheme = 'green' | 'amber' | 'blue'

const api = useApi()
const auth = useAuthStore()
const command = ref('')
const lines = ref<TerminalLine[]>([
  {
    type: 'system',
    value: "Загрузка завершена. Введите 'help' для списка команд.",
    timestamp: new Date().toLocaleTimeString('ru-RU')
  }
])
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
const uptimeStart = new Date()
const activeTab = ref<'terminal' | 'projects' | 'logs'>('terminal')
const theme = ref<TerminalTheme>('green')
const portfolioProjects = ref<Project[]>([])
const portfolioLoading = ref(false)
const showAuthModal = ref(false)
const authModalMode = ref<'login' | 'register'>('login')

const themeStyles = computed(() => {
  if (theme.value === 'amber') {
    return {
      shell: 'text-amber-300',
      muted: 'text-amber-200/70',
      system: 'text-amber-100',
      input: 'text-amber-300',
      output: 'text-amber-200',
      border: 'border-amber-500/30',
      caret: 'terminal-caret-amber'
    }
  }
  if (theme.value === 'blue') {
    return {
      shell: 'text-cyan-300',
      muted: 'text-cyan-200/70',
      system: 'text-cyan-100',
      input: 'text-cyan-300',
      output: 'text-cyan-200',
      border: 'border-cyan-500/30',
      caret: 'terminal-caret-blue'
    }
  }
  return {
    shell: 'text-terminal-green',
    muted: 'text-terminal-green/75',
    system: 'text-cyan-300',
    input: 'text-terminal-green',
    output: 'text-terminal-green/95',
    border: 'border-terminal-gray/80',
    caret: 'terminal-caret'
  }
})

const addLine = (type: TerminalLine['type'], value: string) => {
  lines.value.push({
    type,
    value,
    timestamp: new Date().toLocaleTimeString('ru-RU')
  })
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
    portfolioProjects.value = await api.listProjects()
  } catch {
    portfolioProjects.value = []
  } finally {
    portfolioLoading.value = false
  }
}

const execute = async () => {
  const raw = command.value.trim()
  if (!raw || busy.value) return

  addLine('input', raw)
  history.value.push(raw)
  historyIndex.value = history.value.length
  command.value = ''

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
      `auth=${auth.isAuthenticated ? 'авторизован' : 'гость'}; admin=${auth.isAdmin}; history=${history.value.length}; theme=${theme.value}`
    )
    await scrollToBottom()
    return
  }

  if (raw.startsWith('theme ')) {
    const selected = raw.split(' ')[1] as TerminalTheme | undefined
    if (!selected || ['green', 'amber', 'blue'].indexOf(selected) === -1) {
      addLine('error', 'Использование: theme <green|amber|blue>')
    } else {
      theme.value = selected
      addLine('system', `Тема переключена на ${selected}.`)
    }
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
          timestamp: new Date().toLocaleTimeString('ru-RU')
        }
      ]
    } else {
      const lineType = response.requires_auth || response.forbidden ? 'error' : 'output'
      addLine(lineType, response.output)
      if (response.action === 'open_url' && response.url && typeof window !== 'undefined') {
        window.open(response.url, '_blank', 'noopener,noreferrer')
      }
    }
  } catch {
    addLine('error', 'Backend недоступен или команда завершилась с ошибкой.')
  } finally {
    busy.value = false
    await scrollToBottom()
  }
}

const onKeydown = (event: KeyboardEvent) => {
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
  if (typeof window === 'undefined') return
  const savedHistory = localStorage.getItem('terminal_history')
  const savedTheme = localStorage.getItem('terminal_theme') as TerminalTheme | null

  if (savedHistory) {
    try {
      history.value = JSON.parse(savedHistory) as string[]
      historyIndex.value = history.value.length
    } catch {
      history.value = []
    }
  }
  if (savedTheme && ['green', 'amber', 'blue'].indexOf(savedTheme) !== -1) {
    theme.value = savedTheme
  }
  if (auth.isAuthenticated) {
    await api.restoreSession()
  } else {
    auth.markInitialized()
  }
})

watch(
  history,
  (nextHistory) => {
    if (typeof window === 'undefined') return
    localStorage.setItem('terminal_history', JSON.stringify(nextHistory.slice(-50)))
  },
  { deep: true }
)

watch(theme, (nextTheme) => {
  if (typeof window === 'undefined') return
  localStorage.setItem('terminal_theme', nextTheme)
})

const onAuthSuccess = () => {
  addLine('output', 'Сессия обновлена.')
}
</script>

<template>
  <section class="mx-auto mt-6 flex h-[78vh] w-full max-w-6xl overflow-hidden rounded-xl border border-terminal-gray/90 bg-terminal-black/95 font-mono shadow-2xl shadow-black/40">
    <aside class="hidden w-56 border-r border-terminal-gray/80 bg-black/25 p-4 md:block">
      <div class="mb-4 text-[11px] uppercase tracking-widest text-terminal-gray">Рабочая область</div>
      <ul class="space-y-2 text-xs" :class="themeStyles.muted">
        <li>root: ~/personal_me</li>
        <li>режим: interactive</li>
        <li>auth: {{ auth.isAuthenticated ? 'авторизован' : 'гость' }}</li>
        <li v-if="auth.isAdmin">role: admin</li>
      </ul>
      <div v-if="auth.isAdmin" class="mt-4 space-y-1">
        <NuxtLink
          to="/admin/integrations"
          class="block text-xs text-cyan-300 underline hover:text-cyan-200"
        >
          admin → интеграции
        </NuxtLink>
        <NuxtLink
          to="/admin/projects"
          class="block text-xs text-cyan-300 underline hover:text-cyan-200"
        >
          admin → проекты
        </NuxtLink>
      </div>
      <div class="mt-4">
        <NuxtLink
          to="/projects"
          class="text-xs text-terminal-gray underline hover:text-terminal-green"
        >
          /projects
        </NuxtLink>
      </div>
      <div class="mt-6 text-[11px] uppercase tracking-widest text-terminal-gray">Подсказки</div>
      <ul class="mt-2 space-y-1 text-xs" :class="themeStyles.muted">
        <li>help</li>
        <li>login / register</li>
        <li>reset-request логин</li>
        <li>password старый новый</li>
        <li>theme green|amber|blue</li>
        <li>go github / grafana</li>
        <li>services</li>
        <li>projects / project slug</li>
        <li>clear</li>
      </ul>
    </aside>

    <div class="flex min-w-0 flex-1 flex-col">
      <header class="flex items-center justify-between border-b border-terminal-gray/80 px-4 py-3">
        <div class="flex items-center gap-2">
          <span class="h-3 w-3 rounded-full bg-red-500/90" />
          <span class="h-3 w-3 rounded-full bg-yellow-500/90" />
          <span class="h-3 w-3 rounded-full bg-green-500/90" />
          <span class="ml-3 text-xs" :class="themeStyles.muted">terminal://personal_me/session</span>
        </div>
        <div class="text-xs text-terminal-gray">с {{ uptimeStart.toLocaleTimeString('ru-RU') }}</div>
      </header>
      <div class="flex items-center gap-2 border-b px-4 py-2 text-xs" :class="themeStyles.border">
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
        <ul v-else class="space-y-3">
          <li v-for="item in portfolioProjects" :key="item.id">
            <NuxtLink :to="`/projects/${item.slug}`" class="text-cyan-300 hover:underline">
              {{ item.title }}
            </NuxtLink>
            <span v-if="item.featured" class="ml-1 text-amber-300">★</span>
            <p class="text-terminal-gray">{{ item.summary }}</p>
          </li>
        </ul>
      </div>
      <div v-else class="min-h-0 flex-1 overflow-y-auto p-5 text-sm" :class="themeStyles.output">
        <p class="mb-2">log://session</p>
        <p class="text-terminal-gray">записей в истории: {{ history.length }}</p>
        <p class="text-terminal-gray">тема: {{ theme }}</p>
        <p class="text-terminal-gray">auth: {{ auth.isAuthenticated ? 'авторизован' : 'гость' }}</p>
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
  </section>
  <LoginModal
    v-if="showAuthModal"
    :mode="authModalMode"
    @close="showAuthModal = false"
    @success="onAuthSuccess"
  />
</template>
