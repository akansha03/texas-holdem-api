import pytest
from app.core.game_logic import PokerGame

def test_create_game_with_default_players():
    game = PokerGame()
    assert game.max_players == 2
    assert game.small_blind == 5
    assert game.big_blind == 10
    assert game.stage == 'preflop'
    assert not game.players 

@pytest.mark.parametrize(
        "small_blind,big_blind,match",
        [
            (-1, 10, 'Small blind must be greater than 0'),
            (1, -1, 'Big blind must be greater than 0'),
            (100, 50, r'Big blind \(\d+\) must be greater than small blind \(\d+\)'),
            (-1, -1, 'Small blind must be greater than 0'),
            (5,0, 'Big blind must be greater than 0')
        ]
)
def test_create_game_with_invalid_small_and_big_blind(small_blind, big_blind, match):
    with pytest.raises(ValueError, match=match):
        PokerGame(small_blind=small_blind, big_blind=big_blind)

@pytest.mark.parametrize(
        "max_players, match",
        [
            (0, "Max Players must be between 2 and 10"),
            (1, "Max Players must be between 2 and 10"),
            (11, "Max Players must be between 2 and 10")
        ]
)
def test_create_game_max_player_invalid_boundary_validation(max_players, match):
    with pytest.raises(ValueError, match=match):
        PokerGame(max_players=max_players)

@pytest.mark.parametrize(
        "small_blind,big_blind,max_players",
        [
            (5,10,2),
            (2,8,10),
            (3,9,10)
        ]
)
def test_create_game_max_player_valid_boundary_validation(small_blind, big_blind, max_players):
    game = PokerGame(small_blind=small_blind, big_blind=big_blind, max_players=max_players)
    assert game.small_blind == small_blind
    assert game.big_blind == big_blind
    assert game.max_players == max_players
    assert game.stage == "preflop"
    assert game.pot == 0
    assert game.hand_number == 0
    assert not game.community_cards
    assert not game.deck
    assert game.current_player_index == 0
    assert game.dealer_position == 0
    assert game.betting_round_active == False
    assert game.highest_bet_in_round == 0
    assert not game.players_acted_this_round






