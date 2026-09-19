"""SQLAlchemy ORM Models for Poker Game Database"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Float, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

Base = declarative_base()


class GameStatus(str, enum.Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Player(Base):
    __tablename__ = "players"

    player_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    player_name = Column(String, index=True, nullable=False)
    email = Column(String, nullable=True, unique=True, index=True)
    total_chips = Column(Float, default=1000)
    total_games = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    game_participants = relationship("GameParticipant", back_populates="player")
    hand_results = relationship("HandResult", back_populates="player")

    def __repr__(self):
        return f"<Player(player_id={self.player_id}, name={self.player_name})>"


class GameSession(Base):
    __tablename__ = "game_sessions"

    game_id = Column(String, primary_key=True, index=True)
    game_name = Column(String, nullable=False)
    status = Column(SQLEnum(GameStatus), default=GameStatus.WAITING)
    small_blind = Column(Integer, nullable=False)
    big_blind = Column(Integer, nullable=False)
    max_players = Column(Integer, default=6)
    current_stage = Column(String, default="pre_flop")
    pot = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    participants = relationship("GameParticipant", back_populates="game", cascade="all, delete-orphan")
    hands = relationship("Hand", back_populates="game", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GameSession(game_id={self.game_id}, status={self.status})>"


class GameParticipant(Base):
    __tablename__ = "game_participants"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, ForeignKey("game_sessions.game_id"), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.player_id"), nullable=False)
    starting_chips = Column(Float, nullable=False)
    current_chips = Column(Float, nullable=False)
    position = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    game = relationship("GameSession", back_populates="participants")
    player = relationship("Player", back_populates="game_participants")

    def __repr__(self):
        return f"<GameParticipant(game_id={self.game_id}, player_id={self.player_id})>"


class Hand(Base):
    __tablename__ = "hands"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, ForeignKey("game_sessions.game_id"), nullable=False)
    hand_number = Column(Integer, nullable=False)
    community_cards = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    game = relationship("GameSession", back_populates="hands")
    results = relationship("HandResult", back_populates="hand", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Hand(game_id={self.game_id}, hand_number={self.hand_number})>"


class HandResult(Base):
    __tablename__ = "hand_results"

    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(Integer, ForeignKey("hands.id"), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.player_id"), nullable=False)
    hole_cards = Column(String, nullable=True)
    final_hand = Column(String, nullable=True)
    hand_rank = Column(String, nullable=True)
    amount_won = Column(Float, default=0)
    is_winner = Column(Boolean, default=False)
    folded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    hand = relationship("Hand", back_populates="results")
    player = relationship("Player", back_populates="hand_results")

    def __repr__(self):
        return f"<HandResult(hand_id={self.hand_id}, player_id={self.player_id}, winner={self.is_winner})>"
