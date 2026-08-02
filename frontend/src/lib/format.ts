/** Money in this app is always lakh on the wire; the UI speaks crore. */
export function money(lakh: number | null | undefined): string {
  if (lakh === null || lakh === undefined) return '—'
  if (lakh >= 100) {
    const cr = lakh / 100
    return `₹${cr % 1 === 0 ? cr.toFixed(0) : cr.toFixed(2)} Cr`
  }
  return `₹${lakh} L`
}

/** Compact form for tight spots like team rails. */
export function moneyShort(lakh: number | null | undefined): string {
  if (lakh === null || lakh === undefined) return '—'
  if (lakh >= 100) return `${(lakh / 100).toFixed(1)}cr`
  return `${lakh}L`
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

export const ROLE_SHORT: Record<string, string> = {
  Batter: 'BAT',
  Bowler: 'BOWL',
  'All-Rounder': 'AR',
  'Wicket-Keeper': 'WK',
}

/** Impact bands drive badge colour everywhere, so they live in one place. */
export function impactTone(score: number): {
  text: string
  bg: string
  ring: string
  label: string
} {
  if (score >= 72) return { text: 'text-emerald-300', bg: 'bg-emerald-500/15', ring: 'ring-emerald-400/30', label: 'Elite' }
  if (score >= 62) return { text: 'text-lime-300', bg: 'bg-lime-500/15', ring: 'ring-lime-400/30', label: 'Strong' }
  if (score >= 52) return { text: 'text-amber-300', bg: 'bg-amber-500/15', ring: 'ring-amber-400/30', label: 'Solid' }
  if (score >= 42) return { text: 'text-orange-300', bg: 'bg-orange-500/15', ring: 'ring-orange-400/30', label: 'Fringe' }
  return { text: 'text-rose-300', bg: 'bg-rose-500/15', ring: 'ring-rose-400/30', label: 'Punt' }
}

/** A short vibration on important beats. Silently absent on iOS Safari. */
export function haptic(pattern: number | number[] = 12): void {
  if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
    try {
      navigator.vibrate(pattern)
    } catch {
      /* ignore */
    }
  }
}
