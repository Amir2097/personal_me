/** Preload public SEO config for meta tags and HubIntro. */
export default defineNuxtPlugin(async () => {
  const { load } = useSiteSeoConfig()
  try {
    await load()
  } catch {
    // fallback to runtimeConfig in useSiteSeo
  }
})
