<script setup lang="ts">
const config = useRuntimeConfig()
const store = useKolkhozStore()

const hubHref = computed(() => config.public.hubUrl || '/')
</script>

<template>
  <header class="border-b border-white/10 bg-black/20 backdrop-blur-sm">
    <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-4">
      <div class="flex items-center gap-3">
        <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-cloth-accent/15 text-cloth-accent">
          <AppIcon name="cue" size="lg" />
        </span>
        <div>
          <p class="text-xs uppercase tracking-[0.28em] text-cloth-muted">{{ config.public.brandName }} · hobby</p>
          <h1 class="font-display text-xl font-bold text-cloth-chalk sm:text-2xl">
            Billiards Kolkhoz
          </h1>
        </div>
      </div>
      <nav class="flex flex-wrap items-center gap-2 text-sm">
        <NuxtLink to="/" class="btn-ghost inline-flex items-center gap-1 py-1.5 text-xs">
          <AppIcon name="play" size="sm" /> Режимы
        </NuxtLink>
        <NuxtLink to="/tv" class="btn-ghost inline-flex items-center gap-1 py-1.5 text-xs">
          <AppIcon name="tv" size="sm" /> TV
        </NuxtLink>
        <a :href="hubHref" class="btn-ghost py-1.5 text-xs">← Хаб</a>
        <button
          type="button"
          class="btn-ghost inline-flex items-center gap-1 py-1.5 text-xs"
          :disabled="!store.events.length"
          @click="store.undoLast()"
        >
          <AppIcon name="undo" size="sm" /> Undo
        </button>
      </nav>
    </div>
  </header>
</template>
