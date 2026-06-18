<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { Project } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

const route = useRoute()
const api = useApi()
const project = ref<Project | null>(null)
const busy = ref(true)
const error = ref('')

onMounted(async () => {
  const slug = String(route.params.slug || '')
  try {
    project.value = await api.getProject(slug)
  } catch {
    error.value = 'Проект не найден.'
  } finally {
    busy.value = false
  }
})
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-8 text-terminal-green">
    <div class="mx-auto w-full max-w-3xl font-mono">
      <NuxtLink to="/projects" class="text-sm text-terminal-gray hover:text-terminal-green">
        ← все проекты
      </NuxtLink>

      <p v-if="busy" class="mt-6 text-terminal-gray">Загрузка...</p>
      <p v-else-if="error" class="mt-6 text-red-400">{{ error }}</p>

      <article v-else-if="project" class="mt-6">
        <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">{{ project.slug }}</p>
        <h1 class="mt-2 text-3xl">{{ project.title }}</h1>
        <p class="mt-4 text-terminal-green/85">{{ project.summary }}</p>
        <p v-if="project.tech_stack" class="mt-4 text-sm text-cyan-300">
          Стек: {{ project.tech_stack }}
        </p>
        <p v-if="project.description" class="mt-6 whitespace-pre-wrap text-sm leading-relaxed text-terminal-green/90">
          {{ project.description }}
        </p>
        <div class="mt-8 flex flex-wrap gap-4 text-sm">
          <a
            v-if="project.github_url"
            :href="project.github_url"
            target="_blank"
            rel="noopener noreferrer"
            class="text-terminal-gray hover:text-terminal-green"
          >
            GitHub →
          </a>
          <a
            v-if="project.demo_url"
            :href="project.demo_url"
            target="_blank"
            rel="noopener noreferrer"
            class="text-terminal-gray hover:text-terminal-green"
          >
            Demo →
          </a>
        </div>
      </article>
    </div>
  </main>
</template>
