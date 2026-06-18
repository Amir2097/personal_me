<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { Project } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

const api = useApi()
const projects = ref<Project[]>([])
const busy = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    projects.value = await api.listProjects()
  } catch {
    error.value = 'Не удалось загрузить проекты.'
  } finally {
    busy.value = false
  }
})
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-8 text-terminal-green">
    <div class="mx-auto w-full max-w-5xl font-mono">
      <div class="mb-6 flex items-center justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">portfolio</p>
          <h1 class="text-2xl">Проекты</h1>
        </div>
        <NuxtLink to="/" class="text-sm text-terminal-gray hover:text-terminal-green">
          ← терминал
        </NuxtLink>
      </div>

      <p v-if="error" class="mb-4 text-red-400">{{ error }}</p>
      <p v-else-if="busy" class="text-terminal-gray">Загрузка...</p>

      <div v-else class="grid gap-4 md:grid-cols-2">
        <article
          v-for="project in projects"
          :key="project.id"
          class="rounded-lg border border-terminal-gray/70 bg-black/30 p-5 transition hover:border-terminal-green/40"
        >
          <div class="mb-2 flex items-start justify-between gap-2">
            <h2 class="text-lg">
              <NuxtLink :to="`/projects/${project.slug}`" class="hover:underline">
                {{ project.title }}
              </NuxtLink>
            </h2>
            <span v-if="project.featured" class="text-amber-300">★</span>
          </div>
          <p class="mb-3 text-sm text-terminal-green/80">{{ project.summary }}</p>
          <p v-if="project.tech_stack" class="mb-3 text-xs text-terminal-gray">
            {{ project.tech_stack }}
          </p>
          <div class="flex flex-wrap gap-3 text-xs">
            <NuxtLink :to="`/projects/${project.slug}`" class="text-cyan-300 hover:underline">
              подробнее
            </NuxtLink>
            <a
              v-if="project.github_url"
              :href="project.github_url"
              target="_blank"
              rel="noopener noreferrer"
              class="text-terminal-gray hover:text-terminal-green"
            >
              github
            </a>
            <a
              v-if="project.demo_url"
              :href="project.demo_url"
              target="_blank"
              rel="noopener noreferrer"
              class="text-terminal-gray hover:text-terminal-green"
            >
              demo
            </a>
          </div>
        </article>
      </div>
    </div>
  </main>
</template>
