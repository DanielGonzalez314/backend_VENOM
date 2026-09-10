/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // Esto le dice a Tailwind que busque en TODAS las carpetas de src
  ],
  theme: {
    extend: {
      colors: {
        'venom-purple': '#6d28d9',
        'venom-black': '#0a0a0a',
      }
    },
  },
  plugins: [],
}