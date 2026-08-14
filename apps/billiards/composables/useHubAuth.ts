const USER_KEY = 'dautovtech_billiards_user'

const SSO_CONSUMED_KEY = 'dautovtech_billiards_sso_consumed'

const DEVICE_ID_KEY = 'dautovtech_billiards_device_id'

/** Legacy keys — cleared on boot after cookie migration. */

const LEGACY_ACCESS_KEY = 'dautovtech_billiards_access'

const LEGACY_REFRESH_KEY = 'dautovtech_billiards_refresh'



/** One exchange at a time — middleware / remount must not burn the same one-time code twice. */

let ssoExchangeInFlight: Promise<{ username: string; access_token: string } | null> | null = null

let deviceMintInFlight: Promise<boolean> | null = null



export const useHubAuth = () => {

  const config = useRuntimeConfig()



  const hubUrl = computed(() => String(config.public.hubUrl || '').replace(/\/$/, ''))

  const hubEnabled = computed(() => Boolean(hubUrl.value))



  const apiOrigin = computed(() => {

    const explicit = (config.public.apiBaseUrl as string | undefined)?.replace(/\/$/, '')

    if (explicit) return explicit



    if (import.meta.client) {

      const port = window.location.port

      if (port && port !== '80' && port !== '443') {

        return hubUrl.value

      }

      return window.location.origin

    }



    return hubUrl.value

  })



  const apiUrl = (path: string) => {

    const base = apiOrigin.value.replace(/\/$/, '')

    const normalized = path.startsWith('/') ? path : `/${path}`

    return `${base}${normalized}`

  }



  /** Send Sukno httpOnly cookies on cross-origin API calls. */

  const withCredentials = { credentials: 'include' as const }



  const accessToken = useState<string | null>('billiards-access-token', () => null)

  const username = useState<string | null>('billiards-username', () => null)

  const ready = useState<boolean>('billiards-auth-ready', () => false)

  const usesSuknoCookies = useState<boolean>('billiards-sukno-cookies', () => false)



  const clearLegacyTokenStorage = () => {

    if (!import.meta.client) return

    sessionStorage.removeItem(LEGACY_ACCESS_KEY)

    sessionStorage.removeItem(LEGACY_REFRESH_KEY)

  }



  const markSuknoCookieSession = (user: string | null) => {

    usesSuknoCookies.value = Boolean(user)

    accessToken.value = null

    username.value = user

    clearLegacyTokenStorage()

    if (!import.meta.client) return

    if (user) sessionStorage.setItem(USER_KEY, user)

    else sessionStorage.removeItem(USER_KEY)

  }



  const persistSession = (token: string | null, user: string | null) => {

    usesSuknoCookies.value = false

    accessToken.value = token

    username.value = user

    if (!import.meta.client) return

    if (user) sessionStorage.setItem(USER_KEY, user)

    else sessionStorage.removeItem(USER_KEY)

  }



  const authHeaders = (): Record<string, string> => {

    if (usesSuknoCookies.value) return {}

    const token = accessToken.value

    if (!token) return {}

    return { Authorization: `Bearer ${token}` }

  }



  const deviceId = () => {

    if (!import.meta.client) return ''

    let id = localStorage.getItem(DEVICE_ID_KEY)

    if (!id) {

      id = crypto.randomUUID().replace(/-/g, '')

      localStorage.setItem(DEVICE_ID_KEY, id)

    }

    return id

  }



  const stripSsoCodeFromUrl = () => {

    if (!import.meta.client) return

    const url = new URL(window.location.href)

    if (!url.searchParams.has('sso_code')) return

    url.searchParams.delete('sso_code')

    const next = `${url.pathname}${url.search}${url.hash}`

    window.history.replaceState(window.history.state, '', next)

  }



  const exchangeSsoCode = async (code: string) => {

    if (ssoExchangeInFlight) return ssoExchangeInFlight



    ssoExchangeInFlight = (async () => {

      try {

        if (import.meta.client) {

          sessionStorage.setItem(SSO_CONSUMED_KEY, code)

        }

        stripSsoCodeFromUrl()



        const result = await $fetch<{ username: string; access_token: string }>(

          apiUrl('/api/v1/auth/sso/exchange'),

          {

            method: 'POST',

            body: { code },

            credentials: 'include'

          }

        )

        persistSession(result.access_token, result.username)

        return result

      } catch {

        return null

      } finally {

        ssoExchangeInFlight = null

      }

    })()



    return ssoExchangeInFlight

  }



  const fetchHubMe = async () => {

    return await $fetch<{ username: string; is_admin: boolean }>(apiUrl('/api/v1/auth/me'), {

      ...withCredentials,

      headers: authHeaders()

    })

  }



  const fetchSuknoMe = async () => {

    return await $fetch<{

      username: string

      source: string

      role?: string | null

      email?: string | null

      email_verified?: boolean | null

      display_name?: string | null

      avatar_url?: string | null

      is_admin?: boolean

    }>(apiUrl('/api/v1/billiards/auth/me'), {

      ...withCredentials,

      headers: authHeaders()

    })

  }



  const trySuknoRefresh = async () => {

    try {

      const tokens = await $fetch<{ access_token: string; refresh_token: string; username?: string }>(

        apiUrl('/api/v1/billiards/auth/refresh'),

        { method: 'POST', ...withCredentials, body: {} }

      )

      markSuknoCookieSession(tokens.username || username.value)

      return true

    } catch {

      return false

    }

  }



  const tryCookieSession = async (): Promise<boolean> => {

    try {

      const profile = await fetchSuknoMe()

      if (profile.source === 'account' || profile.source === 'device') {

        markSuknoCookieSession(profile.username)

        return true

      }

    } catch {

      if (await trySuknoRefresh()) {

        try {

          const profile = await fetchSuknoMe()

          markSuknoCookieSession(profile.username)

          return true

        } catch {

          return false

        }

      }

    }

    return false

  }



  const tryRefresh = async () => {

    try {

      const tokens = await $fetch<{ access_token: string; username?: string }>(apiUrl('/api/v1/auth/refresh'), {

        method: 'POST',

        credentials: 'include',

        body: {}

      })

      if (tokens.access_token) {

        persistSession(tokens.access_token, tokens.username || username.value)

      }

      return true

    } catch {

      return false

    }

  }



  const mintDeviceToken = async (): Promise<boolean> => {

    if (!apiOrigin.value) return false

    if (deviceMintInFlight) return deviceMintInFlight



    deviceMintInFlight = (async () => {

      try {

        const result = await $fetch<{ access_token: string; username: string }>(

          apiUrl('/api/v1/billiards/auth/device'),

          {

            method: 'POST',

            ...withCredentials,

            body: { device_id: deviceId() }

          }

        )

        markSuknoCookieSession(result.username)

        return true

      } catch {

        return false

      } finally {

        deviceMintInFlight = null

      }

    })()



    return deviceMintInFlight

  }



  const ensureAuthenticated = async (routeQuery?: Record<string, unknown>): Promise<boolean> => {

    if (!import.meta.client) return false



    clearLegacyTokenStorage()



    if (!username.value && import.meta.client) {

      const storedUser = sessionStorage.getItem(USER_KEY)

      if (storedUser) username.value = storedUser

    }



    let ssoCode: string | null = null

    const fromArg = routeQuery?.sso_code

    if (typeof fromArg === 'string') ssoCode = fromArg

    else if (Array.isArray(fromArg) && typeof fromArg[0] === 'string') ssoCode = fromArg[0]

    else {

      try {

        ssoCode = new URL(window.location.href).searchParams.get('sso_code')

      } catch {

        ssoCode = null

      }

    }



    if (ssoCode) {

      const alreadyConsumed = sessionStorage.getItem(SSO_CONSUMED_KEY) === ssoCode

      if (alreadyConsumed) {

        stripSsoCodeFromUrl()

      } else {

        const result = await exchangeSsoCode(ssoCode)

        if (result) {

          username.value = result.username

          ready.value = true

          return true

        }

      }

    }



    if (!apiOrigin.value) {

      markSuknoCookieSession(null)

      persistSession(null, null)

      ready.value = true

      return false

    }



    if (await tryCookieSession()) {

      ready.value = true

      return true

    }



    if (accessToken.value) {

      try {

        const profile = await fetchSuknoMe()

        username.value = profile.username

        ready.value = true

        return true

      } catch {

        /* hub bearer — fall through */

      }

    }



    if (hubEnabled.value) {

      try {

        const profile = await fetchHubMe()

        username.value = profile.username

        ready.value = true

        return true

      } catch {

        const refreshed = await tryRefresh()

        if (refreshed) {

          try {

            const profile = await fetchHubMe()

            persistSession(accessToken.value, profile.username)

            ready.value = true

            return true

          } catch {

            /* ignore */

          }

        }

      }

    }



    const minted = await mintDeviceToken()

    ready.value = true

    if (!minted) {

      markSuknoCookieSession(null)

      persistSession(null, null)

    }

    return minted

  }



  const isDeviceUser = computed(() => Boolean(username.value?.startsWith('local_')))

  const isHubLinked = computed(

    () => Boolean(username.value) && !isDeviceUser.value && !usesSuknoCookies.value

  )

  const isSignedIn = computed(() => Boolean(username.value || usesSuknoCookies.value || accessToken.value))



  const logoutAccount = async () => {

    try {

      await $fetch(apiUrl('/api/v1/billiards/auth/logout'), {

        method: 'POST',

        ...withCredentials,

        body: {}

      })

    } catch {

      /* ignore */

    }

    markSuknoCookieSession(null)

    ready.value = true

  }



  const loginViaHub = () => {

    if (!import.meta.client || !hubEnabled.value) return

    window.location.href = `${hubUrl.value}/hobby`

  }



  return {

    apiOrigin,

    apiUrl,

    withCredentials,

    hubUrl,

    hubEnabled,

    isHubLinked,

    isDeviceUser,

    isSignedIn,

    accessToken,

    username,

    ready,

    usesSuknoCookies,

    authHeaders,

    ensureAuthenticated,

    loginViaHub,

    redirectToHubLogin: loginViaHub,

    persistSession,

    markSuknoCookieSession,

    logoutAccount,

    fetchSuknoMe,

    trySuknoRefresh

  }

}


