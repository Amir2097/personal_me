<template>
  <main class="min-h-screen bg-terminal-black px-4 py-8 text-terminal-green">
    <div class="mx-auto w-full max-w-6xl">
      <p class="mb-2 text-xs uppercase tracking-[0.25em] text-terminal-gray">Хаб разработчика</p>
      <h1 class="mb-3 font-mono text-xl text-terminal-green">personal_me // Terminal IDE</h1>
      <p class="text-sm text-terminal-green/75">
        Интерактивный командный центр. Введите <span class="text-terminal-green">help</span> или откройте
        <NuxtLink to="/projects" class="text-cyan-300 underline hover:text-cyan-200">портфолио</NuxtLink>.
      </p>
    </div>
    <Terminal />
  </main>
</template>
