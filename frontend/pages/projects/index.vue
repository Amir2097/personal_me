<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Project } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

const api = useApi()
const projects = ref<Project[]>([])
const busy = ref(true)
const error = ref('')

const featured = computed(() => projects.value.filter((item) => item.featured))
const regular = computed(() => projects.value.filter((item) => !item.featured))

useSiteSeo({
  title: 'Projects',
  description: 'Портфолио проектов personal_me',
  path: '/projects'
})

onMounted(async () => {
  try {
    projects.value = await api.listProjects(false)
  } catch {
    error.value = 'Не удалось загрузить проекты.'
  } finally {
    busy.value = false
  }
})
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green md:py-8">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-5 md:gap-6">
      <HubIntro compact />
      <TerminalShell cwd="~/projects" session="terminal://personal_me/projects" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p class="mb-4 text-xs uppercase tracking-[0.25em] text-terminal-gray">portfolio</p>
          <h1 class="mb-6 text-2xl">Проекты</h1>

          <p v-if="error" class="mb-4 text-red-400">{{ error }}</p>
          <p v-else-if="busy" class="text-terminal-gray">Загрузка...</p>

          <template v-else>
            <section v-if="featured.length" class="mb-8">
              <h2 class="mb-4 text-amber-300">★ Featured</h2>
              <div class="grid gap-4 md:grid-cols-2">
                <article
                  v-for="project in featured"
                  :key="`f-${project.id}`"
                  class="rounded-lg border border-amber-500/30 bg-black/30 p-5"
                >
                  <ProjectCard :project="project" />
                </article>
              </div>
            </section>

            <section>
              <h2 v-if="featured.length" class="mb-4 text-terminal-gray">Все проекты</h2>
              <div class="grid gap-4 md:grid-cols-2">
                <article
                  v-for="project in regular"
                  :key="project.id"
                  class="rounded-lg border border-terminal-gray/70 bg-black/30 p-5 transition hover:border-terminal-green/40"
                >
                  <ProjectCard :project="project" />
                </article>
              </div>
            </section>
          </template>
        </div>
      </TerminalShell>
    </div>
  </main>
</template>
