<script setup lang="ts">
import type { AboutResponse } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

const api = useApi()
const about = ref<AboutResponse | null>(null)
const busy = ref(true)

useSiteSeo({
  title: 'About',
  description: 'О разработчике и developer hub personal_me',
  path: '/about'
})

const experienceLines = computed(() => {
  if (!about.value?.experience) return []
  return about.value.experience
    .replace(/\\n/g, '\n')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
})

onMounted(async () => {
  try {
    about.value = await api.getAbout()
  } finally {
    busy.value = false
  }
})
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green md:py-8">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-5 md:gap-6">
      <HubIntro compact />
      <TerminalShell cwd="~/about" session="terminal://personal_me/about" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p v-if="busy" class="text-terminal-gray">Загрузка...</p>
          <template v-else-if="about">
            <header class="border-b border-terminal-gray/50 pb-6">
              <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">about</p>
              <h1 class="mt-2 text-2xl md:text-3xl">{{ about.owner_name }}</h1>
              <p class="mt-3 max-w-2xl text-terminal-green/85">{{ about.tagline }}</p>
            </header>

            <section class="mt-6 rounded-lg border border-terminal-gray/70 bg-black/25 p-5">
              <h2 class="text-xs uppercase tracking-[0.2em] text-terminal-gray">Обо мне</h2>
              <p class="mt-3 whitespace-pre-wrap leading-relaxed text-terminal-green/90">{{ about.bio }}</p>
            </section>

            <section
              v-if="experienceLines.length"
              class="mt-5 rounded-lg border border-terminal-gray/70 bg-black/25 p-5"
            >
              <h2 class="text-xs uppercase tracking-[0.2em] text-terminal-gray">Опыт</h2>
              <ul class="mt-3 space-y-2 text-terminal-green/90">
                <li v-for="(line, index) in experienceLines" :key="index" class="flex gap-2">
                  <span class="text-terminal-gray">›</span>
                  <span>{{ line }}</span>
                </li>
              </ul>
            </section>

            <section v-if="about.skills.length" class="mt-5 rounded-lg border border-terminal-gray/70 bg-black/25 p-5">
              <h2 class="text-xs uppercase tracking-[0.2em] text-terminal-gray">Технологии</h2>
              <div class="mt-3 flex flex-wrap gap-2">
                <span
                  v-for="skill in about.skills"
                  :key="skill"
                  class="rounded border border-terminal-gray/60 bg-terminal-black/80 px-3 py-1 text-xs text-cyan-300"
                >
                  {{ skill }}
                </span>
              </div>
            </section>

            <section class="mt-5 rounded-lg border border-terminal-gray/70 bg-black/25 p-5">
              <h2 class="text-xs uppercase tracking-[0.2em] text-terminal-gray">Резюме</h2>
              <p class="mt-3 text-terminal-gray">
                PDF-резюме будет храниться на сервере. Пока можно открыть страницу резюме или внешнюю ссылку.
              </p>
              <div class="mt-4 flex flex-wrap gap-3">
                <NuxtLink :to="about.resume_path" class="terminal-btn terminal-interactive text-sm text-terminal-green">
                  Открыть ~/resume
                </NuxtLink>
                <a
                  v-if="about.resume_available && about.resume_url"
                  :href="about.resume_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="terminal-btn terminal-interactive text-sm text-terminal-gray hover:text-terminal-green"
                >
                  Скачать PDF ↗
                </a>
              </div>
            </section>

            <section
              v-if="about.contacts?.length"
              class="mt-5 rounded-lg border border-terminal-gray/70 bg-black/25 p-5"
            >
              <h2 class="text-xs uppercase tracking-[0.2em] text-terminal-gray">Связаться</h2>
              <div class="mt-3 flex flex-wrap gap-3">
                <a
                  v-for="item in about.contacts"
                  :key="item.id"
                  :href="item.href || undefined"
                  :target="item.href ? '_blank' : undefined"
                  :rel="item.href ? 'noopener noreferrer' : undefined"
                  class="terminal-interactive text-sm"
                  :class="item.href ? 'text-terminal-gray' : 'pointer-events-none opacity-60 text-terminal-gray'"
                >
                  {{ item.label }} →
                </a>
              </div>
            </section>

            <nav class="mt-6 flex flex-wrap gap-4 border-t border-terminal-gray/40 pt-5">
              <NuxtLink to="/contact" class="terminal-interactive text-sm text-cyan-300">contact →</NuxtLink>
              <NuxtLink to="/projects" class="terminal-interactive text-sm text-cyan-300">projects →</NuxtLink>
            </nav>
          </template>
        </div>
      </TerminalShell>
    </div>
  </main>
</template>
