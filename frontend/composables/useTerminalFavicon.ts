const DEFAULT_ICON = '/favicon.svg'
const ALERT_ICON = '/favicon-alert.svg'

let blinkTimer: ReturnType<typeof setInterval> | null = null
let resetTimer: ReturnType<typeof setTimeout> | null = null

function getIconLink() {
  return document.querySelector<HTMLLinkElement>("link[rel='icon']")
}

export function blinkTerminalFavicon() {
  if (!import.meta.client) return
  const link = getIconLink()
  if (!link) return

  if (blinkTimer) clearInterval(blinkTimer)
  if (resetTimer) clearTimeout(resetTimer)

  let alert = false
  blinkTimer = setInterval(() => {
    link.href = alert ? ALERT_ICON : DEFAULT_ICON
    alert = !alert
  }, 450)

  resetTimer = setTimeout(() => {
    if (blinkTimer) clearInterval(blinkTimer)
    blinkTimer = null
    link.href = DEFAULT_ICON
  }, 4500)
}

export function useTerminalFavicon() {
  const { faviconAlerts } = useTerminalPreferences()

  const notify = (level: 'warn' | 'error' | 'info') => {
    if ((level === 'warn' || level === 'error') && faviconAlerts.value) {
      blinkTerminalFavicon()
    }
  }

  return { notify }
}
