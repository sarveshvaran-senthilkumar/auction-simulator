# AI-Powered IPL Auction Simulator

A full-stack, real-time multiplayer IPL auction simulator with AI-controlled teams, a calibrated Impact Scoring engine, a retention phase mirroring real 2025 mega-auction rules, and RTM (Right-to-Match) mechanics.

## Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- MongoDB

## Setup

### Backend
1. `cd backend`
2. `python -m venv venv`
3. Activate virtual environment:
   - Windows: `.\venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. `pip install -r requirements.txt`
5. Start server: `uvicorn app.main:app --reload`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`
