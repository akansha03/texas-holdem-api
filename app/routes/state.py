"""Game state and showdown endpoints

Routes (prefixed with /api/games/{game_id}):
- GET /state - Get current game state
- GET /showdown - Get showdown results
- POST /advance-stage - Advance to next stage
"""
from fastapi import APIRouter, HTTPException, Path, Query
from app.models.player import GameStateResponse, ShowdownResponse, PlayerStateResponse
from app.core.game_manager import game_manager
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/state", response_model=GameStateResponse)
async def get_game_state(game_id: str = Path(...)):
    """
    Get current game state for UI rendering.

    Returns:
    - Community cards (visible to all)
    - Current pot, stage
    - All player states (hole cards hidden)
    """
    try:
        game_session = game_manager.get_game(game_id)
        if not game_session:
            raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")

        game = game_session.game
        if not game:
            raise HTTPException(status_code=500, detail="Game object is not initialized")

        current_player = game.get_current_player()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game state: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving game state: {str(e)}")

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
            hole_cards=[str(c) for c in player.get_hole_cards()],
            is_current_player=(current_player.player_id == player.player_id) if current_player else False
        )
        players_state.append(player_data)

    # Determine valid actions for current player
    valid_actions = []
    if game.betting_round_active and current_player:
        valid_actions.append("fold")
        if current_player.current_bet >= game.highest_bet_in_round:
            valid_actions.append("check")
        if current_player.current_bet < game.highest_bet_in_round:
            valid_actions.append("call")
        if current_player.get_stacks() > 0:
            valid_actions.append("raise")
            valid_actions.append("all-in")

    # Only show current_turn if betting round is active
    current_turn = None
    if game.betting_round_active and current_player:
        current_turn = current_player.player_id

    # Calculate realistic min_raise based on stage using nested ternary
    min_raise = max(game.highest_bet_in_round, game.big_blind) if game.stage == "preflop" else (game.highest_bet_in_round if game.highest_bet_in_round > 0 else 1)

    return GameStateResponse(
        game_id=game_id,
        stage=game.stage,
        pot=game.pot,
        dealer_position=game.dealer_position,
        current_turn=current_turn,
        highest_bet_in_round=game.highest_bet_in_round,
        players=players_state,
        community_cards=[str(c) for c in game.community_cards],
        valid_actions=valid_actions,
        action_constraints={
            "min_raise": min_raise,
            "max_raise": (current_player.get_stacks() + current_player.current_bet) if current_player else 0
        }
    )


@router.get("/showdown", response_model=ShowdownResponse)
async def get_showdown_results(game_id: str = Path(...)):
    """
    Get showdown results after hand completes.

    Returns:
    - Both players' best hands
    - Winner and pot awarded
    """
    try:
        game_session = game_manager.get_game(game_id)
        if not game_session:
            raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")

        if game_session.game.stage != "showdown":
            raise HTTPException(status_code=400, detail=f"Game is at '{game_session.game.stage}' stage, not showdown")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting showdown results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving showdown results: {str(e)}")

    winners, winning_rank = game_session.game.determine_winner()

    if not winners:
        raise HTTPException(status_code=400, detail="Could not determine winner")

    # Award pot to winner(s)
    game_session.game.distribute_pot()

    # Determine if this was an actual showdown or everyone folded
    active_players = game_session.game.get_active_players()
    completion_reason = "all_folded" if len(active_players) == 1 else "showdown"

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
        pot_awarded=pot_awarded,
        completion_reason=completion_reason
    )


@router.post("/advance-stage")
async def advance_stage(game_id: str = Path(...), admin_token: str = Query(...)):
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
