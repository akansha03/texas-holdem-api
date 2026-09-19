"""Main FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.db.session import reset_db_on_startup

logger = logging.getLogger(__name__)

# Initialize database (drop and recreate if RESET_DB_ON_STARTUP=true)
try:
    #reset_db_on_startup()
    logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    logger.warning("⚠️ Server starting without database. Please ensure PostgreSQL is running.")

# Create FastAPI app
app = FastAPI(
    title="Texas Poker Game API",
    description="Multiplayer Texas Hold'em Poker Game Backend",
    version="0.1.0"
)

# Configure CORS for Swift clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Texas Poker Game API",
        "version": "0.1.0"
    }

# Import and include routers
from app.routes import games, actions, state, players

app.include_router(players.router, prefix="/api/players", tags=["players"])
app.include_router(games.router, prefix="/api/games", tags=["games"])
app.include_router(actions.router, prefix="/api/games/{game_id}/actions", tags=["actions"])
app.include_router(state.router, prefix="/api/games/{game_id}", tags=["state"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Texas Poker Game API",
        "docs": "/docs",
        "health": "/health"
    }
