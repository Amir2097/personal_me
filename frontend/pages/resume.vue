<script setup lang="ts">
import type { AboutResponse } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

const api = useApi()
const about = ref<AboutResponse | null>(null)
const busy = ref(true)

useSiteSeo({
  title: 'Resume',
  description: 'Резюме разработчика',
  path: '/resume'
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
      <TerminalShell cwd="~/resume" session="terminal://personal_me/resume" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p v-if="busy" class="text-terminal-gray">Загрузка...</p>
          <template v-else>
            <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">resume</p>
            <h1 class="mt-2 text-2xl">Резюме</h1>

            <template v-if="about?.resume_available && about.resume_url">
              <p class="mt-4 text-terminal-green/90">
                Файл резюме доступен. Откройте или скачайте PDF.
              </p>
              <div class="mt-6 flex flex-wrap gap-3">
                <a
                  :href="about.resume_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="terminal-btn terminal-interactive text-sm text-terminal-green"
                >
                  Открыть PDF ↗
                </a>
                <NuxtLink to="/about" class="terminal-btn terminal-interactive text-sm text-terminal-gray">
                  ← about
                </NuxtLink>
              </div>
            </template>

            <template v-else>
              <div class="mt-6 rounded-lg border border-dashed border-terminal-gray/60 bg-black/20 p-6">
                <p class="text-terminal-green/90">
                  Резюме скоро будет загружено на сервер и доступно по этому адресу.
                </p>
                <p class="mt-3 text-terminal-gray">
                  Пока загляните в
                  <NuxtLink to="/about" class="terminal-interactive text-cyan-300">about</NuxtLink>
                  или
                  <NuxtLink to="/contact" class="terminal-interactive text-cyan-300">contact</NuxtLink>.
                </p>
              </div>
            </template>
          </template>
        </div>
      </TerminalShell>
    </div>
  </main>
</template>
