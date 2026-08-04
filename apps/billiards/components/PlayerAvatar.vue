<script setup lang="ts">
import { avatarColor, playerInitials } from '~/utils/labels'

const props = withDefaults(
  defineProps<{
    name: string
    size?: 'sm' | 'md' | 'lg'
  }>(),
  { size: 'md' }
)

const initials = computed(() => playerInitials(props.name))
const color = computed(() => avatarColor(props.name))

const sizeClass = computed(() => {
  if (props.size === 'sm') return 'h-8 w-8 text-[10px]'
  if (props.size === 'lg') return 'h-12 w-12 text-base'
  return 'h-10 w-10 text-xs'
})
</script>

<template>
  <span
    class="player-avatar inline-flex shrink-0 items-center justify-center rounded-full font-display font-bold text-white shadow-inner ring-2 ring-white/20"
    :class="sizeClass"
    :style="{ background: color }"
    :title="name"
    aria-hidden="true"
  >
    {{ initials }}
  </span>
</template>
