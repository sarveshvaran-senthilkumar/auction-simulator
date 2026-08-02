"""Bid increments and squad-composition rules."""

from typing import Optional, Tuple

from ..config import settings

# (up to this bid in lakh, increment in lakh)
#
# The real ladder stays at 25L all the way up, which needs ~110 separate bids to
# move a marquee lot from a 2cr base to 14cr. On a phone that is minutes of
# watching the number tick, so the steps widen above 5cr. Lots land on the same
# prices; they just get there in about a quarter of the bids.
INCREMENT_LADDER = [
    (100, 5),
    (200, 10),
    (500, 25),
    (1_000, 50),
    (10_000, 100),
]

MAX_REVISITS = 1  # an unsold player comes back once, then is out for good


def increment_for(current_bid_lakh: int) -> int:
    for ceiling, step in INCREMENT_LADDER:
        if current_bid_lakh < ceiling:
            return step
    return INCREMENT_LADDER[-1][1]


def next_bid(current_bid_lakh: Optional[int], base_price_lakh: int) -> int:
    """The only legal amount a team may bid next."""
    if current_bid_lakh is None:
        return base_price_lakh
    return current_bid_lakh + increment_for(current_bid_lakh)


def can_bid(team, player, amount_lakh: int, min_squad: int = None) -> Tuple[bool, str]:
    """Server-side gate. Returns (allowed, reason_if_not)."""
    min_squad = settings.MIN_SQUAD_SIZE if min_squad is None else min_squad

    if team.purse_remaining_lakh < amount_lakh:
        return False, "Not enough purse"

    if len(team.roster) >= settings.MAX_SQUAD_SIZE:
        return False, "Squad is full (25)"

    if player.is_overseas and team.overseas_used >= settings.MAX_OVERSEAS:
        return False, "Overseas quota full (8)"

    # A team must leave enough purse to reach the minimum legal squad size.
    slots_after = min_squad - (len(team.roster) + 1)
    if slots_after > 0:
        reserve = slots_after * 30  # every remaining slot needs at least a 30L base
        if team.purse_remaining_lakh - amount_lakh < reserve:
            return False, f"Must keep {reserve}L to fill {slots_after} more slots"

    return True, ""


def must_bid(team, min_squad: int = None) -> bool:
    """True when a team still has to fill slots to reach the legal minimum."""
    min_squad = settings.MIN_SQUAD_SIZE if min_squad is None else min_squad
    return len(team.roster) < min_squad
