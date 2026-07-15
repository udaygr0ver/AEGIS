/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        siem: {
          bg: '#090d16',
          card: '#0f172a',
          cardHover: '#1e293b',
          border: '#1e293b',
          accent: '#0ea5e9',
          accentGlow: 'rgba(14, 165, 233, 0.15)',
          critical: '#ef4444',
          high: '#f97316',
          medium: '#eab308',
          low: '#3b82f6',
          textMuted: '#94a3b8'
        }
      }
    },
  },
  plugins: [],
}
