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
const form = ref<ProjectInput>({
  slug: '',
  title: '',
  summary: '',
  description: '',
  tech_stack: '',
  github_url: '',
  demo_url: '',
  is_public: true,
  featured: false,
  sort_order: 0
})

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

const createItem = async () => {
  if (!form.value.slug || !form.value.title) {
    error.value = 'Укажите slug и title.'
    return
  }
  busy.value = true
  error.value = ''
  try {
    await api.createProject(form.value)
    form.value = {
      slug: '',
      title: '',
      summary: '',
      description: '',
      tech_stack: '',
      github_url: '',
      demo_url: '',
      is_public: true,
      featured: false,
      sort_order: 0
    }
    await load()
  } catch {
    error.value = 'Не удалось создать проект.'
  } finally {
    busy.value = false
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
  <main class="min-h-screen bg-terminal-black px-4 py-8 text-terminal-green">
    <div class="mx-auto w-full max-w-5xl font-mono">
      <div class="mb-6 flex items-center justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.25em] text-terminal-gray">admin</p>
          <h1 class="text-xl">Проекты портфолио</h1>
        </div>
        <div class="flex gap-4 text-sm">
          <NuxtLink to="/admin/integrations" class="text-terminal-gray hover:text-terminal-green">
            интеграции
          </NuxtLink>
          <NuxtLink to="/" class="text-terminal-gray hover:text-terminal-green">
            ← терминал
          </NuxtLink>
        </div>
      </div>

      <p v-if="error" class="mb-4 text-sm text-red-400">{{ error }}</p>

      <section class="mb-8 rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
        <h2 class="mb-3 text-sm text-terminal-gray">Новый проект</h2>
        <div class="grid gap-3 md:grid-cols-2">
          <input
            v-model="form.slug"
            placeholder="slug"
            class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
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
            class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
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
          @click="createItem"
        >
          Создать
        </button>
      </section>

      <section class="overflow-x-auto rounded-lg border border-terminal-gray/80">
        <table class="w-full text-left text-sm">
          <thead class="border-b border-terminal-gray/80 text-terminal-gray">
            <tr>
              <th class="px-4 py-3">slug</th>
              <th class="px-4 py-3">title</th>
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
              <td class="px-4 py-3">{{ item.is_public ? 'да' : 'нет' }}</td>
              <td class="px-4 py-3">
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
  </main>
</template>
