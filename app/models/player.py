"""Player-related Pydantic models"""
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# Player Profile (CRUD operations)
class PlayerCreateRequest(BaseModel):
    """Request to create/register a new player"""
    player_name: str
    email: Optional[EmailStr] = None

    @field_validator("player_name")
    @classmethod
    def validate_player_name(cls, v):
        if len(v) < 2:
            raise ValueError("Player name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Player name cannot exceed 100 characters")
        return v


class PlayerUpdateRequest(BaseModel):
    """Request to update player info"""
    player_name: Optional[str] = None
    email: Optional[str] = None


class PlayerProfile(BaseModel):
    """Player profile response"""
    player_id: UUID
    player_name: str
    email: Optional[str] = None
    created_at: datetime
    total_games: int = 0
    total_wins: int = 0
    total_chips_won: int = 0


class PlayerListResponse(BaseModel):
    """List of players"""
    players: List[PlayerProfile]
    total_count: int


# Player State Response
class PlayerStateResponse(BaseModel):
    player_id: str
    name: str
    position: int
    stacks: int
    status: str  # "Active", "Folded", "All-in"
    current_bet: int
    hole_cards: Optional[List[str]] = None  # Only for requesting player
    is_current_player: bool

# Action Requests
class FoldActionRequest(BaseModel):
    player_id: str

class CheckActionRequest(BaseModel):
    player_id: str

class CallActionRequest(BaseModel):
    player_id: str

class RaiseActionRequest(BaseModel):
    player_id: str
    raise_to_amount: int = Field(gt=0, description="Amount must be positive")

class AllInActionRequest(BaseModel):
    player_id: str

# Action Responses
class ActionResponse(BaseModel):
    action: str  # "fold", "check", "call", "raise", "all-in"
    success: bool
    player_id: str
    message: Optional[str] = None
    amount_added: Optional[int] = None
    new_stacks: Optional[int] = None
    pot: Optional[int] = None
    highest_bet_updated: Optional[int] = None
    next_turn: Optional[str] = None
    stage: Optional[str] = None  # Current game stage after action
    community_cards: Optional[List[str]] = None  # If stage advanced

class GameStateResponse(BaseModel):
    game_id: str
    stage: str  # "preflop", "flop", "turn", "river"
    pot: int
    dealer_position: int
    current_turn: Optional[str] = None  # player_id of current player
    highest_bet_in_round: int

    players: List[PlayerStateResponse]
    community_cards: List[str]
    valid_actions: List[str]
    action_constraints: dict  # {"min_raise": 30, "max_raise": 450}

class ShowdownResult(BaseModel):
    player_id: str
    name: str
    hole_cards: List[str]
    best_hand: str
    hand_rank: int
    hand_score: tuple
    final_stacks: int

class ShowdownResponse(BaseModel):
    game_status: str
    showdown_results: List[ShowdownResult]
    winner_id: str
    pot_awarded: int
    completion_reason: str  # "showdown" (multiple players) or "all_folded" (one player)
