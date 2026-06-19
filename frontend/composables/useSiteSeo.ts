export function useSiteSeo(options?: {
  title?: string
  description?: string
  path?: string
}) {
  const runtimeConfig = useRuntimeConfig()
  const { seo } = useSiteSeoConfig()

  const siteName = computed(
    () => seo.value?.site_name || String(runtimeConfig.public.siteName || 'personal_me')
  )
  const siteUrl = computed(
    () => seo.value?.site_url || String(runtimeConfig.public.siteUrl || 'http://localhost')
  )
  const defaultDescription = computed(
    () =>
      seo.value?.seo_description ||
      seo.value?.tagline ||
      String(runtimeConfig.public.tagline || 'Developer terminal hub')
  )
  const titleSuffix = computed(() => seo.value?.seo_title_suffix || 'Terminal IDE')

  const pageTitle = computed(() => {
    if (options?.title) return `${options.title} · ${siteName.value}`
    return `${siteName.value} // ${titleSuffix.value}`
  })

  const pageDescription = computed(() => options?.description || defaultDescription.value)

  const pageUrl = computed(() => {
    const path = options?.path || '/'
    const base = siteUrl.value.replace(/\/$/, '')
    const normalized = path.startsWith('/') ? path : `/${path}`
    return `${base}${normalized}`
  })

  const ogImage = computed(() => seo.value?.og_image_url || undefined)
  const keywords = computed(() => seo.value?.seo_keywords || undefined)

  useSeoMeta({
    title: pageTitle,
    description: pageDescription,
    ogTitle: pageTitle,
    ogDescription: pageDescription,
    ogUrl: pageUrl,
    ogType: 'website',
    ogImage: ogImage,
    twitterCard: 'summary',
    twitterTitle: pageTitle,
    twitterDescription: pageDescription,
    keywords
  })
}
