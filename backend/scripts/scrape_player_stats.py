"""Builds real IPL performance stats from Cricsheet ball-by-ball data.

Cricsheet publishes every IPL delivery under an open licence, which is why it is
the source here rather than scraping Cricinfo: it is legal to redistribute,
stable in format, and detailed enough to compute the phase-specific metrics the
Impact Engine wants (powerplay SR, death-overs economy, dot-ball %).

    python scripts/scrape_player_stats.py            # download if needed, then build
    python scripts/scrape_player_stats.py --refresh  # force a fresh download

Writes data/player_stats.json. Players with no Cricsheet record (uncapped
newcomers, mostly) keep the deterministic fallback from build_seed_data.py so
every player still has a score.
"""

import argparse
import csv
import io
import json
import re
import sys
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.build_seed_data import PLAYERS, build_stats  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
ARCHIVE = RAW_DIR / "ipl_csv2.zip"
SOURCE_URL = "https://cricsheet.org/downloads/ipl_csv2.zip"

# Dismissals credited to the bowler.
BOWLER_WICKETS = {"bowled", "caught", "lbw", "stumped", "caught and bowled", "hit wicket"}

POWERPLAY_OVERS = range(0, 6)    # overs 1-6
DEATH_OVERS = range(16, 20)      # overs 17-20
RECENT_SEASONS = 3               # what counts as "current form"

# Cricsheet's scorecard names that (surname, initial) can't reach: it abbreviates
# given names, and a few players are filed under a different part of their name.
ALIASES = {
    "Dinesh Karthik": "KD Karthik",
    "Varun Chakravarthy": "CV Varun",
    "Wanindu Hasaranga": "PWH de Silva",
    "Dushmantha Chameera": "PVD Chameera",
    "Prasidh Krishna": "M Prasidh Krishna",
    "Sai Sudharsan": "B Sai Sudharsan",
    "Sai Kishore": "R Sai Kishore",
    "Vyshak Vijaykumar": "V Vyshak",
    "Mohsin Khan": "Mohsin Khan",
    "Nitish Kumar Reddy": "N Reddy",
}


def download(force: bool = False) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if ARCHIVE.exists() and not force:
        print(f"using cached {ARCHIVE.name} ({ARCHIVE.stat().st_size // 1024} KB)")
        return
    print(f"downloading {SOURCE_URL} ...")
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "ipl-auction-sim/1.0"})
    with urllib.request.urlopen(req, timeout=180) as res, open(ARCHIVE, "wb") as out:
        out.write(res.read())
    print(f"saved {ARCHIVE.stat().st_size // 1024} KB")


def norm(name: str) -> str:
    return re.sub(r"[^a-z ]", "", name.lower().replace("-", " ")).strip()


def key_of(name: str) -> tuple:
    """(surname, first initial) -- the only shape both naming styles share.

    Cricsheet writes 'V Kohli' and 'JJ Bumrah'; the master pool has full names
    like 'Virat Kohli' but also already-abbreviated ones like 'MS Dhoni'.
    """
    parts = norm(name).split()
    if not parts:
        return ("", "")
    return (parts[-1], parts[0][0] if parts[0] else "")


class Tally:
    def __init__(self) -> None:
        self.matches = set()
        self.bat_innings = set()
        self.bowl_innings = set()
        self.runs = 0
        self.balls_faced = 0
        self.dismissals = 0
        self.fours = 0
        self.sixes = 0
        self.pp_runs = 0
        self.pp_balls = 0
        self.death_runs = 0
        self.death_balls = 0
        self.balls_bowled = 0
        self.runs_conceded = 0
        self.wickets = 0
        self.dots = 0
        self.death_runs_conceded = 0
        self.death_balls_bowled = 0
        self.recent_balls = 0
        self.total_balls = 0
        self.impact_innings = 0


def read_match_meta(z: zipfile.ZipFile) -> tuple:
    """One pass over the info files for each match's winner and season."""
    winners, seasons = {}, {}
    for name in z.namelist():
        if not name.endswith("_info.csv"):
            continue
        match_id = name.replace("_info.csv", "")
        for row in csv.reader(io.StringIO(z.read(name).decode("utf-8", "replace"))):
            if len(row) < 3 or row[0] != "info":
                continue
            if row[1] == "winner":
                winners[match_id] = row[2]
            elif row[1] == "season":
                try:
                    # Seasons appear as "2024" or spanning as "2007/08".
                    seasons[match_id] = int(str(row[2])[:4])
                except ValueError:
                    pass
    return winners, seasons


def build_tallies(latest_season: int, z: zipfile.ZipFile, match_files: list, winners: dict) -> dict:
    tallies = defaultdict(Tally)

    # Per (match, innings, player) running totals, to score match-winning knocks.
    per_innings_runs = defaultdict(int)
    per_innings_wkts = defaultdict(int)
    innings_team = {}

    for idx, filename in enumerate(match_files):
        if idx % 250 == 0:
            print(f"  parsing match {idx}/{len(match_files)}", flush=True)

        reader = csv.DictReader(io.StringIO(z.read(filename).decode("utf-8", "replace")))
        match_id = filename[:-4]

        for row in reader:
            try:
                over = int(float(row["ball"]))
                season = int(str(row["season"])[:4])
            except (ValueError, TypeError, KeyError):
                continue

            innings = row["innings"]
            striker, bowler = row["striker"], row["bowler"]
            runs_off_bat = int(row["runs_off_bat"] or 0)
            wides = int(row["wides"] or 0)
            noballs = int(row["noballs"] or 0)
            byes = int(row["byes"] or 0)
            legbyes = int(row["legbyes"] or 0)
            extras = int(row["extras"] or 0)
            is_recent = season > latest_season - RECENT_SEASONS

            # ---------------------------------------------------------- batting
            bat = tallies[striker]
            bat.matches.add(match_id)
            bat.bat_innings.add((match_id, innings))
            innings_team[(match_id, innings, striker)] = row["batting_team"]
            bat.runs += runs_off_bat
            per_innings_runs[(match_id, innings, striker)] += runs_off_bat
            bat.total_balls += 1
            if is_recent:
                bat.recent_balls += 1

            if not wides:  # a wide is not a ball faced
                bat.balls_faced += 1
                if over in POWERPLAY_OVERS:
                    bat.pp_balls += 1
                    bat.pp_runs += runs_off_bat
                elif over in DEATH_OVERS:
                    bat.death_balls += 1
                    bat.death_runs += runs_off_bat

            if runs_off_bat == 4:
                bat.fours += 1
            elif runs_off_bat == 6:
                bat.sixes += 1

            # ---------------------------------------------------------- bowling
            bwl = tallies[bowler]
            bwl.matches.add(match_id)
            bwl.bowl_innings.add((match_id, innings))
            # Byes and leg-byes are not charged to the bowler.
            conceded = runs_off_bat + wides + noballs
            bwl.runs_conceded += conceded
            if not wides and not noballs:
                bwl.balls_bowled += 1
                if runs_off_bat == 0 and extras - byes - legbyes == 0:
                    bwl.dots += 1
            if over in DEATH_OVERS:
                bwl.death_runs_conceded += conceded
                if not wides and not noballs:
                    bwl.death_balls_bowled += 1

            # --------------------------------------------------------- wickets
            if row.get("player_dismissed"):
                if row["player_dismissed"] == striker:
                    bat.dismissals += 1
                if (row.get("wicket_type") or "").lower() in BOWLER_WICKETS:
                    bwl.wickets += 1
                    per_innings_wkts[(match_id, innings, bowler)] += 1
                    innings_team.setdefault((match_id, innings, bowler), row["bowling_team"])

    # A "match-winning innings": 30+ runs or 3+ wickets, on the winning side.
    for key, runs in per_innings_runs.items():
        match_id, _, player = key
        if runs >= 30 and winners.get(match_id) == innings_team.get(key):
            tallies[player].impact_innings += 1
    for key, wkts in per_innings_wkts.items():
        match_id, _, player = key
        if wkts >= 3 and winners.get(match_id) == innings_team.get(key):
            tallies[player].impact_innings += 1

    return tallies


def to_stats(t: Tally) -> dict:
    """Turn raw tallies into the stat shape seed_db.py loads. None where unknown.

    The minimum-volume guards matter: a bowler who has sent down two overs in his
    career would otherwise post a spectacular economy and outrank real bowlers.
    """
    def ratio(num, den, scale=1.0):
        return round(num / den * scale, 2) if den else None

    runs_from_boundaries = t.fours * 4 + t.sixes * 6
    overs_bowled = t.balls_bowled / 6 if t.balls_bowled else 0
    death_overs = t.death_balls_bowled / 6 if t.death_balls_bowled else 0

    return {
        "matches": len(t.matches),
        "innings": len(t.bat_innings),
        "batting_avg": ratio(t.runs, t.dismissals) if t.balls_faced >= 60 else None,
        "strike_rate": ratio(t.runs, t.balls_faced, 100) if t.balls_faced >= 60 else None,
        "powerplay_sr": ratio(t.pp_runs, t.pp_balls, 100) if t.pp_balls >= 30 else None,
        "death_overs_sr": ratio(t.death_runs, t.death_balls, 100) if t.death_balls >= 30 else None,
        "boundary_pct": ratio(runs_from_boundaries, t.runs, 100) if t.runs >= 100 else None,
        "bowling_avg": ratio(t.runs_conceded, t.wickets) if t.wickets >= 5 else None,
        "economy": ratio(t.runs_conceded, overs_bowled) if t.balls_bowled >= 120 else None,
        "wickets": t.wickets if t.balls_bowled else None,
        "bowling_sr": ratio(t.balls_bowled, t.wickets) if t.wickets >= 5 else None,
        "death_overs_economy": (
            ratio(t.death_runs_conceded, death_overs) if t.death_balls_bowled >= 60 else None
        ),
        "dot_ball_pct": ratio(t.dots, t.balls_bowled, 100) if t.balls_bowled >= 120 else None,
        "match_winning_innings": t.impact_innings,
        # Share of career deliveries in the last few seasons -- real evidence of
        # current form, replacing the age proxy the engine used before.
        "recency": round(t.recent_balls / t.total_balls, 3) if t.total_balls else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="re-download the archive")
    args = parser.parse_args()

    download(force=args.refresh)

    with zipfile.ZipFile(ARCHIVE) as z:
        match_files = sorted(n for n in z.namelist() if re.fullmatch(r"\d+\.csv", n))
        print(f"{len(match_files)} matches in archive")

        winners, seasons = read_match_meta(z)
        # Read every season rather than sampling: the filenames are numeric ids
        # sorted as strings, so the "last" ones are the oldest six-digit matches.
        latest_season = max(seasons.values()) if seasons else 0
        print(f"seasons {min(seasons.values())}-{latest_season}, "
              f"recent = {latest_season - RECENT_SEASONS + 1}+")

        tallies = build_tallies(latest_season, z, match_files, winners)

    print(f"{len(tallies)} distinct players in ball-by-ball data")

    # Index Cricsheet names by (surname, initial); on collision prefer the busier
    # player, so 'S Sharma' resolves to the one with a real career.
    index, by_surname = {}, defaultdict(list)
    for cric_name, t in tallies.items():
        workload = t.total_balls + t.balls_bowled
        k = key_of(cric_name)
        if k not in index or workload > index[k][1]:
            index[k] = (cric_name, workload)
        by_surname[k[0]].append((cric_name, workload))

    def resolve(name: str):
        if name in ALIASES:
            alias = ALIASES[name]
            if alias in tallies:
                return (alias, 0)
        hit = index.get(key_of(name))
        if hit:
            return hit
        # Last resort: an unambiguous surname is good enough.
        candidates = by_surname.get(key_of(name)[0], [])
        if len(candidates) == 1:
            return candidates[0]
        return None

    out, matched, unmatched = [], 0, []
    for name, nation, role, capped, base, rating, age, franchise in PLAYERS:
        hit = resolve(name)
        if hit and tallies[hit[0]].matches:
            stats = to_stats(tallies[hit[0]])
            stats.update(player_name=name, source="cricsheet", cricsheet_name=hit[0])
            matched += 1
        else:
            stats = build_stats(name, role, rating, age, capped)
            stats.update(player_name=name, source="generated")
            stats.setdefault("recency", None)
            unmatched.append(name)
        out.append(stats)

    (DATA_DIR / "player_stats.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"\nmatched {matched}/{len(PLAYERS)} players to real Cricsheet records")
    print(f"{len(unmatched)} fell back to generated stats")
    if unmatched:
        print("  " + ", ".join(unmatched[:18]) + (" ..." if len(unmatched) > 18 else ""))

    print("\nspot check:")
    for want in ("Virat Kohli", "Jasprit Bumrah", "Andre Russell", "Sunil Narine"):
        row = next((r for r in out if r["player_name"] == want), None)
        if row:
            print(f"  {want:18s} src={row['source']:9s} M={row['matches']:>3} "
                  f"SR={row.get('strike_rate')} econ={row.get('economy')} "
                  f"wkts={row.get('wickets')} MWI={row['match_winning_innings']}")


if __name__ == "__main__":
    main()
