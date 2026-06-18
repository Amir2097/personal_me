<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { Integration, IntegrationInput } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

definePageMeta({
  middleware: 'admin'
})

const api = useApi()
const items = ref<Integration[]>([])
const busy = ref(false)
const error = ref('')
const form = ref<IntegrationInput>({
  key: '',
  url: '',
  label: '',
  requires_auth: false,
  use_sso: false,
  enabled: true,
  sort_order: 0
})

const load = async () => {
  busy.value = true
  error.value = ''
  try {
    items.value = await api.listAllIntegrations()
  } catch {
    error.value = 'Не удалось загрузить интеграции.'
  } finally {
    busy.value = false
  }
}

const createItem = async () => {
  if (!form.value.key || !form.value.url) {
    error.value = 'Укажите key и url.'
    return
  }
  busy.value = true
  error.value = ''
  try {
    await api.createIntegration(form.value)
    form.value = {
      key: '',
      url: '',
      label: '',
      requires_auth: false,
      use_sso: false,
      enabled: true,
      sort_order: 0
    }
    await load()
  } catch {
    error.value = 'Не удалось создать интеграцию.'
  } finally {
    busy.value = false
  }
}

const toggleEnabled = async (item: Integration) => {
  busy.value = true
  error.value = ''
  try {
    await api.updateIntegration(item.id, { enabled: !item.enabled })
    await load()
  } catch {
    error.value = 'Не удалось обновить интеграцию.'
  } finally {
    busy.value = false
  }
}

const removeItem = async (item: Integration) => {
  if (!confirm(`Удалить интеграцию "${item.key}"?`)) return
  busy.value = true
  error.value = ''
  try {
    await api.deleteIntegration(item.id)
    await load()
  } catch {
    error.value = 'Не удалось удалить интеграцию.'
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
          <h1 class="text-xl">Интеграции</h1>
        </div>
        <div class="flex gap-4 text-sm">
          <NuxtLink to="/admin/projects" class="text-terminal-gray hover:text-terminal-green">
            проекты
          </NuxtLink>
          <NuxtLink to="/" class="text-terminal-gray hover:text-terminal-green">
            ← терминал
          </NuxtLink>
        </div>
      </div>

      <p v-if="error" class="mb-4 text-sm text-red-400">{{ error }}</p>

      <section class="mb-8 rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
        <h2 class="mb-3 text-sm text-terminal-gray">Новая интеграция</h2>
        <div class="grid gap-3 md:grid-cols-2">
          <input
            v-model="form.key"
            placeholder="key (github)"
            class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
          />
          <input
            v-model="form.url"
            placeholder="url"
            class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
          />
          <input
            v-model="form.label"
            placeholder="label"
            class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
          />
          <input
            v-model.number="form.sort_order"
            type="number"
            placeholder="sort_order"
            class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 text-sm outline-none"
          />
        </div>
        <label class="mt-3 flex items-center gap-2 text-sm">
          <input v-model="form.requires_auth" type="checkbox" />
          требует авторизации
        </label>
        <label class="flex items-center gap-2 text-sm">
          <input v-model="form.use_sso" type="checkbox" />
          SSO (одноразовый код в URL)
        </label>
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
              <th class="px-4 py-3">key</th>
              <th class="px-4 py-3">label</th>
              <th class="px-4 py-3">url</th>
              <th class="px-4 py-3">auth</th>
              <th class="px-4 py-3">status</th>
              <th class="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in items"
              :key="item.id"
              class="border-b border-terminal-gray/40"
            >
              <td class="px-4 py-3">{{ item.key }}</td>
              <td class="px-4 py-3">{{ item.label }}</td>
              <td class="px-4 py-3 text-terminal-gray">{{ item.url }}</td>
              <td class="px-4 py-3">{{ item.requires_auth ? 'да' : 'нет' }}</td>
              <td class="px-4 py-3">{{ item.enabled ? 'on' : 'off' }}</td>
              <td class="px-4 py-3">
                <button
                  class="mr-2 text-terminal-gray hover:text-terminal-green"
                  :disabled="busy"
                  @click="toggleEnabled(item)"
                >
                  {{ item.enabled ? 'выкл' : 'вкл' }}
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
