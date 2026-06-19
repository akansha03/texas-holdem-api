"""Player action endpoints

Routes:
- POST /api/games/{game_id}/actions/fold
- POST /api/games/{game_id}/actions/check
- POST /api/games/{game_id}/actions/call
- POST /api/games/{game_id}/actions/raise
- POST /api/games/{game_id}/actions/all-in
"""
from fastapi import APIRouter, HTTPException
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
async def fold_action(game_id: str, request: FoldActionRequest):
    """Player folds current hand"""
    game_session, player = _validate_game_and_player(game_id, request.player_id)

    if not game_session.game.player_fold(request.player_id):
        raise HTTPException(status_code=400, detail="Could not fold")

    next_player = game_session.game.get_current_player()
    next_turn = next_player.player_id if next_player else None

    return ActionResponse(
        action="fold",
        success=True,
        player_id=request.player_id,
        message="Player folded",
        next_turn=next_turn
    )


@router.post("/check", response_model=ActionResponse)
async def check_action(game_id: str, request: CheckActionRequest):
    """Player checks (passes without betting)"""
    game_session, player = _validate_game_and_player(game_id, request.player_id)

    if not game_session.game.player_check(request.player_id):
        raise HTTPException(
            status_code=400,
            detail="Cannot check - there is a bet to call"
        )

    next_player = game_session.game.get_current_player()
    next_turn = next_player.player_id if next_player else None

    return ActionResponse(
        action="check",
        success=True,
        player_id=request.player_id,
        message="Player checked",
        next_turn=next_turn
    )


@router.post("/call", response_model=ActionResponse)
async def call_action(game_id: str, request: CallActionRequest):
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

    next_player = game_session.game.get_current_player()
    next_turn = next_player.player_id if next_player else None

    return ActionResponse(
        action="call",
        success=True,
        player_id=request.player_id,
        amount_added=amount_to_call,
        new_stacks=player.get_stacks(),
        pot=game_session.game.pot,
        next_turn=next_turn
    )


@router.post("/raise", response_model=ActionResponse)
async def raise_action(game_id: str, request: RaiseActionRequest):
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

    next_player = game_session.game.get_current_player()
    next_turn = next_player.player_id if next_player else None

    return ActionResponse(
        action="raise",
        success=True,
        player_id=request.player_id,
        amount_added=amount_needed,
        new_stacks=player.get_stacks(),
        pot=game_session.game.pot,
        highest_bet_updated=request.raise_to_amount,
        next_turn=next_turn
    )


@router.post("/all-in", response_model=ActionResponse)
async def all_in_action(game_id: str, request: AllInActionRequest):
    """Player bets all remaining chips"""
    game_session, player = _validate_game_and_player(game_id, request.player_id)

    chips_before = player.get_stacks()
    if not game_session.game.player_all_in(request.player_id):
        raise HTTPException(status_code=400, detail="Could not go all-in")

    next_player = game_session.game.get_current_player()
    next_turn = next_player.player_id if next_player else None

    return ActionResponse(
        action="all-in",
        success=True,
        player_id=request.player_id,
        amount_added=chips_before,
        new_stacks=0,
        pot=game_session.game.pot,
        next_turn=next_turn
    )
