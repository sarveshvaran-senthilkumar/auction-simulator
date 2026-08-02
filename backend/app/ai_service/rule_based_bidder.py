"""Rule-based AI franchise. Impact-driven, purse-disciplined, individually jittered."""

import random
from typing import Optional

from ..config import settings
from ..engine import rules
from .impact_engine import TARGET_ROLE_MIX, StatsView, impact_engine


class RuleBasedBidder:
    @staticmethod
    def urgency(room, team, min_squad: int) -> float:
        """0 when there is plenty of auction left, 1 when lots are running out.

        Without this, the franchises with the luckiest aggression jitter win every
        contest and the rest finish on four players -- especially in the short
        formats, where the pool is all premium players and there are no cheap
        fillers late on to mop up with.
        """
        needed = min_squad - len(team.roster)
        if needed <= 0:
            return 0.0
        lots_left = len(getattr(room, "queue", [])) + len(getattr(room, "revisit", []))
        if lots_left <= 0:
            return 1.0
        teams = max(1, len(getattr(room, "teams", {})))
        # Lots this team would need to win, against its fair share of what's left.
        return max(0.0, min(1.0, (needed * teams) / lots_left))

    def value_ceiling(
        self, team, player, venue, min_squad: Optional[int] = None, urgency: float = 0.0
    ) -> int:
        """The most this franchise will pay for this player, right now."""
        min_squad = settings.MIN_SQUAD_SIZE if min_squad is None else min_squad

        impact = impact_engine.compute_impact(
            player, StatsView(player), team.need(), venue
        )
        ceiling = impact.suggested_value_lakh

        # Hard brake on hoarding: once a role is at its target the next one is
        # worth a fraction, and the one after that almost nothing. Without this
        # the batter-heavy early sets let a team buy eight openers.
        have = team.role_counts.get(player.role, 0)
        target = TARGET_ROLE_MIX.get(player.role, 4)
        if have >= target:
            ceiling = int(ceiling * max(0.12, 0.5 ** (have - target + 1)))

        # Purse discipline: never blow the budget needed for the remaining slots.
        slots_to_fill = max(1, min_squad - len(team.roster))
        sustainable = int(team.purse_remaining_lakh / slots_to_fill * 3.2)

        # Running short of lots relative to slots -- stop being precious. Kept
        # deliberately mild: a bigger multiplier here pushes every marquee lot to
        # the top of the purse and makes RTM permanently unaffordable.
        if urgency > 0:
            ceiling = int(ceiling * (1 + urgency * 0.35))
            sustainable = int(sustainable * (1 + urgency * 0.25))

        return max(player.base_price_lakh, min(ceiling, sustainable))

    def decide(self, room, team, lot, venue) -> Optional[int]:
        """Returns the amount to bid, or None to pass."""
        player = lot.player
        min_squad = getattr(room, "min_squad_size", settings.MIN_SQUAD_SIZE)

        if lot.leading_team_id == team.id:
            return None  # never bid against yourself

        amount = rules.next_bid(lot.current_bid_lakh, player.base_price_lakh)
        allowed, _ = rules.can_bid(team, player, amount, min_squad)
        if not allowed:
            return None

        urgency = self.urgency(room, team, min_squad)
        ceiling = self.value_ceiling(team, player, venue, min_squad, urgency)
        if amount > ceiling:
            return None

        # Bidding thins out as the price approaches a team's ceiling, so lots
        # don't always run to the exact same number.
        headroom = (ceiling - amount) / max(1.0, ceiling)
        appetite = min(0.96, 0.25 + headroom * 1.5)

        # A team that still has to reach the legal minimum bids far more freely
        # on cheap lots than its valuation alone would suggest.
        if rules.must_bid(team, min_squad) and amount <= 200:
            appetite = max(appetite, 0.85)

        # And harder still once the lots left won't go round.
        if urgency > 0:
            appetite = max(appetite, 0.45 + urgency * 0.5)

        if random.random() > appetite:
            return None

        return amount

    def think_delay(self) -> float:
        return random.uniform(settings.AI_MIN_DELAY_MS, settings.AI_MAX_DELAY_MS) / 1000.0

    def rtm_decision(self, room, team, lot, venue, min_squad: Optional[int] = None) -> bool:
        """Should this team spend an RTM card to match the winning bid?"""
        if team.rtm_cards <= 0 or lot.current_bid_lakh is None:
            return False
        allowed, _ = rules.can_bid(team, lot.player, lot.current_bid_lakh, min_squad)
        if not allowed:
            return False
        # Evaluate at the same urgency the bidders used -- otherwise the RTM team
        # is comparing a live auction price against a becalmed valuation and
        # always declines.
        urgency = self.urgency(room, team, min_squad or settings.MIN_SQUAD_SIZE)
        ceiling = self.value_ceiling(team, lot.player, venue, min_squad, urgency)
        # RTM is worth using slightly above the open-market ceiling -- you are
        # buying back a known quantity and denying a rival.
        return lot.current_bid_lakh <= ceiling * 1.12



rule_based_bidder = RuleBasedBidder()
