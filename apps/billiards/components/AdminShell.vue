<script setup lang="ts">

const route = useRoute()

const suknoAuth = useSuknoAuth()

const { unlocked, hydrate, unlock, lock } = useSuknoAdmin()

const keyDraft = ref('')

const showLegacyKey = ref(false)

const error = ref('')

const busy = ref(false)

const legacyKeyAllowed = computed(() => Boolean(suknoAuth.config.value?.allow_legacy_admin_key))

onMounted(async () => {
  hydrate()
  try {
    await suknoAuth.loadConfig()
  } catch {
    /* offline */
  }
  try {
    await suknoAuth.fetchMe()
  } catch {
    /* guest */
  }
})



const submitKey = async () => {

  error.value = ''

  busy.value = true

  try {

    await unlock(keyDraft.value.trim())

    keyDraft.value = ''

  } catch {

    error.value = 'Неверный ключ или API недоступен.'

  } finally {

    busy.value = false

  }

}



const logout = async () => {

  lock()

  await suknoAuth.logout()

}

</script>



<template>

  <div>

    <main class="page-shell py-8">

      <p class="section-eyebrow">

        <AppIcon name="settings" class="text-cloth-accent" />

        админка

      </p>



      <div v-if="!unlocked" class="card-surface mx-auto mt-6 max-w-lg p-6">

        <h1 class="font-display text-2xl font-bold">Цифровое Сукно · доступ</h1>

        <p class="mt-2 text-sm text-cloth-muted">

          Войдите аккаунтом с ролью <span class="font-semibold">admin</span><template v-if="legacyKeyAllowed"> или используйте ключ установки (dev)</template>.

        </p>

        <div class="mt-5 flex flex-wrap gap-2">

          <NuxtLink

            :to="{ path: '/auth/login', query: { redirect: route.fullPath } }"

            class="btn-primary text-sm"

          >

            Войти

          </NuxtLink>

          <button
            v-if="legacyKeyAllowed"
            type="button"
            class="btn-ghost text-sm"
            @click="showLegacyKey = !showLegacyKey"
          >

            {{ showLegacyKey ? 'Скрыть ключ' : 'Ключ установки' }}

          </button>

        </div>

        <form v-if="legacyKeyAllowed && showLegacyKey" class="mt-4 space-y-3" @submit.prevent="submitKey">

          <label class="block text-xs text-cloth-muted">

            SUKNO_ADMIN_KEY

            <input

              v-model="keyDraft"

              class="field-input mt-1 w-full"

              type="password"

              autocomplete="current-password"

            />

          </label>

          <p v-if="error" class="text-sm text-amber-700">{{ error }}</p>

          <button type="submit" class="btn-ghost text-sm" :disabled="busy">

            {{ busy ? '…' : 'Открыть ключом' }}

          </button>

        </form>

      </div>



      <div v-else>

        <div class="mt-4 flex flex-wrap items-center justify-between gap-3">

          <h1 class="font-display text-3xl font-bold">Админка</h1>

          <button type="button" class="btn-ghost btn-touch" @click="logout">Выйти</button>

        </div>

        <nav class="mt-4 flex flex-wrap gap-2">

          <NuxtLink to="/admin" class="btn-ghost btn-touch">Обзор</NuxtLink>

          <NuxtLink to="/admin/seo" class="btn-ghost btn-touch">SEO и сайт</NuxtLink>

          <NuxtLink to="/admin/users" class="btn-ghost btn-touch">Пользователи</NuxtLink>
          <NuxtLink to="/admin/audit" class="btn-ghost btn-touch">Журнал</NuxtLink>
          <NuxtLink to="/admin/security" class="btn-ghost btn-touch">2FA</NuxtLink>

        </nav>

        <div class="mt-6">

          <slot />

        </div>

      </div>

    </main>

  </div>

</template>

