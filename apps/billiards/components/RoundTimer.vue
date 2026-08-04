<script setup lang="ts">
const store = useKolkhozStore()

const remainingMs = ref(0)
const hasBeeped = ref(false)
let timer: ReturnType<typeof setInterval> | null = null
let audioCtx: AudioContext | null = null

const format = (ms: number) => {
  const total = Math.max(0, Math.floor(ms / 1000))
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

const ensureAudio = async () => {
  if (typeof window === 'undefined') return null
  if (!audioCtx) audioCtx = new AudioContext()
  if (audioCtx.state === 'suspended') {
    try {
      await audioCtx.resume()
    } catch {
      /* ignore */
    }
  }
  return audioCtx
}

/** Short triple chirp when round time is up (unless muted). */
const beep = async () => {
  if (store.tournament.timerMuted || typeof window === 'undefined') return
  const ctx = await ensureAudio()
  if (!ctx) return
  try {
    for (let i = 0; i < 3; i += 1) {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.value = 880 + i * 60
      const t0 = ctx.currentTime + i * 0.18
      gain.gain.setValueAtTime(0.0001, t0)
      gain.gain.exponentialRampToValueAtTime(0.08, t0 + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.14)
      osc.start(t0)
      osc.stop(t0 + 0.15)
    }
  } catch {
    /* ignore */
  }
}

const tick = () => {
  if (store.timerIsPaused) {
    remainingMs.value = store.tournament.timerPausedRemainingMs || 0
    return
  }
  const ends = store.tournament.roundEndsAt
  if (!ends) {
    remainingMs.value = 0
    hasBeeped.value = false
    return
  }
  const left = new Date(ends).getTime() - Date.now()
  remainingMs.value = left
  if (left <= 0) {
    remainingMs.value = 0
    if (!hasBeeped.value) {
      hasBeeped.value = true
      void beep()
    }
    store.clearRoundTimer()
  }
}

onMounted(() => {
  tick()
  timer = setInterval(tick, 250)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})

watch(
  () => store.tournament.roundEndsAt,
  (value) => {
    if (value) hasBeeped.value = false
  }
)

const urgent = computed(() => remainingMs.value > 0 && remainingMs.value < 60_000 && !store.timerIsPaused)
const visible = computed(() => store.timerIsRunning || store.timerIsPaused)

const panelClass = computed(() => {
  if (store.timerIsPaused) return 'timer-panel--paused'
  if (urgent.value) return 'timer-panel--urgent'
  return 'timer-panel--running'
})

const unlockAudio = () => {
  void ensureAudio()
}
</script>

<template>
  <div v-if="visible" class="timer-panel" :class="panelClass">
    <p class="timer-panel__label">
      {{ store.timerIsPaused ? 'Таймер на паузе' : 'Таймер тура' }}
    </p>
    <p class="font-display text-3xl font-bold tabular-nums">{{ format(remainingMs) }}</p>
    <div class="mt-2 flex flex-wrap gap-2">
      <button
        v-if="store.timerIsRunning"
        type="button"
        class="timer-panel__btn"
        @click="store.pauseRoundTimer(); unlockAudio()"
      >
        <AppIcon name="pause" size="sm" /> Пауза
      </button>
      <button
        v-if="store.timerIsPaused"
        type="button"
        class="timer-panel__btn"
        @click="store.resumeRoundTimer(); unlockAudio()"
      >
        <AppIcon name="play" size="sm" /> Продолжить
      </button>
      <button type="button" class="timer-panel__btn" @click="store.clearRoundTimer()">Стоп</button>
      <button
        type="button"
        class="timer-panel__btn"
        @click="store.setTimerMuted(!store.tournament.timerMuted); unlockAudio()"
      >
        {{ store.tournament.timerMuted ? 'Вкл. звук' : 'Без звука' }}
      </button>
    </div>
  </div>
</template>
