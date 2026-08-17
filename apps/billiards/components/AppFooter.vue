<script setup lang="ts">
const config = useRuntimeConfig()
const { brandName, tagline } = useSuknoSeo()
const suknoAuth = useSuknoAuth()
const year = new Date().getFullYear()
const name = computed(() => brandName.value || String(config.public.brandName || 'Цифровое Сукно'))
const footerConfigReady = ref(false)

onMounted(async () => {
  if (!suknoAuth.config.value) {
    try {
      await suknoAuth.loadConfig()
    } catch {
      /* offline */
    }
  }
  footerConfigReady.value = true
})
</script>

<template>
  <footer class="app-footer">
    <div class="page-shell py-10">
      <div class="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <NuxtLink to="/" class="inline-block no-underline">
            <BrandLogo compact class="brand-logo opacity-90" />
          </NuxtLink>
          <p class="mt-3 max-w-xs text-sm leading-relaxed text-cloth-muted">
            {{ tagline || 'Тренажёр, колхоз и турнирная сетка для русского бильярда.' }}
          </p>
        </div>
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-cloth-muted">Проект</p>
          <ul class="mt-3 space-y-2 text-sm">
            <li><NuxtLink to="/" class="footer-link">Главная</NuxtLink></li>
            <li><NuxtLink to="/kolkhoz" class="footer-link">Колхоз</NuxtLink></li>
            <li><NuxtLink to="/cup" class="footer-link">Турнир</NuxtLink></li>
            <li><NuxtLink to="/academy" class="footer-link">Академия</NuxtLink></li>
          </ul>
        </div>
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-cloth-muted">Аккаунт</p>
          <ul class="mt-3 space-y-2 text-sm">
            <template v-if="suknoAuth.isAccountUser.value">
              <li><NuxtLink to="/profile" class="footer-link">Профиль</NuxtLink></li>
              <li v-if="suknoAuth.isAdmin.value"><NuxtLink to="/admin" class="footer-link">Админка</NuxtLink></li>
            </template>
            <template v-else>
              <li><NuxtLink to="/auth/login" class="footer-link">Войти</NuxtLink></li>
              <li v-if="footerConfigReady && suknoAuth.registrationAllowed.value">
                <NuxtLink to="/auth/register" class="footer-link">Регистрация</NuxtLink>
              </li>
            </template>
          </ul>
        </div>
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.18em] text-cloth-muted">Правовая информация</p>
          <ul class="mt-3 space-y-2 text-sm">
            <li><NuxtLink to="/legal/privacy" class="footer-link">Конфиденциальность</NuxtLink></li>
            <li><NuxtLink to="/legal/terms" class="footer-link">Пользовательское соглашение</NuxtLink></li>
          </ul>
        </div>
      </div>
      <div class="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-[color:var(--hairline)] pt-5 text-xs text-cloth-muted">
        <p>© {{ year }} {{ name }}</p>
        <p>Русский бильярд · пирамида</p>
      </div>
    </div>
  </footer>
</template>
