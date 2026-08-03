export type Role = 'Batter' | 'Bowler' | 'All-Rounder' | 'Wicket-Keeper'

export interface PlayerStats {
  matches?: number | null
  innings?: number | null
  batting_avg?: number | null
  strike_rate?: number | null
  powerplay_sr?: number | null
  death_overs_sr?: number | null
  boundary_pct?: number | null
  bowling_avg?: number | null
  economy?: number | null
  wickets?: number | null
  bowling_sr?: number | null
  death_overs_economy?: number | null
  dot_ball_pct?: number | null
  match_winning_innings?: number | null
}

export interface Player {
  id: string
  name: string
  nationality: string
  role: Role
  is_capped: boolean
  base_price_lakh: number
  set_name: string
  is_overseas: boolean
  age: number | null
  base_impact_score: number
  stats?: PlayerStats
}

export interface Impact {
  base_score: number
  context_score: number
  suggested_value_lakh: number
  breakdown: Record<string, number>
  notes: string[]
}

export interface Team {
  id: string
  franchise_code: string
  is_ai: boolean
  user_id: string | null
  connected: boolean
  purse_remaining_lakh: number
  squad_size: number
  overseas_used: number
  rtm_cards: number
  retention_confirmed: boolean
  role_counts: Record<string, number>
}

export interface BidRecord {
  team_id: string
  franchise_code: string
  amount_lakh: number
}

export interface Lot {
  player: Player
  status: 'BIDDING' | 'CLOSING' | 'RTM_PENDING' | 'SOLD' | 'UNSOLD'
  current_bid_lakh: number | null
  leading_team_id: string | null
  seconds_remaining: number
  history: BidRecord[]
  revisit_count: number
}

export interface Room {
  id: string
  code: string
  status: 'LOBBY' | 'RETENTION' | 'IN_PROGRESS' | 'COMPLETED'
  teams: Team[]
  lot: Lot | null
  lots_done: number
  total_lots: number
  queue_remaining: number
  auction_format: string
  min_squad_size: number
  retention_seconds_remaining: number
}

export interface Franchise {
  code: string
  name: string
  primary: string
  secondary: string
  city: string
}

export interface RosterItem {
  player_id: string
  name: string
  role: Role
  is_overseas: boolean
  price_lakh: number
  acquisition_type: 'AUCTION' | 'RETENTION' | 'RTM'
}

export interface TeamResult extends Team {
  spent_lakh: number
  squad_impact: number
  avg_impact: number
  roster: RosterItem[]
}

/** A line in the auction ticker. */
export interface FeedItem {
  id: number
  kind: 'SOLD' | 'UNSOLD' | 'RTM' | 'INFO'
  text: string
  franchise?: string
}

/** A two-team duel, surfaced as a heads-up card mid-lot. */
export interface BiddingWar {
  player: Player
  price_lakh: number
  opened_at_lakh: number
  bids: number
  leading_team_id: string
  teams: (Team & { spent_lakh: number; last_bid_lakh: number | null })[]
}

/** A transient banner: you took the lead, you were outbid, a lot closed. */
export interface Ack {
  id: number
  tone: 'lead' | 'outbid' | 'won' | 'lost' | 'info'
  title: string
  detail?: string
  franchise?: string
}

/** Either RTM prompt awaiting this user's yes/no. */
export interface Decision {
  kind: 'RTM' | 'COUNTER'
  player: Player
  priceLakh: number
  raiseToLakh?: number
  rtmCardsRemaining?: number
  otherFranchise?: string
  seconds: number
}
