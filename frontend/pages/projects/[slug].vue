<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Project } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

const route = useRoute()
const api = useApi()
const project = ref<Project | null>(null)
const busy = ref(true)
const error = ref('')

const slug = computed(() => String(route.params.slug || ''))
const cwd = computed(() => `~/projects/${slug.value}`)

onMounted(async () => {
  try {
    project.value = await api.getProject(slug.value)
    useSiteSeo({
      title: project.value?.title || slug.value,
      description: project.value?.summary || 'Project details',
      path: `/projects/${slug.value}`
    })
  } catch {
    error.value = 'Проект не найден.'
  } finally {
    busy.value = false
  }
})
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green md:py-8">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-5 md:gap-6">
      <HubIntro compact />
      <TerminalShell :cwd="cwd" :session="`terminal://personal_me/projects/${slug}`" tall>
      <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
        <NuxtLink to="/projects" class="text-terminal-gray hover:text-terminal-green">
          ← ls ../projects
        </NuxtLink>

        <p v-if="busy" class="mt-6 text-terminal-gray">Загрузка...</p>
        <p v-else-if="error" class="mt-6 text-red-400">{{ error }}</p>

        <article v-else-if="project" class="mt-6">
          <img
            v-if="project.image_url"
            :src="project.image_url"
            :alt="project.title"
            class="mb-6 aspect-video w-full max-w-3xl rounded-lg border border-terminal-gray/60 object-cover"
          />
          <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">{{ project.slug }}</p>
          <h1 class="mt-2 text-3xl">{{ project.title }}</h1>
          <p class="mt-4 text-terminal-green/85">{{ project.summary }}</p>
          <p v-if="project.tech_stack" class="mt-4 text-cyan-300">
            Стек: {{ project.tech_stack }}
          </p>
          <p v-if="project.description" class="mt-6 whitespace-pre-wrap leading-relaxed text-terminal-green/90">
            {{ project.description }}
          </p>
          <div v-if="project.gallery?.length" class="mt-8">
            <h2 class="mb-3 text-xs uppercase tracking-widest text-terminal-gray">Галерея</h2>
            <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <a
                v-for="(url, index) in project.gallery"
                :key="`${url}-${index}`"
                :href="url"
                target="_blank"
                rel="noopener noreferrer"
                class="block overflow-hidden rounded-md border border-terminal-gray/60 hover:border-terminal-green/50"
              >
                <img
                  :src="url"
                  :alt="`${project.title} — ${index + 1}`"
                  class="aspect-video w-full object-cover"
                  loading="lazy"
                />
              </a>
            </div>
          </div>
          <div class="mt-8 flex flex-wrap gap-4">
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

      <template #status-actions>
        <NuxtLink to="/projects" class="text-terminal-gray hover:text-terminal-green">cd ../projects</NuxtLink>
      </template>
    </TerminalShell>
    </div>
  </main>
</template>
