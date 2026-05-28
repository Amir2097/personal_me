import { useAuthStore } from '~/stores/auth'

export const useApi = () => {
  const config = useRuntimeConfig()
  const auth = useAuthStore()

  type ExecuteCommandResponse = {
    output: string
    requires_auth: boolean
  }

  type AuthTokensResponse = {
    access_token: string
    refresh_token: string
    token_type: string
  }

  const executeCommandRaw = async (command: string): Promise<ExecuteCommandResponse> => {
    return await $fetch<ExecuteCommandResponse>('/api/v1/terminal/execute', {
      baseURL: config.public.apiBaseUrl,
      method: 'POST',
      headers: auth.token
        ? {
            Authorization: `Bearer ${auth.token}`
          }
        : undefined,
      body: { command }
    })
  }

  const login = async (username: string, password: string): Promise<AuthTokensResponse> => {
    return await $fetch<AuthTokensResponse>('/api/v1/auth/login', {
      baseURL: config.public.apiBaseUrl,
      method: 'POST',
      body: { username, password }
    })
  }

  const register = async (username: string, password: string): Promise<AuthTokensResponse> => {
    return await $fetch<AuthTokensResponse>('/api/v1/auth/register', {
      baseURL: config.public.apiBaseUrl,
      method: 'POST',
      body: { username, password }
    })
  }

  const refresh = async (refreshToken: string): Promise<AuthTokensResponse> => {
    return await $fetch<AuthTokensResponse>('/api/v1/auth/refresh', {
      baseURL: config.public.apiBaseUrl,
      method: 'POST',
      body: { refresh_token: refreshToken }
    })
  }

  const logout = async (refreshToken: string) => {
    return await $fetch('/api/v1/auth/logout', {
      baseURL: config.public.apiBaseUrl,
      method: 'POST',
      body: { refresh_token: refreshToken }
    })
  }

  const executeCommand = async (command: string): Promise<ExecuteCommandResponse> => {
    try {
      return await executeCommandRaw(command)
    } catch (error) {
      const status = (error as { statusCode?: number }).statusCode
      if (status === 401 && auth.refreshToken) {
        try {
          const tokens = await refresh(auth.refreshToken)
          auth.setTokens(tokens.access_token, tokens.refresh_token)
          return await executeCommandRaw(command)
        } catch {
          auth.logout()
        }
      }
      throw error
    }
  }

  return { executeCommand, login, register, refresh, logout }
}
