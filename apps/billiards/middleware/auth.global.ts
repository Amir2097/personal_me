export default defineNuxtRouteMiddleware(async (to) => {
  if (import.meta.server) return

  const auth = useHubAuth()
  await auth.ensureAuthenticated(to.query as Record<string, unknown>)

  const suknoAuth = useSuknoAuth()
  try {
    await suknoAuth.fetchMe()
  } catch {
    /* device / hub bearer session */
  }
})
