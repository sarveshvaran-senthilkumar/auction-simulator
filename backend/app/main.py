from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings

app = FastAPI(
    title="IPL Auction Simulator API",
    description="Backend API for the IPL Auction Simulator",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routers import rooms, players

app.include_router(rooms.router)
app.include_router(players.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": app.version}
