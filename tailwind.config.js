/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{vue,ts,html}'],
  theme: {
    extend: {
      colors: {
        accent: '#6366f1',
        'accent-hover': '#4f46e5',
        sidebar: '#f8fafc',
        chat: '#ffffff',
        danger: '#f87171',
        'danger-hover': '#ef4444',
      },
      spacing: {
        titlebar: '36px',
        sidebar: '260px',
      },
      borderRadius: {
        bubble: '14px',
      },
      fontSize: {
        xs: '12px',
        sm: '13px',
        base: '14px',
        md: '15px',
        lg: '18px',
        xl: '24px',
      },
    },
  },
  plugins: [],
}
