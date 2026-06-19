<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { Project, ProjectInput } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

definePageMeta({
  middleware: 'admin'
})

const api = useApi()
const items = ref<Project[]>([])
const busy = ref(false)
const error = ref('')
const editingId = ref<number | null>(null)

const emptyForm = (): ProjectInput => ({
  slug: '',
  title: '',
  summary: '',
  description: '',
  tech_stack: '',
  github_url: '',
  demo_url: '',
  image_url: '',
  gallery_urls: '',
  is_public: true,
  featured: false,
  sort_order: 0
})

const form = ref<ProjectInput>(emptyForm())

const resetForm = () => {
  editingId.value = null
  form.value = emptyForm()
}

const load = async () => {
  busy.value = true
  error.value = ''
  try {
    items.value = await api.listAllProjects()
  } catch {
    error.value = 'Не удалось загрузить проекты.'
  } finally {
    busy.value = false
  }
}

const saveItem = async () => {
  if (!form.value.title) {
    error.value = 'Укажите title.'
    return
  }
  if (!editingId.value && !form.value.slug) {
    error.value = 'Укажите slug.'
    return
  }
  busy.value = true
  error.value = ''
  try {
    if (editingId.value) {
      const { slug: _, ...payload } = form.value
      await api.updateProject(editingId.value, payload)
    } else {
      await api.createProject(form.value)
    }
    resetForm()
    await load()
  } catch {
    error.value = editingId.value ? 'Не удалось обновить проект.' : 'Не удалось создать проект.'
  } finally {
    busy.value = false
  }
}

const startEdit = (item: Project) => {
  editingId.value = item.id
  form.value = {
    slug: item.slug,
    title: item.title,
    summary: item.summary,
    description: item.description,
    tech_stack: item.tech_stack,
    github_url: item.github_url,
    demo_url: item.demo_url,
    image_url: item.image_url || '',
    gallery_urls: (item.gallery || []).join('\n'),
    is_public: item.is_public,
    featured: item.featured,
    sort_order: item.sort_order
  }
}

const togglePublic = async (item: Project) => {
  busy.value = true
  try {
    await api.updateProject(item.id, { is_public: !item.is_public })
    await load()
  } catch {
    error.value = 'Не удалось обновить проект.'
  } finally {
    busy.value = false
  }
}

const removeItem = async (item: Project) => {
  if (!confirm(`Удалить проект "${item.title}"?`)) return
  busy.value = true
  try {
    await api.deleteProject(item.id)
    if (editingId.value === item.id) resetForm()
    await load()
  } catch {
    error.value = 'Не удалось удалить проект.'
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="min-h-screen bg-terminal-black px-4 py-6 text-terminal-green">
    <TerminalShell cwd="~/admin/projects" session="terminal://personal_me/admin/projects" tall>
      <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
        <p class="mb-1 text-xs uppercase tracking-[0.25em] text-terminal-gray">admin</p>
        <h1 class="mb-6 text-xl">Проекты портфолио</h1>

        <p v-if="error" class="mb-4 text-red-400">{{ error }}</p>

        <section class="mb-8 rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
          <div class="mb-3 flex items-center justify-between gap-3">
            <h2 class="text-sm text-terminal-gray">
              {{ editingId ? `Редактирование #${editingId}` : 'Новый проект' }}
            </h2>
            <button
              v-if="editingId"
              class="text-xs text-terminal-gray hover:text-terminal-green"
              @click="resetForm"
            >
              отмена
            </button>
          </div>
          <div class="grid gap-3 md:grid-cols-2">
            <input
              v-model="form.slug"
              placeholder="slug"
              :disabled="!!editingId"
              class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none disabled:opacity-50"
            />
            <input
              v-model="form.title"
              placeholder="title"
              class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
            />
            <input
              v-model="form.summary"
              placeholder="summary"
              class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none md:col-span-2"
            />
            <textarea
              v-model="form.description"
              placeholder="description"
              rows="3"
              class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none md:col-span-2"
            />
            <input
              v-model="form.tech_stack"
              placeholder="tech stack"
              class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
            />
            <input
              v-model="form.github_url"
              placeholder="github url"
              class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
            />
            <input
              v-model="form.demo_url"
              placeholder="demo url"
              class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none md:col-span-2"
            />
            <input
              v-model="form.image_url"
              placeholder="image_url (обложка, https://...)"
              class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none md:col-span-2"
            />
            <textarea
              v-model="form.gallery_urls"
              placeholder="gallery_urls — по одному URL на строку"
              rows="3"
              class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none md:col-span-2"
            />
          </div>
          <div class="mt-3 flex gap-4 text-sm">
            <label class="flex items-center gap-2">
              <input v-model="form.is_public" type="checkbox" />
              public
            </label>
            <label class="flex items-center gap-2">
              <input v-model="form.featured" type="checkbox" />
              featured
            </label>
          </div>
          <button
            class="mt-4 rounded border border-terminal-green/50 px-4 py-2 text-sm hover:bg-terminal-green/10"
            :disabled="busy"
            @click="saveItem"
          >
            {{ editingId ? 'Сохранить' : 'Создать' }}
          </button>
        </section>

        <section class="overflow-x-auto rounded-lg border border-terminal-gray/80">
          <table class="w-full text-left text-sm">
            <thead class="border-b border-terminal-gray/80 text-terminal-gray">
              <tr>
                <th class="px-4 py-3">slug</th>
                <th class="px-4 py-3">title</th>
                <th class="px-4 py-3">media</th>
                <th class="px-4 py-3">public</th>
                <th class="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in items"
                :key="item.id"
                class="border-b border-terminal-gray/40"
              >
                <td class="px-4 py-3">
                  <NuxtLink :to="`/projects/${item.slug}`" class="hover:underline">
                    {{ item.slug }}
                  </NuxtLink>
                </td>
                <td class="px-4 py-3">{{ item.title }}</td>
                <td class="px-4 py-3 text-xs text-terminal-gray">
                  {{ item.image_url ? 'cover' : '—' }}
                  <span v-if="item.gallery?.length"> +{{ item.gallery.length }}</span>
                </td>
                <td class="px-4 py-3">{{ item.is_public ? 'да' : 'нет' }}</td>
                <td class="px-4 py-3 whitespace-nowrap">
                  <button
                    class="mr-2 text-cyan-300 hover:text-terminal-green"
                    :disabled="busy"
                    @click="startEdit(item)"
                  >
                    edit
                  </button>
                  <button
                    class="mr-2 text-terminal-gray hover:text-terminal-green"
                    :disabled="busy"
                    @click="togglePublic(item)"
                  >
                    {{ item.is_public ? 'скрыть' : 'опубликовать' }}
                  </button>
                  <button
                    class="text-red-400 hover:text-red-300"
                    :disabled="busy"
                    @click="removeItem(item)"
                  >
                    удалить
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </TerminalShell>
  </main>
</template>
