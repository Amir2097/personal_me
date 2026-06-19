<script setup lang="ts">
import type { Project } from '~/composables/useApi'

defineProps<{
  project: Project
}>()
</script>

<template>
  <div>
    <img
      v-if="project.image_url"
      :src="project.image_url"
      :alt="project.title"
      class="mb-4 aspect-video w-full rounded-md border border-terminal-gray/60 object-cover"
      loading="lazy"
    />
    <div class="mb-2 flex items-start justify-between gap-2">
      <h3 class="text-lg">
        <NuxtLink :to="`/projects/${project.slug}`" class="hover:underline">
          {{ project.title }}
        </NuxtLink>
      </h3>
      <span v-if="project.featured" class="text-amber-300">★</span>
    </div>
    <p class="mb-3 text-terminal-green/80">{{ project.summary }}</p>
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
  </div>
</template>
