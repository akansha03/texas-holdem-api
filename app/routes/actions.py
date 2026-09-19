"""Player action endpoints

Routes:
- POST /api/games/{game_id}/actions/fold
- POST /api/games/{game_id}/actions/check
- POST /api/games/{game_id}/actions/call
- POST /api/games/{game_id}/actions/raise
- POST /api/games/{game_id}/actions/all-in
"""
from fastapi import APIRouter, HTTPException, Path
from app.models.player import (
    FoldActionRequest,
    CheckActionRequest,
    CallActionRequest,
    RaiseActionRequest,
    AllInActionRequest,
    ActionResponse
)
from app.core.game_manager import game_manager

router = APIRouter()

def _validate_game_and_player(game_id: str, player_id: str):
    """Helper to validate game exists and player is in it"""
    game_session = game_manager.get_game(game_id)
    if not game_session:
        raise HTTPException(status_code=404, detail="Game not found")

    player = game_session.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not in game")

    # Verify it's this player's turn
    current_player = game_session.game.get_current_player()
    if current_player is None or current_player.player_id != player_id:
        raise HTTPException(status_code=400, detail="Not your turn")

    return game_session, player


@router.post("/fold", response_model=ActionResponse)
async def fold_action(request: FoldActionRequest, game_id: str = Path(...)):
    """Player folds current hand"""
    game_session, player = _validate_game_and_player(game_id, request.player_id)

    if not game_session.game.player_fold(request.player_id):
        raise HTTPException(status_code=400, detail="Could not fold")

    next_player = game_session.game.get_current_player()
    next_turn = next_player.player_id if next_player else None

    if next_turn:
        message = f"{player.player_name} folded. {next_player.player_name} wins the hand"
    else:
        message = f"{player.player_name} folded. Hand complete"

    return ActionResponse(
        action="fold",
        success=True,
        player_id=request.player_id,
        message=message,
        amount_added=0,
        new_stacks=player.get_stacks(),
        pot=game_session.game.pot,
        next_turn=next_turn,
        stage=game_session.game.stage,
        community_cards=[str(c) for c in game_session.game.community_cards]
    )


@router.post("/check", response_model=ActionResponse)
async def check_action(request: CheckActionRequest, game_id: str = Path(...)):
    """Player checks (passes without betting)"""
    game_session, player = _validate_game_and_player(game_id, request.player_id)

    if not game_session.game.player_check(request.player_id):
        raise HTTPException(
            status_code=400,
            detail="Cannot check - there is a bet to call"
        )

    # If betting round is complete, next_turn is None
    if not game_session.game.betting_round_active:
        next_turn = None
        message = f"{player.player_name} checked. Betting round complete"
    else:
        next_player = game_session.game.get_current_player()
        next_turn = next_player.player_id if next_player else None
        message = f"{player.player_name} checked. Next player to act: {next_player.player_name if next_player else 'None'}"

    return ActionResponse(
        action="check",
        success=True,
        player_id=request.player_id,
        message=message,
        amount_added=0,
        new_stacks=player.get_stacks(),
        pot=game_session.game.pot,
        next_turn=next_turn,
        stage=game_session.game.stage,
        community_cards=[str(c) for c in game_session.game.community_cards]
    )


@router.post("/call", response_model=ActionResponse)
async def call_action(request: CallActionRequest, game_id: str = Path(...)):
    """Player matches current bet"""
    game_session, player = _validate_game_and_player(game_id, request.player_id)

    amount_to_call = game_session.game.highest_bet_in_round - player.current_bet
    if amount_to_call > player.get_stacks():
        raise HTTPException(
            status_code=400,
            detail="Insufficient chips to call"
        )

    if not game_session.game.player_call(request.player_id):
        raise HTTPException(status_code=400, detail="Could not call")

    # If betting round is complete, next_turn is None
    if not game_session.game.betting_round_active:
        next_turn = None
        message = "Betting round complete"
    else:
        next_player = game_session.game.get_current_player()
        next_turn = next_player.player_id if next_player else None
        message = f"Player called. Next player to act: {next_player.player_name if next_player else 'None'}"

    return ActionResponse(
        action="call",
        success=True,
        player_id=request.player_id,
        message=message,
        amount_added=amount_to_call,
        new_stacks=player.get_stacks(),
        pot=game_session.game.pot,
        next_turn=next_turn,
        stage=game_session.game.stage,
        community_cards=[str(c) for c in game_session.game.community_cards]
    )


@router.post("/raise", response_model=ActionResponse)
async def raise_action(request: RaiseActionRequest, game_id: str = Path(...)):
    """Player raises the bet"""
    game_session, player = _validate_game_and_player(game_id, request.player_id)

    if request.raise_to_amount <= game_session.game.highest_bet_in_round:
        raise HTTPException(
            status_code=400,
            detail="Raise must be higher than current bet"
        )

    amount_needed = request.raise_to_amount - player.current_bet
    if amount_needed > player.get_stacks():
        raise HTTPException(
            status_code=400,
            detail="Insufficient chips to raise"
        )

    if not game_session.game.player_raise(request.player_id, request.raise_to_amount):
        raise HTTPException(status_code=400, detail="Could not raise")

    # Raises always have a next player (unless only 1 player left)
    next_player = game_session.game.get_current_player()
    next_turn = next_player.player_id if next_player else None
    message = f"{player.player_name} raised to {request.raise_to_amount}. Next player to act: {next_player.player_name if next_player else 'None'}"

    return ActionResponse(
        action="raise",
        success=True,
        player_id=request.player_id,
        message=message,
        amount_added=amount_needed,
        new_stacks=player.get_stacks(),
        pot=game_session.game.pot,
        highest_bet_updated=request.raise_to_amount,
        next_turn=next_turn,
        stage=game_session.game.stage,
        community_cards=[str(c) for c in game_session.game.community_cards]
    )


@router.post("/all-in", response_model=ActionResponse)
async def all_in_action(request: AllInActionRequest, game_id: str = Path(...)):
    """Player bets all remaining chips"""
    game_session, player = _validate_game_and_player(game_id, request.player_id)

    chips_before = player.get_stacks()
    if not game_session.game.player_all_in(request.player_id):
        raise HTTPException(status_code=400, detail="Could not go all-in")

    # If betting round is complete, next_turn is None
    if not game_session.game.betting_round_active:
        next_turn = None
        message = f"{player.player_name} went all-in. Betting round complete"
    else:
        next_player = game_session.game.get_current_player()
        next_turn = next_player.player_id if next_player else None
        message = f"{player.player_name} went all-in for {chips_before} chips. Next player to act: {next_player.player_name if next_player else 'None'}"

    return ActionResponse(
        action="all-in",
        success=True,
        player_id=request.player_id,
        message=message,
        amount_added=chips_before,
        new_stacks=0,
        pot=game_session.game.pot,
        next_turn=next_turn,
        stage=game_session.game.stage,
        community_cards=[str(c) for c in game_session.game.community_cards]
    )
