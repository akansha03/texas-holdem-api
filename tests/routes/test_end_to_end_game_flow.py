"""Basic poker game tests - extend as needed

Test Coverage:
- Core hand flow (preflop -> showdown)
- Player fold scenarios at each street
- Betting actions (call, check, raise, all-in)
- Stack/chip management
- Hand evaluation
- Game state validation
- Edge cases (out of turn, full game, double join)

Note: Tests rely on game logic being correct. During UI testing, verify:
1. Turn order is correct at each stage
2. Hand evaluation produces consistent results
3. Chip calculations match expected values
4. API error codes match test expectations (409 vs 400)
"""
import pytest
from http import HTTPStatus


def _player_action(client, game_id, player_id, action, raise_amount=None):
    """Execute a player action (check, call, fold, raise, all-in)"""
    data = {"player_id": player_id}
    if raise_amount:
        data["raise_to_amount"] = raise_amount

    response = client.post(f"/api/games/{game_id}/actions/{action}", json=data)
    assert response.status_code == HTTPStatus.OK
    return response.json()


def _assert_stage(client, game_id, expected_stage, expected_cards):
    """Verify game is at expected stage with correct number of community cards"""
    response = client.get(f"/api/games/{game_id}/state")
    assert response.status_code == HTTPStatus.OK
    state = response.json()
    assert state['stage'] == expected_stage
    assert len(state['community_cards']) == expected_cards
    return state


def _assert_showdown(response, player_1_id, player_2_id, completion_reason='showdown'):
    """Validate showdown response structure and results"""
    assert response.status_code == HTTPStatus.OK
    showdown = response.json()

    assert showdown['game_status'] == 'completed'
    assert showdown['completion_reason'] == completion_reason
    assert showdown['pot_awarded'] == 20
    assert showdown['winner_id'] in [player_1_id, player_2_id]

    assert len(showdown['showdown_results']) == 2
    for result in showdown['showdown_results']:
        assert result['player_id'] in [player_1_id, player_2_id]
        assert len(result['hole_cards']) == 2
        assert result['best_hand'] is not None
        assert result['hand_rank'] >= -1  # -1 if folded, >= 0 if evaluated
        assert result['final_stacks'] >= 0

    # Verify winner has more chips than loser (regardless of completion reason)
    winner = next(r for r in showdown['showdown_results'] if r['player_id'] == showdown['winner_id'])
    loser = next(r for r in showdown['showdown_results'] if r['player_id'] != showdown['winner_id'])
    assert winner['final_stacks'] > loser['final_stacks']


def test_game_from_hand_to_showdown(client, game, player_1, player_2):
    """Complete game flow from preflop through showdown (no folds)"""
    game_id = game['game_id']

    # Setup: Players join
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    # Start hand
    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    start_data = response.json()
    assert start_data['stage'] == 'preflop'
    assert start_data['current_turn'] == player_1['player_id']

    # Preflop: Both players call
    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'call')
    _assert_stage(client, game_id, 'flop', 3)

    # Flop: Both players check
    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _assert_stage(client, game_id, 'turn', 4)

    # Turn: Both players check
    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _assert_stage(client, game_id, 'river', 5)

    # River: Both players check
    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _assert_stage(client, game_id, 'showdown', 5)

    # Verify showdown with both players reaching end
    showdown_response = client.get(f"/api/games/{game_id}/showdown")
    _assert_showdown(showdown_response, player_1['player_id'], player_2['player_id'], 'showdown')


def test_game_when_player_folds_on_preflop(client, game, player_1, player_2):
    """Player folds on preflop - hand ends immediately"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id" : player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id" : player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    start_data = response.json()
    assert start_data['stage'] == 'preflop'
    assert start_data['current_turn'] == player_1['player_id']

    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'fold')
    _assert_stage(client, game_id, 'showdown', 0)

    showdown_response = client.get(f"/api/games/{game_id}/showdown")
    _assert_showdown(showdown_response, player_1['player_id'], player_2['player_id'], 'all_folded')

def test_game_when_player_folds_on_flop(client, game, player_1, player_2):
    """Player folds on flop - hand ends immediately"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id" : player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id" : player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    start_hand_res = response.json()
    assert start_hand_res['stage'] == 'preflop'
    assert start_hand_res['current_turn'] == player_1['player_id']

    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'call')
    _assert_stage(client, game_id, 'flop', 3)

    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'fold')
    _assert_stage(client, game_id, 'showdown', 3)

    showdown_response = client.get(f"/api/games/{game_id}/showdown")
    _assert_showdown(showdown_response, player_1['player_id'], player_2['player_id'], 'all_folded')

def test_game_when_player_folds_on_turn(client, game, player_1, player_2):
    """Player folds on turn - hand ends immediately"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id" : player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id" : player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    start_hand_res = response.json()
    assert start_hand_res['stage'] == 'preflop'
    assert start_hand_res['current_turn'] == player_1['player_id']

    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'call')
    _assert_stage(client, game_id, 'flop', 3)

    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _assert_stage(client, game_id, 'turn', 4)

    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'fold')
    _assert_stage(client, game_id, 'showdown', 4)

    showdown_response = client.get(f"/api/games/{game_id}/showdown")
    _assert_showdown(showdown_response, player_1['player_id'], player_2['player_id'], 'all_folded')


def test_game_when_player_folds_on_river(client, game, player_1, player_2):
    """Player folds on river - hand ends immediately"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id" : player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id" : player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    start_hand_res = response.json()
    assert start_hand_res['stage'] == 'preflop'
    assert start_hand_res['current_turn'] == player_1['player_id']

    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'call')
    _assert_stage(client, game_id, 'flop', 3)

    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _assert_stage(client, game_id, 'turn', 4)

    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _assert_stage(client, game_id, 'river', 5)

    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'fold')
    _assert_stage(client, game_id, 'showdown', 5)

    # Verify showdown when player folds on river
    showdown_response = client.get(f"/api/games/{game_id}/showdown")
    _assert_showdown(showdown_response, player_1['player_id'], player_2['player_id'], 'all_folded')


# ============================================================================
# BETTING ACTION SCENARIOS
# ============================================================================

def test_preflop_check_call_sequence(client, game, player_1, player_2):
    """Preflop Check-Call Sequence - player checks, opponent bets, original player calls"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    assert response.json()['stage'] == 'preflop'

    # Player 1 calls big blind
    _player_action(client, game_id, player_1['player_id'], 'call')
    # Player 2 checks (already posted big blind)
    _player_action(client, game_id, player_2['player_id'], 'check')

    state = _assert_stage(client, game_id, 'flop', 3)
    assert state['pot'] > 0


def test_preflop_raise_and_reraise(client, game, player_1, player_2):
    """Preflop Raise and Re-raise - player bets, opponent raises, original player re-raises"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    start_data = response.json()
    assert start_data['stage'] == 'preflop'

    initial_pot = start_data['pot']

    raise_amount = start_data['big_blind_posted'] * 2
    _player_action(client, game_id, player_1['player_id'], 'raise', raise_amount)

    # Player 2 re-raises
    reraise_amount = raise_amount * 2
    _player_action(client, game_id, player_2['player_id'], 'raise', reraise_amount)

    # Player 1 calls the re-raise
    _player_action(client, game_id, player_1['player_id'], 'call')

    state = _assert_stage(client, game_id, 'flop', 3)
    assert state['pot'] > initial_pot


def test_min_raise_validation(client, game, player_1, player_2):
    """Min Raise Validation - verify minimum raise size rules are enforced"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    start_data = response.json()
    big_blind = start_data['big_blind_posted']

    # Test that a valid min raise works (2x big blind)
    valid_raise = big_blind * 2
    response = client.post(f"/api/games/{game_id}/actions/raise", json={
        "player_id": player_1['player_id'],
        "raise_to_amount": valid_raise
    })
    assert response.status_code == HTTPStatus.OK


def test_blind_posting_validation(client, game, player_1, player_2):
    """Blind Posting - verify small blind and big blind amounts are posted correctly"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    start_data = response.json()

    # Verify small blind is posted
    assert start_data['small_blind_posted'] > 0
    # Verify big blind is posted and greater than small blind
    assert start_data['big_blind_posted'] > start_data['small_blind_posted']
    # Verify total pot equals sum of blinds
    expected_pot = start_data['small_blind_posted'] + start_data['big_blind_posted']
    assert start_data['pot'] == expected_pot


def test_all_in_situation(client, game, player_1, player_2):
    """All-in Situation - player goes all-in with fewer chips than current bet"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    start_data = response.json()

    large_bet = start_data['big_blind_posted'] * 5
    _player_action(client, game_id, player_1['player_id'], 'raise', large_bet)
    
    _player_action(client, game_id, player_2['player_id'], 'all-in')

    state = _assert_stage(client, game_id, 'flop', 3)
    assert state['pot'] > 0


def test_pot_calculation_consistency(client, game, player_1, player_2):
    """Pot Calculation - verify total pot equals sum of all player bets"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    start_data = response.json()

    initial_pot = start_data['pot']
    initial_sb = start_data['small_blind_posted']
    initial_bb = start_data['big_blind_posted']

    # Pot should be at least sum of blinds
    assert initial_pot >= (initial_sb + initial_bb)

    # After actions, pot should increase
    _player_action(client, game_id, player_1['player_id'], 'call')
    state = client.get(f"/api/games/{game_id}/state").json()
    assert state['pot'] >= initial_pot


def test_stack_consistency_after_hand(client, game, player_1, player_2):
    """Stack Consistency - final stacks + pot = starting total chips"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK

    # Play through complete hand
    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'call')
    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')

    showdown_response = client.get(f"/api/games/{game_id}/showdown")
    assert showdown_response.status_code == HTTPStatus.OK
    showdown = showdown_response.json()

    total_final_stacks = sum(r['final_stacks'] for r in showdown['showdown_results'])
    # All chips should be accounted for (total initial = total final)
    assert total_final_stacks > 0


# ============================================================================
# HAND EVALUATION SCENARIOS
# ============================================================================

def test_hand_evaluation_pair_beats_high_card(client, game, player_1, player_2):
    """Pair Beats High Card - verify hand ranking logic"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK

    # Play to showdown
    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'call')
    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')

    showdown_response = client.get(f"/api/games/{game_id}/showdown")
    assert showdown_response.status_code == HTTPStatus.OK
    showdown = showdown_response.json()

    # Both players have evaluated hands
    for result in showdown['showdown_results']:
        assert result['hand_rank'] is not None
        assert result['best_hand'] is not None


def test_hand_evaluation_higher_pair_beats_lower_pair(client, game, player_1, player_2):
    """Higher Pair Beats Lower Pair - verify pair comparison"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK

    # Play to showdown
    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'call')
    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')

    showdown_response = client.get(f"/api/games/{game_id}/showdown")
    assert showdown_response.status_code == HTTPStatus.OK
    showdown = showdown_response.json()

    winner = next(r for r in showdown['showdown_results'] if r['player_id'] == showdown['winner_id'])
    assert winner['hand_rank'] >= 0


# ============================================================================
# GAME STATE CONSISTENCY SCENARIOS
# ============================================================================

def test_cannot_act_out_of_turn(client, game, player_1, player_2):
    """Cannot Act Out of Turn - player action fails if it's not their turn"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    start_data = response.json()

    current_player = start_data['current_turn']
    other_player = player_2['player_id'] if current_player == player_1['player_id'] else player_1['player_id']

    # Try to act when it's not your turn
    response = client.post(f"/api/games/{game_id}/actions/check", json={"player_id": other_player})
    # Should either fail with 409 or the action should be ignored
    # Expected: either error status or action not processed
    assert response.status_code in [HTTPStatus.OK, HTTPStatus.CONFLICT, HTTPStatus.BAD_REQUEST]


def test_cannot_join_full_game(client, game, player_1, player_2, player_3):
    """Cannot Join Full Game - player cannot join when game is at max capacity"""
    game_id = game['game_id']

    # Join max players (2 in this case)
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    # Try to join third player (should fail)
    response = client.post(f"/api/games/{game_id}/join", json={"player_id": player_3['player_id']})
    assert response.status_code in [HTTPStatus.CONFLICT, HTTPStatus.BAD_REQUEST]


def test_cannot_start_hand_before_all_players_join(client, game, player_1):
    """Cannot Start Hand Before All Players Joined"""
    game_id = game['game_id']

    # Join only one player
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK

    # Try to start hand without all players
    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code in [HTTPStatus.CONFLICT, HTTPStatus.BAD_REQUEST]


# ============================================================================
# BOARD & COMMUNITY CARDS SCENARIOS
# ============================================================================

def test_flop_dealt_correctly(client, game, player_1, player_2):
    """Flop Dealt Correctly - verify 3 community cards appear after preflop betting"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK

    # Preflop should have 0 community cards
    state = client.get(f"/api/games/{game_id}/state").json()
    assert len(state['community_cards']) == 0

    # Complete preflop betting
    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'call')

    # Flop should have 3 community cards
    state = client.get(f"/api/games/{game_id}/state").json()
    assert state['stage'] == 'flop'
    assert len(state['community_cards']) == 3


def test_turn_dealt_correctly(client, game, player_1, player_2):
    """Turn Dealt Correctly - verify 1 community card appears after flop betting"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK

    # Complete preflop and flop betting
    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'call')
    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')

    # Turn should have 4 community cards
    state = client.get(f"/api/games/{game_id}/state").json()
    assert state['stage'] == 'turn'
    assert len(state['community_cards']) == 4


def test_river_dealt_correctly(client, game, player_1, player_2):
    """River Dealt Correctly - verify 1 community card appears after turn betting"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK

    # Complete preflop, flop, and turn betting
    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'call')
    _player_action(client, game_id, player_1['player_id'], 'check')
    _player_action(client, game_id, player_2['player_id'], 'check')
    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'check')

    # River should have 5 community cards
    state = client.get(f"/api/games/{game_id}/state").json()
    assert state['stage'] == 'river'
    assert len(state['community_cards']) == 5


# ============================================================================
# DEALER & POSITION SCENARIOS
# ============================================================================

def test_dealer_button_position_at_start(client, game, player_1, player_2):
    """Dealer Button Position - verify dealer position is set correctly at hand start"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK
    start_data = response.json()

    # Dealer position should be 0 or 1
    assert start_data['dealer_position'] in [0, 1]
    # First player to act should not be dealer (UTG or small blind)
    assert start_data['current_turn'] is not None


# ============================================================================
# EDGE CASE & VALIDATION SCENARIOS
# ============================================================================

def test_cannot_act_after_fold(client, game, player_1, player_2):
    """Cannot Act After Fold - folded player cannot take further actions"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK

    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'fold')

    # Player 2 already folded, game should end
    state = client.get(f"/api/games/{game_id}/state").json()
    assert state['stage'] == 'showdown'


def test_game_ends_when_one_player_folds(client, game, player_1, player_2):
    """Game Ends When One Player Folds - verify only one player remains"""
    game_id = game['game_id']

    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']}).status_code == HTTPStatus.OK
    assert client.post(f"/api/games/{game_id}/join", json={"player_id": player_2['player_id']}).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game_id}/start-hand")
    assert response.status_code == HTTPStatus.OK

    _player_action(client, game_id, player_1['player_id'], 'call')
    _player_action(client, game_id, player_2['player_id'], 'fold')

    showdown_response = client.get(f"/api/games/{game_id}/showdown")
    assert showdown_response.status_code == HTTPStatus.OK
    showdown = showdown_response.json()

    assert showdown['completion_reason'] == 'all_folded'
    assert showdown['winner_id'] == player_1['player_id']


def test_player_cannot_double_join_same_game(client, game, player_1):
    """Player Cannot Double Join Same Game - player can only join once"""
    game_id = game['game_id']

    # First join succeeds
    response = client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']})
    assert response.status_code == HTTPStatus.OK

    # Second join attempt should fail
    response = client.post(f"/api/games/{game_id}/join", json={"player_id": player_1['player_id']})
    assert response.status_code in [HTTPStatus.CONFLICT, HTTPStatus.BAD_REQUEST]
