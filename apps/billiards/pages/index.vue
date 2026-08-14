<script setup lang="ts">
const { username, isHubLinked } = useHubAuth()
const { appPath } = useAppBase()
const { brandName, tagline, motd } = useSuknoSeo()
const clientReady = ref(false)

onMounted(() => {
  clientReady.value = true
})
</script>

<template>
  <div>
    <main class="page-shell py-8 sm:py-12">
      <section class="hero-surface px-6 py-10 sm:px-10 sm:py-14">
        <div class="flex flex-col items-start gap-8 lg:flex-row lg:items-center lg:justify-between lg:gap-12">
          <div class="min-w-0 flex-1">
            <h1 class="sr-only">{{ brandName }}</h1>
            <BrandLogo surface="felt" class="brand-logo brand-logo--hero" />
            <p v-if="tagline" class="mt-4 max-w-2xl text-sm uppercase tracking-[0.18em] text-cloth-accent">
              {{ tagline }}
            </p>
            <p v-if="motd" class="mt-3 max-w-2xl text-sm text-cloth-accent">{{ motd }}</p>
            <p class="mt-5 max-w-2xl text-base leading-relaxed text-cloth-chalk/75">
              Там, где зелёное сукно встречается с точным расчётом, рождается мастерство нового уровня.
            </p>
            <ClientOnly>
              <p v-if="clientReady && isHubLinked && username" class="mt-3 inline-flex items-center gap-2 text-sm text-cloth-accent">
                <AppIcon name="user" size="sm" />
                Вы вошли как <strong class="text-cloth-chalk">{{ username }}</strong>
              </p>
            </ClientOnly>
          </div>
          <img
            :src="appPath('brand/icon.png')"
            :alt="brandName"
            width="224"
            height="224"
            class="mx-auto h-40 w-40 shrink-0 rounded-[1.75rem] object-cover shadow-[0_24px_50px_rgba(0,0,0,0.28)] ring-1 ring-white/20 sm:h-48 sm:w-48 lg:mx-0 lg:h-56 lg:w-56"
          />
        </div>
      </section>

      <div class="mt-10 grid gap-5 lg:grid-cols-3">
        <NuxtLink
          to="/academy"
          class="card-surface group block p-6 transition hover:border-cloth-accent/50 hover:bg-cloth-accent/5"
        >
          <div class="ball-icon ball-icon--felt">
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
          <div class="ball-icon ball-icon--indigo">
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
          <div class="ball-icon ball-icon--amber">
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
    </main>
  </div>
</template>
