"""Game-related Pydantic models"""
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# Requests
class GameCreateRequest(BaseModel):
    game_name: str
    small_blind: int = 5
    big_blind: int = 10
    max_players: int = 2
    starting_chips: int = 1000

    @field_validator("game_name")
    @classmethod
    def validate_game_name(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Game name is required and must be string")
        if len(v) < 1:
            raise ValueError("Game name cannot be empty")
        if len(v) > 100:
            raise ValueError("Game name cannot exceed 100 characters")
        return v.strip()
    '''
    @field_validator("small_blind", "big_blind")
    @classmethod
    def validate_blinds_positive(cls, v):
        """Ensure blinds are positive"""
        if v <= 0:
            raise ValueError("Blinds must be greater than 0")
        return v
    
    @field_validator("big_blind")
    @classmethod
    def validate_big_blind_vs_small(cls, v, info):
        """Ensure big blind is greater than small blind"""
        if "small_blind" in info.data:
            small_blind = info.data["small_blind"]
            if v <= small_blind:
                raise ValueError(
                    f"Big blind ({v}) must be greater than small blind ({small_blind}). "
                    f"Typical ratio is 1:2 (e.g., small_blind=5, big_blind=10)"
                )
        return v
    '''
    @field_validator("max_players")
    @classmethod
    def validate_max_players(cls, v):
        """Ensure max_players is valid"""
        if v < 2:
            raise ValueError("Game must have at least 2 players")
        if v > 10:
            raise ValueError("Game cannot have more than 10 players")
        return v

    @field_validator("starting_chips")
    @classmethod
    def validate_starting_chips(cls, v):
        """Ensure starting chips is reasonable"""
        if v < 10:
            raise ValueError("Starting chips must be at least 10")
        if v > 1000000:
            raise ValueError("Starting chips cannot exceed 1,000,000")
        return v

class GameJoinRequest(BaseModel):
    player_id: str

# Responses
class GameMetadata(BaseModel):
    game_id: str
    game_name: str
    small_blind: int
    big_blind: int
    max_players: int
    starting_chips: int
    status: str  # "waiting_for_players", "in_progress", "completed"
    created_at: datetime

class GameCreateResponse(BaseModel):
    game_id: str
    game_name: str
    status: str
    created_at: datetime
    players: List = []

class GameJoinResponse(BaseModel):
    game_id: str
    player_id: str
    player_name: str
    position: int
    status: str
    message: str

class GameDetailsResponse(BaseModel):
    game_id: str
    status: str
    small_blind: int
    big_blind: int
    players: List[dict]
    current_hand: int
    total_hands: Optional[int] = None

class GameHistoryEntry(BaseModel):
    hand_number: int
    winner_id: str
    winner_name: str
    pot: int
    stage_ended: str  # "showdown", "fold", "all-in"

class GameHistoryResponse(BaseModel):
    game_id: str
    total_hands: int
    hands: List[GameHistoryEntry]


# Start Hand Response Models
class StartHandPlayerState(BaseModel):
    """Player state when hand starts"""
    player_id: UUID
    name: str
    position: int
    stacks: int
    current_bet: int
    hole_cards: List[str]
    status: str


class StartHandResponse(BaseModel):
    """Response when starting a new hand"""
    success: bool
    game_id: str
    hand_number: int
    stage: str
    pot: int
    small_blind_posted: int
    big_blind_posted: int
    current_turn: UUID
    dealer_position: int
    message: str
    players_state: List[StartHandPlayerState]
