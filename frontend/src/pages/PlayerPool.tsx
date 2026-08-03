import { useEffect, useMemo, useState } from 'react'
import { EmptyState, PlayerRow, Spinner } from '../components/ui'
import { api } from '../lib/api'
import { money } from '../lib/format'
import { useAuction } from '../store/auctionStore'
import type { Impact, Player } from '../types'
import { ImpactSheet } from './RetentionPhase'

const ROLE_FILTERS = [
  { id: '', label: 'All' },
  { id: 'Batter', label: 'Batters' },
  { id: 'Bowler', label: 'Bowlers' },
  { id: 'All-Rounder', label: 'All-Rnd' },
  { id: 'Wicket-Keeper', label: 'Keepers' },
]

interface UnsoldPlayer extends Player {
  times_unsold: number
  returns: boolean
}

type Tab = 'pool' | 'unsold'

export default function PlayerPool() {
  const [tab, setTab] = useState<Tab>('pool')
  const [query, setQuery] = useState('')
  const [role, setRole] = useState('')
  const [overseasOnly, setOverseasOnly] = useState(false)
  const [items, setItems] = useState<Player[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [detail, setDetail] = useState<(Player & { impact: Impact }) | null>(null)
  const [unsold, setUnsold] = useState<UnsoldPlayer[]>([])
  const showToast = useAuction((s) => s.showToast)
  const roomCode = useAuction((s) => s.roomCode)
  const unsoldCount = useAuction((s) => s.unsoldCount)

  // Refetch whenever another player goes unsold, so the list stays live.
  useEffect(() => {
    if (!roomCode) return
    api
      .unsold(roomCode)
      .then((data) => setUnsold(data.players))
      .catch(() => {})
  }, [roomCode, unsoldCount, tab])

  // Debounced so typing doesn't fire a request per keystroke on a phone keyboard.
  const params = useMemo(
    () => ({ q: query, role, overseas: overseasOnly ? true : undefined, limit: 80 }),
    [query, role, overseasOnly],
  )

  useEffect(() => {
    let cancelled = false
    const id = window.setTimeout(() => {
      setLoading(true)
      api
        .players(params)
        .then((data) => {
          if (cancelled) return
          setItems(data.items)
          setTotal(data.total)
        })
        .catch(() => {})
        .finally(() => !cancelled && setLoading(false))
    }, 220)
    return () => {
      cancelled = true
      window.clearTimeout(id)
    }
  }, [params])

  async function open(player: Player) {
    try {
      const full = await api.player(player.id)
      setDetail({ ...full, impact: full.impact })
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Could not load player')
    }
  }

  return (
    <>
      <header className="app-header px-4 pb-3">
        {/* Pool vs unsold — the unsold list is where you hunt for bargains
            on the second pass, so it gets equal billing. */}
        <div className="pt-3 flex gap-2 p-1 bg-ink-700 rounded-2xl">
          {([
            { id: 'pool', label: 'All players' },
            { id: 'unsold', label: `Unsold${unsold.length ? ` (${unsold.length})` : ''}` },
          ] as const).map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex-1 h-10 rounded-xl text-sm font-bold transition-colors ${
                tab === t.id ? 'bg-indigo-500 text-white' : 'text-slate-400'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === 'pool' && (
        <div className="mt-2.5">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search players…"
            autoCorrect="off"
            autoCapitalize="words"
            className="w-full h-11 rounded-2xl bg-ink-700 border border-line/10 px-4 outline-none focus:border-indigo-400/60 text-[15px]"
          />
        </div>
        )}
        {tab === 'pool' && (
        <div className="snap-x-rail mt-2.5 -mx-4 px-4">
          {ROLE_FILTERS.map((filter) => (
            <button
              key={filter.id}
              onClick={() => setRole(filter.id)}
              className={`shrink-0 snap-start px-3.5 h-9 rounded-full text-xs font-bold whitespace-nowrap ${
                role === filter.id ? 'bg-indigo-500 text-white' : 'bg-ink-700 text-slate-400'
              }`}
            >
              {filter.label}
            </button>
          ))}
          <button
            onClick={() => setOverseasOnly((v) => !v)}
            className={`shrink-0 snap-start px-3.5 h-9 rounded-full text-xs font-bold whitespace-nowrap ${
              overseasOnly ? 'bg-sky-500 text-white' : 'bg-ink-700 text-slate-400'
            }`}
          >
            ✈ Overseas
          </button>
        </div>
        )}
      </header>

      <div className="app-scroll px-4 pt-3 pb-6">
        {tab === 'pool' ? (
          <>
            <div className="text-[11px] text-slate-500 mb-2 px-1">
              {total} player{total === 1 ? '' : 's'} · sorted by impact
            </div>
            {loading && items.length === 0 ? (
              <Spinner />
            ) : items.length === 0 ? (
              <EmptyState icon="🔍" title="No players match" hint="Try a different filter." />
            ) : (
              <div className="space-y-1.5">
                {items.map((player) => (
                  <PlayerRow
                    key={player.id}
                    player={player}
                    onClick={() => open(player)}
                    subtitle={
                      <span>
                        {money(player.base_price_lakh)} base · {player.set_name}
                      </span>
                    }
                  />
                ))}
              </div>
            )}
          </>
        ) : unsold.length === 0 ? (
          <EmptyState
            icon="🗂️"
            title="Nobody unsold yet"
            hint="Players who draw no bid land here, and most come back around for a second pass."
          />
        ) : (
          <>
            <div className="text-[11px] text-slate-500 mb-2 px-1">
              {unsold.filter((p) => p.returns).length} returning later ·{' '}
              {unsold.filter((p) => !p.returns).length} gone for good
            </div>
            <div className="space-y-1.5">
              {unsold.map((player) => (
                <PlayerRow
                  key={player.id}
                  player={player}
                  onClick={() => open(player)}
                  subtitle={
                    <span className={player.returns ? 'text-amber-400' : 'text-slate-500'}>
                      {player.returns ? 'Returns later' : 'Out of the auction'} ·{' '}
                      {money(player.base_price_lakh)} base
                    </span>
                  }
                />
              ))}
            </div>
          </>
        )}
      </div>

      <ImpactSheet player={detail} onClose={() => setDetail(null)} />
    </>
  )
}
