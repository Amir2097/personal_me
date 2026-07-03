<script setup lang="ts">
const model = defineModel<string>({ default: '' })

withDefaults(
  defineProps<{
    placeholder?: string
    autocomplete?: string
  }>(),
  {
    placeholder: '',
    autocomplete: 'off'
  }
)

const visible = ref(false)
</script>

<template>
  <div class="relative">
    <input
      v-model="model"
      :type="visible ? 'text' : 'password'"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      class="w-full rounded border border-terminal-gray/60 bg-transparent py-2 pl-3 pr-10 outline-none focus:border-terminal-green/50"
    />
    <button
      type="button"
      class="terminal-btn absolute right-2 top-1/2 -translate-y-1/2 px-1 text-[11px] text-terminal-gray hover:text-terminal-green"
      :aria-label="visible ? 'Скрыть пароль' : 'Показать пароль'"
      @click="visible = !visible"
    >
      {{ visible ? 'hide' : 'show' }}
    </button>
  </div>
</template>
