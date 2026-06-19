<script setup lang="ts">
const config = useRuntimeConfig()
const brand = computed(() => String(config.public.brandName || 'DAUTOVTECH').toUpperCase())
</script>

<template>
  <div class="brand-watermark" aria-hidden="true">
    <div class="brand-watermark__layer brand-watermark__layer--primary">
      {{ brand }}
    </div>
    <div class="brand-watermark__layer brand-watermark__layer--ghost">
      {{ brand }}
    </div>
  </div>
</template>
