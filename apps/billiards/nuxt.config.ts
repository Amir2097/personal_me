export default defineNuxtConfig({
  devtools: { enabled: false },
  experimental: {
    // Avoid Vite pre-transform race on "#app-manifest" during Docker/nginx HMR.
    appManifest: false
  },
  devServer: {
    host: '0.0.0.0',
    port: 3010
  },
  css: ['~/assets/css/main.css'],
  modules: ['@nuxtjs/tailwindcss', '@pinia/nuxt'],
  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {}
    }
  },
  app: {
    baseURL: '/billiards/',
    head: {
      title: 'Billiards Kolkhoz Manager',
      meta: [
        { name: 'theme-color', content: '#0c1412' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover' }
      ]
    }
  },
  runtimeConfig: {
    public: {
      hubUrl: process.env.NUXT_PUBLIC_HUB_URL || 'http://localhost',
      brandName: process.env.NUXT_PUBLIC_BRAND_NAME || 'DAUTOVTECH',
      // Empty = same-origin /api via nginx. Standalone :3010 falls back to hubUrl in useHubAuth.
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || ''
    }
  },
  vite: {
    server: {
      allowedHosts: true,
      hmr: process.env.NUXT_VITE_HMR_CLIENT_PORT
        ? {
            clientPort: Number(process.env.NUXT_VITE_HMR_CLIENT_PORT),
            path: '/billiards/_nuxt/'
          }
        : undefined
    }
  },
  typescript: {
    strict: true
  }
})
