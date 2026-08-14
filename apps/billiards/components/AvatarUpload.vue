<script setup lang="ts">
const props = defineProps<{
  username: string
  displayName?: string
  avatarUrl?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  updated: [avatarUrl: string]
}>()

const suknoAuth = useSuknoAuth()
const fileInput = ref<HTMLInputElement | null>(null)
const busy = ref(false)
const localError = ref('')
const previewUrl = ref('')

const currentUrl = computed(() => previewUrl.value || props.avatarUrl || '')
const label = computed(() => props.displayName || props.username)

const openPicker = () => {
  if (props.disabled || busy.value) return
  fileInput.value?.click()
}

const onFileSelected = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) {
    localError.value = 'Выберите изображение (JPEG, PNG, WebP или GIF).'
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    localError.value = 'Файл больше 2 МБ.'
    return
  }
  localError.value = ''
  previewUrl.value = URL.createObjectURL(file)
  busy.value = true
  try {
    const profile = await suknoAuth.uploadAvatar(file)
    previewUrl.value = ''
    emit('updated', profile.avatar_url || '')
  } catch {
    previewUrl.value = ''
    localError.value = 'Не удалось загрузить аватар.'
  } finally {
    busy.value = false
  }
}

const removeAvatar = async () => {
  if (props.disabled || busy.value) return
  if (!props.avatarUrl && !previewUrl.value) return
  localError.value = ''
  busy.value = true
  try {
    const profile = await suknoAuth.deleteAvatar()
    previewUrl.value = ''
    emit('updated', profile.avatar_url || '')
  } catch {
    localError.value = 'Не удалось удалить аватар.'
  } finally {
    busy.value = false
  }
}

onBeforeUnmount(() => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
})
</script>

<template>
  <div class="space-y-3">
    <div class="flex flex-wrap items-center gap-4">
      <PlayerAvatar :name="label" :src="currentUrl" size="xl" />
      <div class="flex flex-col gap-2">
        <input
          ref="fileInput"
          type="file"
          accept="image/jpeg,image/png,image/webp,image/gif"
          class="hidden"
          @change="onFileSelected"
        />
        <button type="button" class="btn-primary text-sm" :disabled="disabled || busy" @click="openPicker">
          {{ busy ? 'Загрузка…' : 'Загрузить фото' }}
        </button>
        <button
          v-if="avatarUrl || previewUrl"
          type="button"
          class="btn-ghost text-sm"
          :disabled="disabled || busy"
          @click="removeAvatar"
        >
          Удалить
        </button>
      </div>
    </div>
    <p class="text-xs text-cloth-muted">JPEG, PNG, WebP или GIF, до 2 МБ.</p>
    <p v-if="localError" class="text-sm text-amber-700">{{ localError }}</p>
  </div>
</template>
