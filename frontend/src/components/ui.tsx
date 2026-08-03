import { AnimatePresence, motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { useEffect } from 'react'
import { impactTone, initials, money, ROLE_SHORT } from '../lib/format'
import { useAuction } from '../store/auctionStore'
import type { Player } from '../types'

/* ------------------------------------------------------------------ colours */

export const FRANCHISE_COLORS: Record<string, string> = {
  CSK: '#F9CD05',
  MI: '#4A8FE7',
  RCB: '#E8404F',
  KKR: '#8B6DC4',
  DC: '#3E7BE8',
  RR: '#F158A0',
  PBKS: '#EE5A5A',
  SRH: '#F58634',
  LSG: '#31B0E8',
  GT: '#C4A661',
}

export function franchiseColor(code?: string | null): string {
  return (code && FRANCHISE_COLORS[code]) || '#64748B'
}

/* -------------------------------------------------------------- primitives */

export function Button({
  children,
  onClick,
  variant = 'primary',
  disabled,
  className = '',
  type = 'button',
}: {
  children: ReactNode
  onClick?: () => void
  variant?: 'primary' | 'ghost' | 'danger' | 'gold'
  disabled?: boolean
  className?: string
  type?: 'button' | 'submit'
}) {
  const styles = {
    primary: 'bg-indigo-500 text-white active:bg-indigo-600 disabled:bg-ink-600 disabled:text-slate-500',
    gold: 'bg-gold-400 text-onAccent active:bg-gold-500 disabled:bg-ink-600 disabled:text-slate-500',
    ghost: 'bg-ink-600 text-slate-200 active:bg-ink-500 disabled:text-slate-600',
    danger: 'bg-rose-500 text-white active:bg-rose-600 disabled:bg-ink-600 disabled:text-slate-500',
  }[variant]

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`tap rounded-2xl px-5 font-bold text-[15px] flex items-center justify-center gap-2 disabled:active:scale-100 ${styles} ${className}`}
    >
      {children}
    </button>
  )
}

export function ImpactBadge({ score, size = 'md' }: { score: number; size?: 'sm' | 'md' | 'lg' }) {
  const tone = impactTone(score)
  const dims = {
    sm: 'text-[11px] px-1.5 py-0.5 min-w-[30px]',
    md: 'text-xs px-2 py-1 min-w-[38px]',
    lg: 'text-lg px-3 py-1.5 min-w-[54px]',
  }[size]
  return (
    <span
      className={`${dims} ${tone.bg} ${tone.text} ring-1 ${tone.ring} rounded-lg font-mono font-bold text-center tabular-nums`}
    >
      {score.toFixed(0)}
    </span>
  )
}

export function Avatar({ name, size = 44 }: { name: string; size?: number }) {
  // A stable hue per name gives every player a recognisable chip without assets.
  const hue = [...name].reduce((acc, ch) => acc + ch.charCodeAt(0), 0) % 360
  return (
    <div
      className="rounded-xl grid place-items-center font-bold shrink-0"
      style={{
        width: size,
        height: size,
        fontSize: size * 0.34,
        background: `linear-gradient(140deg, hsl(${hue} 45% 32%), hsl(${(hue + 40) % 360} 45% 20%))`,
        color: `hsl(${hue} 70% 82%)`,
      }}
    >
      {initials(name)}
    </div>
  )
}

export function RoleChip({ role, overseas }: { role: string; overseas?: boolean }) {
  return (
    <span className="inline-flex items-center gap-1">
      <span className="chip bg-ink-500 text-slate-300">{ROLE_SHORT[role] ?? role}</span>
      {overseas && <span className="chip bg-sky-500/15 text-sky-300">✈</span>}
    </span>
  )
}

export function PurseBar({
  remaining,
  total = 12000,
  color = '#818CF8',
}: {
  remaining: number
  total?: number
  color?: string
}) {
  const pct = Math.max(0, Math.min(100, (remaining / total) * 100))
  return (
    <div className="h-1.5 w-full bg-ink-500 rounded-full overflow-hidden">
      <motion.div
        className="h-full rounded-full"
        style={{ background: color }}
        animate={{ width: `${pct}%` }}
        transition={{ type: 'spring', stiffness: 120, damping: 20 }}
      />
    </div>
  )
}

/* ------------------------------------------------------------ player rows */

export function PlayerRow({
  player,
  right,
  onClick,
  selected,
  subtitle,
}: {
  player: Player
  right?: ReactNode
  onClick?: () => void
  selected?: boolean
  subtitle?: ReactNode
}) {
  return (
    <button
      onClick={onClick}
      disabled={!onClick}
      className={`tap w-full flex items-center gap-3 p-3 rounded-2xl text-left transition-colors ${
        selected ? 'bg-indigo-500/15 ring-1 ring-indigo-400/40' : 'bg-ink-700'
      } ${onClick ? '' : 'active:scale-100'}`}
    >
      <Avatar name={player.name} />
      <div className="min-w-0 flex-1">
        <div className="font-semibold text-[15px] truncate">{player.name}</div>
        <div className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
          <RoleChip role={player.role} overseas={player.is_overseas} />
          {subtitle ?? <span>{money(player.base_price_lakh)}</span>}
        </div>
      </div>
      {right ?? <ImpactBadge score={player.base_impact_score} />}
    </button>
  )
}

/* ---------------------------------------------------------------- overlays */

export function BottomSheet({
  open,
  onClose,
  title,
  children,
  dismissible = true,
}: {
  open: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  dismissible?: boolean
}) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && dismissible && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose, dismissible])

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-end"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={dismissible ? onClose : undefined}
          />
          <motion.div
            className="relative w-full bg-ink-800 rounded-t-3xl max-h-[88%] flex flex-col border-t border-line/10"
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', stiffness: 320, damping: 34 }}
            // Drag-to-dismiss, the gesture people expect from a native sheet.
            drag={dismissible ? 'y' : false}
            dragConstraints={{ top: 0, bottom: 0 }}
            dragElastic={{ top: 0, bottom: 0.4 }}
            onDragEnd={(_, info) => {
              if (dismissible && info.offset.y > 110) onClose()
            }}
          >
            <div className="shrink-0 pt-2.5 pb-1 grid place-items-center">
              <div className="w-10 h-1 rounded-full bg-line/20" />
            </div>
            {title && (
              <div className="shrink-0 px-5 pb-3 text-base font-bold">{title}</div>
            )}
            <div className="overflow-y-auto px-5 above-tabbar">{children}</div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export function Toast() {
  const toast = useAuction((s) => s.toast)
  const clearToast = useAuction((s) => s.clearToast)

  useEffect(() => {
    if (!toast) return
    const id = window.setTimeout(clearToast, 2600)
    return () => window.clearTimeout(id)
  }, [toast, clearToast])

  return (
    <AnimatePresence>
      {toast && (
        <motion.div
          className="fixed left-4 right-4 z-[60] flex justify-center"
          style={{ top: 'calc(var(--safe-top) + 12px)' }}
          initial={{ opacity: 0, y: -24 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -24 }}
        >
          <div
            className={`px-4 py-2.5 rounded-2xl text-sm font-semibold shadow-xl ${
              toast.tone === 'ok' ? 'bg-emerald-500 text-white' : 'bg-rose-500 text-white'
            }`}
          >
            {toast.text}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export function EmptyState({ icon, title, hint }: { icon: string; title: string; hint?: string }) {
  return (
    <div className="py-16 text-center">
      <div className="text-4xl mb-3 opacity-60">{icon}</div>
      <div className="font-semibold text-slate-300">{title}</div>
      {hint && <div className="text-sm text-slate-500 mt-1 px-8">{hint}</div>}
    </div>
  )
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="py-16 grid place-items-center gap-3">
      <div className="w-7 h-7 rounded-full border-2 border-line/15 border-t-indigo-400 animate-spin" />
      {label && <div className="text-sm text-slate-400">{label}</div>}
    </div>
  )
}
