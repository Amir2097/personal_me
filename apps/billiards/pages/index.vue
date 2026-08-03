<script setup lang="ts">
const store = useKolkhozStore()
const config = useRuntimeConfig()
const importError = ref('')

const startCasual = () => {
  store.setMode('casual')
  navigateTo('/casual')
}

const startTournament = () => {
  store.setMode('tournament')
  navigateTo('/tournament')
}

const downloadSave = () => {
  const blob = new Blob([store.exportJson()], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `kolkhoz-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const onImportFile = async (event: Event) => {
  importError.value = ''
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  try {
    store.importJson(await file.text())
  } catch {
    importError.value = 'Не удалось импортировать файл.'
  }
}
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-6xl px-4 py-8 sm:py-12">
      <section class="max-w-3xl">
        <p class="flex items-center gap-2 text-sm text-cloth-muted">
          <AppIcon name="cue" class="text-cloth-accent" />
          Подсервис {{ config.public.brandName }}
        </p>
        <h2 class="mt-2 font-display text-3xl font-extrabold tracking-tight text-cloth-chalk sm:text-5xl">
          Колхоз на зелёном сукне
        </h2>
        <p class="mt-4 max-w-2xl text-base leading-relaxed text-cloth-chalk/75">
          Считаем фишки за столом: забил шар — забрал у <strong class="text-cloth-accent">предыдущего</strong> в круге.
          Быстрый стол или турнир с категориями. Всё хранится локально.
        </p>
      </section>

      <InfoCallout class="mt-6 max-w-3xl" title="Правило выплат" icon="chip">
        Не со всех игроков сразу. Порядок сидения = круг. Игрок A забирает фишки только у игрока перед ним.
        Размер выплаты зависит от тарифа/форы того, у кого забирают, и типа шара.
      </InfoCallout>

      <div class="mt-10 grid gap-5 md:grid-cols-2">
        <button
          type="button"
          class="card-surface group p-6 text-left transition hover:border-cloth-accent/50 hover:bg-cloth-accent/5"
          @click="startCasual"
        >
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-cloth-accent/15 text-cloth-accent">
            <AppIcon name="ball" size="lg" />
          </div>
          <p class="mt-4 text-xs uppercase tracking-[0.2em] text-cloth-accent">Режим Б</p>
          <h3 class="mt-2 font-display text-2xl font-bold">Быстрый стол</h3>
          <p class="mt-3 text-sm text-cloth-chalk/70">
            3–5 человек, цветные шары, фора. Идеально для одной партии без сетки туров.
          </p>
          <span class="mt-6 inline-flex items-center gap-1 text-sm font-semibold text-cloth-accent group-hover:underline">
            Начать <AppIcon name="arrow" size="sm" />
          </span>
        </button>

        <button
          type="button"
          class="card-surface group p-6 text-left transition hover:border-cloth-accent/50 hover:bg-cloth-accent/5"
          @click="startTournament"
        >
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-cloth-accent/15 text-cloth-accent">
            <AppIcon name="trophy" size="lg" />
          </div>
          <p class="mt-4 text-xs uppercase tracking-[0.2em] text-cloth-accent">Режим А</p>
          <h3 class="mt-2 font-display text-2xl font-bold">Турнир по турам</h3>
          <p class="mt-3 text-sm text-cloth-chalk/70">
            Категории 1–2–3, тарифы туров, несколько столов, таймер и выбывание.
          </p>
          <span class="mt-6 inline-flex items-center gap-1 text-sm font-semibold text-cloth-accent group-hover:underline">
            Настроить <AppIcon name="arrow" size="sm" />
          </span>
        </button>
      </div>

      <section class="card-surface mt-8 p-5">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="flex items-center gap-2 font-display text-lg font-bold">
              <AppIcon name="chip" class="text-cloth-accent" /> Сохранённая сессия
            </h3>
            <p class="mt-1 text-sm text-cloth-muted">
              Режим: {{ store.mode || '—' }} · игроков: {{ store.players.length }} · событий: {{ store.events.length }}
            </p>
            <p v-if="importError" class="mt-1 text-xs text-red-300">{{ importError }}</p>
          </div>
          <div class="flex flex-wrap gap-2">
            <NuxtLink v-if="store.mode === 'casual'" to="/casual/play" class="btn-primary text-sm">Продолжить</NuxtLink>
            <NuxtLink v-if="store.mode === 'tournament'" to="/tournament/play" class="btn-primary text-sm">Продолжить</NuxtLink>
            <NuxtLink to="/tv" class="btn-ghost inline-flex items-center gap-1 text-sm">
              <AppIcon name="tv" size="sm" /> TV
            </NuxtLink>
            <button type="button" class="btn-ghost text-sm" @click="downloadSave">Export</button>
            <label class="btn-ghost cursor-pointer text-sm">
              Import
              <input type="file" accept="application/json,.json" class="hidden" @change="onImportFile" />
            </label>
            <button type="button" class="btn-ghost text-sm" @click="store.resetAll()">Сбросить</button>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
