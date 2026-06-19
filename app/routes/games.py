"""Game management endpoints

Routes:
- POST /api/games - Create new game
- GET /api/games/{game_id} - Get game details
- POST /api/games/{game_id}/join - Join game
- POST /api/games/{game_id}/start-hand - Start new hand (deal cards, post blinds)
- GET /api/games/{game_id}/history - Get game history
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.game import (
    GameCreateRequest,
    GameCreateResponse,
    GameJoinRequest,
    GameJoinResponse,
    GameDetailsResponse,
    GameHistoryResponse,
    StartHandResponse,
    StartHandPlayerState
)
from app.core.game_manager import game_manager
from app.db import get_db
from app.db import crud

router = APIRouter()


@router.post("", response_model=GameCreateResponse)
async def create_game(request: GameCreateRequest, db: Session = Depends(get_db)):
    """Create a new poker game session"""
    # Validate blinds
    if request.small_blind <= 0 or request.big_blind <= 0:
        raise HTTPException(
            status_code=400,
            detail="Blinds must be positive values"
        )

    if request.big_blind <= request.small_blind:
        raise HTTPException(
            status_code=400,
            detail=f"Big blind ({request.big_blind}) must be greater than small blind ({request.small_blind})"
        )

    # Validate starting chips vs blinds
    if request.starting_chips < request.big_blind * 10:
        raise HTTPException(
            status_code=400,
            detail=f"Starting chips ({request.starting_chips}) should be at least 10x the big blind ({request.big_blind * 10} recommended)"
        )

    # Create game in memory (for game logic)
    game_session = game_manager.create_game(
        game_name=request.game_name,
        small_blind=request.small_blind,
        big_blind=request.big_blind,
        max_players=request.max_players,
        starting_chips=request.starting_chips
    )

    # Store game in database
    db_game = crud.create_game_session(
        db,
        game_id=game_session.game_id,
        game_name=request.game_name,
        small_blind=request.small_blind,
        big_blind=request.big_blind,
        max_players=request.max_players
    )

    # Store starting_chips in game metadata (using pot field as a temp storage)
    db_game.current_stage = f"starting_chips:{request.starting_chips}"
    db.commit()

    return GameCreateResponse(
        game_id=game_session.game_id,
        game_name=game_session.game_name,
        status="waiting",
        created_at=db_game.created_at,
        players=[]
    )


@router.get("/{game_id}", response_model=GameDetailsResponse)
async def get_game_details(game_id: str, db: Session = Depends(get_db)):
    """Get game metadata and player list"""
    # Get from in-memory first (if active game)
    game_session = game_manager.get_game(game_id)

    if not game_session:
        # Fallback to database
        db_game = crud.get_game_session(db, game_id)
        if not db_game:
            raise HTTPException(status_code=404, detail="Game not found")

        participants = crud.get_game_participants(db, game_id)
        return GameDetailsResponse(
            game_id=db_game.game_id,
            status=db_game.status.value,
            small_blind=db_game.small_blind,
            big_blind=db_game.big_blind,
            players=[{
                "player_id": p.player_id,
                "name": p.player.player_name,
                "position": p.position,
                "stacks": int(p.current_chips),
                "status": "Active"
            } for p in participants],
            current_hand=0,
            total_hands=len(crud.get_game_hands(db, game_id))
        )

    return GameDetailsResponse(
        game_id=game_session.game_id,
        status=game_session.status,
        small_blind=game_session.small_blind,
        big_blind=game_session.big_blind,
        players=game_session.get_players_state(),
        current_hand=game_session.current_hand,
        total_hands=len(game_session.hand_history)
    )


@router.post("/{game_id}/join", response_model=GameJoinResponse)
async def join_game(game_id: str, request: GameJoinRequest, db: Session = Depends(get_db)):
    """Player joins an existing game"""
    # Get game from memory first
    game_session = game_manager.get_game(game_id)
    if not game_session:
        # Check database
        db_game = crud.get_game_session(db, game_id)
        if not db_game:
            raise HTTPException(status_code=404, detail="Game not found")

        if db_game.status.value != "waiting":
            raise HTTPException(
                status_code=409,
                detail="Game has already started or is completed"
            )

        # Load game back into memory (for active play)
        game_session = game_manager.create_game(
            game_name=db_game.game_name,
            small_blind=db_game.small_blind,
            big_blind=db_game.big_blind,
            max_players=db_game.max_players
        )
        game_session.game_id = game_id

    if game_session.status != "waiting_for_players":
        raise HTTPException(
            status_code=409,
            detail="Game has already started or is completed"
        )

    if not game_manager.join_game(game_id, request.player_id, request.player_name):
        raise HTTPException(
            status_code=409,
            detail="Could not join game (full or invalid)"
        )

    # Add player to database
    player = game_session.get_player(request.player_id)

    # Get starting chips from game metadata
    db_game = crud.get_game_session(db, game_id)
    starting_chips_str = db_game.current_stage.split(":")[1] if ":" in db_game.current_stage else "1000"
    starting_chips = int(starting_chips_str)

    crud.add_game_participant(
        db,
        game_id=game_id,
        player_id=request.player_id,
        starting_chips=starting_chips,
        position=player.position
    )

    # Update game status if all players joined
    if len(game_session.players) == game_session.max_players:
        crud.update_game_status(db, game_id, "in_progress")

    message = "Game will start when all players join"
    if game_session.status == "in_progress":
        message = "Game has started!"

    return GameJoinResponse(
        game_id=game_session.game_id,
        player_id=request.player_id,
        player_name=request.player_name,
        position=player.position,
        status="joined",
        message=message
    )


@router.get("/{game_id}/history", response_model=GameHistoryResponse)
async def get_game_history(game_id: str, db: Session = Depends(get_db)):
    """Get game history (all hands played)"""
    # Check memory first
    game_session = game_manager.get_game(game_id)
    if game_session:
        return GameHistoryResponse(
            game_id=game_session.game_id,
            total_hands=len(game_session.hand_history),
            hands=game_session.hand_history
        )

    # Check database
    db_game = crud.get_game_session(db, game_id)
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    hands = crud.get_game_hands(db, game_id)
    return GameHistoryResponse(
        game_id=game_id,
        total_hands=len(hands),
        hands=[]
    )


@router.post("/{game_id}/start-hand", response_model=StartHandResponse)
async def start_hand(game_id: str, db: Session = Depends(get_db)):
    """
    Start a new hand - deal hole cards and post blinds

    Flow:
    1. Initialize new hand (shuffle deck, deal hole cards)
    2. Post small and big blinds
    3. Set first player to act (after big blind)

    Returns game state with hole cards dealt and blinds posted
    """
    # Get game from memory
    game_session = game_manager.get_game(game_id)
    if not game_session:
        raise HTTPException(status_code=404, detail="Game not found")

    # Check if game has started
    if game_session.status != "in_progress":
        raise HTTPException(
            status_code=409,
            detail="Game must have all players joined before starting hand"
        )

    # Check if hand already in progress
    if game_session.game.betting_round_active:
        raise HTTPException(
            status_code=409,
            detail="Hand is already in progress"
        )

    try:
        # Start new hand (deal hole cards)
        game_session.game.start_new_hand()

        # Post blinds (small blind and big blind)
        game_session.game.post_blinds()

        # Record hand in database
        db_hand = crud.create_hand(
            db,
            game_id=game_id,
            hand_number=game_session.game.hand_number
        )

        # Get first player to act
        current_player = game_session.game.get_current_player()

        # Build players state
        players_state = [
            StartHandPlayerState(
                player_id=p.player_id,
                name=p.player_name,
                position=p.position,
                stacks=p.get_stacks(),
                current_bet=p.current_bet,
                hole_cards=[str(c) for c in p.get_hole_cards()],
                status=p.status
            )
            for p in game_session.game.players
        ]

        return StartHandResponse(
            success=True,
            game_id=game_id,
            hand_number=game_session.game.hand_number,
            stage=game_session.game.stage,
            pot=game_session.game.pot,
            small_blind_posted=game_session.game.small_blind,
            big_blind_posted=game_session.game.big_blind,
            current_turn=current_player.player_id if current_player else None,
            dealer_position=game_session.game.dealer_position,
            message=f"Hand #{game_session.game.hand_number} started! Blinds posted. Waiting for first action.",
            players_state=players_state
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
