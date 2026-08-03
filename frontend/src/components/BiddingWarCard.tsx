import { AnimatePresence, motion } from 'framer-motion'
import { useEffect } from 'react'
import { money, moneyShort } from '../lib/format'
import { useAuction } from '../store/auctionStore'
import { franchiseColor } from './ui'

/** Heads-up card when two franchises lock horns over one player.
 *
 *  Deliberately shaped like an OS notification — it slides in from the top,
 *  shows the two sides face to face, and clears itself.
 */
export function BiddingWarCard() {
  const war = useAuction((s) => s.war)
  const dismissWar = useAuction((s) => s.dismissWar)
  const teamId = useAuction((s) => s.teamId)

  useEffect(() => {
    if (!war) return
    const id = window.setTimeout(dismissWar, 6000)
    return () => window.clearTimeout(id)
  }, [war, dismissWar])

  return (
    <AnimatePresence>
      {war && (
        <motion.div
          key={`${war.player.id}-${war.bids}`}
          initial={{ opacity: 0, y: -30, scale: 0.94 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.96 }}
          transition={{ type: 'spring', stiffness: 340, damping: 28 }}
          drag="y"
          dragConstraints={{ top: 0, bottom: 0 }}
          dragElastic={{ top: 0.5, bottom: 0 }}
          onDragEnd={(_, info) => info.offset.y < -40 && dismissWar()}
          onClick={dismissWar}
          className="fixed left-3 right-3 z-40 rounded-2xl bg-ink-800/95 backdrop-blur-md ring-1 ring-line/15 shadow-2xl overflow-hidden"
          style={{ top: 'calc(var(--safe-top) + 78px)' }}
        >
          <div className="px-3.5 pt-3 pb-2 flex items-center gap-2">
            <span className="text-base leading-none">🔥</span>
            <span className="text-[11px] font-black uppercase tracking-wider text-amber-400">
              Bidding war
            </span>
            <span className="ml-auto text-[11px] text-slate-500 tabular-nums">
              {war.bids} bids · from {moneyShort(war.opened_at_lakh)}
            </span>
          </div>

          <div className="px-3.5 pb-1 text-sm font-bold truncate">{war.player.name}</div>
          <div className="px-3.5 pb-2.5 text-lg font-black tabular-nums text-gold-400">
            {money(war.price_lakh)}
          </div>

          <div className="grid grid-cols-2 gap-px bg-line/10">
            {war.teams.map((team) => {
              const accent = franchiseColor(team.franchise_code)
              const leading = team.id === war.leading_team_id
              const isMe = team.id === teamId
              return (
                <div key={team.id} className="bg-ink-800 px-3.5 py-2.5">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[13px] font-black" style={{ color: accent }}>
                      {team.franchise_code}
                    </span>
                    {isMe && <span className="text-[9px] text-emerald-400 font-bold">YOU</span>}
                    {leading && (
                      <span className="ml-auto text-[9px] font-black text-emerald-400">
                        LEADING
                      </span>
                    )}
                  </div>
                  <div className="mt-1.5 space-y-0.5 text-[11px] text-slate-400 tabular-nums">
                    <Row label="Purse" value={moneyShort(team.purse_remaining_lakh)} />
                    <Row label="Squad" value={`${team.squad_size}/25`} />
                    <Row label="Overseas" value={`${team.overseas_used}/8`} />
                    <Row label="RTM" value={String(team.rtm_cards)} />
                  </div>
                </div>
              )
            })}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2">
      <span className="text-slate-500">{label}</span>
      <span className="font-semibold text-slate-300">{value}</span>
    </div>
  )
}
