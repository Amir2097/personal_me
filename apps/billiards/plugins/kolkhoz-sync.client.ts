export default defineNuxtPlugin(() => {
  if (!import.meta.client) return

  const store = useKolkhozStore()
  const sync = useKolkhozSync()
  sync.hydrateMeta()

  // Host: any local mutation → debounced push to API.
  store.$subscribe(() => {
    sync.onLocalChange()
  })

  // Resume follower polling after reload.
  if (sync.role.value === 'follower' && sync.roomCode.value) {
    sync.startPolling()
  }
})
