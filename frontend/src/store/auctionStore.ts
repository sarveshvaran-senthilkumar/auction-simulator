import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  Ack,
  BiddingWar,
  Decision,
  FeedItem,
  Franchise,
  Impact,
  Lot,
  Room,
  TeamResult,
} from '../types'
import { money } from '../lib/format'

/** Identity survives a reload so refreshing the phone doesn't lose your franchise. */
interface Session {
  userId: string | null
  displayName: string
  roomCode: string | null
  teamId: string | null
  franchiseCode: string | null
}

interface AuctionState extends Session {
  connected: boolean
  room: Room | null
  lot: Lot | null
  secondsRemaining: number
  nextBidLakh: number
  impacts: Record<string, Impact>
  feed: FeedItem[]
  decision: Decision | null
  toast: { text: string; tone: 'error' | 'ok' } | null
  results: TeamResult[] | null
  franchises: Franchise[]
  lastSold: { name: string; franchise: string; price: number; kind: string } | null
  acks: Ack[]
  war: BiddingWar | null
  unsoldCount: number

  setSession: (s: Partial<Session>) => void
  setFranchises: (f: Franchise[]) => void
  setConnected: (c: boolean) => void
  applyEvent: (type: string, payload: any) => void
  pushFeed: (item: Omit<FeedItem, 'id'>) => void
  showToast: (text: string, tone?: 'error' | 'ok') => void
  clearToast: () => void
  clearDecision: () => void
  pushAck: (ack: Omit<Ack, 'id'>) => void
  dismissAck: (id: number) => void
  dismissWar: () => void
  reset: () => void
}

let feedId = 0

const emptySession: Session = {
  userId: null,
  displayName: '',
  roomCode: null,
  teamId: null,
  franchiseCode: null,
}

export const useAuction = create<AuctionState>()(
  persist(
    (set, get) => ({
      ...emptySession,
      connected: false,
      room: null,
      lot: null,
      secondsRemaining: 0,
      nextBidLakh: 0,
      impacts: {},
      feed: [],
      decision: null,
      toast: null,
      results: null,
      franchises: [],
      lastSold: null,
      acks: [],
      war: null,
      unsoldCount: 0,

      setSession: (s) => set(s),
      setFranchises: (franchises) => set({ franchises }),
      setConnected: (connected) => set({ connected }),

      pushFeed: (item) =>
        set((state) => ({
          // Newest first, and bounded — an auction emits hundreds of these.
          feed: [{ ...item, id: ++feedId }, ...state.feed].slice(0, 60),
        })),

      showToast: (text, tone = 'error') => set({ toast: { text, tone } }),
      clearToast: () => set({ toast: null }),
      clearDecision: () => set({ decision: null }),

      // At most two acknowledgements on screen, newest last.
      pushAck: (ack) =>
        set((state) => ({ acks: [...state.acks, { ...ack, id: ++feedId }].slice(-2) })),
      dismissAck: (id) => set((state) => ({ acks: state.acks.filter((a) => a.id !== id) })),
      dismissWar: () => set({ war: null }),

      reset: () =>
        set({
          ...emptySession,
          room: null,
          lot: null,
          impacts: {},
          feed: [],
          decision: null,
          results: null,
          lastSold: null,
          acks: [],
          war: null,
          unsoldCount: 0,
        }),

      applyEvent: (type, payload) => {
        const state = get()

        switch (type) {
          case 'SNAPSHOT':
            set({
              room: payload.room,
              lot: payload.room?.lot ?? null,
              teamId: payload.my_team_id ?? state.teamId,
              secondsRemaining: payload.room?.lot?.seconds_remaining ?? 0,
            })
            break

          case 'ROOM_UPDATE':
            set({ room: payload, lot: payload.lot ?? state.lot })
            break

          case 'RETENTION_TICK':
            set((s) =>
              s.room
                ? { room: { ...s.room, retention_seconds_remaining: payload.seconds_remaining } }
                : {},
            )
            break

          case 'RETENTION_COMPLETE':
            set({ room: payload })
            get().pushFeed({ kind: 'INFO', text: 'Retentions locked. Auction starting.' })
            break

          case 'LOT_STARTED':
            set({
              lot: payload.lot,
              secondsRemaining: payload.lot.seconds_remaining,
              nextBidLakh: payload.next_bid_lakh,
              lastSold: null,
              // A new lot clears anything left over from the last one.
              acks: [],
              war: null,
            })
            break

          case 'IMPACT_SCORES':
            set({ impacts: payload.per_team })
            break

          case 'TIMER_TICK':
            set({ secondsRemaining: payload.seconds_remaining })
            break

          case 'BID_PLACED': {
            const wasLeading = state.lot?.leading_team_id === state.teamId
            const nowLeading = payload.team_id === state.teamId

            set((s) => ({
              lot: s.lot
                ? {
                    ...s.lot,
                    current_bid_lakh: payload.amount_lakh,
                    leading_team_id: payload.team_id,
                    history: payload.history,
                  }
                : s.lot,
              nextBidLakh: payload.next_bid_lakh,
              secondsRemaining: payload.seconds_remaining,
            }))

            if (nowLeading && !wasLeading) {
              get().pushAck({
                tone: 'lead',
                title: 'Highest bid is yours',
                detail: `${state.lot?.player.name ?? 'This lot'} at ${money(payload.amount_lakh)}`,
              })
            } else if (wasLeading && !nowLeading) {
              get().pushAck({
                tone: 'outbid',
                title: `Outbid by ${payload.franchise_code}`,
                detail: `Now ${money(payload.amount_lakh)}`,
                franchise: payload.franchise_code,
              })
            }
            break
          }

          case 'BIDDING_WAR':
            set({ war: payload })
            break

          case 'LOT_SOLD': {
            const mine = payload.team_id === state.teamId
            // Only call it a loss if you were actually in the bidding.
            const contested = (state.lot?.history ?? []).some((b) => b.team_id === state.teamId)

            set((s) => ({
              lot: s.lot ? { ...s.lot, status: 'SOLD' } : s.lot,
              war: null,
              lastSold: {
                name: payload.player.name,
                franchise: payload.franchise_code,
                price: payload.price_lakh,
                kind: payload.acquisition_type,
              },
            }))

            if (mine) {
              get().pushAck({
                tone: 'won',
                title: `${payload.player.name} is yours`,
                detail: `${money(payload.price_lakh)}${
                  payload.acquisition_type === 'RTM' ? ' via RTM' : ''
                }`,
                franchise: payload.franchise_code,
              })
            } else if (contested) {
              get().pushAck({
                tone: 'lost',
                title: `${payload.franchise_code} took ${payload.player.name}`,
                detail: money(payload.price_lakh),
                franchise: payload.franchise_code,
              })
            }

            get().pushFeed({
              kind: payload.acquisition_type === 'RTM' ? 'RTM' : 'SOLD',
              franchise: payload.franchise_code,
              text: `${payload.player.name} → ${payload.franchise_code} · ${money(
                payload.price_lakh,
              )}${payload.acquisition_type === 'RTM' ? ' (RTM)' : ''}`,
            })
            break
          }

          case 'LOT_UNSOLD':
            set((s) => ({
              lot: s.lot ? { ...s.lot, status: 'UNSOLD' } : s.lot,
              war: null,
              unsoldCount: payload.unsold_count ?? s.unsoldCount,
            }))
            get().pushFeed({
              kind: 'UNSOLD',
              text: `${payload.player.name} unsold${payload.revisit ? ' · returns later' : ''}`,
            })
            break

          case 'RTM_WINDOW':
            set((s) => ({ lot: s.lot ? { ...s.lot, status: 'RTM_PENDING' } : s.lot }))
            get().pushFeed({
              kind: 'RTM',
              franchise: payload.rtm_franchise_code,
              text: `${payload.rtm_franchise_code} considering RTM on ${payload.player.name}`,
            })
            break

          case 'RTM_PROMPT':
            set({
              decision: {
                kind: 'RTM',
                player: payload.player,
                priceLakh: payload.price_lakh,
                rtmCardsRemaining: payload.rtm_cards_remaining,
                seconds: payload.seconds,
              },
            })
            break

          case 'RTM_COUNTER_PROMPT':
            set({
              decision: {
                kind: 'COUNTER',
                player: payload.player,
                priceLakh: payload.current_price_lakh,
                raiseToLakh: payload.raise_to_lakh,
                otherFranchise: payload.rtm_franchise_code,
                seconds: payload.seconds,
              },
            })
            break

          case 'RTM_DECLINED':
            get().pushFeed({
              kind: 'RTM',
              franchise: payload.franchise_code,
              text: `${payload.franchise_code} declined RTM`,
            })
            break

          case 'RTM_COUNTERED':
            get().pushFeed({
              kind: 'RTM',
              franchise: payload.franchise_code,
              text: `${payload.franchise_code} raised to ${money(payload.price_lakh)}`,
            })
            break

          case 'RTM_LAPSED':
            get().pushFeed({
              kind: 'RTM',
              franchise: payload.franchise_code,
              text: `${payload.franchise_code} could not match — player released`,
            })
            break

          case 'AUCTION_COMPLETED':
            set((s) => ({
              results: payload.teams,
              room: s.room ? { ...s.room, status: 'COMPLETED' } : s.room,
            }))
            break

          case 'BID_REJECTED':
            get().showToast(payload.reason)
            break

          case 'ERROR':
            get().showToast(payload.reason)
            break
        }
      },
    }),
    {
      name: 'ipl-auction-session',
      // Only identity is worth persisting; live auction state comes from the socket.
      partialize: (s) => ({
        userId: s.userId,
        displayName: s.displayName,
        roomCode: s.roomCode,
        teamId: s.teamId,
        franchiseCode: s.franchiseCode,
      }),
    },
  ),
)
