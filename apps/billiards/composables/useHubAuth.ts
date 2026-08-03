const SESSION_KEY = 'dautovtech_billiards_access'
const USER_KEY = 'dautovtech_billiards_user'

export const useHubAuth = () => {
  const config = useRuntimeConfig()

  const apiBase = computed(() => {
    const explicit = (config.public.apiBaseUrl as string | undefined)?.replace(/\/$/, '')
    if (explicit) return explicit
    // Behind nginx (same origin) relative /api works; standalone :3010 uses hub.
    if (import.meta.client) {
      const port = window.location.port
      if (port && port !== '80' && port !== '443') {
        return String(config.public.hubUrl || 'http://localhost').replace(/\/$/, '')
      }
    }
    return ''
  })

  const hubUrl = computed(() => String(config.public.hubUrl || 'http://localhost').replace(/\/$/, ''))

  const accessToken = useState<string | null>('billiards-access-token', () => null)
  const username = useState<string | null>('billiards-username', () => null)
  const ready = useState<boolean>('billiards-auth-ready', () => false)

  const readStoredToken = () => {
    if (!import.meta.client) return null
    return sessionStorage.getItem(SESSION_KEY)
  }

  const persistSession = (token: string | null, user: string | null) => {
    accessToken.value = token
    username.value = user
    if (!import.meta.client) return
    if (token) sessionStorage.setItem(SESSION_KEY, token)
    else sessionStorage.removeItem(SESSION_KEY)
    if (user) sessionStorage.setItem(USER_KEY, user)
    else sessionStorage.removeItem(USER_KEY)
  }

  const authHeaders = (): Record<string, string> => {
    const token = accessToken.value || readStoredToken()
    if (!token) return {}
    return { Authorization: `Bearer ${token}` }
  }

  const stripSsoCodeFromUrl = () => {
    if (!import.meta.client) return
    const url = new URL(window.location.href)
    if (!url.searchParams.has('sso_code')) return
    url.searchParams.delete('sso_code')
    const next = `${url.pathname}${url.search}${url.hash}`
    // replaceState — без повторного запуска route middleware (в отличие от navigateTo).
    window.history.replaceState(window.history.state, '', next)
  }

  const exchangeSsoCode = async (code: string) => {
    const result = await $fetch<{ username: string; access_token: string }>(
      `${apiBase.value}/api/v1/auth/sso/exchange`,
      {
        method: 'POST',
        body: { code },
        credentials: 'include'
      }
    )
    persistSession(result.access_token, result.username)
    return result
  }

  const fetchMe = async () => {
    return await $fetch<{ username: string; is_admin: boolean }>(`${apiBase.value}/api/v1/auth/me`, {
      credentials: 'include',
      headers: authHeaders()
    })
  }

  const tryRefresh = async () => {
    try {
      const tokens = await $fetch<{ access_token: string; username?: string }>(
        `${apiBase.value}/api/v1/auth/refresh`,
        {
          method: 'POST',
          credentials: 'include',
          body: {}
        }
      )
      if (tokens.access_token) {
        persistSession(tokens.access_token, tokens.username || username.value)
      }
      return true
    } catch {
      return false
    }
  }

  const ensureAuthenticated = async (): Promise<boolean> => {
    if (!import.meta.client) return false

    if (!accessToken.value) {
      const stored = readStoredToken()
      if (stored) accessToken.value = stored
      const storedUser = sessionStorage.getItem(USER_KEY)
      if (storedUser) username.value = storedUser
    }

    const route = useRoute()
    const ssoCode = typeof route.query.sso_code === 'string' ? route.query.sso_code : null
    if (ssoCode) {
      try {
        const result = await exchangeSsoCode(ssoCode)
        stripSsoCodeFromUrl()
        username.value = result.username
        ready.value = true
        // После успешного SSO не зовём navigateTo — иначе middleware обрывается и уходит на хаб.
        return true
      } catch {
        // Fall through to cookie/Bearer check.
      }
    }

    try {
      const profile = await fetchMe()
      username.value = profile.username
      ready.value = true
      return true
    } catch {
      const refreshed = await tryRefresh()
      if (refreshed) {
        try {
          const profile = await fetchMe()
          username.value = profile.username
          ready.value = true
          return true
        } catch {
          /* ignore */
        }
      }
    }

    persistSession(null, null)
    ready.value = true
    return false
  }

  const redirectToHubLogin = () => {
    if (!import.meta.client) return
    // Ведём на /hobby с флагом — страница публичная и сама покажет форму входа.
    const target = `${hubUrl.value}/hobby?auth=required`
    window.location.href = target
  }

  return {
    apiBase,
    hubUrl,
    accessToken,
    username,
    ready,
    ensureAuthenticated,
    redirectToHubLogin,
    persistSession
  }
}
