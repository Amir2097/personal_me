<script setup lang="ts">
const store = useKolkhozStore()
const { hydrateTheme } = useClothTheme()

let rafId = 0
let targetScroll = 0
let currentScroll = 0

const applyScroll = () => {
  // Soft lerp removes the "snap" feel from raw scroll updates.
  currentScroll += (targetScroll - currentScroll) * 0.14
  document.documentElement.style.setProperty('--table-scroll', currentScroll.toFixed(2))

  if (Math.abs(targetScroll - currentScroll) > 0.15) {
    rafId = requestAnimationFrame(applyScroll)
  } else {
    currentScroll = targetScroll
    document.documentElement.style.setProperty('--table-scroll', currentScroll.toFixed(2))
    rafId = 0
  }
}

const onScroll = () => {
  targetScroll = window.scrollY || 0
  if (!rafId) rafId = requestAnimationFrame(applyScroll)
}

onMounted(() => {
  hydrateTheme()
  store.hydrate()
  targetScroll = window.scrollY || 0
  currentScroll = targetScroll
  document.documentElement.style.setProperty('--table-scroll', currentScroll.toFixed(2))

  window.addEventListener('scroll', onScroll, { passive: true })
  onBeforeUnmount(() => {
    window.removeEventListener('scroll', onScroll)
    if (rafId) cancelAnimationFrame(rafId)
  })
})
</script>

<template>
  <div class="grunge-shell min-h-screen">
    <NuxtPage />
  </div>
</template>
