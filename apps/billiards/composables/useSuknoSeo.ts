import type { SuknoSeo } from '~/composables/useSuknoAdmin'

const FALLBACK_DESCRIPTION =
  'Цифровое Сукно — тренажёр, колхоз и турнирная сетка для русского бильярда.'

export const useSuknoSeo = () => {
  const { apiUrl, apiOrigin } = useHubAuth()
  const config = useRuntimeConfig()
  const { appPath } = useAppBase()

  const seo = useState<SuknoSeo | null>('sukno-public-seo', () => null)
  const brandName = computed(() => seo.value?.brand_name || String(config.public.brandName || 'Цифровое Сукно'))
  const title = computed(() => seo.value?.seo_title?.trim() || brandName.value)
  const description = computed(() => seo.value?.seo_description?.trim() || FALLBACK_DESCRIPTION)
  const keywords = computed(() => seo.value?.seo_keywords?.trim() || '')
  const tagline = computed(() => seo.value?.tagline?.trim() || '')
  const motd = computed(() => seo.value?.motd?.trim() || '')
  const ogImage = computed(() => seo.value?.og_image_url?.trim() || appPath('brand/icon.png'))
  const canonical = computed(() => seo.value?.site_url?.replace(/\/$/, '') || '')

  const hydrate = async () => {
    if (!apiOrigin.value) return
    try {
      seo.value = await $fetch<SuknoSeo>(apiUrl('/api/v1/site/seo'))
    } catch {
      /* offline / API down — keep built-in defaults */
    }
  }

  return { seo, brandName, title, description, keywords, tagline, motd, ogImage, canonical, hydrate }
}
