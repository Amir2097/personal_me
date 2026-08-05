export default defineNuxtPlugin(() => {
  if (!import.meta.client) return

  const store = useKolkhozStore()
  const sync = useKolkhozSync()
  sync.hydrateMeta()

  // Host: any local mutation → debounced push to API.
  store.$subscribe(() => {
    sync.onLocalChange()
  })

  // Resume follower only if the room still exists (validated async).
  if (sync.role.value === 'follower' && sync.roomCode.value) {
    void sync.resumeFollowerIfPossible()
  }
})
