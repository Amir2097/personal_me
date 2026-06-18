import { useAuthStore } from '~/stores/auth'

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
  is_public?: boolean
  featured?: boolean
  sort_order?: number
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
    email?: string
  ): Promise<AuthTokensResponse> => {
    return await $fetch<AuthTokensResponse>('/api/v1/auth/register', {
      ...fetchDefaults,
      method: 'POST',
      body: { username, password, email: email || undefined }
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

  const listProjects = async (): Promise<Project[]> => {
    return await $fetch<Project[]>('/api/v1/projects', fetchDefaults)
  }

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
    deleteProject
  }
}
