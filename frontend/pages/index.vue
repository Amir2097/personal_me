<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green md:py-8">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-5 md:gap-6">
      <HubIntro />
      <Terminal />
    </div>
  </main>
</template>

<script setup lang="ts">
useSiteSeo({
  path: '/'
})
</script>
