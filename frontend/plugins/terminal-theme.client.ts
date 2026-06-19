/** Sync terminal theme, FX and cursor prefs on the document root. */
export default defineNuxtPlugin(() => {
  const { resolvedTheme } = useTerminalTheme()
  const { flags } = useTerminalFx()
  useTerminalPreferences()

  watch(
    resolvedTheme,
    (value) => {
      document.documentElement.dataset.terminalTheme = value
    },
    { immediate: true }
  )

  watch(
    flags,
    (value) => {
      applyTerminalFxFlags(value)
    },
    { immediate: true, deep: true }
  )
})
