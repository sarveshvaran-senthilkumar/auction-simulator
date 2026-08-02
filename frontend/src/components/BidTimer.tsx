import { motion } from 'framer-motion'

/** Circular countdown. Turns amber then red as the hammer approaches. */
export function BidTimer({ seconds, active }: { seconds: number; active: boolean }) {
  const size = 52
  const stroke = 4
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius

  // The window is 12s on a fresh lot and 7s after a bid, so normalise on 12.
  const pct = Math.max(0, Math.min(1, seconds / 12))
  const color = !active ? '#475569' : seconds <= 3 ? '#F43F5E' : seconds <= 6 ? '#FBBF24' : '#818CF8'

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#22304F"
          strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          animate={{ strokeDashoffset: circumference * (1 - pct) }}
          transition={{ duration: 0.4, ease: 'linear' }}
        />
      </svg>
      <motion.div
        className="absolute inset-0 grid place-items-center font-black tabular-nums text-lg"
        style={{ color }}
        animate={active && seconds <= 3 ? { scale: [1, 1.16, 1] } : { scale: 1 }}
        transition={{ duration: 0.5, repeat: active && seconds <= 3 ? Infinity : 0 }}
      >
        {active ? seconds : '—'}
      </motion.div>
    </div>
  )
}
