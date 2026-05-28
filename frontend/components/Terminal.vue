<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useApi } from '~/composables/useApi'
import { useAuthStore } from '~/stores/auth'

/**
 * Terminal line model used to render command history and backend output.
 */
interface TerminalLine {
  type: 'input' | 'output' | 'error' | 'system'
  value: string
  timestamp: string
}

type TerminalTheme = 'green' | 'amber' | 'blue'

/**
 * Component props:
 * - prompt: terminal prompt prefix displayed before command input.
 */
withDefaults(defineProps<{ prompt?: string }>(), {
  prompt: 'guest@personal-me:~$'
})

const api = useApi()
const auth = useAuthStore()
const command = ref('')
const lines = ref<TerminalLine[]>([
  {
    type: 'system',
    value: "Boot sequence complete. Type 'help' to see available commands.",
    timestamp: new Date().toLocaleTimeString()
  }
])
const history = ref<string[]>([])
const historyIndex = ref(-1)
const busy = ref(false)
const terminalEl = ref<HTMLElement | null>(null)
const terminalLines = computed<TerminalLine[]>(() => lines.value)
const prompt = computed(() => (auth.isAuthenticated ? 'admin@personal-me:~$' : 'guest@personal-me:~$'))
const uptimeStart = new Date()
const activeTab = ref<'terminal' | 'projects' | 'logs'>('terminal')
const theme = ref<TerminalTheme>('green')

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
    timestamp: new Date().toLocaleTimeString()
  })
}

const scrollToBottom = async () => {
  await nextTick()
  if (terminalEl.value) {
    terminalEl.value.scrollTop = terminalEl.value.scrollHeight
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
    if (!auth.refreshToken) {
      addLine('error', 'You are not authenticated.')
      await scrollToBottom()
      return
    }
    try {
      busy.value = true
      await api.logout(auth.refreshToken)
      auth.logout()
      addLine('output', 'Logged out successfully.')
    } catch {
      addLine('error', 'Logout request failed.')
    } finally {
      busy.value = false
      await scrollToBottom()
    }
    return
  }

  if (raw === 'whoami') {
    addLine('output', auth.isAuthenticated ? 'admin' : 'guest')
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
      `auth=${auth.isAuthenticated ? 'authorized' : 'guest'}; history=${history.value.length}; theme=${theme.value}`
    )
    await scrollToBottom()
    return
  }

  if (raw.startsWith('theme ')) {
    const selected = raw.split(' ')[1] as TerminalTheme | undefined
    if (!selected || ['green', 'amber', 'blue'].indexOf(selected) === -1) {
      addLine('error', "Usage: theme <green|amber|blue>")
    } else {
      theme.value = selected
      addLine('system', `Theme switched to ${selected}.`)
    }
    await scrollToBottom()
    return
  }

  if (raw.startsWith('login ')) {
    const [_, username, password] = raw.split(' ')
    if (!username || !password) {
      addLine('error', 'Usage: login <username> <password>')
      await scrollToBottom()
      return
    }
    try {
      busy.value = true
      const response = (await api.login(username, password)) as {
        access_token: string
        refresh_token: string
      }
      auth.setTokens(response.access_token, response.refresh_token)
      addLine('output', 'Authentication successful.')
    } catch {
      addLine('error', 'Authentication failed.')
    } finally {
      busy.value = false
      await scrollToBottom()
    }
    return
  }

  if (raw.startsWith('register ')) {
    const [_, username, password] = raw.split(' ')
    if (!username || !password) {
      addLine('error', 'Usage: register <username> <password>')
      await scrollToBottom()
      return
    }
    try {
      busy.value = true
      const response = await api.register(username, password)
      auth.setTokens(response.access_token, response.refresh_token)
      addLine('output', 'Registration successful. You are authenticated.')
    } catch {
      addLine('error', 'Registration failed. Username may already exist.')
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
          value: 'Terminal cleared.',
          timestamp: new Date().toLocaleTimeString()
        }
      ]
    } else {
      addLine(response.requires_auth ? 'error' : 'output', response.output)
    }
  } catch {
    addLine('error', 'Backend unavailable or command failed.')
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

onMounted(() => {
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
</script>

<template>
  <section class="mx-auto mt-6 flex h-[78vh] w-full max-w-6xl overflow-hidden rounded-xl border border-terminal-gray/90 bg-terminal-black/95 font-mono shadow-2xl shadow-black/40">
    <aside class="hidden w-56 border-r border-terminal-gray/80 bg-black/25 p-4 md:block">
      <div class="mb-4 text-[11px] uppercase tracking-widest text-terminal-gray">Workspace</div>
      <ul class="space-y-2 text-xs" :class="themeStyles.muted">
        <li>root: ~/personal_me</li>
        <li>mode: interactive</li>
        <li>auth: {{ auth.isAuthenticated ? 'authorized' : 'guest' }}</li>
      </ul>
      <div class="mt-6 text-[11px] uppercase tracking-widest text-terminal-gray">Hints</div>
      <ul class="mt-2 space-y-1 text-xs" :class="themeStyles.muted">
        <li>help</li>
        <li>register username pass</li>
        <li>login username pass</li>
        <li>theme green|amber|blue</li>
        <li>whoami / pwd / session</li>
        <li>projects</li>
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
        <div class="text-xs text-terminal-gray">since {{ uptimeStart.toLocaleTimeString() }}</div>
      </header>
      <div class="flex items-center gap-2 border-b px-4 py-2 text-xs" :class="themeStyles.border">
        <button
          class="rounded px-2 py-1"
          :class="activeTab === 'terminal' ? [themeStyles.output, 'bg-white/10'] : 'text-terminal-gray'"
          @click="activeTab = 'terminal'"
        >
          terminal
        </button>
        <button
          class="rounded px-2 py-1"
          :class="activeTab === 'projects' ? [themeStyles.output, 'bg-white/10'] : 'text-terminal-gray'"
          @click="activeTab = 'projects'"
        >
          projects
        </button>
        <button
          class="rounded px-2 py-1"
          :class="activeTab === 'logs' ? [themeStyles.output, 'bg-white/10'] : 'text-terminal-gray'"
          @click="activeTab = 'logs'"
        >
          logs
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
        <p class="mb-2">project://personal_me</p>
        <p class="text-terminal-gray">- backend (FastAPI)</p>
        <p class="text-terminal-gray">- frontend (Nuxt 3)</p>
        <p class="text-terminal-gray">- infra (Docker/Nginx)</p>
      </div>
      <div v-else class="min-h-0 flex-1 overflow-y-auto p-5 text-sm" :class="themeStyles.output">
        <p class="mb-2">log://session</p>
        <p class="text-terminal-gray">history entries: {{ history.length }}</p>
        <p class="text-terminal-gray">theme: {{ theme }}</p>
        <p class="text-terminal-gray">auth: {{ auth.isAuthenticated ? 'authorized' : 'guest' }}</p>
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
</template>
