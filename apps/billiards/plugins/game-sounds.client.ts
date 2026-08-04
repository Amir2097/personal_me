export default defineNuxtPlugin(() => {
  if (!import.meta.client) return

  const store = useKolkhozStore()
  const sounds = useGameSounds()
  let lastLen = store.events.length

  // Unlock AudioContext on first pointer interaction (browser autoplay policy).
  const unlockOnce = () => {
    sounds.unlock()
    window.removeEventListener('pointerdown', unlockOnce)
  }
  window.addEventListener('pointerdown', unlockOnce, { once: true })

  store.$subscribe(() => {
    const len = store.events.length
    if (len > lastLen) {
      // Play for each newly appended event (score + pot claim can land together).
      for (let i = lastLen; i < len; i += 1) {
        const event = store.events[i]
        if (event) sounds.playForEventKind(event.kind, event.ballId)
      }
    }
    lastLen = len
  })
})
