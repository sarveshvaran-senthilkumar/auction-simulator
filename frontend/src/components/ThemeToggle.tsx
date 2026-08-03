import { motion } from 'framer-motion'
import { haptic } from '../lib/format'
import { useAuth } from '../store/authStore'

/** Sun/moon switch. Small enough for a header, still a 44px touch target. */
export function ThemeToggle({ className = '' }: { className?: string }) {
  const theme = useAuth((s) => s.theme)
  const toggleTheme = useAuth((s) => s.toggleTheme)
  const isDark = theme === 'dark'

  return (
    <button
      onClick={() => {
        haptic(10)
        toggleTheme()
      }}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      className={`tap w-11 h-11 grid place-items-center rounded-xl bg-ink-600 active:bg-ink-500 ${className}`}
    >
      <motion.span
        key={theme}
        initial={{ rotate: -60, opacity: 0, scale: 0.6 }}
        animate={{ rotate: 0, opacity: 1, scale: 1 }}
        transition={{ type: 'spring', stiffness: 320, damping: 20 }}
        className="text-lg leading-none"
      >
        {isDark ? '🌙' : '☀️'}
      </motion.span>
    </button>
  )
}
