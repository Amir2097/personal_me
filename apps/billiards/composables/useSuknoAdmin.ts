const ADMIN_TOKEN_KEY = 'sukno_admin_access'

export type SuknoSeo = {
  brand_name: string
  tagline: string
  site_url: string
  seo_title: string
  seo_description: string
  seo_keywords: string
  og_image_url: string
  motd: string
}

export type SuknoSiteSettings = SuknoSeo & {
  motd: string
  updated_at: string
}

export type AdminUserRow = {
  username: string
  email: string
  role: string
  display_name: string
  email_verified: boolean
  is_active: boolean
  created_at: string
  last_login_at?: string | null
}

export type AuditLogRow = {
  id: number
  created_at: string
  actor_username: string
  action: string
  target: string
  details: Record<string, unknown>
}

export const useSuknoAdmin = () => {
  const { apiUrl, withCredentials, authHeaders } = useHubAuth()
  const suknoAuth = useSuknoAuth()

  const legacyToken = useState<string | null>('sukno-admin-token', () => null)

  const readLegacyStored = () => {
    if (!import.meta.client) return null
    return sessionStorage.getItem(ADMIN_TOKEN_KEY)
  }

  const persistLegacy = (value: string | null) => {
    legacyToken.value = value
    if (!import.meta.client) return
    if (value) sessionStorage.setItem(ADMIN_TOKEN_KEY, value)
    else sessionStorage.removeItem(ADMIN_TOKEN_KEY)
  }

  const hydrate = () => {
    if (!legacyToken.value) persistLegacy(readLegacyStored())
  }

  const unlocked = computed(() => suknoAuth.isAdmin.value || Boolean(legacyToken.value))

  const adminHeaders = (): Record<string, string> => {
    if (suknoAuth.isAdmin.value) return authHeaders()
    const current = legacyToken.value || readLegacyStored()
    if (!current) return {}
    return { Authorization: `Bearer ${current}` }
  }

  const adminFetchInit = (): RequestInit => ({
    ...withCredentials,
    headers: adminHeaders()
  })

  const unlock = async (key: string) => {
    try {
      const result = await $fetch<{ access_token: string }>(apiUrl('/api/v1/site/admin/unlock'), {
        method: 'POST',
        body: { key }
      })
      persistLegacy(result.access_token)
    } catch {
      throw new Error('Legacy admin key отключён или неверный ключ.')
    }
  }

  const lock = () => {
    persistLegacy(null)
  }

  const loadSettings = async () => {
    hydrate()
    return await $fetch<SuknoSiteSettings>(apiUrl('/api/v1/site/settings'), adminFetchInit())
  }

  const saveSettings = async (payload: Partial<Omit<SuknoSiteSettings, 'brand_name' | 'updated_at'>>) => {
    hydrate()
    return await $fetch<SuknoSiteSettings>(apiUrl('/api/v1/site/settings'), {
      method: 'PATCH',
      ...adminFetchInit(),
      body: payload
    })
  }

  const loadUsers = async () => {
    hydrate()
    return await $fetch<AdminUserRow[]>(apiUrl('/api/v1/site/admin/users'), adminFetchInit())
  }

  const updateUser = async (
    username: string,
    payload: Partial<Pick<AdminUserRow, 'role' | 'display_name' | 'is_active'>>
  ) => {
    hydrate()
    return await $fetch(apiUrl(`/api/v1/site/admin/users/${encodeURIComponent(username)}`), {
      method: 'PATCH',
      ...adminFetchInit(),
      body: payload
    })
  }

  const loadAudit = async (limit = 50) => {
    hydrate()
    return await $fetch<AuditLogRow[]>(apiUrl(`/api/v1/site/admin/audit?limit=${limit}`), adminFetchInit())
  }

  return {
    legacyToken,
    unlocked,
    hydrate,
    unlock,
    lock,
    adminHeaders,
    loadSettings,
    saveSettings,
    loadUsers,
    updateUser,
    loadAudit
  }
}
