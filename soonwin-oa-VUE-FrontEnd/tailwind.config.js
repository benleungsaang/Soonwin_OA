/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  // 关键：关闭 Preflight CSS 重置，避免与 Element Plus 冲突
  corePlugins: {
    preflight: false,
  },
  plugins: [],
}
