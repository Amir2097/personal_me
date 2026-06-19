<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { Contact, ContactInput } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

definePageMeta({
  middleware: 'admin'
})

const api = useApi()
const items = ref<Contact[]>([])
const busy = ref(false)
const error = ref('')
const form = ref<ContactInput>({
  key: '',
  label: '',
  value: '',
  kind: 'link',
  enabled: true,
  sort_order: 0
})

const kindOptions = [
  { value: 'link', label: 'link — URL (GitHub, Telegram, сайт)' },
  { value: 'email', label: 'email — mailto:' },
  { value: 'text', label: 'text — только текст (без ссылки)' }
]

const load = async () => {
  busy.value = true
  error.value = ''
  try {
    items.value = await api.listAllContacts()
  } catch {
    error.value = 'Не удалось загрузить контакты.'
  } finally {
    busy.value = false
  }
}

const createItem = async () => {
  if (!form.value.key || !form.value.value) {
    error.value = 'Укажите key и value.'
    return
  }
  busy.value = true
  error.value = ''
  try {
    await api.createContact(form.value)
    form.value = {
      key: '',
      label: '',
      value: '',
      kind: 'link',
      enabled: true,
      sort_order: 0
    }
    await load()
  } catch {
    error.value = 'Не удалось создать контакт.'
  } finally {
    busy.value = false
  }
}

const toggleEnabled = async (item: Contact) => {
  busy.value = true
  error.value = ''
  try {
    await api.updateContact(item.id, { enabled: !item.enabled })
    await load()
  } catch {
    error.value = 'Не удалось обновить контакт.'
  } finally {
    busy.value = false
  }
}

const removeItem = async (item: Contact) => {
  if (!confirm(`Удалить контакт "${item.key}"?`)) return
  busy.value = true
  error.value = ''
  try {
    await api.deleteContact(item.id)
    await load()
  } catch {
    error.value = 'Не удалось удалить контакт.'
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
      <TerminalShell cwd="~/admin/contacts" session="terminal://personal_me/admin/contacts" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p class="mb-1 text-xs uppercase tracking-[0.25em] text-terminal-gray">admin</p>
          <h1 class="mb-2 text-xl">Контакты</h1>
          <p class="mb-6 text-terminal-gray">
            Каналы связи для команды <code class="text-terminal-green">contact</code> и страницы
            <NuxtLink to="/contact" class="text-cyan-300 hover:underline">/contact</NuxtLink>.
          </p>
          <p v-if="error" class="mb-4 text-red-400">{{ error }}</p>

          <section class="mb-8 rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
            <h2 class="mb-3 text-terminal-gray">Новый канал</h2>
            <div class="grid gap-3 md:grid-cols-2">
              <input
                v-model="form.key"
                placeholder="key (telegram, email, github)"
                class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
              />
              <input
                v-model="form.label"
                placeholder="label (Telegram)"
                class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
              />
              <input
                v-model="form.value"
                placeholder="value (URL, email или текст)"
                class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none md:col-span-2"
              />
              <select
                v-model="form.kind"
                class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
              >
                <option v-for="option in kindOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <input
                v-model.number="form.sort_order"
                type="number"
                placeholder="sort_order"
                class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none"
              />
            </div>
            <button
              class="mt-4 rounded border border-terminal-green/50 px-4 py-2 hover:bg-terminal-green/10"
              :disabled="busy"
              @click="createItem"
            >
              Создать
            </button>
          </section>

          <section class="overflow-x-auto rounded-lg border border-terminal-gray/80">
            <table class="w-full min-w-[720px] text-left text-sm">
              <thead class="border-b border-terminal-gray/60 text-terminal-gray">
                <tr>
                  <th class="px-4 py-3">key</th>
                  <th class="px-4 py-3">label</th>
                  <th class="px-4 py-3">value</th>
                  <th class="px-4 py-3">kind</th>
                  <th class="px-4 py-3">status</th>
                  <th class="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in items" :key="item.id" class="border-b border-terminal-gray/40">
                  <td class="px-4 py-3">{{ item.key }}</td>
                  <td class="px-4 py-3">{{ item.label }}</td>
                  <td class="px-4 py-3 text-terminal-gray">{{ item.value }}</td>
                  <td class="px-4 py-3 text-terminal-gray">{{ item.kind }}</td>
                  <td class="px-4 py-3">
                    <button
                      class="text-xs uppercase"
                      :class="item.enabled ? 'text-terminal-green' : 'text-red-400'"
                      :disabled="busy"
                      @click="toggleEnabled(item)"
                    >
                      {{ item.enabled ? 'on' : 'off' }}
                    </button>
                  </td>
                  <td class="px-4 py-3">
                    <button class="text-red-400 hover:text-red-300" :disabled="busy" @click="removeItem(item)">
                      удалить
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </section>
        </div>
      </TerminalShell>
    </div>
  </main>
</template>
