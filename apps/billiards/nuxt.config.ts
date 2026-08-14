const appBase = (() => {
  const raw = process.env.NUXT_APP_BASE_URL ?? '/billiards/'
  if (!raw || raw === '/') return '/'
  return raw.endsWith('/') ? raw : `${raw}/`
})()

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
    baseURL: appBase,
    head: {
      title: 'Цифровое Сукно',
      htmlAttrs: { 'data-theme': 'light', lang: 'ru' },
      meta: [
        { name: 'theme-color', content: '#f2f7f4' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover' },
        {
          name: 'description',
          content: 'Цифровое Сукно — тренажёр, колхоз и турнирная сетка для русского бильярда.'
        }
      ]
    }
  },
  runtimeConfig: {
    public: {
      hubUrl: process.env.NUXT_PUBLIC_HUB_URL ?? 'http://localhost',
      brandName: process.env.NUXT_PUBLIC_BRAND_NAME || 'Цифровое Сукно',
      // Empty = same-origin /api via nginx. Standalone :3010 uses an explicit API origin.
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || ''
    }
  },
  vite: {
    server: {
      allowedHosts: true,
      hmr: process.env.NUXT_VITE_HMR_CLIENT_PORT
        ? {
            clientPort: Number(process.env.NUXT_VITE_HMR_CLIENT_PORT),
            path: `${appBase}_nuxt/`
          }
        : undefined
    }
  },
  typescript: {
    strict: true
  }
})
