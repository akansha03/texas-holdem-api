"""Database Session Management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.db.models import Base
import logging

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def drop_and_recreate_db():
    """Drop all tables and recreate them - for testing only"""
    logger.warning("🔄 DROPPING ALL TABLES FOR FRESH DATABASE START")
    Base.metadata.drop_all(bind=engine)
    logger.info("✅ All tables dropped")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ All tables recreated successfully")


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)


def reset_db_on_startup():
    """Reset database on startup if RESET_DB_ON_STARTUP is true"""
    if settings.reset_db_on_startup:
        drop_and_recreate_db()
    else:
        init_db()


def get_db():
    """Dependency injection for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
