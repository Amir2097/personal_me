import { useAuthStore } from '~/stores/auth'

export type SiteLegalPublic = {
  site_name: string
  owner_name: string
  site_url: string
  privacy_policy: string
  terms_of_use: string
  updated_at: string
}

export type Integration = {
  id: number
  key: string
  url: string
  label: string
  requires_auth: boolean
  use_sso: boolean
  enabled: boolean
  sort_order: number
  created_at: string
}

export type IntegrationInput = {
  key: string
  url: string
  label?: string
  requires_auth?: boolean
  use_sso?: boolean
  enabled?: boolean
  sort_order?: number
}

export type Project = {
  id: number
  slug: string
  title: string
  summary: string
  description: string
  tech_stack: string
  github_url: string
  demo_url: string
  image_url: string
  gallery: string[]
  is_public: boolean
  featured: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export type ProjectInput = {
  slug: string
  title: string
  summary?: string
  description?: string
  tech_stack?: string
  github_url?: string
  demo_url?: string
  image_url?: string
  gallery_urls?: string
  is_public?: boolean
  featured?: boolean
  sort_order?: number
}

export type FeedbackInput = {
  name: string
  email: string
  message: string
  company?: string
}

export const useApi = () => {
  const config = useRuntimeConfig()
  const auth = useAuthStore()

  const apiBaseUrl = import.meta.client
    ? config.public.apiBaseUrl
    : config.apiInternalUrl

  const fetchDefaults = {
    baseURL: apiBaseUrl,
    credentials: 'include' as const
  }

  type ExecuteCommandResponse = {
    output: string
    requires_auth: boolean
    forbidden?: boolean
    action?: string | null
    url?: string | null
  }

  type AuthTokensResponse = {
    access_token: string
    refresh_token: string
    token_type: string
    username?: string
    is_admin?: boolean
  }

  type UserProfileResponse = {
    username: string
    is_admin: boolean
    email?: string | null
  }

  type AboutResponse = {
    owner_name: string
    tagline: string
    bio: string
    experience: string
    skills: string[]
    github_url: string
    telegram: string
    resume_url: string
    resume_available: boolean
    resume_path: string
    motd: string
    web_path: string
    contacts: Contact[]
  }

  type Contact = {
    id: number
    key: string
    label: string
    value: string
    kind: 'link' | 'email' | 'text'
    enabled: boolean
    sort_order: number
    href: string | null
    created_at: string
  }

  type ContactInput = {
    key: string
    label?: string
    value: string
    kind?: 'link' | 'email' | 'text'
    enabled?: boolean
    sort_order?: number
  }

  type SiteStatusResponse = {
    api: string
    database: string
    smtp: string
    version: string
  }

  type SiteSeoPublic = {
    site_name: string
    owner_name: string
    tagline: string
    site_url: string
    seo_title_suffix: string
    seo_description: string
    seo_keywords: string
    og_image_url: string
  }

  type SiteSettings = SiteSeoPublic & {
    bio: string
    experience: string
    skills: string
    motd: string
    resume_url: string
    privacy_policy: string
    terms_of_use: string
    updated_at: string
  }

  type OAuthClient = {
    id: number
    client_id: string
    name: string
    redirect_uris: string[]
    scopes: string
    enabled: boolean
  }

  type OAuthClientInput = {
    client_id: string
    client_secret: string
    name?: string
    redirect_uris: string[]
    scopes?: string
  }

  type AdminUserStats = {
    total: number
    active: number
    banned: number
    admins: number
  }

  type AdminUser = {
    id: number
    username: string
    email: string | null
    is_admin: boolean
    is_active: boolean
    created_at: string
    last_login_at: string | null
    last_session_at: string | null
  }

  type AuthConfigResponse = {
    allow_registration: boolean
    expose_reset_token: boolean
    password_reset_via_email: boolean
  }

  type PasswordResetResponse = {
    message: string
    reset_token: string | null
    expires_in_minutes: number
  }

  const getAuthConfig = async (): Promise<AuthConfigResponse> => {
    return await $fetch<AuthConfigResponse>('/api/v1/auth/config', fetchDefaults)
  }

  const executeCommandRaw = async (command: string): Promise<ExecuteCommandResponse> => {
    return await $fetch<ExecuteCommandResponse>('/api/v1/terminal/execute', {
      ...fetchDefaults,
      method: 'POST',
      body: { command }
    })
  }

  const login = async (username: string, password: string): Promise<AuthTokensResponse> => {
    return await $fetch<AuthTokensResponse>('/api/v1/auth/login', {
      ...fetchDefaults,
      method: 'POST',
      body: { username, password }
    })
  }

  const register = async (
    username: string,
    password: string,
    email?: string,
    acceptTerms = false
  ): Promise<AuthTokensResponse> => {
    return await $fetch<AuthTokensResponse>('/api/v1/auth/register', {
      ...fetchDefaults,
      method: 'POST',
      body: { username, password, email: email || undefined, accept_terms: acceptTerms }
    })
  }

  const me = async (): Promise<UserProfileResponse> => {
    return await $fetch<UserProfileResponse>('/api/v1/auth/me', fetchDefaults)
  }

  const refresh = async (): Promise<AuthTokensResponse> => {
    return await $fetch<AuthTokensResponse>('/api/v1/auth/refresh', {
      ...fetchDefaults,
      method: 'POST',
      body: {}
    })
  }

  const logout = async () => {
    return await $fetch('/api/v1/auth/logout', {
      ...fetchDefaults,
      method: 'POST',
      body: {}
    })
  }

  const requestPasswordReset = async (username: string): Promise<PasswordResetResponse> => {
    return await $fetch<PasswordResetResponse>('/api/v1/auth/password-reset/request', {
      ...fetchDefaults,
      method: 'POST',
      body: { username }
    })
  }

  const confirmPasswordReset = async (token: string, newPassword: string) => {
    return await $fetch('/api/v1/auth/password-reset/confirm', {
      ...fetchDefaults,
      method: 'POST',
      body: { token, new_password: newPassword }
    })
  }

  const changePassword = async (currentPassword: string, newPassword: string) => {
    return await $fetch('/api/v1/auth/change-password', {
      ...fetchDefaults,
      method: 'POST',
      body: { current_password: currentPassword, new_password: newPassword }
    })
  }

  const listIntegrations = async (): Promise<Integration[]> => {
    return await $fetch<Integration[]>('/api/v1/integrations', fetchDefaults)
  }

  const listAllIntegrations = async (): Promise<Integration[]> => {
    return await $fetch<Integration[]>('/api/v1/integrations/all', fetchDefaults)
  }

  const createIntegration = async (payload: IntegrationInput): Promise<Integration> => {
    return await $fetch<Integration>('/api/v1/integrations', {
      ...fetchDefaults,
      method: 'POST',
      body: payload
    })
  }

  const updateIntegration = async (
    id: number,
    payload: Partial<IntegrationInput>
  ): Promise<Integration> => {
    return await $fetch<Integration>(`/api/v1/integrations/${id}`, {
      ...fetchDefaults,
      method: 'PATCH',
      body: payload
    })
  }

  const deleteIntegration = async (id: number): Promise<void> => {
    await $fetch(`/api/v1/integrations/${id}`, {
      ...fetchDefaults,
      method: 'DELETE'
    })
  }

  const listProjects = async (featured = false): Promise<Project[]> => {
    const query = featured ? '?featured=true' : ''
    return await $fetch<Project[]>(`/api/v1/projects${query}`, fetchDefaults)
  }

  const listFeaturedProjects = async (): Promise<Project[]> => listProjects(true)

  const listAllProjects = async (): Promise<Project[]> => {
    return await $fetch<Project[]>('/api/v1/projects/all', fetchDefaults)
  }

  const getProject = async (slug: string): Promise<Project> => {
    return await $fetch<Project>(`/api/v1/projects/${slug}`, fetchDefaults)
  }

  const createProject = async (payload: ProjectInput): Promise<Project> => {
    return await $fetch<Project>('/api/v1/projects', {
      ...fetchDefaults,
      method: 'POST',
      body: payload
    })
  }

  const updateProject = async (
    id: number,
    payload: Partial<ProjectInput>
  ): Promise<Project> => {
    return await $fetch<Project>(`/api/v1/projects/${id}`, {
      ...fetchDefaults,
      method: 'PATCH',
      body: payload
    })
  }

  const deleteProject = async (id: number): Promise<void> => {
    await $fetch(`/api/v1/projects/${id}`, {
      ...fetchDefaults,
      method: 'DELETE'
    })
  }

  const getAbout = async (): Promise<AboutResponse> => {
    return await $fetch<AboutResponse>('/api/v1/site/about', fetchDefaults)
  }

  const getSiteSeo = async (): Promise<SiteSeoPublic> => {
    return await $fetch<SiteSeoPublic>('/api/v1/site/seo', fetchDefaults)
  }

  const getSiteLegal = async (): Promise<SiteLegalPublic> => {
    return await $fetch<SiteLegalPublic>('/api/v1/site/legal', fetchDefaults)
  }

  const getSiteSettings = async (): Promise<SiteSettings> => {
    return await $fetch<SiteSettings>('/api/v1/site/settings', fetchDefaults)
  }

  const updateSiteSettings = async (
    payload: Partial<Omit<SiteSettings, 'updated_at'>>
  ): Promise<SiteSettings> => {
    return await $fetch<SiteSettings>('/api/v1/site/settings', {
      ...fetchDefaults,
      method: 'PATCH',
      body: payload
    })
  }

  const getSiteStatus = async (): Promise<SiteStatusResponse> => {
    return await $fetch<SiteStatusResponse>('/api/v1/site/status', fetchDefaults)
  }

  const getFeedbackConfig = async (): Promise<{ enabled: boolean }> => {
    return await $fetch<{ enabled: boolean }>('/api/v1/feedback/config', fetchDefaults)
  }

  const submitFeedback = async (payload: FeedbackInput): Promise<{ message: string }> => {
    return await $fetch<{ message: string }>('/api/v1/feedback', {
      ...fetchDefaults,
      method: 'POST',
      body: payload
    })
  }

  const updateProfile = async (email: string | null): Promise<UserProfileResponse> => {
    return await $fetch<UserProfileResponse>('/api/v1/auth/profile', {
      ...fetchDefaults,
      method: 'PATCH',
      body: { email }
    })
  }

  const listOAuthClients = async (): Promise<OAuthClient[]> => {
    return await $fetch<OAuthClient[]>('/api/v1/oidc/clients', fetchDefaults)
  }

  const createOAuthClient = async (payload: OAuthClientInput): Promise<OAuthClient> => {
    return await $fetch<OAuthClient>('/api/v1/oidc/clients', {
      ...fetchDefaults,
      method: 'POST',
      body: payload
    })
  }

  const deleteOAuthClient = async (id: number): Promise<void> => {
    await $fetch(`/api/v1/oidc/clients/${id}`, {
      ...fetchDefaults,
      method: 'DELETE'
    })
  }

  const listContacts = async (): Promise<Contact[]> => {
    return await $fetch<Contact[]>('/api/v1/contacts', fetchDefaults)
  }

  const listAllContacts = async (): Promise<Contact[]> => {
    return await $fetch<Contact[]>('/api/v1/contacts/all', fetchDefaults)
  }

  const createContact = async (payload: ContactInput): Promise<Contact> => {
    return await $fetch<Contact>('/api/v1/contacts', {
      ...fetchDefaults,
      method: 'POST',
      body: payload
    })
  }

  const updateContact = async (
    id: number,
    payload: Partial<ContactInput>
  ): Promise<Contact> => {
    return await $fetch<Contact>(`/api/v1/contacts/${id}`, {
      ...fetchDefaults,
      method: 'PATCH',
      body: payload
    })
  }

  const deleteContact = async (id: number): Promise<void> => {
    await $fetch(`/api/v1/contacts/${id}`, {
      ...fetchDefaults,
      method: 'DELETE'
    })
  }

  const getUserStats = async (): Promise<AdminUserStats> => {
    return await $fetch<AdminUserStats>('/api/v1/users/stats', fetchDefaults)
  }

  const listUsers = async (): Promise<AdminUser[]> => {
    return await $fetch<AdminUser[]>('/api/v1/users', fetchDefaults)
  }

  const updateUser = async (
    id: number,
    payload: { is_active?: boolean; is_admin?: boolean }
  ): Promise<AdminUser> => {
    return await $fetch<AdminUser>(`/api/v1/users/${id}`, {
      ...fetchDefaults,
      method: 'PATCH',
      body: payload
    })
  }

  const revokeUserSessions = async (id: number): Promise<void> => {
    await $fetch(`/api/v1/users/${id}/revoke-sessions`, {
      ...fetchDefaults,
      method: 'POST'
    })
  }

  const restoreSession = async (): Promise<boolean> => {
    try {
      const profile = await me()
      auth.setSession(profile.username, profile.is_admin)
      return true
    } catch {
      auth.logout()
      return false
    }
  }

  const executeCommand = async (command: string): Promise<ExecuteCommandResponse> => {
    try {
      return await executeCommandRaw(command)
    } catch (error) {
      const status = (error as { statusCode?: number }).statusCode
      if (status === 401) {
        try {
          await refresh()
          await restoreSession()
          return await executeCommandRaw(command)
        } catch {
          auth.logout()
        }
      }
      throw error
    }
  }

  return {
    getAuthConfig,
    executeCommand,
    login,
    register,
    me,
    refresh,
    logout,
    restoreSession,
    requestPasswordReset,
    confirmPasswordReset,
    changePassword,
    listIntegrations,
    listAllIntegrations,
    createIntegration,
    updateIntegration,
    deleteIntegration,
    listProjects,
    listAllProjects,
    getProject,
    createProject,
    updateProject,
    deleteProject,
    getAbout,
    getSiteSeo,
    getSiteLegal,
    getSiteSettings,
    updateSiteSettings,
    getSiteStatus,
    getFeedbackConfig,
    submitFeedback,
    updateProfile,
    listFeaturedProjects,
    listOAuthClients,
    createOAuthClient,
    deleteOAuthClient,
    listContacts,
    listAllContacts,
    createContact,
    updateContact,
    deleteContact,
    getUserStats,
    listUsers,
    updateUser,
    revokeUserSessions
  }
}
