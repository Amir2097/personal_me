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
          deep: '#0c1412',
          green: '#1a4d3a',
          felt: '#0f3d2e',
          accent: '#c8a45c',
          chalk: '#e8f0ea',
          muted: '#6b8578'
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
