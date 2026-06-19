/** Terminal UI preferences stored in localStorage. */

export function useTerminalPreferences() {
  const cursorEnabled = useState('terminal-cursor-enabled', () => true)
  const soundEnabled = useState('terminal-sound-enabled', () => false)
  const faviconAlerts = useState('terminal-favicon-alerts', () => true)

  onMounted(() => {
    cursorEnabled.value = localStorage.getItem('terminal_cursor') !== 'off'
    soundEnabled.value = localStorage.getItem('terminal_sound') === 'on'
    faviconAlerts.value = localStorage.getItem('terminal_favicon_alerts') !== 'off'
    applyCursor(cursorEnabled.value)
  })

  const applyCursor = (enabled: boolean) => {
    if (!import.meta.client) return
    if (enabled) {
      delete document.documentElement.dataset.terminalCursor
    } else {
      document.documentElement.dataset.terminalCursor = 'off'
    }
  }

  watch(cursorEnabled, (value) => {
    if (import.meta.client) {
      localStorage.setItem('terminal_cursor', value ? 'on' : 'off')
      applyCursor(value)
    }
  })

  watch(soundEnabled, (value) => {
    if (import.meta.client) {
      localStorage.setItem('terminal_sound', value ? 'on' : 'off')
    }
  })

  watch(faviconAlerts, (value) => {
    if (import.meta.client) {
      localStorage.setItem('terminal_favicon_alerts', value ? 'on' : 'off')
    }
  })

  return { cursorEnabled, soundEnabled, faviconAlerts }
}
