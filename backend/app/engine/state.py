"""In-memory state for a live auction room.

The database holds the player universe and the final result; the second-to-second
auction state lives here, guarded by one asyncio.Lock per room.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..ai_service.impact_engine import TeamNeed
from ..config import settings


@dataclass
class PlayerRef:
    """A denormalised player row, cached at room start so lots need no DB hit."""
    id: str
    name: str
    nationality: str
    role: str
    is_capped: bool
    base_price_lakh: int
    set_name: str
    set_order: int
    is_overseas: bool
    age: Optional[int]
    base_impact_score: float
    stats: Dict[str, Optional[float]] = field(default_factory=dict)

    def public(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "nationality": self.nationality,
            "role": self.role,
            "is_capped": self.is_capped,
            "base_price_lakh": self.base_price_lakh,
            "set_name": self.set_name,
            "is_overseas": self.is_overseas,
            "age": self.age,
            "base_impact_score": round(self.base_impact_score, 1),
            "stats": self.stats,
        }


@dataclass
class RosterItem:
    player_id: str
    name: str
    role: str
    is_overseas: bool
    price_lakh: int
    acquisition_type: str  # AUCTION | RETENTION | RTM

    def public(self) -> dict:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "role": self.role,
            "is_overseas": self.is_overseas,
            "price_lakh": self.price_lakh,
            "acquisition_type": self.acquisition_type,
        }


@dataclass
class TeamState:
    id: str
    franchise_code: str
    user_id: Optional[str] = None
    is_ai: bool = True
    purse_remaining_lakh: int = settings.DEFAULT_PURSE_LAKH
    overseas_used: int = 0
    rtm_cards: int = 0
    retention_confirmed: bool = False
    roster: List[RosterItem] = field(default_factory=list)
    # Per-team bidding personality, so ten AI franchises don't act as one.
    aggression: float = 1.0
    connected: bool = False

    @property
    def role_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for item in self.roster:
            counts[item.role] = counts.get(item.role, 0) + 1
        return counts

    def need(self) -> TeamNeed:
        return TeamNeed(
            purse_remaining_lakh=self.purse_remaining_lakh,
            squad_size=len(self.roster),
            max_squad_size=settings.MAX_SQUAD_SIZE,
            overseas_used=self.overseas_used,
            max_overseas=settings.MAX_OVERSEAS,
            role_counts=self.role_counts,
            franchise_code=self.franchise_code,
            aggression=self.aggression,
        )

    def add(self, player: PlayerRef, price_lakh: int, acquisition: str) -> None:
        self.roster.append(RosterItem(
            player_id=player.id,
            name=player.name,
            role=player.role,
            is_overseas=player.is_overseas,
            price_lakh=price_lakh,
            acquisition_type=acquisition,
        ))
        self.purse_remaining_lakh -= price_lakh
        if player.is_overseas:
            self.overseas_used += 1

    def public(self) -> dict:
        return {
            "id": self.id,
            "franchise_code": self.franchise_code,
            "is_ai": self.is_ai,
            "user_id": self.user_id,
            "connected": self.connected,
            "purse_remaining_lakh": self.purse_remaining_lakh,
            "squad_size": len(self.roster),
            "overseas_used": self.overseas_used,
            "rtm_cards": self.rtm_cards,
            "retention_confirmed": self.retention_confirmed,
            "role_counts": self.role_counts,
        }


@dataclass
class BidRecord:
    team_id: str
    franchise_code: str
    amount_lakh: int
    at: float = field(default_factory=time.time)

    def public(self) -> dict:
        return {
            "team_id": self.team_id,
            "franchise_code": self.franchise_code,
            "amount_lakh": self.amount_lakh,
        }


@dataclass
class LotState:
    player: PlayerRef
    status: str = "BIDDING"  # BIDDING | RTM_PENDING | SOLD | UNSOLD
    current_bid_lakh: Optional[int] = None
    leading_team_id: Optional[str] = None
    history: List[BidRecord] = field(default_factory=list)
    deadline: float = 0.0
    # Bids reset `deadline`, so without an absolute stop two well-funded teams
    # can trade increments indefinitely and the lot never closes.
    hard_deadline: float = 0.0
    revisit_count: int = 0
    # RTM sub-state
    rtm_team_id: Optional[str] = None
    rtm_deadline: float = 0.0
    rtm_final_price: Optional[int] = None

    @property
    def seconds_remaining(self) -> int:
        stop = min(self.deadline, self.hard_deadline) if self.hard_deadline else self.deadline
        return max(0, int(round(stop - time.time())))

    def public(self) -> dict:
        return {
            "player": self.player.public(),
            "status": self.status,
            "current_bid_lakh": self.current_bid_lakh,
            "leading_team_id": self.leading_team_id,
            "seconds_remaining": self.seconds_remaining,
            "history": [b.public() for b in self.history[-8:]],
            "revisit_count": self.revisit_count,
        }


@dataclass
class RoomState:
    id: str
    code: str
    status: str = "LOBBY"
    teams: Dict[str, TeamState] = field(default_factory=dict)
    players: Dict[str, PlayerRef] = field(default_factory=dict)
    # franchise_code -> set of player_ids from that franchise's 2024 squad
    squads_2024: Dict[str, set] = field(default_factory=dict)
    venues: Dict[str, object] = field(default_factory=dict)

    queue: List[str] = field(default_factory=list)       # player ids yet to come up
    revisit: List[str] = field(default_factory=list)     # unsold, awaiting a second pass
    # How many times each player has already gone unsold. Lives on the room, not
    # the lot: a fresh LotState is built for every pass, so a per-lot counter
    # would always read zero and requeue the same player forever.
    revisit_counts: Dict[str, int] = field(default_factory=dict)
    # Every player who has gone unsold at least once, oldest first, so the app
    # can show what is coming back around.
    unsold_log: List[str] = field(default_factory=list)
    lot: Optional[LotState] = None
    lots_done: int = 0
    total_lots: int = 0
    retention_deadline: float = 0.0

    # A full 244-lot mega auction is a multi-hour sitting -- too long for a phone.
    # The format trims the pool to the best players, and the legal minimum squad
    # size scales down with it so teams can still fill out.
    auction_format: str = "STANDARD"
    min_squad_size: int = settings.MIN_SQUAD_SIZE

    def team_by_user(self, user_id: str) -> Optional[TeamState]:
        for team in self.teams.values():
            if team.user_id == user_id:
                return team
        return None

    def unsold_players(self) -> List[dict]:
        """Unsold players, flagged by whether they still have a pass left."""
        pending = set(self.revisit)
        sold = {i.player_id for t in self.teams.values() for i in t.roster}
        out = []
        for pid in self.unsold_log:
            player = self.players.get(pid)
            if player is None or pid in sold:
                continue  # picked up on a later pass
            out.append({
                **player.public(),
                "times_unsold": self.revisit_counts.get(pid, 0),
                "returns": pid in pending,
            })
        return out

    def owner_2024(self, player_id: str) -> Optional[TeamState]:
        for team in self.teams.values():
            if player_id in self.squads_2024.get(team.franchise_code, set()):
                return team
        return None

    def public(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "status": self.status,
            "teams": [t.public() for t in self.teams.values()],
            "lot": self.lot.public() if self.lot else None,
            "lots_done": self.lots_done,
            "total_lots": self.total_lots,
            "queue_remaining": len(self.queue) + len(self.revisit),
            "auction_format": self.auction_format,
            "min_squad_size": self.min_squad_size,
            "retention_seconds_remaining": (
                max(0, int(round(self.retention_deadline - time.time())))
                if self.status == "RETENTION" else 0
            ),
        }
