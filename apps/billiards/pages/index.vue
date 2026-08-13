<script setup lang="ts">
const config = useRuntimeConfig()
const { username } = useHubAuth()
const clientReady = ref(false)

onMounted(() => {
  clientReady.value = true
})
</script>

<template>
  <div>
    <AppHeader />
    <main class="mx-auto max-w-6xl px-4 py-8 sm:py-12">
      <section class="hero-surface rounded-2xl px-5 py-6 sm:px-8 sm:py-8">
        <p class="flex items-center gap-2 text-sm text-cloth-muted">
          <AppIcon name="cue" class="text-cloth-accent" />
          Подсервис {{ config.public.brandName }}
        </p>
        <h2 class="mt-2 font-display text-3xl font-extrabold tracking-tight text-cloth-chalk sm:text-5xl">
          Бильярд
        </h2>
        <p class="mt-4 max-w-2xl text-base leading-relaxed text-cloth-chalk/75">
          Три направления в одном сервисе:
          <strong class="text-cloth-chalk">тренажёр</strong>,
          <strong class="text-cloth-chalk">колхоз</strong> и
          <strong class="text-cloth-chalk">турнир</strong> на олимпийской сетке или системе до двух поражений.
        </p>
        <ClientOnly>
          <p v-if="clientReady && username" class="mt-3 inline-flex items-center gap-2 text-sm text-cloth-accent">
            <AppIcon name="user" size="sm" />
            Вы вошли как <strong class="text-cloth-chalk">{{ username }}</strong>
          </p>
        </ClientOnly>
      </section>

      <div class="mt-10 grid gap-5 lg:grid-cols-3">
        <NuxtLink
          to="/academy"
          class="card-surface group block p-6 transition hover:border-cloth-accent/50 hover:bg-cloth-accent/5"
        >
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-300">
            <AppIcon name="ball" size="lg" />
          </div>
          <p class="mt-4 text-xs uppercase tracking-[0.2em] text-cloth-accent">Академия</p>
          <h3 class="mt-2 font-display text-2xl font-bold">Тренажёр</h3>
          <p class="mt-3 text-sm text-cloth-chalk/70">
            Каталог упражнений по русской пирамиде: схемы стола, траектории, точка удара на битке,
            фиксация результатов и прогресс по попыткам.
          </p>
          <ul class="mt-4 space-y-1 text-xs text-cloth-muted">
            <li>· уровни от новичка до профи</li>
            <li>· чужие, свояки, контроль, дуплеты</li>
            <li>· интерактивная проверка на некоторых упражнениях</li>
          </ul>
          <span class="mt-6 inline-flex items-center gap-1 text-sm font-semibold text-cloth-accent group-hover:underline">
            Открыть академию <AppIcon name="arrow" size="sm" />
          </span>
        </NuxtLink>

        <NuxtLink
          to="/kolkhoz"
          class="card-surface group block p-6 transition hover:border-cloth-accent/50 hover:bg-cloth-accent/5"
        >
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-cloth-accent/15 text-cloth-accent">
            <AppIcon name="chip" size="lg" />
          </div>
          <p class="mt-4 text-xs uppercase tracking-[0.2em] text-cloth-accent">Колхоз</p>
          <h3 class="mt-2 font-display text-2xl font-bold">Игра с друзьями</h3>
          <p class="mt-3 text-sm text-cloth-chalk/70">
            Быстрый стол на 2–5 человек или турнир по турам. Скоринг, штрафы, банк, синхронизация
            комнаты и табло для зала.
          </p>
          <ul class="mt-4 space-y-1 text-xs text-cloth-muted">
            <li>· быстрый стол: партии, форы, расчёт</li>
            <li>· турнир: подробная или организаторская</li>
            <li>· сохранение сессии и история партий</li>
          </ul>
          <span class="mt-6 inline-flex items-center gap-1 text-sm font-semibold text-cloth-accent group-hover:underline">
            Выбрать режим колхоза <AppIcon name="arrow" size="sm" />
          </span>
        </NuxtLink>

        <NuxtLink
          to="/cup"
          class="card-surface group block p-6 transition hover:border-cloth-accent/50 hover:bg-cloth-accent/5"
        >
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500/15 text-amber-300">
            <AppIcon name="trophy" size="lg" />
          </div>
          <p class="mt-4 text-xs uppercase tracking-[0.2em] text-cloth-accent">Турнир</p>
          <h3 class="mt-2 font-display text-2xl font-bold">Олимпийская сетка</h3>
          <p class="mt-3 text-sm text-cloth-chalk/70">
            Классический плей-офф: олимпийская система или до двух поражений, счёт партий и шаров,
            пульт матча и табло для зала.
          </p>
          <ul class="mt-4 space-y-1 text-xs text-cloth-muted">
            <li>· сетка до 64 игроков, свободные места — пропуск тура</li>
            <li>· партии и шары, таймер удара по желанию</li>
            <li>· история именованных турниров</li>
          </ul>
          <span class="mt-6 inline-flex items-center gap-1 text-sm font-semibold text-cloth-accent group-hover:underline">
            Открыть турнир <AppIcon name="arrow" size="sm" />
          </span>
        </NuxtLink>
      </div>

      <section class="card-surface mt-8 p-5">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="flex items-center gap-2 font-display text-lg font-bold">
              <AppIcon name="tv" class="text-cloth-accent" /> Табло зала
            </h3>
            <p class="mt-1 text-sm text-cloth-muted">
              Полноэкранный режим для телевизора: таймер тура, игроки, банк и события стола.
            </p>
          </div>
          <NuxtLink to="/tv" class="btn-ghost inline-flex items-center gap-2 text-sm">
            <AppIcon name="tv" size="sm" /> Открыть табло
          </NuxtLink>
        </div>
      </section>
    </main>
  </div>
</template>
