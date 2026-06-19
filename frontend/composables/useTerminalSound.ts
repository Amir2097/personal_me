/** Short terminal key click via Web Audio API. */

let audioContext: AudioContext | null = null

export function playTerminalKeySound() {
  if (!import.meta.client) return
  try {
    audioContext ||= new AudioContext()
    const ctx = audioContext
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'square'
    osc.frequency.value = 920
    gain.gain.value = 0.015
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start()
    osc.stop(ctx.currentTime + 0.025)
  } catch {
    // ignore autoplay / unsupported
  }
}
