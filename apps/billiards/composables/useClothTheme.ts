export type ClothTheme = 'dark' | 'light'

const STORAGE_KEY = 'dautovtech_kolkhoz_theme'

const applyDom = (theme: ClothTheme) => {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.theme = theme
  document.documentElement.style.colorScheme = theme
}

export const useClothTheme = () => {
  // Light "Daylight Lounge" is the primary theme; dark is the evening variant.
  const theme = useState<ClothTheme>('kolkhoz-theme', () => 'light')

  const hydrateTheme = () => {
    if (!import.meta.client) return
    const saved = localStorage.getItem(STORAGE_KEY)
    const next: ClothTheme = saved === 'dark' ? 'dark' : 'light'
    theme.value = next
    applyDom(next)
  }

  const setTheme = (next: ClothTheme) => {
    theme.value = next
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, next)
      applyDom(next)
    }
  }

  const toggleTheme = () => {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  return {
    theme,
    isLight: computed(() => theme.value === 'light'),
    hydrateTheme,
    setTheme,
    toggleTheme
  }
}
