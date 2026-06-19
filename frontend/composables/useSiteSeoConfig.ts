export type SiteSeoPublic = {
  site_name: string
  owner_name: string
  tagline: string
  site_url: string
  seo_title_suffix: string
  seo_description: string
  seo_keywords: string
  og_image_url: string
}

export type SiteSettings = SiteSeoPublic & {
  bio: string
  experience: string
  skills: string
  motd: string
  resume_url: string
  privacy_policy: string
  terms_of_use: string
  updated_at: string
}

export function useSiteSeoConfig() {
  const seo = useState<SiteSeoPublic | null>('site-seo-config', () => null)

  const load = async () => {
    if (seo.value) return seo.value
    const config = useRuntimeConfig()
    const baseURL = import.meta.client ? config.public.apiBaseUrl : config.apiInternalUrl
    seo.value = await $fetch<SiteSeoPublic>('/api/v1/site/seo', {
      baseURL,
      credentials: 'include'
    })
    return seo.value
  }

  return { seo, load }
}
