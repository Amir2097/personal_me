<script setup lang="ts">
import type { SiteSettings } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

definePageMeta({
  middleware: 'admin'
})

const api = useApi()
const { seo, load: reloadSeo } = useSiteSeoConfig()
const busy = ref(false)
const error = ref('')
const message = ref('')
const form = ref<Omit<SiteSettings, 'updated_at'>>({
  site_name: '',
  owner_name: '',
  tagline: '',
  bio: '',
  experience: '',
  skills: '',
  site_url: '',
  seo_title_suffix: 'Terminal IDE',
  seo_description: '',
  seo_keywords: '',
  og_image_url: '',
  motd: '',
  resume_url: '',
  privacy_policy: '',
  terms_of_use: ''
})

const previewTitle = computed(() => {
  const name = form.value.site_name || 'personal_me'
  const suffix = form.value.seo_title_suffix || 'Terminal IDE'
  return `${name} // ${suffix}`
})

const previewDescription = computed(
  () => form.value.seo_description || form.value.tagline || '—'
)

const previewUrl = computed(() => {
  const base = (form.value.site_url || 'http://localhost').replace(/\/$/, '')
  return `${base}/`
})

const load = async () => {
  busy.value = true
  error.value = ''
  try {
    const data = await api.getSiteSettings()
    const { updated_at: _, ...rest } = data
    form.value = rest
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
    await api.updateSiteSettings(form.value)
    seo.value = null
    await reloadSeo()
    message.value = 'Настройки сохранены. SEO и about обновятся на сайте.'
    await load()
  } catch {
    error.value = 'Не удалось сохранить настройки.'
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green md:py-8">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-5 md:gap-6">
      <HubIntro compact />
      <TerminalShell cwd="~/admin/seo" session="terminal://personal_me/admin/seo" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p class="mb-1 text-xs uppercase tracking-[0.25em] text-terminal-gray">admin</p>
          <h1 class="mb-2 text-xl">SEO и контент сайта</h1>
          <p class="mb-6 text-terminal-gray">
            Все meta-теги, about и MOTD. Изменения применяются сразу после сохранения.
          </p>

          <p v-if="error" class="mb-4 text-red-400">{{ error }}</p>
          <p v-if="message" class="mb-4 text-cyan-300">{{ message }}</p>

          <div class="grid gap-6 lg:grid-cols-2">
            <section class="space-y-5">
              <div class="rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
                <h2 class="mb-3 text-xs uppercase tracking-widest text-terminal-gray">SEO</h2>
                <div class="space-y-3">
                  <input
                    v-model="form.site_name"
                    placeholder="site_name (personal_me)"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                  <input
                    v-model="form.site_url"
                    placeholder="site_url (https://example.com)"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                  <input
                    v-model="form.seo_title_suffix"
                    placeholder="seo_title_suffix"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                  <textarea
                    v-model="form.seo_description"
                    rows="3"
                    placeholder="seo_description (если пусто — tagline)"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                  <input
                    v-model="form.seo_keywords"
                    placeholder="seo_keywords (через запятую)"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                  <input
                    v-model="form.og_image_url"
                    placeholder="og_image_url (https://.../og.png)"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                </div>
              </div>

              <div class="rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
                <h2 class="mb-3 text-xs uppercase tracking-widest text-terminal-gray">About / контент</h2>
                <div class="space-y-3">
                  <input
                    v-model="form.owner_name"
                    placeholder="owner_name"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                  <input
                    v-model="form.tagline"
                    placeholder="tagline"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                  <textarea
                    v-model="form.bio"
                    rows="4"
                    placeholder="bio"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                  <textarea
                    v-model="form.experience"
                    rows="4"
                    placeholder="experience (каждая строка — пункт опыта)"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                  <input
                    v-model="form.skills"
                    placeholder="skills (Python, FastAPI, ...)"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                  <input
                    v-model="form.resume_url"
                    placeholder="resume_url (PDF, пока внешняя ссылка)"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                  <input
                    v-model="form.motd"
                    placeholder="motd (после login в терминале)"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
                  />
                </div>
              </div>

              <div class="rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
                <h2 class="mb-3 text-xs uppercase tracking-widest text-terminal-gray">Юридические документы</h2>
                <p class="mb-3 text-xs text-terminal-gray">
                  Если поля пустые — на сайте показываются стартовые шаблоны. Проверьте текст перед production.
                </p>
                <div class="space-y-3">
                  <textarea
                    v-model="form.privacy_policy"
                    rows="8"
                    placeholder="privacy_policy (политика конфиденциальности)"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 font-mono text-xs outline-none"
                  />
                  <textarea
                    v-model="form.terms_of_use"
                    rows="8"
                    placeholder="terms_of_use (пользовательское соглашение)"
                    class="w-full rounded border border-terminal-gray/60 bg-transparent px-3 py-2 font-mono text-xs outline-none"
                  />
                  <div class="flex flex-wrap gap-3 text-xs">
                    <NuxtLink to="/legal/privacy" target="_blank" class="terminal-interactive text-cyan-300 underline">
                      /legal/privacy
                    </NuxtLink>
                    <NuxtLink to="/legal/terms" target="_blank" class="terminal-interactive text-cyan-300 underline">
                      /legal/terms
                    </NuxtLink>
                  </div>
                </div>
              </div>

              <button
                class="terminal-btn terminal-interactive text-sm text-terminal-green"
                :disabled="busy"
                @click="save"
              >
                Сохранить
              </button>
            </section>

            <section class="space-y-4">
              <div class="rounded-lg border border-cyan-500/30 bg-black/40 p-4">
                <h2 class="mb-3 text-xs uppercase tracking-widest text-cyan-300">Предпросмотр SEO</h2>
                <div class="space-y-4 text-xs">
                  <div>
                    <div class="text-terminal-gray">title</div>
                    <div class="mt-1 text-base text-terminal-green">{{ previewTitle }}</div>
                  </div>
                  <div>
                    <div class="text-terminal-gray">description</div>
                    <div class="mt-1 leading-relaxed text-terminal-green/90">{{ previewDescription }}</div>
                  </div>
                  <div>
                    <div class="text-terminal-gray">og:url</div>
                    <div class="mt-1 break-all text-cyan-300">{{ previewUrl }}</div>
                  </div>
                  <div v-if="form.seo_keywords">
                    <div class="text-terminal-gray">keywords</div>
                    <div class="mt-1 text-terminal-green/80">{{ form.seo_keywords }}</div>
                  </div>
                  <div v-if="form.og_image_url">
                    <div class="text-terminal-gray">og:image</div>
                    <div class="mt-1 break-all text-terminal-green/80">{{ form.og_image_url }}</div>
                  </div>
                </div>
              </div>

              <div class="rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
                <h2 class="mb-3 text-xs uppercase tracking-widest text-terminal-gray">Предпросмотр about</h2>
                <h3 class="text-lg">{{ form.owner_name || '—' }}</h3>
                <p class="mt-2 text-terminal-green/85">{{ form.tagline || '—' }}</p>
                <p class="mt-4 whitespace-pre-wrap text-terminal-green/80">{{ form.bio || '—' }}</p>
                <div v-if="form.skills" class="mt-4 flex flex-wrap gap-2">
                  <span
                    v-for="skill in form.skills.split(',').map((s) => s.trim()).filter(Boolean)"
                    :key="skill"
                    class="rounded border border-terminal-gray/50 px-2 py-0.5 text-xs text-cyan-300"
                  >
                    {{ skill }}
                  </span>
                </div>
              </div>

              <p class="text-xs text-terminal-gray">
                Контакты — в
                <NuxtLink to="/admin/contacts" class="terminal-interactive text-cyan-300">/admin/contacts</NuxtLink>.
                Env-переменные SITE_* используются только при первом seed.
              </p>
            </section>
          </div>
        </div>
      </TerminalShell>
    </div>
  </main>
</template>
