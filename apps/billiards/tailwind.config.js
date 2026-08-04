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
          green: 'var(--cloth-green)',
          felt: 'var(--cloth-felt)',
          accent: 'var(--cloth-accent)',
          chalk: 'var(--cloth-chalk)',
          muted: 'var(--cloth-muted)'
        }
      },
      fontFamily: {
        display: ['Syne', 'system-ui', 'sans-serif'],
        body: ['DM Sans', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: []
}
