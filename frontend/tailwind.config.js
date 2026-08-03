/** @type {import('tailwindcss').Config} */

// Every palette colour resolves through a CSS variable so the light/dark toggle
// is a single `data-theme` swap on <html> rather than a `dark:` variant on every
// element. The `<alpha-value>` placeholder keeps Tailwind's `/50` opacity syntax
// working against the variables.
const v = (name) => `rgb(var(--${name}) / <alpha-value>)`

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          900: v('ink-900'),
          800: v('ink-800'),
          700: v('ink-700'),
          600: v('ink-600'),
          500: v('ink-500'),
        },
        // The text ramp inverts between themes: slate-100 is the brightest text
        // in dark mode and the darkest in light mode, so existing classes hold
        // their meaning ("most prominent") instead of their literal colour.
        slate: {
          100: v('slate-100'),
          200: v('slate-200'),
          300: v('slate-300'),
          400: v('slate-400'),
          500: v('slate-500'),
          600: v('slate-600'),
        },
        gold: {
          400: v('gold-400'),
          500: v('gold-500'),
        },
        // Hairlines and dividers — white-ish on dark, ink-ish on light.
        line: v('line'),
        // Text that sits on a gold/accent fill. Stays dark in both themes.
        onAccent: v('on-accent'),
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      animation: {
        'slide-up': 'slide-up 0.28s cubic-bezier(0.16, 1, 0.3, 1)',
        pop: 'pop 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
      },
      keyframes: {
        'slide-up': {
          from: { transform: 'translateY(100%)' },
          to: { transform: 'translateY(0)' },
        },
        pop: {
          '0%': { transform: 'scale(0.85)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
