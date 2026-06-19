export type TerminalFxFlag = 'scanlines' | 'glow' | 'vignette' | 'grain'

export type TerminalFxPreset = 'off' | 'minimal' | 'retro' | 'hacker'

export const TERMINAL_FX_PRESETS: Record<TerminalFxPreset, TerminalFxFlag[]> = {
  off: [],
  minimal: [],
  retro: ['scanlines', 'vignette'],
  hacker: ['scanlines', 'glow', 'vignette', 'grain']
}

const VALID_FLAGS = new Set<TerminalFxFlag>(['scanlines', 'glow', 'vignette', 'grain'])

export function parseFxFlags(raw: string | null): TerminalFxFlag[] {
  if (!raw) return []
  return raw
    .split(/\s+/)
    .filter((item): item is TerminalFxFlag => VALID_FLAGS.has(item as TerminalFxFlag))
}

export function applyTerminalFxFlags(flags: TerminalFxFlag[]) {
  if (!import.meta.client) return
  if (flags.length) {
    document.documentElement.dataset.terminalFx = flags.join(' ')
  } else {
    delete document.documentElement.dataset.terminalFx
  }
}

export function useTerminalFx() {
  const flags = useState<TerminalFxFlag[]>('terminal-fx-flags', () => [])

  const sync = (value: TerminalFxFlag[]) => {
    if (import.meta.client) {
      localStorage.setItem('terminal_fx', value.join(' '))
      applyTerminalFxFlags(value)
    }
  }

  onMounted(() => {
    flags.value = parseFxFlags(localStorage.getItem('terminal_fx'))
    applyTerminalFxFlags(flags.value)
  })

  watch(flags, sync, { deep: true })

  const setPreset = (preset: TerminalFxPreset) => {
    flags.value = [...TERMINAL_FX_PRESETS[preset]]
  }

  const toggleFlag = (flag: TerminalFxFlag) => {
    if (flags.value.includes(flag)) {
      flags.value = flags.value.filter((item) => item !== flag)
    } else {
      flags.value = [...flags.value, flag]
    }
  }

  const label = computed(() => (flags.value.length ? flags.value.join(', ') : 'off'))

  return { flags, label, setPreset, toggleFlag }
}
