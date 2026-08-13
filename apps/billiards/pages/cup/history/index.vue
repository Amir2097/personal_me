<script setup lang="ts">
import { cupFormatTitle } from '~/utils/cupLabels'

const history = useCupHistory()
const { username } = useHubAuth()

onMounted(() => {
  void history.refresh()
})
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-6xl px-4 py-8">
      <NuxtLink to="/cup" class="btn-ghost text-sm">← Турнир</NuxtLink>

      <section class="hero-surface mt-4 rounded-2xl px-5 py-5 sm:px-6">
        <h1 class="font-display text-3xl font-bold text-cloth-chalk">История турниров</h1>
        <p class="mt-2 text-sm text-cloth-chalk/75">
          Локальные снимки
          <span v-if="username"> и синхронизация с хабом ({{ username }})</span>.
        </p>
      </section>

      <p v-if="history.error.value" class="mt-3 text-sm text-amber-300">{{ history.error.value }}</p>

      <div v-if="!history.items.value.length" class="card-surface mt-6 p-5 text-sm text-cloth-muted">
        Пока нет сохранённых турниров. Завершите турнир и нажмите «Сохранить в историю».
      </div>

      <div class="mt-6 grid gap-3 md:grid-cols-2">
        <NuxtLink
          v-for="item in history.items.value"
          :key="String(item.id)"
          :to="`/cup/history/${item.id}`"
          class="card-surface block p-4 transition hover:border-cloth-accent/50"
        >
          <div class="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 class="font-display text-xl font-bold text-cloth-chalk">{{ item.title }}</h2>
              <p class="mt-1 text-sm text-cloth-muted">
                {{ cupFormatTitle(item.format) }} · игроков: {{ item.player_count }} ·
                {{ item.source === 'hub' ? 'хаб' : 'локально' }}
              </p>
              <p v-if="item.winner_name" class="mt-1 text-sm text-emerald-300">Победитель: {{ item.winner_name }}</p>
            </div>
            <p class="text-xs text-cloth-muted">{{ new Date(item.created_at).toLocaleString('ru-RU') }}</p>
          </div>
        </NuxtLink>
      </div>
    </main>
  </div>
</template>
