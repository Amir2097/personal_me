<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    icon?: 'info' | 'cue' | 'chip' | 'users' | 'ball' | 'trophy' | 'clock'
  }>(),
  { icon: 'info' }
)
</script>

<template>
  <aside class="info-callout flex gap-3 rounded-xl border border-cloth-accent/25 bg-cloth-accent/5 px-4 py-3 text-sm text-cloth-chalk/85">
    <span class="mt-0.5 text-cloth-accent">
      <AppIcon :name="icon" size="sm" />
    </span>
    <div class="min-w-0">
      <p class="font-semibold text-cloth-accent">{{ title }}</p>
      <p class="mt-1 leading-relaxed text-cloth-muted">
        <slot />
      </p>
    </div>
  </aside>
</template>
