import { useApi } from '~/composables/useApi'
import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware(async () => {
  const api = useApi()
  const auth = useAuthStore()
  try {
    const profile = await api.me()
    auth.setSession(profile.username, profile.is_admin)
  } catch {
    return navigateTo('/')
  }
})
