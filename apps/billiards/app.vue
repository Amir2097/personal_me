<script setup lang="ts">
const store = useKolkhozStore()

onMounted(() => {
  store.hydrate()
})
</script>

<template>
  <div class="min-h-screen">
    <NuxtPage />
  </div>
</template>
