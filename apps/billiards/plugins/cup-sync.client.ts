export default defineNuxtPlugin(() => {
  if (!import.meta.client) return

  const store = useCupStore()
  const sync = useCupSync()
  sync.hydrateMeta()

  store.$subscribe(() => {
    sync.onLocalChange()
  })

  if (sync.roomCode.value && (sync.role.value === 'follower' || sync.role.value === 'host')) {
    void sync.resumeFollowerIfPossible()
  }
})
