import { joinAppPath, normalizeAppBase } from '~/utils/appBase'

export const useAppBase = () => {
  const config = useRuntimeConfig()

  const baseURL = computed(() => normalizeAppBase(String(config.app.baseURL || '/')))

  const appPath = (path: string) => joinAppPath(baseURL.value, path)

  const appHref = (path: string, query?: Record<string, string>) => {
    const url = import.meta.client
      ? new URL(appPath(path), window.location.origin)
      : new URL(appPath(path), 'http://localhost')
    if (query) {
      for (const [key, value] of Object.entries(query)) url.searchParams.set(key, value)
    }
    return url.toString()
  }

  return { baseURL, appPath, appHref }
}
