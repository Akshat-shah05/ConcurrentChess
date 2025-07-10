/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'chess-dark': '#2c3e50',
        'chess-light': '#ecf0f1',
        'chess-board-dark': '#b58863',
        'chess-board-light': '#f0d9b5',
        'chess-highlight': '#7b61ff',
        'chess-move': '#7b61ff',
        'chess-capture': '#ff6b6b',
      },
      fontFamily: {
        'chess': ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} 