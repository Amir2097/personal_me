<script setup lang="ts">
import { useApi } from '~/composables/useApi'

const api = useApi()
const enabled = ref(false)
const name = ref('')
const email = ref('')
const message = ref('')
const company = ref('')
const busy = ref(false)
const error = ref('')
const success = ref('')

onMounted(async () => {
  try {
    const config = await api.getFeedbackConfig()
    enabled.value = config.enabled
  } catch {
    enabled.value = false
  }
})

const submit = async () => {
  if (!name.value.trim() || !email.value.trim() || !message.value.trim()) {
    error.value = 'Заполните имя, email и сообщение.'
    return
  }
  if (message.value.trim().length < 10) {
    error.value = 'Сообщение слишком короткое (минимум 10 символов).'
    return
  }
  busy.value = true
  error.value = ''
  success.value = ''
  try {
    const response = await api.submitFeedback({
      name: name.value.trim(),
      email: email.value.trim(),
      message: message.value.trim(),
      company: company.value
    })
    success.value = response.message
    name.value = ''
    email.value = ''
    message.value = ''
    company.value = ''
  } catch {
    error.value = 'Не удалось отправить сообщение. Попробуйте позже или используйте контакты выше.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="mt-10 border-t border-terminal-gray/50 pt-8">
    <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">feedback</p>
    <h2 class="mt-2 text-xl">Написать сообщение</h2>

    <p v-if="!enabled" class="mt-4 text-terminal-gray">
      Форма временно недоступна. Используйте контакты выше или email из раздела about.
    </p>

    <form v-else class="mt-5 space-y-3" @submit.prevent="submit">
      <div class="absolute -left-[9999px] opacity-0" aria-hidden="true">
        <input v-model="company" type="text" tabindex="-1" autocomplete="off" />
      </div>
      <div class="grid gap-3 md:grid-cols-2">
        <input
          v-model="name"
          type="text"
          autocomplete="name"
          placeholder="ваше имя"
          class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
        />
        <input
          v-model="email"
          type="email"
          autocomplete="email"
          placeholder="email"
          class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
        />
      </div>
      <textarea
        v-model="message"
        rows="5"
        placeholder="сообщение"
        class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
      />
      <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
      <p v-if="success" class="text-sm text-cyan-300">{{ success }}</p>
      <button
        type="submit"
        class="terminal-btn rounded border border-terminal-green/50 px-4 py-2 text-sm hover:bg-terminal-green/10"
        :disabled="busy"
      >
        Отправить
      </button>
    </form>
  </section>
</template>
