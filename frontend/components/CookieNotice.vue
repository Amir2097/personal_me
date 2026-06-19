<script setup lang="ts">
const STORAGE_KEY = 'legal_cookie_notice_ack_v1'

const visible = ref(false)

onMounted(() => {
  if (import.meta.server) return
  visible.value = localStorage.getItem(STORAGE_KEY) !== '1'
})

const dismiss = () => {
  localStorage.setItem(STORAGE_KEY, '1')
  visible.value = false
}
</script>

<template>
  <div
    v-if="visible"
    class="fixed bottom-0 left-0 right-0 z-[60] border-t border-terminal-gray/60 bg-terminal-black/95 px-4 py-3 font-mono text-xs text-terminal-green backdrop-blur-sm"
    role="dialog"
    aria-label="Уведомление о cookies"
  >
    <div class="mx-auto flex max-w-6xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <p class="text-terminal-green/90 leading-relaxed">
        Мы используем обязательные cookies для авторизации и localStorage для настроек терминала.
        Подробнее —
        <NuxtLink to="/legal/privacy" class="terminal-interactive text-cyan-300 underline">
          политика конфиденциальности
        </NuxtLink>.
      </p>
      <button
        type="button"
        class="terminal-btn shrink-0 rounded border border-terminal-green/50 px-3 py-1.5 hover:bg-terminal-green/10"
        @click="dismiss"
      >
        Понятно
      </button>
    </div>
  </div>
</template>
