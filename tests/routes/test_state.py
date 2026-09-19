import pytest

def test_game_state_at_preflop(game_at_preflop):
    # Verify preflop hand initialization with blinds posted
    assert game_at_preflop['hand_number'] == 1
    assert game_at_preflop['stage'] == 'preflop'
    assert game_at_preflop['small_blind_posted'] == 5
    assert game_at_preflop['big_blind_posted'] == 10
    assert game_at_preflop['pot'] == 15
    assert game_at_preflop['dealer_position'] == 0
    assert game_at_preflop['message'] == 'Hand #1 started! Blinds posted. Waiting for first action.'
    assert len(game_at_preflop['players_state']) == 2
    assert len(game_at_preflop['community_cards']) == 0


def test_game_state_at_flop(game_at_flop):
    # Verify flop stage has 3 community cards and betting round reset
    assert game_at_flop['stage'] == 'flop'
    assert len(game_at_flop['community_cards']) == 3
    assert game_at_flop['pot'] == 15
    assert game_at_flop['betting_round_reset'] == True


def test_game_state_at_turn(game_at_turn):
    # Verify turn stage has 4 community cards
    assert game_at_turn['stage'] == 'turn'
    assert len(game_at_turn['community_cards']) == 4
    assert game_at_turn['pot'] == 15
    assert game_at_turn['betting_round_reset'] == True


def test_game_state_at_river(game_at_river):
    # Verify river stage has 5 community cards
    assert game_at_river['stage'] == 'river'
    assert len(game_at_river['community_cards']) == 5
    assert game_at_river['pot'] == 15
    assert game_at_river['betting_round_reset'] == True