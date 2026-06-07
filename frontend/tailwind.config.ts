/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#9b8cff',
          500: '#6d5dfb',
          600: '#5847e8',
          700: '#4738ca',
          800: '#3730a3',
          900: '#312e81',
        },
        cyan: {
          300: '#67e8f9',
          400: '#22d3ee',
          500: '#06b6d4',
        },
        surface: {
          DEFAULT: '#070a12',
          100: '#0d1320',
          200: '#121a2b',
          300: '#182238',
          400: '#21314d',
        },
      },
      fontFamily: {
        sans: ['Inter var', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      boxShadow: {
        glass: '0 4px 24px rgba(0,0,0,0.3)',
        panel: '0 18px 60px rgba(0,0,0,0.28)',
        glow: '0 0 0 1px rgba(109,93,251,0.12), 0 24px 80px rgba(34,211,238,0.08)',
      },
    },
  },
  plugins: [],
}
