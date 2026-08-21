/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0A0A0F',
        surface: {
          DEFAULT: '#12141A',
          hover: '#181B22',
          card: '#151821',
          border: '#232733',
        },
        brand: {
          blue: '#4F46E5',
          indigo: '#6366F1',
          purple: '#8B5CF6',
          cyan: '#06B6D4',
        },
        priority: {
          critical: '#EF4444',
          high: '#F59E0B',
          medium: '#3B82F6',
          low: '#10B981',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Outfit', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
