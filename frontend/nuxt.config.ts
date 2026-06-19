export default defineNuxtConfig({
  devtools: { enabled: true },
  experimental: {
    // Avoid Vite pre-transform race on "#app-manifest" during dev startup (Docker/nginx).
    appManifest: false
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
    head: {
      link: [
        { rel: 'manifest', href: '/manifest.webmanifest' },
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }
      ],
      meta: [{ name: 'theme-color', content: '#0b0f10' }]
    }
  },
  runtimeConfig: {
    apiInternalUrl: process.env.NUXT_API_INTERNAL_URL || 'http://localhost:8000',
    public: {
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL ?? '',
      siteName: process.env.NUXT_PUBLIC_SITE_NAME || 'personal_me',
      brandName: process.env.NUXT_PUBLIC_BRAND_NAME || 'DAUTOVTECH',
      ownerName: process.env.NUXT_PUBLIC_OWNER_NAME || '',
      tagline:
        process.env.NUXT_PUBLIC_TAGLINE ||
        'Интерактивный командный центр: портфолио, интеграции и сервисы в одном терминале. Введите help или откройте projects.',
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL || 'http://localhost'
    }
  },
  vite: {
    server: {
      hmr: process.env.NUXT_VITE_HMR_CLIENT_PORT
        ? {
            clientPort: Number(process.env.NUXT_VITE_HMR_CLIENT_PORT),
            path: '/_nuxt/'
          }
        : undefined,
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
