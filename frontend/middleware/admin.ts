export default defineNuxtRouteMiddleware(() => {
  const auth = useAuthStore()
  if (!auth.isAuthenticated || !auth.isAdmin) {
    return navigateTo('/')
  }
})
