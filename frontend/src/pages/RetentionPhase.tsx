import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useMemo, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import type { SocketContext } from '../RoomGate'
import {
  BottomSheet,
  Button,
  franchiseColor,
  ImpactBadge,
  PlayerRow,
  PurseBar,
  Spinner,
} from '../components/ui'
import { api } from '../lib/api'
import { haptic, money } from '../lib/format'
import { useAuction } from '../store/auctionStore'
import type { Impact, Player } from '../types'

/** Slab costs, mirroring the backend's RetentionSlabRules. */
const CAPPED_SLABS = [1800, 1400, 1100, 1800, 1400]
const UNCAPPED_COST = 400
const MAX_CAPPED = 5
const MAX_UNCAPPED = 2
const MAX_TOTAL = 6

interface PoolPlayer extends Player {
  impact: Impact
}

export default function RetentionPhase() {
  const socket = useOutletContext<SocketContext>()
  const { roomCode, teamId, franchiseCode } = useAuction()
  const room = useAuction((s) => s.room)
  const showToast = useAuction((s) => s.showToast)

  const [pool, setPool] = useState<PoolPlayer[]>([])
  const [purse, setPurse] = useState(12000)
  const [venue, setVenue] = useState<{ ground_name: string; pitch_tendency: string | null } | null>(null)
  const [picked, setPicked] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [detail, setDetail] = useState<PoolPlayer | null>(null)
  const [submitted, setSubmitted] = useState(false)

  const myTeam = room?.teams.find((t) => t.id === teamId)
  const secondsLeft = room?.retention_seconds_remaining ?? 0

  useEffect(() => {
    if (!roomCode || !teamId) return
    api
      .retentionPool(roomCode, teamId)
      .then((data) => {
        setPool(data.players)
        setPurse(data.purse_lakh)
        setVenue(data.venue)
      })
      .catch((err) => showToast(err.message))
      .finally(() => setLoading(false))
  }, [roomCode, teamId, showToast])

  // Costs depend on pick order: the first capped player always takes the 18cr slab.
  const priced = useMemo(() => {
    let cappedSeen = 0
    return picked.map((id) => {
      const player = pool.find((p) => p.id === id)!
      if (player?.is_capped) {
        cappedSeen += 1
        return { player, cost: CAPPED_SLABS[cappedSeen - 1] ?? 0, slot: cappedSeen }
      }
      return { player, cost: UNCAPPED_COST, slot: null }
    })
  }, [picked, pool])

  const totalCost = priced.reduce((sum, p) => sum + p.cost, 0)
  const cappedCount = priced.filter((p) => p.player?.is_capped).length
  const uncappedCount = priced.length - cappedCount
  const remaining = purse - totalCost
  const rtmCards = MAX_TOTAL - picked.length

  function toggle(player: PoolPlayer) {
    haptic(10)
    if (picked.includes(player.id)) {
      setPicked(picked.filter((id) => id !== player.id))
      return
    }
    if (picked.length >= MAX_TOTAL) return showToast(`Maximum ${MAX_TOTAL} retentions`)
    if (player.is_capped && cappedCount >= MAX_CAPPED) return showToast('Maximum 5 capped')
    if (!player.is_capped && uncappedCount >= MAX_UNCAPPED) return showToast('Maximum 2 uncapped')

    const nextCost = player.is_capped ? CAPPED_SLABS[cappedCount] : UNCAPPED_COST
    if (nextCost > remaining) return showToast('Not enough purse for that slab')

    setPicked([...picked, player.id])
  }

  function confirm() {
    socket.confirmRetention(picked)
    setSubmitted(true)
    setConfirmOpen(false)
    haptic([25, 50, 25])
  }

  const accent = franchiseColor(franchiseCode)
  const confirmedCount = room?.teams.filter((t) => t.retention_confirmed).length ?? 0

  if (loading) {
    return (
      <div className="app-scroll">
        <Spinner label="Loading your 2024 squad…" />
      </div>
    )
  }

  if (submitted || myTeam?.retention_confirmed) {
    return (
      <div className="app-scroll grid place-items-center px-8">
        <div className="text-center">
          <motion.div
            initial={{ scale: 0.7, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-5xl mb-4"
          >
            🔒
          </motion.div>
          <div className="text-xl font-bold mb-2">Retentions locked</div>
          <p className="text-slate-400 text-sm mb-6">
            Waiting for the other franchises to finish.
          </p>
          <div className="text-3xl font-black tabular-nums" style={{ color: accent }}>
            {confirmedCount}/10
          </div>
          <div className="text-xs text-slate-500 mt-1">teams confirmed</div>
          {secondsLeft > 0 && (
            <div className="mt-6 text-sm text-slate-500">
              Auto-completing in {secondsLeft}s
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <>
      <header className="app-header px-5 pb-3">
        <div className="flex items-center justify-between pt-3">
          <div>
            <div className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">
              Retention
            </div>
            <div className="text-xl font-black" style={{ color: accent }}>
              {franchiseCode}
            </div>
          </div>
          <div className="text-right">
            <div className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">
              Purse left
            </div>
            <div
              className={`text-xl font-black tabular-nums ${
                remaining < 2000 ? 'text-amber-400' : 'text-slate-100'
              }`}
            >
              {money(remaining)}
            </div>
          </div>
        </div>
        <div className="mt-2">
          <PurseBar remaining={remaining} color={accent} />
        </div>

        {/* Slot rail: shows exactly what each additional pick will cost. */}
        <div className="flex gap-1.5 mt-3">
          {Array.from({ length: MAX_TOTAL }).map((_, i) => {
            const entry = priced[i]
            const nextCappedCost = CAPPED_SLABS[cappedCount] ?? 0
            return (
              <div
                key={i}
                className={`flex-1 rounded-lg py-1.5 text-center border ${
                  entry
                    ? 'border-transparent'
                    : 'border-dashed border-white/15 bg-transparent'
                }`}
                style={entry ? { background: `${accent}26` } : undefined}
              >
                <div className="text-[9px] uppercase tracking-wide text-slate-500 leading-none">
                  {entry
                    ? entry.slot
                      ? `Slot ${entry.slot}`
                      : 'Uncap'
                    : i === picked.length
                      ? 'Next'
                      : '—'}
                </div>
                <div className="text-[11px] font-bold tabular-nums mt-0.5">
                  {entry
                    ? money(entry.cost)
                    : i === picked.length && cappedCount < MAX_CAPPED
                      ? money(nextCappedCost)
                      : ''}
                </div>
              </div>
            )
          })}
        </div>
      </header>

      <div className="app-scroll px-5 pt-4 pb-44">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold">Your 2024 squad</h2>
          <div className="text-xs text-slate-500">
            {cappedCount}/5 capped · {uncappedCount}/2 uncapped
          </div>
        </div>

        {venue && (
          <div className="text-[11px] text-slate-500 mb-3 px-1">
            Home: {venue.ground_name.split(',')[0]}
            {venue.pitch_tendency && ` · ${venue.pitch_tendency.replace('_', ' ').toLowerCase()}`}
          </div>
        )}

        <div className="space-y-2">
          {pool.map((player) => {
            const idx = picked.indexOf(player.id)
            const entry = idx >= 0 ? priced[idx] : null
            return (
              <div key={player.id} className="relative">
                <PlayerRow
                  player={player}
                  selected={idx >= 0}
                  onClick={() => toggle(player)}
                  subtitle={
                    <span className={player.is_capped ? 'text-slate-400' : 'text-sky-400'}>
                      {player.is_capped ? 'Capped' : 'Uncapped'} · worth{' '}
                      {money(player.impact.suggested_value_lakh)}
                    </span>
                  }
                  right={
                    <div className="flex flex-col items-end gap-1">
                      <ImpactBadge score={player.impact.base_score} />
                      {entry && (
                        <span className="text-[10px] font-bold tabular-nums text-emerald-300">
                          −{money(entry.cost)}
                        </span>
                      )}
                    </div>
                  }
                />
                <button
                  onClick={() => setDetail(player)}
                  className="absolute right-1 top-1 w-7 h-7 grid place-items-center text-slate-600 text-xs"
                  aria-label={`Why ${player.name} scores ${player.impact.base_score}`}
                >
                  ⓘ
                </button>
              </div>
            )
          })}
        </div>
      </div>

      <div className="shrink-0 px-5 pt-3 bg-ink-800/95 backdrop-blur border-t border-white/5 above-tabbar">
        <div className="flex items-center justify-between text-xs mb-2">
          <span className="text-slate-400">
            {picked.length} retained · <span className="text-gold-400 font-bold">{rtmCards} RTM cards</span>
          </span>
          {secondsLeft > 0 && (
            <span className={secondsLeft <= 30 ? 'text-rose-400 font-bold' : 'text-slate-500'}>
              {Math.floor(secondsLeft / 60)}:{String(secondsLeft % 60).padStart(2, '0')}
            </span>
          )}
        </div>
        <Button variant="gold" className="w-full h-14" onClick={() => setConfirmOpen(true)}>
          {picked.length === 0 ? 'Retain nobody' : `Confirm ${picked.length} retention${picked.length > 1 ? 's' : ''}`}
        </Button>
      </div>

      {/* Confirm — irreversible, so it states the consequences plainly. */}
      <BottomSheet open={confirmOpen} onClose={() => setConfirmOpen(false)} title="Lock retentions?">
        <p className="text-sm text-slate-400 mb-4">This can't be undone.</p>
        <div className="space-y-2 mb-4">
          {priced.map(({ player, cost, slot }) => (
            <div key={player.id} className="flex items-center justify-between text-sm">
              <span className="truncate mr-3">{player.name}</span>
              <span className="text-slate-400 tabular-nums shrink-0">
                {slot ? `Slot ${slot}` : 'Uncapped'} · {money(cost)}
              </span>
            </div>
          ))}
          {priced.length === 0 && (
            <div className="text-sm text-slate-500">
              No retentions — you'll go into the auction with a full purse and all 6 RTM cards.
            </div>
          )}
        </div>
        <div className="flex justify-between text-sm font-bold border-t border-white/10 pt-3 mb-2">
          <span>Purse after</span>
          <span className="tabular-nums">{money(remaining)}</span>
        </div>
        <div className="flex justify-between text-sm font-bold mb-5">
          <span>RTM cards</span>
          <span className="tabular-nums text-gold-400">{rtmCards}</span>
        </div>
        <Button variant="gold" className="w-full h-13 py-4 mb-2" onClick={confirm}>
          Lock it in
        </Button>
        <Button variant="ghost" className="w-full h-12 mb-2" onClick={() => setConfirmOpen(false)}>
          Keep editing
        </Button>
      </BottomSheet>

      <ImpactSheet player={detail} onClose={() => setDetail(null)} />
    </>
  )
}

/** The plan's "why this score" panel, as a mobile sheet. */
export function ImpactSheet({
  player,
  onClose,
}: {
  player: (Player & { impact: Impact }) | null
  onClose: () => void
}) {
  const LABELS: Record<string, string> = {
    base_performance: 'Base performance',
    context_total: 'Fit with your side',
    blended_score: 'Blended score',
    role_scarcity: 'Role scarcity',
    overseas_balance: 'Overseas balance',
    venue_fit: 'Home ground fit',
    longevity: 'Longevity',
    budget_headroom: 'Budget headroom',
  }

  return (
    <BottomSheet open={!!player} onClose={onClose} title={player?.name}>
      <AnimatePresence>
        {player && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <div className="flex items-center gap-3 mb-5">
              <ImpactBadge score={player.impact.base_score} size="lg" />
              <div>
                <div className="text-sm text-slate-400">Suggested value</div>
                <div className="text-xl font-black">
                  {money(player.impact.suggested_value_lakh)}
                </div>
              </div>
            </div>

            {player.impact.notes.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-5">
                {player.impact.notes.map((note) => (
                  <span key={note} className="chip bg-indigo-500/15 text-indigo-300">
                    {note}
                  </span>
                ))}
              </div>
            )}

            <div className="space-y-2.5 mb-5">
              {Object.entries(player.impact.breakdown).map(([key, value]) => {
                // The 0-1 context factors and the 0-100 scores share one bar scale.
                const pct = value <= 1 ? value * 100 : value
                return (
                  <div key={key}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-400">{LABELS[key] ?? key}</span>
                      <span className="tabular-nums font-semibold">
                        {value <= 1 ? `${(value * 100).toFixed(0)}%` : value.toFixed(1)}
                      </span>
                    </div>
                    <div className="h-1 bg-ink-600 rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-indigo-400 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(100, pct)}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>

            {player.stats && Object.values(player.stats).some((v) => v != null) && (
              <>
                <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Career
                </div>
                <div className="grid grid-cols-3 gap-2 mb-4">
                  {statTiles(player.stats).map(([label, value]) => (
                    <div key={label} className="bg-ink-700 rounded-xl p-2.5 text-center">
                      <div className="text-base font-bold tabular-nums">{value}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">{label}</div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </BottomSheet>
  )
}

function statTiles(stats: Record<string, any>): [string, string][] {
  const tiles: [string, string][] = []
  const add = (label: string, value: any, digits = 1) => {
    if (value !== null && value !== undefined) tiles.push([label, Number(value).toFixed(digits)])
  }
  add('Matches', stats.matches, 0)
  add('Bat avg', stats.batting_avg)
  add('SR', stats.strike_rate)
  add('Wickets', stats.wickets, 0)
  add('Econ', stats.economy)
  add('Bowl avg', stats.bowling_avg)
  add('PP SR', stats.powerplay_sr)
  add('Death SR', stats.death_overs_sr)
  add('Dot %', stats.dot_ball_pct)
  return tiles.slice(0, 6)
}
