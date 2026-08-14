/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './components/**/*.{vue,js,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './app.vue'
  ],
  theme: {
    extend: {
      colors: {
        cloth: {
          deep: 'var(--cloth-deep)',
          charcoal: 'var(--cloth-charcoal)',
          card: 'var(--cloth-card)',
          green: 'var(--cloth-green)',
          felt: 'var(--cloth-felt)',
          accent: 'var(--cloth-accent)',
          success: 'var(--cloth-success)',
          danger: 'var(--cloth-danger)',
          info: 'var(--cloth-info)',
          strong: 'var(--cloth-strong)',
          chalk: 'var(--cloth-chalk)',
          muted: 'var(--cloth-muted)',
          border: 'var(--cloth-border)'
        }
      },
      fontFamily: {
        display: ['Space Grotesk', 'Inter', 'system-ui', 'sans-serif'],
        body: ['Inter', 'Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace']
      },
      borderRadius: {
        hero: 'var(--radius-hero)',
        card: 'var(--radius-card)',
        panel: 'var(--radius-panel)',
        field: 'var(--radius-field)',
        control: 'var(--radius-control)'
      },
      boxShadow: {
        glow: '0 0 24px var(--cloth-glow-accent)',
        felt: '0 10px 30px var(--cloth-shadow)'
      },
      screens: {
        '3xl': '1800px'
      }
    }
  },
  plugins: []
}
