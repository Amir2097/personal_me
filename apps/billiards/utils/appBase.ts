/** Normalize Nuxt app.baseURL to always end with a single slash. */
export const normalizeAppBase = (raw: string | undefined | null) => {
  const value = (raw || '/').trim() || '/'
  if (value === '/') return '/'
  return value.endsWith('/') ? value : `${value}/`
}

/** Join a path onto the app base (`/tv` → `/billiards/tv` or `/tv`). */
export const joinAppPath = (baseURL: string | undefined | null, path: string) => {
  const base = normalizeAppBase(baseURL)
  const clean = path.replace(/^\//, '')
  return `${base}${clean}`
}
