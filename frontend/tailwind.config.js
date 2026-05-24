/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: '#5b8af0',
        secondary: '#8b7cf8',
      },
    },
  },
  plugins: [],
};