import {
  isAdminRole,
  isOperatorRole
} from '~/utils/suknoRoles'

export type SuknoAuthConfig = {
  allow_registration: boolean
  require_email_verification: boolean
  expose_reset_token: boolean
  expose_verification_token: boolean
  password_reset_via_email: boolean
  email_verification_via_email: boolean
  allow_legacy_admin_key: boolean
}

export type SuknoMe = {
  username: string
  source: 'account' | 'device' | 'hub' | 'legacy_admin'
  role?: string | null
  email?: string | null
  email_verified?: boolean | null
  display_name?: string | null
  avatar_url?: string | null
  is_admin?: boolean
}

export type SuknoProfile = {
  username: string
  email: string
  role: string
  display_name: string
  avatar_url: string
  bio: string
  location: string
  telegram: string
  email_verified: boolean
  is_active: boolean
  totp_enabled?: boolean
  created_at?: string | null
  last_login_at?: string | null
}

export type SuknoTokens = {
  access_token: string
  refresh_token: string
  username: string
  role?: string
  email_verified?: boolean
}

export type LoginResult = {
  requires_totp: boolean
  challenge_token?: string | null
  access_token?: string | null
  refresh_token?: string | null
  username: string
  role?: string
  email_verified?: boolean
}

export type TotpStatus = {
  eligible: boolean
  enabled: boolean
  pending_setup: boolean
}

export type TotpSetup = {
  secret: string
  otpauth_url: string
}

export type RegisterResult = {
  message: string
  username: string
  verification_required: boolean
  verification_token?: string | null
  access_token?: string | null
  refresh_token?: string | null
}

export const useSuknoAuth = () => {
  const {
    apiUrl,
    withCredentials,
    markSuknoCookieSession,
    username,
    ready,
    fetchSuknoMe,
    trySuknoRefresh
  } = useHubAuth()

  const profile = useState<SuknoMe | null>('billiards-sukno-profile', () => null)
  const config = useState<SuknoAuthConfig | null>('billiards-auth-config', () => null)

  const clearAccountSession = () => {
    profile.value = null
    markSuknoCookieSession(null)
  }

  const loadConfig = async () => {
    config.value = await $fetch<SuknoAuthConfig>(apiUrl('/api/v1/billiards/auth/config'))
    return config.value
  }

  const fetchMe = async () => {
    const me = await fetchSuknoMe()
    profile.value = me
    username.value = me.username
    if (me.source === 'account' || me.source === 'device') {
      markSuknoCookieSession(me.username)
    }
    return me
  }

  const login = async (loginName: string, password: string) => {
    const result = await $fetch<LoginResult>(apiUrl('/api/v1/billiards/auth/login'), {
      method: 'POST',
      ...withCredentials,
      body: { username: loginName, password }
    })
    if (result.requires_totp && result.challenge_token) {
      return result
    }
    markSuknoCookieSession(result.username)
    await fetchMe()
    return result
  }

  const verifyTotp = async (challengeToken: string, code: string) => {
    const tokens = await $fetch<SuknoTokens>(apiUrl('/api/v1/billiards/auth/totp/verify'), {
      method: 'POST',
      ...withCredentials,
      body: { challenge_token: challengeToken, code }
    })
    markSuknoCookieSession(tokens.username)
    await fetchMe()
    return tokens
  }

  const totpStatus = async () => {
    return await $fetch<TotpStatus>(apiUrl('/api/v1/billiards/auth/totp/status'), withCredentials)
  }

  const totpSetup = async () => {
    return await $fetch<TotpSetup>(apiUrl('/api/v1/billiards/auth/totp/setup'), {
      method: 'POST',
      ...withCredentials
    })
  }

  const totpEnable = async (code: string) => {
    return await $fetch<TotpStatus>(apiUrl('/api/v1/billiards/auth/totp/enable'), {
      method: 'POST',
      ...withCredentials,
      body: { code }
    })
  }

  const totpDisable = async (password: string, code: string) => {
    return await $fetch<TotpStatus>(apiUrl('/api/v1/billiards/auth/totp/disable'), {
      method: 'POST',
      ...withCredentials,
      body: { password, code }
    })
  }

  const register = async (payload: {
    username: string
    email: string
    password: string
    accept_terms: boolean
  }) => {
    const result = await $fetch<RegisterResult>(apiUrl('/api/v1/billiards/auth/register'), {
      method: 'POST',
      ...withCredentials,
      body: payload
    })
    if (result.access_token && result.refresh_token) {
      markSuknoCookieSession(result.username)
      await fetchMe()
    }
    return result
  }

  const logout = async () => {
    try {
      await $fetch(apiUrl('/api/v1/billiards/auth/logout'), {
        method: 'POST',
        ...withCredentials,
        body: {}
      })
    } catch {
      /* ignore */
    }
    clearAccountSession()
    ready.value = true
  }

  const verifyEmail = async (token: string) => {
    return await $fetch<SuknoProfile>(apiUrl('/api/v1/billiards/auth/verify-email'), {
      method: 'POST',
      body: { token }
    })
  }

  const resendVerification = async (login: string) => {
    return await $fetch<{ message: string; verification_token?: string | null }>(
      apiUrl('/api/v1/billiards/auth/resend-verification'),
      { method: 'POST', body: { login } }
    )
  }

  const requestPasswordReset = async (login: string) => {
    return await $fetch<{ message: string; reset_token?: string | null }>(
      apiUrl('/api/v1/billiards/auth/password-reset/request'),
      { method: 'POST', body: { login } }
    )
  }

  const confirmPasswordReset = async (token: string, newPassword: string) => {
    return await $fetch(apiUrl('/api/v1/billiards/auth/password-reset/confirm'), {
      method: 'POST',
      body: { token, new_password: newPassword }
    })
  }

  const loadProfile = async () => {
    return await $fetch<SuknoProfile>(apiUrl('/api/v1/billiards/auth/profile'), withCredentials)
  }

  const updateProfile = async (payload: {
    display_name?: string
    bio?: string
    location?: string
    telegram?: string
  }) => {
    const result = await $fetch<SuknoProfile>(apiUrl('/api/v1/billiards/auth/profile'), {
      method: 'PATCH',
      ...withCredentials,
      body: payload
    })
    await fetchMe()
    return result
  }

  const mediaUrl = (path?: string | null) => {
    if (!path) return ''
    if (/^(https?:|blob:|data:)/i.test(path)) return path
    return apiUrl(path)
  }

  const uploadAvatar = async (file: File) => {
    const body = new FormData()
    body.append('file', file)
    const result = await $fetch<SuknoProfile>(apiUrl('/api/v1/billiards/auth/avatar'), {
      method: 'POST',
      ...withCredentials,
      body
    })
    await fetchMe()
    return result
  }

  const deleteAvatar = async () => {
    const result = await $fetch<SuknoProfile>(apiUrl('/api/v1/billiards/auth/avatar'), {
      method: 'DELETE',
      ...withCredentials
    })
    await fetchMe()
    return result
  }

  const changePassword = async (currentPassword: string, newPassword: string) => {
    return await $fetch<{ message: string }>(apiUrl('/api/v1/billiards/auth/change-password'), {
      method: 'POST',
      ...withCredentials,
      body: { current_password: currentPassword, new_password: newPassword }
    })
  }

  const isAccountUser = computed(() => profile.value?.source === 'account')
  const isAdmin = computed(() =>
    isAdminRole(profile.value?.role, profile.value?.is_admin)
  )
  const isOperator = computed(() => isOperatorRole(profile.value?.role))
  const registrationAllowed = computed(() => config.value?.allow_registration !== false)

  return {
    config,
    profile,
    isAccountUser,
    isAdmin,
    isOperator,
    registrationAllowed,
    loadConfig,
    fetchMe,
    trySuknoRefresh,
    login,
    verifyTotp,
    totpStatus,
    totpSetup,
    totpEnable,
    totpDisable,
    register,
    logout,
    verifyEmail,
    resendVerification,
    requestPasswordReset,
    confirmPasswordReset,
    loadProfile,
    updateProfile,
    mediaUrl,
    uploadAvatar,
    deleteAvatar,
    changePassword,
    clearAccountSession
  }
}
