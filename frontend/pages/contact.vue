<script setup lang="ts">
import type { Contact } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

const api = useApi()
const contacts = ref<Contact[]>([])
const busy = ref(true)
const config = useRuntimeConfig()

useSiteSeo({
  title: 'Contact',
  description: `Связаться с ${config.public.ownerName || 'разработчиком'}`,
  path: '/contact'
})

onMounted(async () => {
  try {
    contacts.value = await api.listContacts()
  } finally {
    busy.value = false
  }
})
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green md:py-8">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-5 md:gap-6">
      <HubIntro compact />
      <TerminalShell cwd="~/contact" session="terminal://personal_me/contact" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">contact</p>
          <h1 class="mt-2 text-2xl">Связаться</h1>
          <p class="mt-3 text-terminal-gray">
            В терминале: <span class="text-terminal-green">contact</span> или
            <span class="text-terminal-green">contact &lt;key&gt;</span>
          </p>

          <p v-if="busy" class="mt-8 text-terminal-gray">Загрузка...</p>
          <p v-else-if="!contacts.length" class="mt-8 text-terminal-gray">
            Контакты пока не опубликованы.
          </p>
          <ul v-else class="mt-8 space-y-4">
            <li
              v-for="item in contacts"
              :key="item.id"
              class="rounded-lg border border-terminal-gray/80 bg-black/30 p-4"
            >
              <div class="text-xs uppercase tracking-widest text-terminal-gray">{{ item.key }}</div>
              <div class="mt-1 text-lg">{{ item.label }}</div>
              <div class="mt-2 text-terminal-green/90">{{ item.value }}</div>
              <a
                v-if="item.href"
                :href="item.href"
                target="_blank"
                rel="noopener noreferrer"
                class="mt-3 inline-block text-cyan-300 hover:underline"
              >
                Открыть →
              </a>
            </li>
          </ul>

          <FeedbackForm />
        </div>
      </TerminalShell>
    </div>
  </main>
</template>
