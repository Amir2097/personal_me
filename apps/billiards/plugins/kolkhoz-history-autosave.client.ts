/** Debounced cloud snapshot while a kolkhoz session is in progress. */

const AUTOSAVE_DELAY_MS = 90_000

export default defineNuxtPlugin(() => {
  if (!import.meta.client) return

  const store = useKolkhozStore()
  const history = useKolkhozHistory()

  history.hydrateLastSaved()

  let timer: ReturnType<typeof setTimeout> | null = null
  let lastFingerprint = ''

  const fingerprint = () =>
    JSON.stringify({
      players: store.players.length,
      events: store.events.length,
      mode: store.mode,
      round: store.currentRound?.number ?? 0,
      updatedAt: store.updatedAt
    })

  const schedule = () => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(async () => {
      if (!store.players.length && !store.events.length) return
      const fp = fingerprint()
      if (fp === lastFingerprint) return
      const saved = await history.saveCurrent('', { asNew: false })
      if (saved) lastFingerprint = fp
    }, AUTOSAVE_DELAY_MS)
  }

  store.$subscribe(() => {
    schedule()
  })
})
