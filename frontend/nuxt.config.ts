export default defineNuxtConfig({
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  modules: ['@nuxtjs/tailwindcss', '@pinia/nuxt'],
  runtimeConfig: {
    apiInternalUrl: process.env.NUXT_API_INTERNAL_URL || 'http://localhost:8000',
    public: {
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL ?? ''
    }
  },
  vite: {
    server: {
      proxy: {
        '/api': {
          target: process.env.NUXT_API_INTERNAL_URL || 'http://localhost:8000',
          changeOrigin: true
        }
      }
    }
  },
  typescript: {
    strict: true
  }
})
