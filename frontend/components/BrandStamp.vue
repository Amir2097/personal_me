<script setup lang="ts">
const config = useRuntimeConfig()

withDefaults(
  defineProps<{
    variant?: 'pill' | 'micro'
  }>(),
  {
    variant: 'pill'
  }
)

const brand = computed(() => String(config.public.brandName || 'DAUTOVTECH').toUpperCase())
</script>

<template>
  <NuxtLink
    to="/"
    class="brand-stamp terminal-interactive"
    :class="variant === 'micro' ? 'brand-stamp--micro' : 'brand-stamp--pill'"
    :aria-label="brand"
  >
    <span class="brand-stamp__mark" aria-hidden="true">◆</span>
    <span class="brand-stamp__text">{{ brand }}</span>
  </NuxtLink>
</template>
