<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    username?: string
    displayName?: string
    avatarUrl?: string
    size?: 'xs' | 'sm' | 'md' | 'lg'
  }>(),
  {
    username: '',
    displayName: '',
    avatarUrl: '',
    size: 'md'
  }
)

const sizeClass = computed(() => {
  if (props.size === 'xs') return 'h-6 w-6 text-[10px]'
  if (props.size === 'sm') return 'h-8 w-8 text-xs'
  if (props.size === 'lg') return 'h-20 w-20 text-2xl'
  return 'h-10 w-10 text-sm'
})

const label = computed(() => props.displayName || props.username || '?')

const initials = computed(() => {
  const source = (props.displayName || props.username || '?').trim()
  const parts = source.split(/\s+/).filter(Boolean)
  if (parts.length >= 2) {
    return `${parts[0]![0] || ''}${parts[1]![0] || ''}`.toUpperCase()
  }
  return source.slice(0, 2).toUpperCase()
})

const broken = ref(false)
</script>

<template>
  <div
    class="relative shrink-0 overflow-hidden rounded-md border border-terminal-gray/60 bg-black/40"
    :class="sizeClass"
    :title="label"
  >
    <img
      v-if="avatarUrl && !broken"
      :src="avatarUrl"
      :alt="label"
      class="h-full w-full object-cover"
      @error="broken = true"
    />
    <div
      v-else
      class="flex h-full w-full items-center justify-center bg-gradient-to-br from-terminal-green/20 to-cyan-500/10 font-semibold text-terminal-green"
    >
      {{ initials }}
    </div>
  </div>
</template>
