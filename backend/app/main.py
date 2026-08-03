from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db.database import Base, engine
from .routers import auth, players, rooms
from .ws import auction_socket

app = FastAPI(
    title="IPL Auction Simulator API",
    description="Backend API for the IPL Auction Simulator",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    # Auth rides in an Authorization header, not a cookie, so credentials are
    # never needed — which is also what lets allow_origins be ["*"] in dev.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(players.router)
app.include_router(auction_socket.router)


@app.on_event("startup")
async def on_startup() -> None:
    # Create any table the seeder hasn't (e.g. after a schema addition).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": app.version}
