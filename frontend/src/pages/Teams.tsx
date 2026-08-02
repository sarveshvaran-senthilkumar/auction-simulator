import { motion } from 'framer-motion'
import { franchiseColor, PurseBar } from '../components/ui'
import { money, ROLE_SHORT } from '../lib/format'
import { useAuction } from '../store/auctionStore'

export default function Teams() {
  const room = useAuction((s) => s.room)
  const teamId = useAuction((s) => s.teamId)
  const franchises = useAuction((s) => s.franchises)

  const teams = [...(room?.teams ?? [])].sort(
    (a, b) => b.squad_size - a.squad_size || b.purse_remaining_lakh - a.purse_remaining_lakh,
  )

  return (
    <>
      <header className="app-header px-5 pb-3">
        <div className="pt-3">
          <div className="text-lg font-bold">All Franchises</div>
          <div className="text-xs text-slate-500">
            {room?.lots_done ?? 0} of {room?.total_lots ?? 0} lots done
          </div>
        </div>
      </header>

      <div className="app-scroll px-5 pt-4 pb-6 space-y-2.5">
        {teams.map((team, i) => {
          const accent = franchiseColor(team.franchise_code)
          const isMe = team.id === teamId
          const info = franchises.find((f) => f.code === team.franchise_code)

          return (
            <motion.div
              key={team.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.02 }}
              className={`rounded-2xl p-3.5 border ${
                isMe ? 'border-white/20 bg-ink-600' : 'border-white/5 bg-ink-700'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-xl grid place-items-center font-black text-xs shrink-0"
                  style={{ background: accent, color: '#0B1120' }}
                >
                  {team.franchise_code}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-bold text-sm truncate">
                    {info?.name ?? team.franchise_code}
                    {isMe && <span className="text-emerald-400 font-normal text-xs ml-1.5">you</span>}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {team.is_ai ? 'AI managed' : team.connected ? 'Human · online' : 'Human · away'}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-sm font-black tabular-nums">
                    {money(team.purse_remaining_lakh)}
                  </div>
                  <div className="text-[10px] text-slate-500 tabular-nums">
                    {team.squad_size} players
                  </div>
                </div>
              </div>

              <div className="mt-2.5">
                <PurseBar remaining={team.purse_remaining_lakh} color={accent} />
              </div>

              <div className="flex items-center gap-1.5 mt-2.5 flex-wrap">
                {Object.entries(team.role_counts).map(([role, count]) => (
                  <span key={role} className="chip bg-ink-500 text-slate-400 text-[10px]">
                    {ROLE_SHORT[role] ?? role} {count}
                  </span>
                ))}
                <span className="chip bg-sky-500/15 text-sky-300 text-[10px]">
                  ✈ {team.overseas_used}/8
                </span>
                {team.rtm_cards > 0 && (
                  <span className="chip bg-gold-400/15 text-gold-400 text-[10px]">
                    {team.rtm_cards} RTM
                  </span>
                )}
              </div>
            </motion.div>
          )
        })}
      </div>
    </>
  )
}
