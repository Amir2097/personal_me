<script setup lang="ts">
import type { SiteLegalPublic } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

const props = defineProps<{
  doc: 'privacy' | 'terms'
}>()

const api = useApi()
const legal = ref<SiteLegalPublic | null>(null)
const busy = ref(true)

const title = computed(() =>
  props.doc === 'privacy' ? 'Политика конфиденциальности' : 'Пользовательское соглашение'
)
const body = computed(() => {
  if (!legal.value) return ''
  return props.doc === 'privacy' ? legal.value.privacy_policy : legal.value.terms_of_use
})

useSiteSeo({
  title: title.value,
  description: `${title.value} — personal_me`,
  path: `/legal/${props.doc}`
})

onMounted(async () => {
  try {
    legal.value = await api.getSiteLegal()
  } finally {
    busy.value = false
  }
})
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green md:py-8">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-5 md:gap-6">
      <HubIntro compact />
      <TerminalShell :cwd="`~/legal/${doc}`" :session="`terminal://personal_me/legal/${doc}`" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p v-if="busy" class="text-terminal-gray">Загрузка...</p>
          <template v-else-if="legal">
            <header class="border-b border-terminal-gray/50 pb-6">
              <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">legal</p>
              <h1 class="mt-2 text-2xl md:text-3xl">{{ title }}</h1>
              <p class="mt-2 text-xs text-terminal-gray">
                Обновлено: {{ new Date(legal.updated_at).toLocaleDateString('ru-RU') }}
              </p>
            </header>
            <article class="mt-6 whitespace-pre-wrap leading-relaxed text-terminal-green/90">
              {{ body }}
            </article>
            <nav class="mt-8 flex flex-wrap gap-4 border-t border-terminal-gray/40 pt-6 text-xs">
              <NuxtLink
                v-if="doc === 'terms'"
                to="/legal/privacy"
                class="terminal-interactive text-cyan-300 underline"
              >
                политика конфиденциальности
              </NuxtLink>
              <NuxtLink
                v-else
                to="/legal/terms"
                class="terminal-interactive text-cyan-300 underline"
              >
                пользовательское соглашение
              </NuxtLink>
              <NuxtLink to="/contact" class="terminal-interactive text-terminal-gray underline hover:text-terminal-green">
                контакты
              </NuxtLink>
            </nav>
          </template>
          <p v-else class="text-red-400">Не удалось загрузить документ.</p>
        </div>
      </TerminalShell>
    </div>
  </main>
</template>
