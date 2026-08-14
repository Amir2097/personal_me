<script setup lang="ts">
const store = useKolkhozStore()
const { hydrateTheme } = useClothTheme()
const { appPath } = useAppBase()
const { title, description, keywords, ogImage, canonical, brandName, hydrate: hydrateSeo } = useSuknoSeo()

useHead(() => ({
  title: title.value,
  titleTemplate: (page?: string) => {
    if (!page || page === title.value || page === brandName.value) return title.value
    return `${page} · ${brandName.value}`
  },
  link: [
    { rel: 'icon', type: 'image/svg+xml', href: appPath('favicon.svg') },
    { rel: 'apple-touch-icon', href: appPath('brand/icon.png') },
    ...(canonical.value ? [{ rel: 'canonical', href: canonical.value }] : [])
  ],
  meta: [
    { name: 'description', content: description.value },
    ...(keywords.value ? [{ name: 'keywords', content: keywords.value }] : []),
    { property: 'og:title', content: title.value },
    { property: 'og:description', content: description.value },
    { property: 'og:image', content: ogImage.value },
    ...(canonical.value ? [{ property: 'og:url', content: canonical.value }] : []),
    { name: 'theme-color', content: '#0b1311' }
  ]
}))

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
  void hydrateSeo()
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
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>
