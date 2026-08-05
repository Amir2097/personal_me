export type GameSoundKind =
  | 'score'
  | 'fine'
  | 'pot_claim'
  | 'pot_return'
  | 'miss'
  | 'dropout'
  | 'timer'
  | 'ui'

type Tone = { freq: number; dur: number; type?: OscillatorType; gain?: number; delay?: number }

const PATTERNS: Record<GameSoundKind, Tone[]> = {
  score: [
    { freq: 520, dur: 0.07, type: 'triangle', gain: 0.07 },
    { freq: 780, dur: 0.1, type: 'triangle', gain: 0.06, delay: 0.06 }
  ],
  fine: [
    { freq: 220, dur: 0.12, type: 'sawtooth', gain: 0.045 },
    { freq: 180, dur: 0.14, type: 'sawtooth', gain: 0.04, delay: 0.1 }
  ],
  pot_claim: [
    { freq: 660, dur: 0.08, type: 'square', gain: 0.05 },
    { freq: 990, dur: 0.12, type: 'square', gain: 0.045, delay: 0.08 }
  ],
  pot_return: [
    { freq: 400, dur: 0.1, type: 'sine', gain: 0.05 },
    { freq: 320, dur: 0.12, type: 'sine', gain: 0.04, delay: 0.09 }
  ],
  miss: [{ freq: 260, dur: 0.06, type: 'triangle', gain: 0.035 }],
  dropout: [
    { freq: 300, dur: 0.08, type: 'sine', gain: 0.04 },
    { freq: 200, dur: 0.14, type: 'sine', gain: 0.035, delay: 0.08 }
  ],
  timer: [
    { freq: 880, dur: 0.14, type: 'sine', gain: 0.08 },
    { freq: 940, dur: 0.14, type: 'sine', gain: 0.08, delay: 0.18 },
    { freq: 1000, dur: 0.14, type: 'sine', gain: 0.08, delay: 0.36 }
  ],
  ui: [{ freq: 600, dur: 0.04, type: 'sine', gain: 0.03 }]
}

/** Shared across all composable callers (header, timer, plugin, TV). */
let sharedCtx: AudioContext | null = null
/** Chrome autoplay: AudioContext may only start after a user gesture. */
let audioUnlocked = false

/**
 * Lightweight WebAudio SFX for Kolkhoz (no asset files).
 * Respects tournament.timerMuted as global mute for all game sounds.
 */
export const useGameSounds = () => {
  const store = useKolkhozStore()

  const ensureAudio = async () => {
    if (typeof window === 'undefined') return null
    // Do not construct AudioContext until a real user gesture unlocked audio.
    if (!audioUnlocked && !sharedCtx) return null
    if (!sharedCtx) {
      sharedCtx = new AudioContext()
    }
    if (sharedCtx.state === 'suspended') {
      try {
        await sharedCtx.resume()
      } catch {
        return null
      }
    }
    audioUnlocked = sharedCtx.state === 'running'
    return audioUnlocked ? sharedCtx : null
  }

  /** Call only from click / pointer / key handlers — never from onMounted. */
  const unlock = () => {
    if (typeof window === 'undefined') return
    audioUnlocked = true
    void ensureAudio()
  }

  const play = async (kind: GameSoundKind) => {
    if (typeof window === 'undefined') return
    if (store.tournament.timerMuted) return
    if (!audioUnlocked) return
    const ctx = await ensureAudio()
    if (!ctx) return
    const tones = PATTERNS[kind]
    try {
      for (const tone of tones) {
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()
        osc.type = tone.type || 'sine'
        osc.frequency.value = tone.freq
        osc.connect(gain)
        gain.connect(ctx.destination)
        const t0 = ctx.currentTime + (tone.delay || 0)
        const peak = tone.gain ?? 0.05
        gain.gain.setValueAtTime(0.0001, t0)
        gain.gain.exponentialRampToValueAtTime(peak, t0 + 0.015)
        gain.gain.exponentialRampToValueAtTime(0.0001, t0 + tone.dur)
        osc.start(t0)
        osc.stop(t0 + tone.dur + 0.02)
      }
    } catch {
      /* ignore */
    }
  }

  const playForEventKind = (kind: string, _ballId?: string) => {
    if (kind === 'score') {
      void play('score')
      return
    }
    if (kind === 'penalty' || kind === 'fine_place' || kind === 'casual_foul') {
      void play('fine')
      return
    }
    if (kind === 'fine_claim') {
      void play('pot_claim')
      return
    }
    if (kind === 'fine_return') {
      void play('pot_return')
      return
    }
    if (kind === 'dropout') {
      void play('dropout')
      return
    }
  }

  return { play, playForEventKind, unlock, ensureAudio }
}
