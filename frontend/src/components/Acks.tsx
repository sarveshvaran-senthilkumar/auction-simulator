import { AnimatePresence, motion } from 'framer-motion'
import { useEffect } from 'react'
import { useAuction } from '../store/auctionStore'
import type { Ack } from '../types'
import { franchiseColor } from './ui'

const TONES: Record<Ack['tone'], { icon: string; ring: string; bg: string; text: string }> = {
  lead: { icon: '🔨', ring: 'ring-emerald-400/40', bg: 'bg-emerald-500/15', text: 'text-emerald-300' },
  outbid: { icon: '⚡', ring: 'ring-amber-400/40', bg: 'bg-amber-500/15', text: 'text-amber-300' },
  won: { icon: '🎉', ring: 'ring-gold-400/50', bg: 'bg-gold-400/15', text: 'text-gold-400' },
  lost: { icon: '💔', ring: 'ring-rose-400/40', bg: 'bg-rose-500/15', text: 'text-rose-300' },
  info: { icon: 'ℹ️', ring: 'ring-line/20', bg: 'bg-ink-600', text: 'text-slate-300' },
}

// "Won" is worth reading properly; the rest are glanceable.
const DWELL: Record<Ack['tone'], number> = {
  lead: 2600,
  outbid: 3000,
  won: 4200,
  lost: 3000,
  info: 3000,
}

/** Stacked acknowledgement banners, in the notification slot below the header. */
export function Acks() {
  const acks = useAuction((s) => s.acks)

  return (
    <div className="fixed left-3 right-3 z-40 pointer-events-none space-y-2"
         style={{ top: 'calc(var(--safe-top) + 78px)' }}>
      <AnimatePresence initial={false}>
        {acks.map((ack) => (
          <AckCard key={ack.id} ack={ack} />
        ))}
      </AnimatePresence>
    </div>
  )
}

function AckCard({ ack }: { ack: Ack }) {
  const dismissAck = useAuction((s) => s.dismissAck)
  const tone = TONES[ack.tone]

  useEffect(() => {
    const id = window.setTimeout(() => dismissAck(ack.id), DWELL[ack.tone])
    return () => window.clearTimeout(id)
  }, [ack.id, ack.tone, dismissAck])

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -14, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.18 } }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      onClick={() => dismissAck(ack.id)}
      className={`pointer-events-auto flex items-center gap-3 px-3.5 py-2.5 rounded-2xl ring-1 backdrop-blur-md shadow-lg ${tone.bg} ${tone.ring} bg-ink-800/90`}
    >
      <span className="text-lg leading-none shrink-0">{tone.icon}</span>
      <div className="min-w-0 flex-1">
        <div className={`text-sm font-bold truncate ${tone.text}`}>{ack.title}</div>
        {ack.detail && (
          <div className="text-[11px] text-slate-400 truncate">{ack.detail}</div>
        )}
      </div>
      {ack.franchise && (
        <span
          className="text-[10px] font-black shrink-0"
          style={{ color: franchiseColor(ack.franchise) }}
        >
          {ack.franchise}
        </span>
      )}
    </motion.div>
  )
}
