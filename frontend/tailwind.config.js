/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Warm, earthy palette - feels human-made
        surface: {
          50: '#fdfcfb',
          100: '#f8f6f3',
          200: '#f0ece6',
          300: '#e4ddd3',
          400: '#c9c0b3',
          500: '#a89d8e',
          600: '#8a7e6e',
          700: '#6b5f50',
          800: '#4a4035',
          900: '#2d2520',
        },
        // Olive green - primary (organic, trustworthy)
        sage: {
          50: '#f4f7f4',
          100: '#e5ede5',
          200: '#c9d9c9',
          300: '#a3bfa3',
          400: '#7da37d',
          500: '#5a8a5a',
          600: '#476e47',
          700: '#3a5a3a',
          800: '#2f482f',
          900: '#253b25',
        },
        // Warm amber for warnings
        amber: {
          50: '#fef9ee',
          100: '#fdf0d3',
          200: '#fadda5',
          300: '#f7c56d',
          400: '#f4a832',
          500: '#f19115',
          600: '#e2720b',
          700: '#bb540b',
          800: '#954210',
          900: '#793710',
        },
        // Muted red for alerts
        rose: {
          50: '#fef2f2',
          100: '#ffe1e1',
          200: '#ffc8c8',
          300: '#fea3a3',
          400: '#fb6e6e',
          500: '#f43f3f',
          600: '#e12020',
          700: '#bd1616',
          800: '#9c1616',
          900: '#811919',
        },
      },
      fontFamily: {
        sans: ['"Source Sans 3"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)',
        'card-hover': '0 4px 12px 0 rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.04)',
        'soft': '0 2px 8px -2px rgb(0 0 0 / 0.06)',
      },
    },
  },
  plugins: [],
}
