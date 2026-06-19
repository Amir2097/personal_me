export type ResolvedTerminalTheme = 'green' | 'amber' | 'blue'

export type TerminalTheme = ResolvedTerminalTheme | 'auto'

export type TerminalThemeStyles = {
  shell: string
  muted: string
  system: string
  input: string
  output: string
  border: string
  caret: string
}

const VALID_THEMES: TerminalTheme[] = ['green', 'amber', 'blue', 'auto']
const RESOLVED_THEMES: ResolvedTerminalTheme[] = ['green', 'amber', 'blue']

export function isTerminalTheme(value: string | null | undefined): value is TerminalTheme {
  return !!value && VALID_THEMES.includes(value as TerminalTheme)
}

export function getTerminalThemeStyles(theme: ResolvedTerminalTheme): TerminalThemeStyles {
  if (theme === 'amber') {
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
  if (theme === 'blue') {
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
}

function resolveAutoTheme(): ResolvedTerminalTheme {
  if (!import.meta.client) return 'green'
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'amber' : 'green'
}

export function useTerminalTheme() {
  const theme = useState<TerminalTheme>('terminal-theme', () => 'green')
  const autoResolved = useState<ResolvedTerminalTheme>('terminal-theme-auto', () => 'green')

  const refreshAuto = () => {
    autoResolved.value = resolveAutoTheme()
  }

  onMounted(() => {
    const saved = localStorage.getItem('terminal_theme')
    if (isTerminalTheme(saved)) {
      theme.value = saved
    }
    refreshAuto()
  })

  let mediaQuery: MediaQueryList | null = null
  if (import.meta.client) {
    onMounted(() => {
      mediaQuery = window.matchMedia('(prefers-color-scheme: light)')
      mediaQuery.addEventListener('change', refreshAuto)
    })
    onUnmounted(() => {
      mediaQuery?.removeEventListener('change', refreshAuto)
    })
  }

  watch(theme, (nextTheme) => {
    if (import.meta.client) {
      localStorage.setItem('terminal_theme', nextTheme)
    }
  })

  const resolvedTheme = computed<ResolvedTerminalTheme>(() =>
    theme.value === 'auto' ? autoResolved.value : theme.value
  )

  const themeStyles = computed(() => getTerminalThemeStyles(resolvedTheme.value))

  const themeLabel = computed(() =>
    theme.value === 'auto' ? `auto(${resolvedTheme.value})` : theme.value
  )

  return { theme, resolvedTheme, themeLabel, themeStyles }
}
