import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Avatar, Button, franchiseColor, Spinner } from '../components/ui'
import { api } from '../lib/api'
import { money } from '../lib/format'
import { useAuction } from '../store/auctionStore'
import type { TeamResult } from '../types'

export default function Results() {
  const navigate = useNavigate()
  const roomCode = useAuction((s) => s.roomCode)
  const teamId = useAuction((s) => s.teamId)
  const stored = useAuction((s) => s.results)
  const reset = useAuction((s) => s.reset)
  const [teams, setTeams] = useState<TeamResult[] | null>(stored)
  const [expanded, setExpanded] = useState<string | null>(teamId)

  useEffect(() => {
    if (teams || !roomCode) return
    api
      .results(roomCode)
      .then((data) => setTeams(data.teams))
      .catch(() => {})
  }, [teams, roomCode])

  if (!teams) {
    return (
      <div className="app-scroll">
        <Spinner label="Tallying up…" />
      </div>
    )
  }

  const ranked = [...teams].sort((a, b) => b.squad_impact - a.squad_impact)
  const myRank = ranked.findIndex((t) => t.id === teamId) + 1
  const allBuys = teams.flatMap((t) =>
    t.roster.filter((p) => p.acquisition_type !== 'RETENTION').map((p) => ({ ...p, team: t.franchise_code })),
  )
  const priciest = [...allBuys].sort((a, b) => b.price_lakh - a.price_lakh).slice(0, 5)

  return (
    <>
      <header className="app-header px-5 pb-4">
        <div className="pt-3 text-center">
          <div className="text-3xl mb-1">🏆</div>
          <div className="text-xl font-black">Auction Complete</div>
          {myRank > 0 && (
            <div className="text-sm text-slate-400 mt-1">
              You finished <span className="font-bold text-gold-400">#{myRank}</span> by squad strength
            </div>
          )}
        </div>
      </header>

      <div className="app-scroll px-5 pt-4 pb-6">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2.5">
          Squad strength
        </h3>
        <div className="space-y-2 mb-7">
          {ranked.map((team, i) => {
            const accent = franchiseColor(team.franchise_code)
            const isMe = team.id === teamId
            const isOpen = expanded === team.id
            const maxImpact = ranked[0].squad_impact || 1

            return (
              <motion.div
                key={team.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className={`rounded-2xl overflow-hidden border ${
                  isMe ? 'border-line/20' : 'border-line/5'
                }`}
              >
                <button
                  onClick={() => setExpanded(isOpen ? null : team.id)}
                  className="w-full p-3 flex items-center gap-3 bg-ink-700 text-left"
                >
                  <span className="w-5 text-center font-black text-slate-600 text-sm">{i + 1}</span>
                  <div
                    className="w-9 h-9 rounded-xl grid place-items-center font-black text-[11px] shrink-0"
                    style={{ background: accent, color: '#0B1120' }}
                  >
                    {team.franchise_code}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-bold">
                        {team.franchise_code}
                        {isMe && <span className="text-emerald-400 text-xs ml-1.5">you</span>}
                      </span>
                      <span className="tabular-nums font-bold">{team.squad_impact.toFixed(0)}</span>
                    </div>
                    <div className="h-1 bg-ink-500 rounded-full mt-1.5 overflow-hidden">
                      <motion.div
                        className="h-full rounded-full"
                        style={{ background: accent }}
                        initial={{ width: 0 }}
                        animate={{ width: `${(team.squad_impact / maxImpact) * 100}%` }}
                        transition={{ delay: 0.15 + i * 0.04, duration: 0.5 }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-500 mt-1 tabular-nums">
                      <span>
                        {team.squad_size} players · avg {team.avg_impact.toFixed(0)}
                      </span>
                      <span>spent {money(team.spent_lakh)}</span>
                    </div>
                  </div>
                </button>

                {isOpen && (
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: 'auto' }}
                    className="bg-ink-800 overflow-hidden"
                  >
                    <div className="p-3 space-y-1.5">
                      {[...team.roster]
                        .sort((a, b) => b.price_lakh - a.price_lakh)
                        .map((p) => (
                          <div key={p.player_id} className="flex items-center gap-2.5">
                            <Avatar name={p.name} size={30} />
                            <div className="min-w-0 flex-1">
                              <div className="text-xs font-semibold truncate">{p.name}</div>
                              <div className="text-[10px] text-slate-500">
                                {p.role}
                                {p.acquisition_type !== 'AUCTION' && ` · ${p.acquisition_type}`}
                              </div>
                            </div>
                            <span className="text-xs font-bold tabular-nums shrink-0">
                              {money(p.price_lakh)}
                            </span>
                          </div>
                        ))}
                      {team.roster.length === 0 && (
                        <div className="text-xs text-slate-500 py-2">No players.</div>
                      )}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )
          })}
        </div>

        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2.5">
          Biggest buys
        </h3>
        <div className="space-y-1.5 mb-8">
          {priciest.map((p, i) => (
            <div key={p.player_id} className="flex items-center gap-3 bg-ink-700 rounded-2xl p-2.5">
              <span className="w-4 text-center font-black text-slate-600 text-xs">{i + 1}</span>
              <Avatar name={p.name} size={34} />
              <div className="min-w-0 flex-1">
                <div className="text-sm font-semibold truncate">{p.name}</div>
                <div className="text-[10px] text-slate-500">
                  {p.team}
                  {p.acquisition_type === 'RTM' && ' · RTM'}
                </div>
              </div>
              <span className="text-sm font-black tabular-nums" style={{ color: franchiseColor(p.team) }}>
                {money(p.price_lakh)}
              </span>
            </div>
          ))}
        </div>

        <Button
          variant="gold"
          className="w-full h-14 mb-3"
          onClick={() => {
            reset()
            navigate('/', { replace: true })
          }}
        >
          New Auction
        </Button>
      </div>
    </>
  )
}
