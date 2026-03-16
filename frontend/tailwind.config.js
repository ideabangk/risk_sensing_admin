/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        blue: {
          50:  '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3182F6',
          600: '#3182F6',
          700: '#1D6EF5',
          800: '#1558D6',
          900: '#1044B2',
        },
      },
    },
  },
  plugins: [],
}
