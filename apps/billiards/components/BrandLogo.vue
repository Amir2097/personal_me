<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    compact?: boolean
    /** mist = dark inks on pale UI; felt = light inks on the green hero. */
    surface?: 'auto' | 'mist' | 'felt'
  }>(),
  { compact: false, surface: 'auto' }
)

const uid = useId().replace(/[^a-zA-Z0-9_-]/g, '')

const titleFill = computed(() => {
  if (props.surface === 'felt') return '#f8fafc'
  if (props.surface === 'mist') return '#0b1311'
  return 'var(--brand-title)'
})

const subtitleFill = computed(() => {
  if (props.surface === 'felt') return '#6ee7b7'
  if (props.surface === 'mist') return '#047857'
  return 'var(--brand-subtitle)'
})

const tagFill = computed(() => {
  if (props.surface === 'felt') return '#facc15'
  if (props.surface === 'mist') return '#b45309'
  return 'var(--brand-tag)'
})
</script>

<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 320 80"
    overflow="visible"
    role="img"
    aria-label="Цифровое Сукно"
    class="brand-logo"
  >
    <defs>
      <radialGradient :id="`ballGlow-${uid}`" cx="35%" cy="35%" r="65%">
        <stop offset="0%" stop-color="#10b981" />
        <stop offset="60%" stop-color="#052e2b" />
        <stop offset="100%" stop-color="#0b1311" />
      </radialGradient>
      <pattern :id="`gridPattern-${uid}`" width="6" height="6" patternUnits="userSpaceOnUse">
        <path d="M 6 0 L 0 0 0 6" fill="none" stroke="rgba(16, 185, 129, 0.25)" stroke-width="0.8" />
      </pattern>
    </defs>

    <g transform="translate(10, 5)">
      <circle cx="35" cy="35" r="32" :fill="`url(#gridPattern-${uid})`" stroke="#10b981" stroke-width="1.5" opacity="0.8" />
      <circle cx="35" cy="35" r="26" :fill="`url(#ballGlow-${uid})`" stroke="#10b981" stroke-width="1.5" />
      <line x1="35" y1="5" x2="35" y2="65" stroke="#facc15" stroke-width="1.5" stroke-dasharray="3,3" opacity="0.85" />
      <line x1="5" y1="35" x2="65" y2="35" stroke="#10b981" stroke-width="1" stroke-dasharray="2,2" opacity="0.6" />
      <circle cx="35" cy="35" r="4.5" fill="#facc15" />
      <circle cx="35" cy="35" r="8" fill="none" stroke="#facc15" stroke-width="1" opacity="0.8" />
    </g>

    <text
      x="92"
      y="38"
      font-family="'Space Grotesk', 'Helvetica Neue', Arial, sans-serif"
      font-weight="800"
      font-size="19"
      :fill="titleFill"
      letter-spacing="1"
    >
      ЦИФРОВОЕ
    </text>
    <text
      x="92"
      y="58"
      font-family="'Space Grotesk', 'Helvetica Neue', Arial, sans-serif"
      font-weight="700"
      font-size="17"
      :fill="subtitleFill"
      letter-spacing="3"
    >
      СУКНО
    </text>
    <text
      v-if="!compact"
      x="92"
      y="70"
      font-family="'JetBrains Mono', ui-monospace, monospace"
      font-size="7.5"
      :fill="tagFill"
      letter-spacing="1.5"
    >
      DIGITAL FELT PLATFORM
    </text>
  </svg>
</template>
