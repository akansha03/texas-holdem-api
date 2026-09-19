import pytest
from app.core.game_logic import Player
from app.core.game_logic.card import PokerCard

@pytest.mark.parametrize(
        "player_id,player_name,starting_chips,position",
        [
            ("p1", "John", 1000, 0),
            ("p2","Jane",200,1)
        ]
)
def test_create_a_player(player_id, player_name, starting_chips, position):
    player = Player(player_id=player_id, player_name=player_name, starting_chips=starting_chips, position=position)
    assert player.player_id == player_id
    assert player.player_name == player_name
    assert player.starting_chips == starting_chips
    assert player.position == position
    assert player.stacks == starting_chips
    assert player.status == 'Active'
    assert not player.hole_cards

def test_create_a_player_and_receive_hole_cards():
    player = Player("p1", "John Doe", 1000, 0)
    player.receive_hole_cards(PokerCard('S', 'Q'), PokerCard('H', '10'))
    assert player.get_hole_cards() == [PokerCard('S', 'Q'), PokerCard('H', '10')]
    assert player.player_id == "p1"
    assert player.player_name == "John Doe"
    assert player.starting_chips == 1000
    assert player.position == 0


@pytest.mark.parametrize(
        "starting_chips,additional_chips",
        [
            (2000, 100),
            (1000, 0),
            (3000, 4500)
        ]
)
def test_create_player_and_add_chips(starting_chips, additional_chips):
    player = Player("p1", "Jane", starting_chips=starting_chips, position=0)
    player.add_chips(additional_chips)
    assert player.get_stacks() == starting_chips+additional_chips
    assert player.status == 'Active'

def test_create_player_and_deduct_chips():
    player = Player("p2", "John Doe", 2000, 0)
    assert player.player_name == "John Doe"
    assert player.deduct_chips(1000)
    assert player.get_stacks() == 1000
    assert player.current_bet == 1000
    assert player.status == 'Active'

def test_create_player_and_deduct_more_than_chips():
    player = Player("p1", "Jane Doe", 3000, 0)
    assert not player.deduct_chips(4000)
    assert not player.deduct_chips(-1)
    assert player.status == 'Active'

def test_create_player_and_deduct_all_chips_and_all_in():
    player = Player("p1", "John", 1000, 1)
    assert player.deduct_chips(1000)
    assert player.status == "All-in"
    assert player.get_stacks() == 0
    assert player.current_bet == 1000