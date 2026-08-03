<script setup lang="ts">
const store = useKolkhozStore()

const remainingMs = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const format = (ms: number) => {
  const total = Math.max(0, Math.floor(ms / 1000))
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

const beep = () => {
  if (store.tournament.timerMuted || typeof window === 'undefined') return
  try {
    const ctx = new AudioContext()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.frequency.value = 880
    gain.gain.value = 0.05
    osc.start()
    osc.stop(ctx.currentTime + 0.25)
  } catch {
    /* ignore */
  }
}

const tick = () => {
  const ends = store.tournament.roundEndsAt
  if (!ends) {
    remainingMs.value = 0
    return
  }
  const left = new Date(ends).getTime() - Date.now()
  remainingMs.value = left
  if (left <= 0) {
    remainingMs.value = 0
    beep()
    store.clearRoundTimer()
  }
}

onMounted(() => {
  tick()
  timer = setInterval(tick, 500)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})

const urgent = computed(() => remainingMs.value > 0 && remainingMs.value < 60_000)
</script>

<template>
  <div
    v-if="store.tournament.roundEndsAt"
    class="fixed bottom-4 right-4 z-40 rounded-2xl border px-4 py-3 shadow-2xl"
    :class="urgent ? 'border-red-400/60 bg-red-950/90 text-red-100' : 'border-cloth-accent/40 bg-cloth-deep/95 text-cloth-chalk'"
  >
    <p class="text-[10px] uppercase tracking-widest text-cloth-muted">Таймер тура</p>
    <p class="font-display text-3xl font-bold tabular-nums">{{ format(remainingMs) }}</p>
    <div class="mt-2 flex gap-2">
      <button type="button" class="btn-ghost py-1 text-[11px]" @click="store.clearRoundTimer()">Стоп</button>
      <button type="button" class="btn-ghost py-1 text-[11px]" @click="store.setTimerMuted(!store.tournament.timerMuted)">
        {{ store.tournament.timerMuted ? 'звук' : 'mute' }}
      </button>
    </div>
  </div>
</template>
