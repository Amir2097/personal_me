<script setup lang="ts">
const config = useRuntimeConfig()
const { seo } = useSiteSeoConfig()

const siteName = computed(() => seo.value?.site_name || config.public.siteName)
const tagline = computed(() => seo.value?.tagline || config.public.tagline)
const ownerName = computed(() => seo.value?.owner_name || config.public.ownerName)
const titleSuffix = computed(() => seo.value?.seo_title_suffix || 'Terminal IDE')

withDefaults(
  defineProps<{
    compact?: boolean
  }>(),
  {
    compact: false
  }
)
</script>

<template>
  <header class="font-mono">
    <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">хаб разработчика</p>
    <h1 class="mt-1 text-xl text-terminal-green md:text-2xl">
      {{ siteName }} // {{ titleSuffix }}
    </h1>
    <p v-if="!compact" class="mt-2 max-w-3xl text-sm leading-relaxed text-terminal-green/75">
      {{ tagline }}
    </p>
    <p v-else class="mt-1 text-sm text-terminal-gray">
      {{ ownerName }} · developer hub
    </p>

    <nav
      v-if="!compact"
      class="mt-4 flex flex-wrap gap-x-5 gap-y-2 border-t border-terminal-gray/40 pt-4 text-xs"
      aria-label="Быстрая навигация"
    >
      <span>
        <span class="text-cyan-300">работодателям</span>
        <span class="text-terminal-gray"> → </span>
        <NuxtLink to="/projects" class="text-terminal-green hover:underline">projects</NuxtLink>
        <span class="text-terminal-gray"> · </span>
        <NuxtLink to="/about" class="text-terminal-green hover:underline">about</NuxtLink>
        <span class="text-terminal-gray"> · </span>
        <span class="text-terminal-gray">команда </span>
        <code class="text-terminal-green/90">projects</code>
      </span>
      <span>
        <span class="text-cyan-300">пользователям</span>
        <span class="text-terminal-gray"> → </span>
        <span class="text-terminal-gray">команда </span>
        <code class="text-terminal-green/90">services</code>
        <span class="text-terminal-gray"> · </span>
        <code class="text-terminal-green/90">go &lt;service&gt;</code>
      </span>
      <span>
        <span class="text-cyan-300">гостям</span>
        <span class="text-terminal-gray"> → </span>
        <span class="text-terminal-gray">команда </span>
        <code class="text-terminal-green/90">help</code>
        <span class="text-terminal-gray"> · </span>
        <NuxtLink to="/" class="text-terminal-green hover:underline">терминал</NuxtLink>
      </span>
    </nav>
  </header>
</template>
