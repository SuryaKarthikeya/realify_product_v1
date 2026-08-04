/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        serif: ['Inter', 'sans-serif'],
        mono: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(16, 24, 40, 0.04), 0 1px 3px rgba(16, 24, 40, 0.03)',
      },
      colors: {
        ws: {
          page:    '#F6F7F8',
          card:    '#FFFFFF',
          line:    '#E9EBEE',
          hair:    '#EFF1F3',
          rule:    '#D7DCE2',
          ink:     '#0F1115',
          body:    '#374151',
          muted:   '#5D6470',
          faint:   '#6B7280',
          pill:    '#F3F4F6',
          black:   '#111318',
        },
        // ── Brand palette — edit CSS vars in src/index.css to retheme the whole app ──
        brand: 'rgb(var(--color-brand) / <alpha-value>)',
        'brand-hover': 'rgb(var(--color-brand-hover) / <alpha-value>)',
        'brand-subtle': 'rgb(var(--color-brand-subtle) / <alpha-value>)',
        // ── Cobalt-blue accent palette — edit CSS vars in src/index.css ──
        'cb-200': 'rgb(var(--cb-200) / <alpha-value>)',
        'cb-300': 'rgb(var(--cb-300) / <alpha-value>)',
        'cb-400': 'rgb(var(--cb-400) / <alpha-value>)',
        'cb-500': 'rgb(var(--cb-500) / <alpha-value>)',
        'cb-600': 'rgb(var(--cb-600) / <alpha-value>)',
        'cb-700': 'rgb(var(--cb-700) / <alpha-value>)',
        'cb-800': 'rgb(var(--cb-800) / <alpha-value>)',
        'cb-850': 'rgb(var(--cb-850) / <alpha-value>)',
        'cb-900': 'rgb(var(--cb-900) / <alpha-value>)',
      },
    },
  },
  plugins: [],
}