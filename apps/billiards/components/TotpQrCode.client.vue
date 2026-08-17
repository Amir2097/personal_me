<script setup lang="ts">
const props = defineProps<{
  otpauthUrl: string
}>()

const dataUrl = ref('')
const failed = ref(false)

watch(
  () => props.otpauthUrl,
  async (url) => {
    dataUrl.value = ''
    failed.value = false
    if (!url) return
    try {
      const QRCode = await import('qrcode')
      dataUrl.value = await QRCode.toDataURL(url, {
        width: 220,
        margin: 2,
        color: { dark: '#1a3d2e', light: '#ffffff' }
      })
    } catch {
      failed.value = true
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="flex flex-col items-center gap-2">
    <img
      v-if="dataUrl"
      :src="dataUrl"
      alt="QR-код для приложения-аутентификатора"
      class="rounded-xl bg-white p-2 shadow-sm"
      width="220"
      height="220"
    />
    <p v-else-if="failed" class="text-center text-xs text-cloth-muted">
      Не удалось построить QR — введите секрет вручную или откройте ссылку ниже.
    </p>
    <p v-else class="text-xs text-cloth-muted">Генерация QR…</p>
  </div>
</template>
