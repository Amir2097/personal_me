<script setup lang="ts">
import { avatarColor, playerInitials } from '~/utils/labels'

const props = withDefaults(
  defineProps<{
    name: string
    src?: string
    size?: 'sm' | 'md' | 'lg' | 'xl'
  }>(),
  { src: '', size: 'md' }
)

const initials = computed(() => playerInitials(props.name))
const color = computed(() => avatarColor(props.name))
const broken = ref(false)

watch(
  () => props.src,
  () => {
    broken.value = false
  }
)

const sizeClass = computed(() => {
  if (props.size === 'sm') return 'h-8 w-8 text-[10px]'
  if (props.size === 'lg') return 'h-12 w-12 text-base'
  if (props.size === 'xl') return 'h-24 w-24 text-2xl'
  return 'h-10 w-10 text-xs'
})
</script>

<template>
  <span
    class="player-avatar inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full font-display font-bold text-white shadow-inner ring-2 ring-white/20"
    :class="sizeClass"
    :style="src && !broken ? undefined : { background: color }"
    :title="name"
  >
    <img
      v-if="src && !broken"
      :src="src"
      :alt="name"
      class="h-full w-full object-cover"
      @error="broken = true"
    />
    <span v-else aria-hidden="true">{{ initials }}</span>
  </span>
</template>
