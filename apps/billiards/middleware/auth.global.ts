export default defineNuxtRouteMiddleware(async (to) => {
  // Auth is client-only: SSO code + cookies live in the browser.
  if (import.meta.server) return

  // TV can join a sync room by code without hub login (read-only poll).
  const path = to.path.replace(/\/$/, '') || '/'
  if (path === '/tv' || path.endsWith('/tv')) {
    return
  }

  const auth = useHubAuth()
  const ok = await auth.ensureAuthenticated(to.query as Record<string, unknown>)
  if (!ok) {
    auth.redirectToHubLogin()
    return abortNavigation()
  }
})
