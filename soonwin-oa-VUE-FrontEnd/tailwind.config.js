/** @type {import('tailwindcss').Config} */
/**
 * Tailwind CSS 配置
 * ⚠️ 注意：本项目使用 Element Plus，必须关闭 preflight 避免冲突！
 * ⚠️ 核心布局用 scoped CSS，勿依赖 Tailwind 工具类（可能在 Vite 中不可靠）
 * 详见: [[tailwind-element-plus-conflict]]
 */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  corePlugins: {
    preflight: false, // 必须关闭！否则 Element Plus 样式全乱
  },
  plugins: [],
}
