export default defineNuxtPlugin(() => {
  if (!import.meta.client) return

  const store = useCupStore()
  const sync = useCupSync()
  sync.hydrateMeta()

  store.$subscribe(() => {
    sync.onLocalChange()
  })

  if (sync.role.value === 'follower' && sync.roomCode.value) {
    void sync.resumeFollowerIfPossible()
  }
})
