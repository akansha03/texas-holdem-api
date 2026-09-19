import pytest
from app.core.game_manager import GameManager

def test_create_a_game_with_a_valid_name():
    manager = GameManager()
    game = manager.create_game("Texas Hold'em Table",5, 10, 3, 3000)
    assert game.status == "waiting_for_players"
    assert game.game_name == "Texas Hold'em Table"

def test_create_and_get_game():
    manager = GameManager()
    game = manager.create_game("Texas Poker Game", 1, 2, 2, 1000)
    new_game = manager.get_game(game.game_id)
    assert new_game.game_name == "Texas Poker Game"
    assert new_game.small_blind == 1
    assert new_game.big_blind == 2
    assert new_game.max_players == 2
    assert new_game.starting_chips == 1000
    assert new_game.status == "waiting_for_players"

def test_get_an_invalid_game():
    manager = GameManager()
    session = manager.get_game('abc')
    assert not session

def test_add_player_to_game():
    manager = GameManager()
    game = manager.create_game("Texas Poker Game", 5, 10, 2, 1000)
    result = manager.join_game(game.game_id, "p1", "John")
    assert result is True
    assert len(game.players) == 1

def test_add_player_to_invalid_game():
    manager = GameManager()
    assert not manager.join_game("123", "p2", "Jane")

def test_delete_a_valid_game():
    manager = GameManager()
    game = manager.create_game("Texas Poker Game", 5, 10, 2, 1000)
    assert manager.get_game(game.game_id).game_name == "Texas Poker Game"
    manager.delete_game(game.game_id)
    assert not manager.get_game(game.game_id)

def test_get_all_players():
    manager = GameManager()
    manager.create_game("Texas Poker Game", 5, 10, 2, 1000)
    manager.create_game("Poker", 1, 2, 10, 1000)
    manager.create_game("General Poker Game", 2, 10, 5, 5000)
    assert len(manager.get_all_games()) == 3
    manager.delete_all_games()
    assert len(manager.get_all_games()) == 0



