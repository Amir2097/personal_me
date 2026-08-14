<script setup lang="ts">
withDefaults(
  defineProps<{
    size?: 'sm' | 'md' | 'lg'
  }>(),
  { size: 'md' }
)

const uid = useId().replace(/[^a-zA-Z0-9_-]/g, '')
</script>

<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 100 100"
    role="img"
    aria-label="Цифровое Сукно"
    :class="size === 'sm' ? 'h-8 w-8' : size === 'lg' ? 'h-16 w-16' : 'h-10 w-10'"
  >
    <defs>
      <radialGradient :id="`favGlow-${uid}`" cx="35%" cy="35%" r="65%">
        <stop offset="0%" stop-color="#10b981" />
        <stop offset="70%" stop-color="#052e2b" />
        <stop offset="100%" stop-color="#0b1311" />
      </radialGradient>
      <pattern :id="`favGrid-${uid}`" width="10" height="10" patternUnits="userSpaceOnUse">
        <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(16, 185, 129, 0.3)" stroke-width="1" />
      </pattern>
    </defs>
    <rect width="100" height="100" rx="22" fill="#0b1311" stroke="rgba(255,255,255,0.1)" stroke-width="2" />
    <rect x="8" y="8" width="84" height="84" rx="16" :fill="`url(#favGrid-${uid})`" />
    <circle cx="50" cy="50" r="34" :fill="`url(#favGlow-${uid})`" stroke="#10b981" stroke-width="2.5" />
    <line x1="50" y1="12" x2="50" y2="88" stroke="#facc15" stroke-width="2" stroke-dasharray="4,3" />
    <circle cx="50" cy="50" r="6" fill="#facc15" />
    <circle cx="50" cy="50" r="12" fill="none" stroke="#facc15" stroke-width="1.5" />
  </svg>
</template>
