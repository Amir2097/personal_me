<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    url: string
    label?: string
    size?: number
  }>(),
  { size: 200 }
)

const dataUrl = ref('')
const failed = ref(false)

watch(
  () => props.url,
  async (url) => {
    dataUrl.value = ''
    failed.value = false
    if (!url) return
    try {
      const { toQrDataUrl } = await import('~/utils/qrCode')
      dataUrl.value = await toQrDataUrl(url, props.size)
    } catch {
      failed.value = true
    }
  },
  { immediate: true }
)
</script>

<template>
  <div v-if="url" class="flex flex-col items-center gap-1.5">
    <img
      v-if="dataUrl"
      :src="dataUrl"
      :alt="label || 'QR-код комнаты'"
      class="rounded-xl bg-white p-2 shadow-sm"
      :width="size"
      :height="size"
    />
    <p v-else-if="failed" class="text-center text-[11px] text-cloth-muted">QR недоступен</p>
    <p v-if="label && dataUrl" class="text-center text-[10px] text-cloth-muted">{{ label }}</p>
  </div>
</template>
