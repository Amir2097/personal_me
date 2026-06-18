<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const code = ref('')
const state = ref('')

onMounted(() => {
  code.value = String(route.query.code || '')
  state.value = String(route.query.state || '')
})
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-terminal-black px-4 text-terminal-green">
    <div class="w-full max-w-lg rounded-xl border border-terminal-gray/80 bg-black/40 p-6 font-mono text-sm">
      <h1 class="mb-4 text-lg">OAuth callback</h1>
      <p class="text-terminal-gray">authorization code получен (dev):</p>
      <pre class="mt-3 overflow-x-auto rounded bg-black/50 p-3 text-xs text-cyan-300">{{ code }}</pre>
      <p v-if="state" class="mt-3 text-terminal-gray">state: {{ state }}</p>
      <NuxtLink to="/" class="mt-6 inline-block text-terminal-gray hover:text-terminal-green">← терминал</NuxtLink>
    </div>
  </main>
</template>
