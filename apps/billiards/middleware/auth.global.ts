export default defineNuxtRouteMiddleware(async (to) => {
  // Auth is client-only: SSO code + cookies live in the browser.
  if (import.meta.server) return

  const auth = useHubAuth()
  const ok = await auth.ensureAuthenticated(to.query as Record<string, unknown>)
  if (!ok) {
    auth.redirectToHubLogin()
    return abortNavigation()
  }
})
