import { useEffect, useState } from 'react'
import { Avatar, EmptyState, franchiseColor, PurseBar } from '../components/ui'
import { api } from '../lib/api'
import { money } from '../lib/format'
import { useAuction } from '../store/auctionStore'
import type { RosterItem } from '../types'

const ROLE_ORDER = ['Batter', 'All-Rounder', 'Wicket-Keeper', 'Bowler']

export default function MySquad() {
  const room = useAuction((s) => s.room)
  const roomCode = useAuction((s) => s.roomCode)
  const teamId = useAuction((s) => s.teamId)
  const [roster, setRoster] = useState<RosterItem[]>([])

  const myTeam = room?.teams.find((t) => t.id === teamId)
  const accent = franchiseColor(myTeam?.franchise_code)

  // The socket carries counters, not the roster itself, so poll for the list.
  useEffect(() => {
    if (!roomCode || !teamId) return
    const load = () =>
      api
        .results(roomCode)
        .then((data) => {
          const mine = data.teams.find((t: any) => t.id === teamId)
          if (mine) setRoster(mine.roster)
        })
        .catch(() => {})
    load()
    const id = window.setInterval(load, 5000)
    return () => window.clearInterval(id)
  }, [roomCode, teamId, myTeam?.squad_size])

  const grouped = ROLE_ORDER.map((role) => ({
    role,
    players: roster.filter((p) => p.role === role).sort((a, b) => b.price_lakh - a.price_lakh),
  })).filter((g) => g.players.length > 0)

  const spent = 12000 - (myTeam?.purse_remaining_lakh ?? 12000)

  return (
    <>
      <header className="app-header px-5 pb-4">
        <div className="pt-3 flex items-center gap-3">
          <div
            className="w-11 h-11 rounded-xl grid place-items-center font-black text-sm"
            style={{ background: accent, color: '#0B1120' }}
          >
            {myTeam?.franchise_code}
          </div>
          <div className="flex-1">
            <div className="text-lg font-bold">My Squad</div>
            <div className="text-xs text-slate-500">
              {myTeam?.squad_size ?? 0} of 25 · {myTeam?.overseas_used ?? 0}/8 overseas
            </div>
          </div>
          <div className="text-right">
            <div className="text-lg font-black tabular-nums">
              {money(myTeam?.purse_remaining_lakh ?? 0)}
            </div>
            <div className="text-[10px] text-slate-500">left of ₹120 Cr</div>
          </div>
        </div>
        <div className="mt-3">
          <PurseBar remaining={myTeam?.purse_remaining_lakh ?? 0} color={accent} />
        </div>
        <div className="flex justify-between text-[11px] text-slate-500 mt-1.5">
          <span>Spent {money(spent)}</span>
          <span className="text-gold-400 font-semibold">{myTeam?.rtm_cards ?? 0} RTM left</span>
        </div>
      </header>

      <div className="app-scroll px-5 pt-4 pb-6">
        {roster.length === 0 ? (
          <EmptyState
            icon="👥"
            title="No players yet"
            hint="Retentions and winning bids land here."
          />
        ) : (
          grouped.map((group) => (
            <div key={group.role} className="mb-5">
              <div className="flex items-center justify-between mb-2 px-1">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  {group.role}
                </h3>
                <span className="text-xs text-slate-600">{group.players.length}</span>
              </div>
              <div className="space-y-1.5">
                {group.players.map((p) => (
                  <div
                    key={p.player_id}
                    className="flex items-center gap-3 bg-ink-700 rounded-2xl p-2.5"
                  >
                    <Avatar name={p.name} size={38} />
                    <div className="min-w-0 flex-1">
                      <div className="font-semibold text-sm truncate">{p.name}</div>
                      <div className="mt-0.5">
                        <span
                          className={`chip text-[10px] ${
                            p.acquisition_type === 'RETENTION'
                              ? 'bg-emerald-500/15 text-emerald-300'
                              : p.acquisition_type === 'RTM'
                                ? 'bg-gold-400/15 text-gold-400'
                                : 'bg-ink-500 text-slate-400'
                          }`}
                        >
                          {p.acquisition_type}
                        </span>
                        {p.is_overseas && (
                          <span className="chip bg-sky-500/15 text-sky-300 text-[10px] ml-1">✈</span>
                        )}
                      </div>
                    </div>
                    <div className="text-sm font-bold tabular-nums shrink-0">
                      {money(p.price_lakh)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </>
  )
}
