<script setup lang="ts">
import type { SuknoSiteSettings } from '~/composables/useSuknoAdmin'

useHead({ title: 'SEO · Админка' })

const admin = useSuknoAdmin()
const { hydrate: reloadPublicSeo } = useSuknoSeo()

const busy = ref(false)
const error = ref('')
const message = ref('')
const form = ref({
  tagline: '',
  site_url: '',
  seo_title: 'Цифровое Сукно',
  seo_description: '',
  seo_keywords: '',
  og_image_url: '',
  motd: ''
})

const previewTitle = computed(() => form.value.seo_title.trim() || 'Цифровое Сукно')
const previewDescription = computed(
  () => form.value.seo_description.trim() || 'Цифровое Сукно — тренажёр, колхоз и турнирная сетка.'
)

const applyRow = (row: SuknoSiteSettings) => {
  form.value = {
    tagline: row.tagline,
    site_url: row.site_url,
    seo_title: row.seo_title,
    seo_description: row.seo_description,
    seo_keywords: row.seo_keywords,
    og_image_url: row.og_image_url,
    motd: row.motd
  }
}

const load = async () => {
  if (!admin.unlocked.value) return
  busy.value = true
  error.value = ''
  try {
    applyRow(await admin.loadSettings())
  } catch {
    error.value = 'Не удалось загрузить настройки.'
  } finally {
    busy.value = false
  }
}

const save = async () => {
  busy.value = true
  error.value = ''
  message.value = ''
  try {
    applyRow(await admin.saveSettings(form.value))
    await reloadPublicSeo()
    message.value = 'Сохранено. Meta на сайте обновятся сразу.'
  } catch {
    error.value = 'Не удалось сохранить.'
  } finally {
    busy.value = false
  }
}

watch(
  () => admin.unlocked.value,
  (ok) => {
    if (ok) void load()
  }
)

onMounted(() => {
  admin.hydrate()
  if (admin.unlocked.value) void load()
})
</script>

<template>
  <AdminShell>
    <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <form class="card-surface space-y-4 p-5" @submit.prevent="save">
        <h2 class="font-display text-xl font-bold">SEO и тексты сайта</h2>
        <p class="text-sm text-cloth-muted">
          Бренд зафиксирован: <strong class="text-cloth-chalk">Цифровое Сукно</strong>. Здесь только выдача поисковикам и короткие тексты установки.
        </p>

        <label class="block text-xs text-cloth-muted">
          Title
          <input v-model="form.seo_title" class="field-input mt-1 w-full" maxlength="160" />
        </label>
        <label class="block text-xs text-cloth-muted">
          Description
          <textarea v-model="form.seo_description" class="field-input mt-1 w-full" rows="3" maxlength="600" />
        </label>
        <label class="block text-xs text-cloth-muted">
          Keywords (через запятую)
          <input v-model="form.seo_keywords" class="field-input mt-1 w-full" maxlength="400" />
        </label>
        <label class="block text-xs text-cloth-muted">
          Канонический URL сайта
          <input v-model="form.site_url" class="field-input mt-1 w-full" maxlength="500" placeholder="https://sukno.example" />
        </label>
        <label class="block text-xs text-cloth-muted">
          OG image URL (пусто = иконка бренда)
          <input v-model="form.og_image_url" class="field-input mt-1 w-full" maxlength="500" />
        </label>
        <label class="block text-xs text-cloth-muted">
          Слоган на главной
          <input v-model="form.tagline" class="field-input mt-1 w-full" maxlength="240" />
        </label>
        <label class="block text-xs text-cloth-muted">
          Сообщение на главной (MOTD)
          <input v-model="form.motd" class="field-input mt-1 w-full" maxlength="280" />
        </label>

        <p v-if="error" class="text-sm text-amber-700">{{ error }}</p>
        <p v-if="message" class="text-sm text-cloth-accent">{{ message }}</p>
        <button type="submit" class="btn-primary text-sm" :disabled="busy || !admin.unlocked.value">
          {{ busy ? '…' : 'Сохранить' }}
        </button>
      </form>

      <aside class="card-surface h-fit p-5">
        <p class="text-xs uppercase tracking-[0.2em] text-cloth-muted">превью выдачи</p>
        <p class="mt-3 text-sm text-sky-800">{{ (form.site_url || 'https://сайт').replace(/\/$/, '') }}</p>
        <p class="mt-1 font-display text-lg font-bold text-blue-800">{{ previewTitle }}</p>
        <p class="mt-1 text-sm text-cloth-muted">{{ previewDescription }}</p>
      </aside>
    </div>
  </AdminShell>
</template>
