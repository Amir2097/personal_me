<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    name:
      | 'cue'
      | 'ball'
      | 'users'
      | 'trophy'
      | 'tv'
      | 'info'
      | 'undo'
      | 'settings'
      | 'clock'
      | 'chip'
      | 'arrow'
      | 'play'
    size?: 'sm' | 'md' | 'lg'
  }>(),
  { size: 'md' }
)

const sizeClass = computed(() => {
  if (props.size === 'sm') return 'h-4 w-4'
  if (props.size === 'lg') return 'h-8 w-8'
  return 'h-5 w-5'
})
</script>

<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="inline-block shrink-0"
    :class="sizeClass"
    aria-hidden="true"
  >
    <template v-if="name === 'cue'">
      <path d="M3 21 14 10" />
      <path d="m14 10 2.5-2.5a2.1 2.1 0 0 1 3 3L17 13" />
      <circle cx="18.5" cy="5.5" r="1.5" />
    </template>
    <template v-else-if="name === 'ball'">
      <circle cx="12" cy="12" r="9" />
      <circle cx="9" cy="10" r="1.5" fill="currentColor" stroke="none" />
    </template>
    <template v-else-if="name === 'users'">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </template>
    <template v-else-if="name === 'trophy'">
      <path d="M8 21h8" />
      <path d="M12 17v4" />
      <path d="M7 4h10v5a5 5 0 0 1-10 0V4Z" />
      <path d="M17 4h2a2 2 0 0 1 0 4h-2" />
      <path d="M7 4H5a2 2 0 0 0 0 4h2" />
    </template>
    <template v-else-if="name === 'tv'">
      <rect x="2" y="7" width="20" height="13" rx="2" />
      <path d="m8 7 4-4 4 4" />
    </template>
    <template v-else-if="name === 'info'">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 16v-4" />
      <path d="M12 8h.01" />
    </template>
    <template v-else-if="name === 'undo'">
      <path d="M3 7v6h6" />
      <path d="M21 17a9 9 0 0 0-15-6.7L3 13" />
    </template>
    <template v-else-if="name === 'settings'">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </template>
    <template v-else-if="name === 'clock'">
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </template>
    <template v-else-if="name === 'chip'">
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="4" />
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2" />
    </template>
    <template v-else-if="name === 'arrow'">
      <path d="M5 12h14" />
      <path d="m13 6 6 6-6 6" />
    </template>
    <template v-else-if="name === 'play'">
      <circle cx="12" cy="12" r="9" />
      <path d="m10 8 6 4-6 4V8Z" fill="currentColor" stroke="none" />
    </template>
  </svg>
</template>
