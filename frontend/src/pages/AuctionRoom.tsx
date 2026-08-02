import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import type { SocketContext } from '../RoomGate'
import { BidTimer } from '../components/BidTimer'
import {
  Avatar,
  BottomSheet,
  franchiseColor,
  ImpactBadge,
  RoleChip,
  Spinner,
} from '../components/ui'
import { haptic, money, moneyShort } from '../lib/format'
import { useAuction } from '../store/auctionStore'
import { ImpactSheet } from './RetentionPhase'

export default function AuctionRoom() {
  const socket = useOutletContext<SocketContext>()
  const [feedOpen, setFeedOpen] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)

  const room = useAuction((s) => s.room)
  const lot = useAuction((s) => s.lot)
  const teamId = useAuction((s) => s.teamId)
  const nextBid = useAuction((s) => s.nextBidLakh)
  const seconds = useAuction((s) => s.secondsRemaining)
  const impacts = useAuction((s) => s.impacts)
  const feed = useAuction((s) => s.feed)
  const lastSold = useAuction((s) => s.lastSold)
  const connected = useAuction((s) => s.connected)

  const myTeam = room?.teams.find((t) => t.id === teamId)
  const myImpact = teamId ? impacts[teamId] : undefined
  const leading = room?.teams.find((t) => t.id === lot?.leading_team_id)
  const iAmLeading = lot?.leading_team_id === teamId
  const canAfford = (myTeam?.purse_remaining_lakh ?? 0) >= nextBid
  const bidding = lot?.status === 'BIDDING'

  if (!room || !lot) {
    return (
      <div className="app-scroll">
        <Spinner label={connected ? 'Waiting for the next lot…' : 'Connecting…'} />
      </div>
    )
  }

  const player = lot.player
  const accent = franchiseColor(leading?.franchise_code)

  return (
    <>
      {/* Header: progress + timer, the two things you always need visible. */}
      <header className="app-header px-4 pb-2">
        <div className="flex items-center justify-between pt-2.5 gap-3">
          <div className="min-w-0">
            <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold truncate">
              {player.set_name}
            </div>
            <div className="text-xs text-slate-400 tabular-nums">
              Lot {room.lots_done + 1} of {room.total_lots}
            </div>
          </div>
          <BidTimer seconds={seconds} active={bidding} />
        </div>
        <div className="h-0.5 bg-ink-600 rounded-full mt-2 overflow-hidden">
          <motion.div
            className="h-full bg-indigo-400"
            animate={{ width: `${(room.lots_done / Math.max(1, room.total_lots)) * 100}%` }}
          />
        </div>
      </header>

      <div className="app-scroll px-4 pt-3 pb-2">
        {/* Player card */}
        <motion.button
          key={player.id}
          initial={{ opacity: 0, y: 14, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          onClick={() => setDetailOpen(true)}
          className="w-full card p-4 text-left active:scale-[0.99] transition-transform"
        >
          <div className="flex items-start gap-3">
            <Avatar name={player.name} size={56} />
            <div className="min-w-0 flex-1">
              <div className="text-xl font-black leading-tight truncate">{player.name}</div>
              <div className="flex items-center gap-2 mt-1.5">
                <RoleChip role={player.role} overseas={player.is_overseas} />
                <span className="text-xs text-slate-400">{player.nationality}</span>
              </div>
              <div className="text-xs text-slate-500 mt-1.5">
                Base {money(player.base_price_lakh)}
                {player.age ? ` · ${player.age}y` : ''}
                {!player.is_capped && ' · uncapped'}
              </div>
            </div>
            <ImpactBadge score={player.base_impact_score} size="lg" />
          </div>

          {myImpact && (
            <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">
                  Worth to you
                </div>
                <div className="text-base font-bold text-indigo-300">
                  {money(myImpact.suggested_value_lakh)}
                </div>
              </div>
              <div className="flex flex-wrap gap-1 justify-end max-w-[55%]">
                {myImpact.notes.slice(0, 2).map((note) => (
                  <span key={note} className="chip bg-indigo-500/15 text-indigo-300 text-[10px]">
                    {note}
                  </span>
                ))}
                <span className="text-[10px] text-slate-600 self-center">tap for detail</span>
              </div>
            </div>
          )}
        </motion.button>

        {/* Current bid — the biggest thing on screen. */}
        <div className="mt-4 text-center">
          <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">
            {lot.current_bid_lakh ? 'Current bid' : 'Opening at'}
          </div>
          <AnimatePresence mode="popLayout">
            <motion.div
              key={lot.current_bid_lakh ?? 'base'}
              initial={{ scale: 0.82, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 1.08, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 420, damping: 26 }}
              className="text-[40px] leading-none font-black tabular-nums my-1"
              style={{ color: lot.current_bid_lakh ? accent : '#E2E8F0' }}
            >
              {money(lot.current_bid_lakh ?? player.base_price_lakh)}
            </motion.div>
          </AnimatePresence>
          <div className="h-5 text-sm font-semibold">
            {leading ? (
              <span style={{ color: accent }}>
                {iAmLeading ? 'You lead' : leading.franchise_code}
                {leading.is_ai && !iAmLeading && ' (AI)'}
              </span>
            ) : (
              <span className="text-slate-600">no bids yet</span>
            )}
          </div>
        </div>

        {/* Live bid ladder */}
        <div className="mt-3 flex gap-1.5 overflow-x-auto no-scrollbar h-8 items-center">
          {lot.history.length === 0 && (
            <span className="text-xs text-slate-600">Bids will appear here</span>
          )}
          {[...lot.history].reverse().map((bid, i) => (
            <motion.div
              key={`${bid.team_id}-${bid.amount_lakh}`}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1 - i * 0.13, x: 0 }}
              className="shrink-0 px-2 py-1 rounded-lg text-[11px] font-bold tabular-nums"
              style={{
                background: `${franchiseColor(bid.franchise_code)}22`,
                color: franchiseColor(bid.franchise_code),
              }}
            >
              {bid.franchise_code} {moneyShort(bid.amount_lakh)}
            </motion.div>
          ))}
        </div>

        {/* Sold / unsold stamp */}
        <AnimatePresence>
          {lot.status === 'SOLD' && lastSold && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="mt-4 rounded-2xl p-4 text-center"
              style={{ background: `${franchiseColor(lastSold.franchise)}1F` }}
            >
              <div
                className="text-2xl font-black tracking-widest"
                style={{ color: franchiseColor(lastSold.franchise) }}
              >
                {lastSold.kind === 'RTM' ? 'RTM!' : 'SOLD!'}
              </div>
              <div className="text-sm mt-1">
                {lastSold.franchise} · {money(lastSold.price)}
              </div>
            </motion.div>
          )}
          {lot.status === 'UNSOLD' && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="mt-4 rounded-2xl p-4 text-center bg-slate-500/10"
            >
              <div className="text-2xl font-black tracking-widest text-slate-400">UNSOLD</div>
            </motion.div>
          )}
          {lot.status === 'RTM_PENDING' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-4 rounded-2xl p-4 text-center bg-gold-400/10"
            >
              <div className="text-lg font-black text-gold-400">RTM WINDOW</div>
              <div className="text-xs text-slate-400 mt-1">2024 owner is deciding…</div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Team purse rail */}
        <button
          onClick={() => setFeedOpen(true)}
          className="mt-4 w-full flex gap-1.5 overflow-x-auto no-scrollbar pb-1"
        >
          {room.teams.map((team) => {
            const isMe = team.id === teamId
            const isLeading = team.id === lot.leading_team_id
            return (
              <div
                key={team.id}
                className={`shrink-0 rounded-xl px-2.5 py-1.5 min-w-[62px] border ${
                  isLeading ? 'border-current' : 'border-white/5'
                } ${isMe ? 'bg-ink-600' : 'bg-ink-700'}`}
                style={{ color: franchiseColor(team.franchise_code) }}
              >
                <div className="text-[10px] font-black">{team.franchise_code}</div>
                <div className="text-[11px] font-bold tabular-nums text-slate-300">
                  {moneyShort(team.purse_remaining_lakh)}
                </div>
                <div className="text-[9px] text-slate-500 tabular-nums">
                  {team.squad_size}p · {team.rtm_cards}r
                </div>
              </div>
            )
          })}
        </button>

        {/* Ticker preview */}
        <button
          onClick={() => setFeedOpen(true)}
          className="mt-3 w-full text-left text-xs text-slate-500 truncate px-1 pb-2"
        >
          {feed[0] ? `· ${feed[0].text}` : 'Auction feed'}
        </button>
      </div>

      {/* Thumb-zone bid bar. */}
      <div className="shrink-0 px-4 pt-3 bg-ink-800/95 backdrop-blur border-t border-white/5 above-tabbar">
        <div className="flex items-center justify-between text-xs mb-2 px-1">
          <span className="text-slate-400">
            Purse <span className="font-bold text-slate-200">{money(myTeam?.purse_remaining_lakh ?? 0)}</span>
          </span>
          <span className="text-slate-400">
            {myTeam?.squad_size ?? 0}/25 · {myTeam?.overseas_used ?? 0}/8 overseas
          </span>
        </div>
        <button
          disabled={!bidding || iAmLeading || !canAfford || !connected}
          onClick={() => {
            haptic(24)
            socket.placeBid(nextBid)
          }}
          className="tap w-full h-16 rounded-2xl font-black text-lg flex items-center justify-center gap-2 bg-gold-400 text-ink-900 active:bg-gold-500 disabled:bg-ink-600 disabled:text-slate-500 disabled:active:scale-100"
        >
          {!connected
            ? 'Reconnecting…'
            : !bidding
              ? 'Lot closed'
              : iAmLeading
                ? 'You lead this lot'
                : !canAfford
                  ? 'Not enough purse'
                  : `BID ${money(nextBid)}`}
        </button>
      </div>

      <BottomSheet open={feedOpen} onClose={() => setFeedOpen(false)} title="Auction feed">
        {feed.length === 0 ? (
          <p className="text-sm text-slate-500 pb-6">Nothing yet.</p>
        ) : (
          <div className="space-y-1.5 pb-4">
            {feed.map((item) => (
              <div key={item.id} className="flex items-start gap-2 text-sm py-1.5">
                <span
                  className="w-1 h-1 rounded-full mt-2 shrink-0"
                  style={{ background: franchiseColor(item.franchise) }}
                />
                <span className={item.kind === 'UNSOLD' ? 'text-slate-500' : 'text-slate-300'}>
                  {item.text}
                </span>
              </div>
            ))}
          </div>
        )}
      </BottomSheet>

      <ImpactSheet
        player={detailOpen && myImpact ? { ...player, impact: myImpact } : null}
        onClose={() => setDetailOpen(false)}
      />
    </>
  )
}
