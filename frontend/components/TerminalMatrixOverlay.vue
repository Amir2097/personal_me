<script setup lang="ts">
const { active } = useTerminalMatrix()
const canvasRef = ref<HTMLCanvasElement | null>(null)
let raf = 0

const stop = () => {
  cancelAnimationFrame(raf)
  const canvas = canvasRef.value
  const ctx = canvas?.getContext('2d')
  if (canvas && ctx) ctx.clearRect(0, 0, canvas.width, canvas.height)
}

const runMatrix = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const chars = '01アイウエオカキクケコサシスセソ'
  const fontSize = 14
  const columns = Math.floor(canvas.width / fontSize)
  const drops = Array.from({ length: columns }, () => Math.random() * -40)
  let frame = 0

  const draw = () => {
    if (!active.value) {
      stop()
      return
    }
    ctx.fillStyle = 'rgba(11, 15, 16, 0.12)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.fillStyle = '#00ff88'
    ctx.font = `${fontSize}px JetBrains Mono, monospace`
    for (let i = 0; i < drops.length; i += 1) {
      const char = chars[Math.floor(Math.random() * chars.length)]
      ctx.fillText(char, i * fontSize, drops[i] * fontSize)
      if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
        drops[i] = 0
      }
      drops[i] += 1
    }
    frame += 1
    if (frame > 420) {
      active.value = false
      stop()
      return
    }
    raf = requestAnimationFrame(draw)
  }

  stop()
  raf = requestAnimationFrame(draw)
}

watch(active, (value) => {
  if (value) nextTick(runMatrix)
  else stop()
})
</script>

<template>
  <canvas
    v-show="active"
    ref="canvasRef"
    class="pointer-events-none fixed inset-0 z-[10000] opacity-80"
  />
</template>
