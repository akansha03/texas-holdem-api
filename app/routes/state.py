"""Game state and showdown endpoints

Routes (prefixed with /api/games/{game_id}):
- GET /state - Get current game state
- GET /showdown - Get showdown results
- POST /advance-stage - Advance to next stage
"""
from fastapi import APIRouter, HTTPException
from app.models.player import GameStateResponse, ShowdownResponse, PlayerStateResponse
from app.core.game_manager import game_manager
from app.config import settings
from typing import Optional

router = APIRouter()


@router.get("/state", response_model=GameStateResponse)
async def get_game_state(game_id: str, player_id: Optional[str] = None):
    """
    Get current game state for UI rendering.

    Returns:
    - Community cards (visible to all)
    - Hole cards (only for requesting player)
    - Current pot, stage, valid actions
    - All player states (except hidden cards)
    """
    game_session = game_manager.get_game(game_id)
    if not game_session:
        raise HTTPException(status_code=404, detail="Game not found")

    game = game_session.game
    current_player = game.get_current_player()

    # Build player states
    players_state = []
    for player in game.players:
        player_data = PlayerStateResponse(
            player_id=player.player_id,
            name=player.player_name,
            position=player.position,
            stacks=player.get_stacks(),
            status=player.status,
            current_bet=player.current_bet,
            hole_cards=[str(c) for c in player.get_hole_cards()] if player_id == player.player_id else None,
            is_current_player=(current_player.player_id == player.player_id) if current_player else False
        )
        players_state.append(player_data)

    # Determine valid actions for current player
    valid_actions = []
    if current_player and player_id == current_player.player_id:
        valid_actions.append("fold")
        if current_player.current_bet >= game.highest_bet_in_round:
            valid_actions.append("check")
        if current_player.current_bet < game.highest_bet_in_round:
            valid_actions.append("call")
        if current_player.get_stacks() > 0:
            valid_actions.append("raise")
            valid_actions.append("all-in")

    return GameStateResponse(
        game_id=game_id,
        stage=game.stage,
        pot=game.pot,
        dealer_position=game.dealer_position,
        current_turn=current_player.player_id if current_player else None,
        highest_bet_in_round=game.highest_bet_in_round,
        players=players_state,
        community_cards=[str(c) for c in game.community_cards],
        valid_actions=valid_actions,
        action_constraints={
            "min_raise": game.highest_bet_in_round + 1,
            "max_raise": (current_player.get_stacks() + current_player.current_bet) if current_player else 0
        }
    )


@router.get("/showdown", response_model=ShowdownResponse)
async def get_showdown_results(game_id: str):
    """
    Get showdown results after hand completes.

    Returns:
    - Both players' best hands
    - Winner and pot awarded
    """
    game_session = game_manager.get_game(game_id)
    if not game_session:
        raise HTTPException(status_code=404, detail="Game not found")

    if game_session.game.stage != "showdown":
        raise HTTPException(status_code=400, detail="Game is not at showdown stage")

    winners, winning_rank = game_session.game.determine_winner()

    if not winners:
        raise HTTPException(status_code=400, detail="Could not determine winner")

    # Build showdown results for all players
    showdown_results = []
    for player in game_session.game.players:
        all_cards = player.hole_cards + game_session.game.community_cards
        hand_eval = game_session.game.hand_evaluator.evaluate_hand(all_cards)
        hand_rank, hand_kickers = hand_eval

        from app.models.player import ShowdownResult
        result = ShowdownResult(
            player_id=player.player_id,
            name=player.player_name,
            hole_cards=[str(c) for c in player.hole_cards],
            best_hand=game_session.game.hand_evaluator.get_hand_name(hand_rank),
            hand_rank=hand_rank,
            hand_score=(hand_rank, hand_kickers),
            final_stacks=player.get_stacks()
        )
        showdown_results.append(result)

    winner_id = winners[0].player_id if winners else None
    pot_awarded = game_session.game.pot

    return ShowdownResponse(
        game_status="completed",
        showdown_results=showdown_results,
        winner_id=winner_id,
        pot_awarded=pot_awarded
    )


@router.post("/advance-stage")
async def advance_stage(game_id: str, admin_token: str):
    """
    Advance game to next stage (flop -> turn -> river).
    Called by server when betting round completes.

    Requires admin token for security.
    """
    if admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")

    game_session = game_manager.get_game(game_id)
    if not game_session:
        raise HTTPException(status_code=404, detail="Game not found")

    game = game_session.game
    old_stage = game.stage

    game.advance_stage()

    return {
        "stage": game.stage,
        "community_cards": [str(c) for c in game.community_cards],
        "pot": game.pot,
        "betting_round_reset": True,
        "current_turn": game.get_current_player().player_id if game.get_current_player() else None,
        "previous_stage": old_stage
    }
