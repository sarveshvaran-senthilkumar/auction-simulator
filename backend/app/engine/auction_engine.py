"""The room state machine: LOBBY -> RETENTION -> IN_PROGRESS -> COMPLETED.

One `asyncio.Lock` per room serialises every mutation, so concurrent bids from
several phones resolve deterministically: first to acquire the lock wins.
"""

import asyncio
import random
import time
from typing import Awaitable, Callable, Dict, List, Optional

from sqlalchemy import select

from ..ai_service.ai_retention_agent import ai_retention_agent
from ..ai_service.impact_engine import StatsView, impact_engine
from ..ai_service.rule_based_bidder import rule_based_bidder
from ..config import settings
from ..db.database import AsyncSessionLocal
from ..db.models import (
    AcquisitionType,
    Bid,
    Player,
    PlayerStats,
    RosterEntry,
    Room,
    RoomStatus,
    RTMCard,
    Squad2024Entry,
    Team,
    TeamRetention,
    UnsoldRecord,
    Venue,
)
from . import rules
from .retention_engine import retention_engine
from .state import BidRecord, LotState, PlayerRef, RoomState, TeamState

# (event_type, payload, target_user_id or None for broadcast)
Emitter = Callable[[str, str, dict, Optional[str]], Awaitable[None]]

STAT_FIELDS = [
    "matches", "innings", "batting_avg", "strike_rate", "powerplay_sr",
    "death_overs_sr", "boundary_pct", "bowling_avg", "economy", "wickets",
    "bowling_sr", "death_overs_economy", "dot_ball_pct", "match_winning_innings",
]

# How many lots each format puts under the hammer. None = the whole pool.
FORMAT_LOTS = {"QUICK": 80, "STANDARD": 150, "FULL": None}

# A duel is two teams trading this many bids with nobody else joining in. The
# app raises a heads-up card when one starts, and again every few bids after.
WAR_BIDS = 6
WAR_REPEAT_EVERY = 4


class AuctionEngine:
    def __init__(self) -> None:
        self.rooms: Dict[str, RoomState] = {}
        self.locks: Dict[str, asyncio.Lock] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.emit: Optional[Emitter] = None

    # ------------------------------------------------------------- plumbing
    def set_emitter(self, emitter: Emitter) -> None:
        self.emit = emitter

    async def _send(self, room_code: str, event: str, payload: dict, to_user: Optional[str] = None) -> None:
        if self.emit:
            await self.emit(room_code, event, payload, to_user)

    def lock(self, room_code: str) -> asyncio.Lock:
        return self.locks.setdefault(room_code, asyncio.Lock())

    def get(self, room_code: str) -> Optional[RoomState]:
        return self.rooms.get(room_code)

    # -------------------------------------------------------------- loading
    async def load_room(self, room_code: str) -> RoomState:
        """Hydrate a room's full working set from the database, once."""
        if room_code in self.rooms:
            return self.rooms[room_code]

        async with AsyncSessionLocal() as session:
            room_row = (await session.execute(
                select(Room).where(Room.room_code == room_code)
            )).scalar_one_or_none()
            if room_row is None:
                raise KeyError(f"no room {room_code}")

            config = room_row.config_json or {}
            room = RoomState(
                id=room_row.id,
                code=room_row.room_code,
                status=room_row.status.value,
                auction_format=str(config.get("format", "STANDARD")).upper(),
            )
            if room.auction_format not in FORMAT_LOTS:
                room.auction_format = "STANDARD"

            team_rows = (await session.execute(
                select(Team).where(Team.room_id == room_row.id)
            )).scalars().all()
            for t in team_rows:
                room.teams[t.id] = TeamState(
                    id=t.id,
                    franchise_code=t.franchise_code,
                    user_id=t.user_id,
                    is_ai=t.is_ai,
                    purse_remaining_lakh=t.purse_remaining_lakh,
                    overseas_used=t.overseas_slots_used or 0,
                    retention_confirmed=bool(t.retention_confirmed),
                    aggression=round(random.uniform(0.92, 1.24), 3),
                )

            rows = (await session.execute(
                select(Player, PlayerStats).outerjoin(
                    PlayerStats, PlayerStats.player_id == Player.id
                )
            )).all()
            for player, stats in rows:
                room.players[player.id] = PlayerRef(
                    id=player.id,
                    name=player.name,
                    nationality=player.nationality,
                    role=player.role.value,
                    is_capped=player.is_capped,
                    base_price_lakh=player.base_price_lakh,
                    set_name=player.set_name or "Uncapped",
                    set_order=player.set_order if player.set_order is not None else 99,
                    is_overseas=player.is_overseas,
                    age=player.age,
                    base_impact_score=(stats.base_impact_score if stats else 45.0) or 45.0,
                    stats={f: getattr(stats, f, None) for f in STAT_FIELDS} if stats else {},
                )

            for entry in (await session.execute(select(Squad2024Entry))).scalars().all():
                room.squads_2024.setdefault(entry.franchise_code, set()).add(entry.player_id)

            for venue in (await session.execute(select(Venue))).scalars().all():
                room.venues[venue.franchise_code] = venue

        self.rooms[room_code] = room
        return room

    def venue_for(self, room: RoomState, team: TeamState):
        return room.venues.get(team.franchise_code)

    def squad_2024_of(self, room: RoomState, team: TeamState) -> List[PlayerRef]:
        ids = room.squads_2024.get(team.franchise_code, set())
        squad = [room.players[pid] for pid in ids if pid in room.players]
        squad.sort(key=lambda p: p.base_impact_score, reverse=True)
        return squad

    # ------------------------------------------------------------ retention
    async def start_retention(self, room_code: str) -> RoomState:
        async with self.lock(room_code):
            room = await self.load_room(room_code)
            if room.status != "LOBBY":
                return room

            room.status = "RETENTION"
            room.retention_deadline = time.time() + settings.RETENTION_TIMEOUT_SECONDS

            for team in room.teams.values():
                if team.is_ai:
                    picks = ai_retention_agent.decide_retentions(
                        team, self.squad_2024_of(room, team), self.venue_for(room, team)
                    )
                    self._apply_retentions(room, team, picks)

            await self._persist_room_status(room)

        await self._send(room_code, "ROOM_UPDATE", room.public())
        # Watchdog: if a human never confirms, AI completes their picks on expiry.
        self.tasks[f"{room_code}:retention"] = asyncio.create_task(
            self._retention_watchdog(room)
        )
        await self._maybe_start_auction(room)
        return room

    async def _retention_watchdog(self, room: RoomState) -> None:
        while room.status == "RETENTION":
            await asyncio.sleep(1.0)
            remaining = max(0, int(round(room.retention_deadline - time.time())))
            await self._send(room.code, "RETENTION_TICK", {"seconds_remaining": remaining})
            if remaining <= 0:
                await self._maybe_start_auction(room)
                return

    def _apply_retentions(self, room: RoomState, team: TeamState, picks: List[dict]) -> List[dict]:
        priced = retention_engine.assign_slots(picks)
        for pick in priced:
            player = room.players.get(pick["player_id"])
            if player is None:
                continue
            team.add(player, pick["retention_cost_lakh"], "RETENTION")
        team.rtm_cards = retention_engine.calculate_rtm_cards(len(priced))
        team.retention_confirmed = True
        return priced

    async def submit_retention(
        self, room_code: str, team_id: str, player_ids: List[str]
    ) -> tuple[bool, str]:
        async with self.lock(room_code):
            room = self.rooms.get(room_code)
            if room is None or room.status != "RETENTION":
                return False, "Retention phase is not open"

            team = room.teams.get(team_id)
            if team is None:
                return False, "Unknown team"
            if team.retention_confirmed:
                return False, "Already confirmed"

            owned = room.squads_2024.get(team.franchise_code, set())
            picks = []
            for pid in player_ids:
                if pid not in owned:
                    return False, "Player was not in your 2024 squad"
                player = room.players.get(pid)
                if player is None:
                    return False, "Unknown player"
                picks.append({"player_id": pid, "is_capped": player.is_capped})

            priced = retention_engine.assign_slots(picks)
            ok, reason = retention_engine.validate(picks, team.purse_remaining_lakh)
            if not ok:
                return False, reason

            self._apply_retentions(room, team, picks)
            await self._persist_retentions(room, team, priced)

        await self._send(room_code, "ROOM_UPDATE", room.public())
        await self._maybe_start_auction(room)
        return True, ""

    async def _maybe_start_auction(self, room: RoomState) -> None:
        if room.status != "RETENTION":
            return
        pending = [t for t in room.teams.values() if not t.retention_confirmed]
        timed_out = time.time() >= room.retention_deadline
        if pending and not timed_out:
            return

        async with self.lock(room.code):
            for team in pending:  # auto-complete anyone who ran out of time
                picks = ai_retention_agent.decide_retentions(
                    team, self.squad_2024_of(room, team), self.venue_for(room, team)
                )
                self._apply_retentions(room, team, picks)

            self._build_pool(room)
            room.status = "IN_PROGRESS"
            await self._persist_room_status(room)

        await self._send(room.code, "RETENTION_COMPLETE", room.public())
        self.tasks[room.code] = asyncio.create_task(self._auction_loop(room))

    def _build_pool(self, room: RoomState) -> None:
        retained = {item.player_id for team in room.teams.values() for item in team.roster}
        pool = [p for pid, p in room.players.items() if pid not in retained]

        limit = FORMAT_LOTS.get(room.auction_format)
        if limit is not None and len(pool) > limit:
            # Keep the most valuable players, then restore auctioneer order.
            pool.sort(key=lambda p: p.base_impact_score, reverse=True)
            pool = pool[:limit]

        # Auctioneer order: by set, then most expensive base price first.
        pool.sort(key=lambda p: (p.set_order, -p.base_price_lakh, p.name))
        room.queue = [p.id for p in pool]
        room.total_lots = len(pool)
        room.lots_done = 0

        # Scale the legal minimum squad to what this pool can actually supply,
        # otherwise the purse-reserve rule freezes every team in a short format.
        teams = len(room.teams) or 1
        retained_avg = sum(len(t.roster) for t in room.teams.values()) / teams
        reachable = int(retained_avg + (len(pool) / teams) * 0.85)
        room.min_squad_size = max(9, min(settings.MIN_SQUAD_SIZE, reachable))

    # -------------------------------------------------------------- auction
    def _next_player(self, room: RoomState) -> Optional[PlayerRef]:
        while room.queue:
            return room.players[room.queue.pop(0)]
        while room.revisit:
            return room.players[room.revisit.pop(0)]
        return None

    def _any_team_can_still_buy(self, room: RoomState) -> bool:
        return any(
            len(t.roster) < settings.MAX_SQUAD_SIZE and t.purse_remaining_lakh >= 30
            for t in room.teams.values()
        )

    async def _auction_loop(self, room: RoomState) -> None:
        try:
            while True:
                player = self._next_player(room)
                if player is None or not self._any_team_can_still_buy(room):
                    break
                await self._run_lot(room, player)
                await asyncio.sleep(1.2)  # a beat between lots, so the UI can land

            room.status = "COMPLETED"
            await self._persist_room_status(room)
            await self._send(room.code, "AUCTION_COMPLETED", self.results(room))
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # keep a crash visible instead of silently stalling
            await self._send(room.code, "ERROR", {"reason": f"Auction loop failed: {exc}"})
            raise

    async def _run_lot(self, room: RoomState, player: PlayerRef) -> None:
        now = time.time()
        lot = LotState(
            player=player,
            deadline=now + settings.BID_TIMER_SECONDS,
            hard_deadline=now + settings.MAX_LOT_SECONDS,
            revisit_count=room.revisit_counts.get(player.id, 0),
        )
        room.lot = lot

        await self._send(room.code, "LOT_STARTED", {
            "lot": lot.public(),
            "next_bid_lakh": rules.next_bid(None, player.base_price_lakh),
            "lots_done": room.lots_done,
            "total_lots": room.total_lots,
        })
        await self._send(room.code, "IMPACT_SCORES", self._impact_for_all(room, player))

        # Each AI franchise gets its own reaction time for this lot.
        think_at = {
            t.id: time.time() + rule_based_bidder.think_delay()
            for t in room.teams.values() if t.is_ai
        }
        last_tick = -1

        while lot.status == "BIDDING":
            now = time.time()

            if now >= lot.deadline or now >= lot.hard_deadline:
                break

            async with self.lock(room.code):
                for team_id, due in list(think_at.items()):
                    if now < due or lot.status != "BIDDING":
                        continue
                    team = room.teams[team_id]
                    amount = rule_based_bidder.decide(
                        room, team, lot, self.venue_for(room, team)
                    )
                    if amount is not None:
                        self._accept_bid(room, lot, team, amount)
                        await self._broadcast_bid(room, lot, team)
                        # Everyone re-thinks once the price moves.
                        think_at = {
                            t.id: time.time() + rule_based_bidder.think_delay()
                            for t in room.teams.values() if t.is_ai
                        }
                        break
                    think_at[team_id] = now + rule_based_bidder.think_delay()

            remaining = lot.seconds_remaining
            if remaining != last_tick:
                last_tick = remaining
                await self._send(room.code, "TIMER_TICK", {"seconds_remaining": remaining})

            await asyncio.sleep(0.2)

        # Shut the gate under the lock, so a bid that arrives in the same tick as
        # the expiry is either fully accepted or cleanly rejected -- never half-applied.
        async with self.lock(room.code):
            if lot.status == "BIDDING":
                lot.status = "CLOSING"
        await self._close_lot(room, lot)

    def _accept_bid(self, room: RoomState, lot: LotState, team: TeamState, amount: int) -> None:
        lot.current_bid_lakh = amount
        lot.leading_team_id = team.id
        lot.history.append(BidRecord(team.id, team.franchise_code, amount))
        lot.deadline = time.time() + settings.BID_RESET_SECONDS

    async def _broadcast_bid(self, room: RoomState, lot: LotState, team: TeamState) -> None:
        await self._send(room.code, "BID_PLACED", {
            "team_id": team.id,
            "franchise_code": team.franchise_code,
            "amount_lakh": lot.current_bid_lakh,
            "next_bid_lakh": rules.next_bid(lot.current_bid_lakh, lot.player.base_price_lakh),
            "seconds_remaining": lot.seconds_remaining,
            "history": [b.public() for b in lot.history[-8:]],
        })
        await self._maybe_announce_war(room, lot)

    async def _maybe_announce_war(self, room: RoomState, lot: LotState) -> None:
        """Flag a two-team duel, with a side-by-side of where each side stands."""
        if len(lot.history) < WAR_BIDS:
            return

        recent = lot.history[-WAR_BIDS:]
        duellists = {b.team_id for b in recent}
        if len(duellists) != 2:
            return

        # Announce on the bid that starts the duel, then periodically after.
        depth = len(lot.history)
        if depth != WAR_BIDS and (depth - WAR_BIDS) % WAR_REPEAT_EVERY != 0:
            return

        # Order by who is currently in front.
        ordered = sorted(duellists, key=lambda tid: tid != lot.leading_team_id)
        teams = [room.teams[tid] for tid in ordered if tid in room.teams]
        if len(teams) != 2:
            return

        opened_at = lot.history[0].amount_lakh
        await self._send(room.code, "BIDDING_WAR", {
            "player": lot.player.public(),
            "price_lakh": lot.current_bid_lakh,
            "opened_at_lakh": opened_at,
            "bids": depth,
            "leading_team_id": lot.leading_team_id,
            "teams": [
                {
                    **t.public(),
                    "spent_lakh": settings.DEFAULT_PURSE_LAKH - t.purse_remaining_lakh,
                    "last_bid_lakh": next(
                        (b.amount_lakh for b in reversed(lot.history) if b.team_id == t.id),
                        None,
                    ),
                }
                for t in teams
            ],
        })

    async def place_bid(self, room_code: str, team_id: str, amount: int) -> tuple[bool, str]:
        async with self.lock(room_code):
            room = self.rooms.get(room_code)
            if room is None or room.lot is None or room.lot.status != "BIDDING":
                return False, "No lot open for bidding"

            lot, team = room.lot, room.teams.get(team_id)
            if time.time() >= min(lot.deadline, lot.hard_deadline):
                return False, "Too late — the hammer is down"
            if team is None:
                return False, "Unknown team"
            if lot.leading_team_id == team.id:
                return False, "You are already the highest bidder"

            expected = rules.next_bid(lot.current_bid_lakh, lot.player.base_price_lakh)
            if amount != expected:
                # Someone else got the lock first and the price moved.
                return False, f"Bid must be {expected}L"

            allowed, reason = rules.can_bid(team, lot.player, amount, room.min_squad_size)
            if not allowed:
                return False, reason

            self._accept_bid(room, lot, team, amount)

        await self._broadcast_bid(room, room.lot, team)
        return True, ""

    # ------------------------------------------------------------------ RTM
    async def _close_lot(self, room: RoomState, lot: LotState) -> None:
        if lot.leading_team_id is None:
            await self._mark_unsold(room, lot)
            return

        winner = room.teams[lot.leading_team_id]
        owner = room.owner_2024(lot.player.id)

        eligible = (
            owner is not None
            and owner.id != winner.id
            and owner.rtm_cards > 0
            and rules.can_bid(owner, lot.player, lot.current_bid_lakh, room.min_squad_size)[0]
        )
        if not eligible:
            await self._sell(room, lot, winner, lot.current_bid_lakh, "AUCTION")
            return

        await self._run_rtm(room, lot, owner, winner)

    async def _run_rtm(self, room: RoomState, lot: LotState, owner: TeamState, winner: TeamState) -> None:
        lot.status = "RTM_PENDING"
        lot.rtm_team_id = owner.id
        lot.rtm_deadline = time.time() + settings.RTM_DECISION_SECONDS

        await self._send(room.code, "RTM_WINDOW", {
            "player": lot.player.public(),
            "rtm_team_id": owner.id,
            "rtm_franchise_code": owner.franchise_code,
            "winning_team_id": winner.id,
            "winning_franchise_code": winner.franchise_code,
            "price_lakh": lot.current_bid_lakh,
            "seconds": settings.RTM_DECISION_SECONDS,
        })

        exercised = await self._await_decision(
            room, lot, owner,
            prompt_event="RTM_PROMPT",
            prompt_payload={
                "player": lot.player.public(),
                "price_lakh": lot.current_bid_lakh,
                "rtm_cards_remaining": owner.rtm_cards,
                "seconds": settings.RTM_DECISION_SECONDS,
            },
            ai_choice=lambda: rule_based_bidder.rtm_decision(
                room, owner, lot, self.venue_for(room, owner), room.min_squad_size
            ),
        )

        owner.rtm_cards -= 1  # the card is spent either way

        if not exercised:
            await self._send(room.code, "RTM_DECLINED", {
                "team_id": owner.id, "franchise_code": owner.franchise_code,
            })
            await self._sell(room, lot, winner, lot.current_bid_lakh, "AUCTION")
            return

        # Real 2025 rule: the original bidder gets exactly one raise, and the
        # RTM team must then pay that number or let the player go.
        final_price = lot.current_bid_lakh
        raise_to = lot.current_bid_lakh + rules.increment_for(lot.current_bid_lakh) * 2
        can_raise = rules.can_bid(winner, lot.player, raise_to, room.min_squad_size)[0]

        if can_raise:
            lot.rtm_deadline = time.time() + settings.RTM_DECISION_SECONDS
            raised = await self._await_decision(
                room, lot, winner,
                prompt_event="RTM_COUNTER_PROMPT",
                prompt_payload={
                    "player": lot.player.public(),
                    "current_price_lakh": lot.current_bid_lakh,
                    "raise_to_lakh": raise_to,
                    "rtm_franchise_code": owner.franchise_code,
                    "seconds": settings.RTM_DECISION_SECONDS,
                },
                ai_choice=lambda: raise_to <= rule_based_bidder.value_ceiling(
                    winner, lot.player, self.venue_for(room, winner), room.min_squad_size
                ),
            )
            if raised:
                final_price = raise_to
                await self._send(room.code, "RTM_COUNTERED", {
                    "franchise_code": winner.franchise_code, "price_lakh": raise_to,
                })

        if rules.can_bid(owner, lot.player, final_price, room.min_squad_size)[0]:
            await self._sell(room, lot, owner, final_price, "RTM")
        else:
            # Priced out of their own match -- the original bidder keeps the player.
            await self._send(room.code, "RTM_LAPSED", {
                "franchise_code": owner.franchise_code,
                "reason": "Could not match the raised price",
            })
            await self._sell(room, lot, winner, lot.current_bid_lakh, "AUCTION")

    async def _await_decision(
        self, room: RoomState, lot: LotState, team: TeamState,
        prompt_event: str, prompt_payload: dict, ai_choice,
    ) -> bool:
        """Ask a team yes/no. AI answers itself; humans get a private prompt."""
        if team.is_ai or team.user_id is None:
            await asyncio.sleep(random.uniform(0.8, 1.8))
            return bool(ai_choice())

        self._pending_decision = getattr(self, "_pending_decision", {})
        key = (room.code, team.id)
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending_decision[key] = future

        await self._send(room.code, prompt_event, prompt_payload, team.user_id)
        try:
            return bool(await asyncio.wait_for(future, timeout=settings.RTM_DECISION_SECONDS))
        except asyncio.TimeoutError:
            return False
        finally:
            self._pending_decision.pop(key, None)

    async def resolve_decision(self, room_code: str, team_id: str, choice: bool) -> bool:
        pending = getattr(self, "_pending_decision", {})
        future = pending.get((room_code, team_id))
        if future is None or future.done():
            return False
        future.set_result(choice)
        return True

    # ----------------------------------------------------------- settlement
    async def _sell(
        self, room: RoomState, lot: LotState, team: TeamState, price: int, acquisition: str
    ) -> None:
        lot.status = "SOLD"
        team.add(lot.player, price, acquisition)
        room.lots_done += 1

        await self._persist_sale(room, team, lot.player, price, acquisition)
        await self._send(room.code, "LOT_SOLD", {
            "player": lot.player.public(),
            "team_id": team.id,
            "franchise_code": team.franchise_code,
            "price_lakh": price,
            "acquisition_type": acquisition,
            "team": team.public(),
        })
        await self._send(room.code, "ROOM_UPDATE", room.public())

    async def _mark_unsold(self, room: RoomState, lot: LotState) -> None:
        lot.status = "UNSOLD"
        room.lots_done += 1
        seen = room.revisit_counts.get(lot.player.id, 0)
        revisit = seen < rules.MAX_REVISITS
        if lot.player.id not in room.unsold_log:
            room.unsold_log.append(lot.player.id)
        if revisit:
            room.revisit_counts[lot.player.id] = seen + 1
            room.revisit.append(lot.player.id)
            # A second pass is another lot under the hammer, so the denominator
            # has to grow too -- otherwise progress runs past 100%.
            room.total_lots += 1

        await self._persist_unsold(room, lot.player, revisit)
        await self._send(room.code, "LOT_UNSOLD", {
            "player": lot.player.public(),
            "revisit": revisit,
            "unsold_count": len(room.unsold_players()),
        })

    def _impact_for_all(self, room: RoomState, player: PlayerRef) -> dict:
        stats = StatsView(player)
        per_team = {}
        for team in room.teams.values():
            result = impact_engine.compute_impact(
                player, stats, team.need(), self.venue_for(room, team)
            )
            per_team[team.id] = result.model_dump()
        return {"player_id": player.id, "per_team": per_team}

    def results(self, room: RoomState) -> dict:
        teams = []
        for team in room.teams.values():
            spent = settings.DEFAULT_PURSE_LAKH - team.purse_remaining_lakh
            squad_impact = sum(
                room.players[i.player_id].base_impact_score
                for i in team.roster if i.player_id in room.players
            )
            teams.append({
                **team.public(),
                "spent_lakh": spent,
                "squad_impact": round(squad_impact, 1),
                "avg_impact": round(squad_impact / len(team.roster), 1) if team.roster else 0.0,
                "roster": [i.public() for i in team.roster],
            })
        teams.sort(key=lambda t: t["squad_impact"], reverse=True)
        return {"teams": teams, "lots_done": room.lots_done, "total_lots": room.total_lots}

    # ----------------------------------------------------------- persistence
    async def _persist_room_status(self, room: RoomState) -> None:
        async with AsyncSessionLocal() as session:
            row = (await session.execute(
                select(Room).where(Room.id == room.id)
            )).scalar_one_or_none()
            if row is not None:
                row.status = RoomStatus(room.status)
            for team in room.teams.values():
                trow = (await session.execute(
                    select(Team).where(Team.id == team.id)
                )).scalar_one_or_none()
                if trow is not None:
                    trow.purse_remaining_lakh = team.purse_remaining_lakh
                    trow.overseas_slots_used = team.overseas_used
                    trow.retention_confirmed = team.retention_confirmed
            await session.commit()

    async def _persist_retentions(self, room: RoomState, team: TeamState, priced: List[dict]) -> None:
        async with AsyncSessionLocal() as session:
            for pick in priced:
                session.add(TeamRetention(
                    room_id=room.id,
                    team_id=team.id,
                    player_id=pick["player_id"],
                    retention_cost_lakh=pick["retention_cost_lakh"],
                    slot_no=pick["slot_no"],
                    is_uncapped=pick["is_uncapped"],
                ))
                session.add(RosterEntry(
                    team_id=team.id,
                    player_id=pick["player_id"],
                    acquisition_type=AcquisitionType.RETENTION,
                    price_lakh=pick["retention_cost_lakh"],
                ))
            session.add(RTMCard(room_id=room.id, team_id=team.id, cards_remaining=team.rtm_cards))
            await session.commit()

    async def _persist_unsold(
        self, room: RoomState, player: PlayerRef, returns_later: bool
    ) -> None:
        async with AsyncSessionLocal() as session:
            session.add(UnsoldRecord(
                room_id=room.id,
                player_id=player.id,
                pass_number=room.revisit_counts.get(player.id, 0) + 1,
                returns_later=returns_later,
            ))
            await session.commit()

    async def _persist_sale(
        self, room: RoomState, team: TeamState, player: PlayerRef, price: int, acquisition: str
    ) -> None:
        async with AsyncSessionLocal() as session:
            session.add(RosterEntry(
                team_id=team.id,
                player_id=player.id,
                acquisition_type=AcquisitionType(acquisition),
                price_lakh=price,
                round_number=room.lots_done,
            ))
            session.add(Bid(
                room_id=room.id, team_id=team.id, player_id=player.id,
                amount_lakh=price, is_winning=True,
            ))
            await session.commit()


auction_engine = AuctionEngine()
