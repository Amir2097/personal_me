<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { OAuthClient, OAuthClientInput } from '~/composables/useApi'
import { useApi } from '~/composables/useApi'

definePageMeta({
  middleware: 'admin'
})

const api = useApi()
const items = ref<OAuthClient[]>([])
const busy = ref(false)
const error = ref('')
const form = ref<OAuthClientInput>({
  client_id: '',
  client_secret: '',
  name: '',
  redirect_uris: ['http://localhost/oauth/callback'],
  scopes: 'openid profile'
})

const load = async () => {
  busy.value = true
  error.value = ''
  try {
    items.value = await api.listOAuthClients()
  } catch {
    error.value = 'Не удалось загрузить OIDC clients.'
  } finally {
    busy.value = false
  }
}

const createItem = async () => {
  if (!form.value.client_id || !form.value.client_secret) {
    error.value = 'Укажите client_id и client_secret.'
    return
  }
  busy.value = true
  error.value = ''
  try {
    await api.createOAuthClient(form.value)
    form.value.client_id = ''
    form.value.client_secret = ''
    await load()
  } catch {
    error.value = 'Не удалось создать клиента.'
  } finally {
    busy.value = false
  }
}

const removeItem = async (item: OAuthClient) => {
  busy.value = true
  error.value = ''
  try {
    await api.deleteOAuthClient(item.id)
    await load()
  } catch {
    error.value = 'Не удалось удалить клиента.'
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
      <TerminalShell cwd="~/admin/oidc-clients" session="terminal://personal_me/admin/oidc" tall>
        <div class="min-h-0 flex-1 overflow-y-auto p-5 text-sm">
          <p class="mb-1 text-xs uppercase tracking-[0.25em] text-terminal-gray">admin</p>
          <h1 class="mb-6 text-xl">OIDC clients</h1>
          <p v-if="error" class="mb-4 text-red-400">{{ error }}</p>

          <section class="mb-8 rounded-lg border border-terminal-gray/80 bg-black/30 p-4">
            <h2 class="mb-3 text-terminal-gray">Новый client</h2>
            <div class="grid gap-3 md:grid-cols-2">
              <input v-model="form.client_id" placeholder="client_id" class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none" />
              <input v-model="form.client_secret" placeholder="client_secret" type="password" class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none" />
              <input v-model="form.name" placeholder="name" class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none" />
              <input v-model="form.redirect_uris[0]" placeholder="redirect_uri" class="rounded border border-terminal-gray/60 bg-transparent px-3 py-2 outline-none md:col-span-2" />
            </div>
            <button class="mt-4 rounded border border-terminal-green/50 px-4 py-2 hover:bg-terminal-green/10" :disabled="busy" @click="createItem">
              Создать
            </button>
          </section>

          <section class="overflow-x-auto rounded-lg border border-terminal-gray/80">
            <table class="w-full text-left text-sm">
              <thead class="border-b border-terminal-gray/80 text-terminal-gray">
                <tr>
                  <th class="px-4 py-3">client_id</th>
                  <th class="px-4 py-3">name</th>
                  <th class="px-4 py-3">redirects</th>
                  <th class="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in items" :key="item.id" class="border-b border-terminal-gray/40">
                  <td class="px-4 py-3">{{ item.client_id }}</td>
                  <td class="px-4 py-3">{{ item.name }}</td>
                  <td class="px-4 py-3 text-terminal-gray">{{ item.redirect_uris.join(', ') }}</td>
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
