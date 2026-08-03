export default defineNuxtRouteMiddleware(async () => {
  // Auth is client-only: SSO code + cookies live in the browser.
  if (import.meta.server) return

  const auth = useHubAuth()
  const ok = await auth.ensureAuthenticated()
  if (!ok) {
    auth.redirectToHubLogin()
    return abortNavigation()
  }
})
