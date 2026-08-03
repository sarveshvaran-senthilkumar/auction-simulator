# IPL Auction Simulator — Mobile

A phone-first IPL mega-auction game. Ten franchises, a ₹120 Cr purse, a retention
phase on the real 2025 slab rules, RTM cards, and nine AI franchises bidding
against you in real time over a WebSocket.

Runs as an installable PWA — open it in your phone's browser and add it to the
home screen. No app store, no native toolchain.

## Prerequisites

- Python 3.11+
- Node.js 18+

That's it. The app ships with a seeded SQLite database — no PostgreSQL, no MongoDB.

## Setup

### Backend

```bash
cd backend
python -m venv venv
# Windows:   .\venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt

python scripts/build_seed_data.py      # writes data/*.json (256 players, 10 squads)
python scripts/scrape_player_stats.py  # real career stats from Cricsheet (~1 min)
python -m app.db.seed_db               # loads everything into auction.db

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite prints a `Network:` URL such as `http://192.168.0.5:5173`. **Open that on
your phone** (same Wi-Fi) — the dev server proxies `/api` and `/ws` to the
backend, so nothing else needs configuring. In Safari or Chrome, use *Share →
Add to Home Screen* to install it.

## Accounts

The app opens on a sign-in screen. Create an account with a username, email and
password — that name is what appears in the lobby, the bid feed and the
`Welcome, <you>` greeting on the home screen.

### Google sign-in (optional)

The "Continue with Google" button only appears once you supply a client id;
without one the app just uses username/password. To enable it:

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   -> **Create Credentials** -> **OAuth client ID** -> **Web application**.
2. Under **Authorised JavaScript origins**, add the URLs you actually open the
   app from, e.g. `http://localhost:5173` and `http://192.168.11.249:5173`.
   Google matches these exactly, so add every host you use, including your phone's.
3. Copy the client id into `backend/.env`:

```ini
GOOGLE_CLIENT_ID=1234567890-abcdefg.apps.googleusercontent.com
SECRET_KEY=some-long-random-string
```

4. Restart the backend. The button appears on both the login and register screens.

Google accounts are matched to existing password accounts by verified email, so
signing in either way reaches the same franchise history.

> `SECRET_KEY` signs every session token. Change it from the default before
> exposing the app beyond your own network.

## How a game goes

1. **Create** a room, pick an auction length, and share the 6-character code.
2. **Lobby** — claim a franchise. Everything unclaimed is run by the AI.
3. **Retention** — pick up to 6 players from your 2024 squad. Capped slots cost
   ₹18/14/11/18/14 Cr in pick order, uncapped a flat ₹4 Cr. Every player you
   *don't* retain becomes an RTM card (6 − retained).
4. **Auction** — lots run by set (Marquee first), one tap to bid. You get a
   banner when you take the lead, when you're outbid, and when a lot closes. If
   two franchises trade six bids on the same player, a bidding-war card slides
   in showing both sides' purse, squad and RTM cards. When a player from your
   2024 squad is about to be sold elsewhere you get an RTM prompt: match the
   price, the winning bidder gets one raise, and you pay that or let them go.
   Players who draw no bid land in the **Unsold** tab and most come back for a
   second pass later on.
5. **Results** — squads ranked by total Impact Score, with the biggest buys.

### Auction length

| Format | Lots | Rough sitting |
| --- | --- | --- |
| Quick | 80 | ~30 min |
| Standard | 150 | ~1 hour |
| Full | everyone unretained | 2 hours+ |

A real mega auction runs to 570 lots. The short formats keep the highest-impact
players and scale the legal minimum squad size down to match the smaller pool.

## Impact Score

Every player carries a 0–100 score, and every screen that shows one can explain it.

- **Layer 1 — base performance.** Role-weighted career stats against calibrated
  weights in `data/weights.json`, computed once at seed time. The numbers are
  **real**: `scripts/scrape_player_stats.py` derives them from Cricsheet's
  ball-by-ball record of all 1,243 IPL matches — strike rate, powerplay and
  death-overs splits, economy, dot-ball %, and match-winning performances.
  251 of 256 players match a real record; the handful of uncapped newcomers with
  no IPL history fall back to a generated estimate, flagged as `source:
  generated`.
  Scores are shrunk towards the league average in proportion to how many matches
  they're based on, so one hot season doesn't put a teenager above Kohli.
- **Layer 2 — context.** What the player is worth *to your side right now*: role
  scarcity, overseas slots left, home-ground pitch fit, longevity, budget headroom.
- **Layer 3 — value.** The blended score mapped through a price curve to a
  suggested rupee ceiling — which is also what the AI bids against.

Refresh the stats any time with:

```bash
python scripts/scrape_player_stats.py --refresh   # re-download from Cricsheet
python -m app.db.seed_db                          # recompute every score
```

Tap any player to see the full breakdown.

## Testing

```bash
# Backend: a complete AI-only auction, checking every rule invariant
cd backend && python scripts/smoke_auction.py

# Backend: HTTP + WebSocket client flow against a running server
python scripts/smoke_client.py

# Frontend: headless walk through Register -> Home -> Lobby -> Retention
cd frontend && npm install --no-save jsdom && npm run test:flow
```

## Notable adaptations from the original plan

The plan targeted a desktop, multi-database build. What changed, and why:

- **SQLite instead of PostgreSQL + MongoDB.** The app now starts with zero
  database setup. `DATABASE_URL` still accepts a Postgres URL if you want one.
- **Cricsheet instead of Cricinfo/BCCI scraping.** The plan scraped a BCCI PDF,
  Wikipedia and Cricinfo. Cricsheet publishes the same underlying data under an
  open licence in a stable format, so `scripts/scrape_player_stats.py` uses that
  and the fragile HTML scrapers were dropped. The player roster itself lives in
  a maintained table in `scripts/build_seed_data.py`.
- **Wider bid increments above ₹5 Cr.** The real ladder stays at ₹25 L, which
  needs ~110 separate bids to move a marquee lot from ₹2 Cr to ₹14 Cr. Lots land
  on the same prices, in about a quarter of the bids.
- **A hard per-lot time cap** (`MAX_LOT_SECONDS`). Bids reset the timer, so two
  well-funded teams could otherwise trade increments indefinitely.
- **Single-screen mobile layouts.** The three-column retention and auction
  screens became one scrolling column with a fixed header, a thumb-zone action
  bar, and bottom sheets for detail.

## Configuration

Backend settings live in `backend/app/config.py` and can be overridden with a
`backend/.env`:

| Setting | Default | Meaning |
| --- | --- | --- |
| `DEFAULT_PURSE_LAKH` | 12000 | ₹120 Cr per franchise |
| `BID_TIMER_SECONDS` | 15 | opening window on a fresh lot |
| `BID_RESET_SECONDS` | 15 | your time to counter after each bid |
| `MAX_LOT_SECONDS` | 180 | hard stop on one lot |
| `SECRET_KEY` | dev default | signs session tokens — **change this** |
| `GOOGLE_CLIENT_ID` | blank | enables the Google sign-in button |
| `MAX_SQUAD_SIZE` / `MAX_OVERSEAS` | 25 / 8 | squad caps |
| `RETENTION_TIMEOUT_SECONDS` | 180 | before AI completes your picks |
| `AI_MIN_DELAY_MS` / `AI_MAX_DELAY_MS` | 700 / 2600 | how long AI teams "think" |
