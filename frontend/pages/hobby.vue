<script setup lang="ts">
const config = useRuntimeConfig()

useSiteSeo({
  title: 'Hobby',
  description: 'Хобби и подсервисы DAUTOVTECH: бильярд «Колхоз» и другие.',
  path: '/hobby'
})

const billiardsUrl = computed(() => {
  const base = (config.public.siteUrl || '').replace(/\/$/, '')
  return `${base}/billiards/`
})
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green md:py-8">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-5 md:gap-6">
      <HubIntro compact />
      <TerminalShell cwd="~/hobby" session="terminal://dautovtech/hobby" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">hobby</p>
          <h1 class="mt-2 text-xl">Хобби и подсервисы</h1>
          <p class="mt-2 max-w-2xl text-terminal-gray">
            Отдельные приложения экосистемы {{ config.public.brandName || 'DAUTOVTECH' }}.
            Запускаются как подсервисы и доступны из терминала командой
            <code class="text-terminal-green">go billiards</code>.
          </p>

          <div class="mt-6 grid gap-4 md:grid-cols-2">
            <a
              :href="billiardsUrl"
              class="block rounded-lg border border-terminal-gray/70 bg-black/30 p-5 transition hover:border-terminal-green/50 hover:bg-terminal-green/5"
              target="_blank"
              rel="noopener noreferrer"
            >
              <p class="text-xs uppercase tracking-widest text-amber-300">billiards</p>
              <h2 class="mt-2 text-lg text-terminal-green">Kolkhoz Manager</h2>
              <p class="mt-2 text-xs leading-relaxed text-terminal-gray">
                Русский бильярд «Колхоз»: быстрый стол с цветными шарами и турнир по турам
                с категориями, тарифами, рассадкой и TV-табло. Offline-first.
              </p>
              <p class="mt-4 text-xs text-cyan-300">открыть /billiards/ →</p>
              <p class="mt-2 text-[11px] text-terminal-gray">
                Если видите 502 — контейнер <code class="text-terminal-green">billiards</code> ещё стартует
                (<code class="text-terminal-green">docker compose logs -f billiards</code>).
              </p>
            </a>

            <div class="rounded-lg border border-dashed border-terminal-gray/50 bg-black/20 p-5 text-terminal-gray">
              <p class="text-xs uppercase tracking-widest">soon</p>
              <h2 class="mt-2 text-lg">Другие хобби</h2>
              <p class="mt-2 text-xs">Сюда можно добавлять следующие подсервисы платформы.</p>
            </div>
          </div>

          <section class="mt-6 rounded-lg border border-terminal-gray/60 bg-black/20 p-4 text-xs text-terminal-gray">
            <p>Терминал:</p>
            <pre class="mt-2 text-terminal-green">services
go billiards</pre>
          </section>
        </div>
      </TerminalShell>
    </div>
  </main>
</template>
