import pytest
from http import HTTPStatus

# ===== GAME CREATION TESTS =====

def test_create_game_with_valid_name(client):
    """Create game with all valid parameters"""
    response = client.post("/api/games", json={
        "game_name" : "Texas Poker Game",
        "small_blind" : 5,
        "big_blind" : 10,
        "max_players" : 2,
        "starting_chips" : 2000
    })
    assert response.status_code == HTTPStatus.CREATED

def test_create_game_with_negative_small_blind(client):
    """Reject game creation with negative small blind"""
    response = client.post("/api/games", json={
        "game_name" : "Poker Game",
        "small_blind" : -1,
        "big_blind" : 10,
        "max_players" : 3,
        "starting_chips" : 2000
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_create_game_with_negative_big_blind(client):
    """Reject game creation with negative big blind"""
    response = client.post("/api/games", json={
        "game_name" : "Texas Hold Poker Game",
        "small_blind" : 2,
        "big_blind" : -10,
        "max_players" : 2,
        "starting_chips" : 1000
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_create_game_with_negative_blinds(client):
    """Reject game creation when both blinds are negative"""
    response = client.post("/api/games", json={
        "game_name" : "Poker Game",
        "small_blind" : -1,
        "big_blind" : -2,
        "max_players" : 2,
        "starting_chips" : 1000
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_create_game_with_same_small_and_big_blind(client):
    """Reject game creation when small blind equals big blind"""
    response = client.post("/api/games", json={
        "game_name" : "Poker Test Game",
        "small_blind" : 2,
        "big_blind" : 2,
        "max_players" : 2,
        "starting_chips" : 500
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_create_game_with_empty_payload(client):
    """Reject game creation with empty payload"""
    response = client.post("/api/games", json = {})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_create_game_with_mandatory_fields(client):
    """Create game with only mandatory field (game_name)"""
    response = client.post("/api/games", json = {
        "game_name" : "Poker Game"
    })
    assert response.status_code == HTTPStatus.CREATED

def test_create_game_with_small_blind_greater_than_big_blind(client):
    """Reject game creation when small blind exceeds big blind"""
    response = client.post("/api/games", json={
        "game_name" : "Poker Gamer",
        "small_blind" : 10,
        "big_blind" : 5,
    })
    assert response.status_code == HTTPStatus.BAD_REQUEST

@pytest.mark.parametrize(
        "num_of_players,status_code",
        [
            (1, HTTPStatus.UNPROCESSABLE_ENTITY),(0, HTTPStatus.UNPROCESSABLE_ENTITY),(2, HTTPStatus.CREATED),
            (10, HTTPStatus.CREATED),(11, HTTPStatus.UNPROCESSABLE_ENTITY)
        ]
)
def test_create_game_with_max_players_boundaries(client, num_of_players, status_code):
    """Validate max_players boundary constraints (2-10 players allowed)"""
    response = client.post("/api/games", json = {
        "game_name" : "Poker Hand Game",
        "max_players" : num_of_players
    })
    assert response.status_code == status_code

def test_create_game_validation_with_starting_chips(client):
    """Reject game with starting chips below minimum (10)"""
    reponse = client.post("/api/games", json={
        "game_name" : "Texas Poker Game",
        "starting_chips": 5
    })
    assert reponse.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_create_game_response_structure(client):
    """Validate complete game creation response structure and required fields"""
    response = client.post("/api/games", json={
        "game_name": "E2E Test Game",
        "small_blind": 5,
        "big_blind": 10,
        "max_players": 4,
        "starting_chips": 1000
    })
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()

    required_fields = ['game_id', 'game_name', 'status', 'created_at', 'players']
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    assert isinstance(data['game_id'], str)
    assert isinstance(data['game_name'], str)
    assert data['game_name'] == 'E2E Test Game'
    assert isinstance(data['status'], str)
    assert data['status'] in ['waiting', 'waiting_for_players']
    assert isinstance(data['created_at'], str)
    assert isinstance(data['players'], list)

# ===== GET GAME DETAILS TESTS =====

def test_get_game_details_with_valid_id(game, client):
    """Fetch game details with valid game ID"""
    response = client.get(f'/api/games/{game['game_id']}')
    assert response.status_code == HTTPStatus.OK
    assert game['game_name'] == 'Texas Poker Game'
    assert game['status'] == 'waiting'
    assert not game['players']

def test_get_game_details_with_invalid_id(client):
    """Return 404 when fetching game with invalid ID"""
    response = client.get("/api/games/999")
    assert response.status_code == HTTPStatus.NOT_FOUND

def test_get_game_details_with_null_id(client):
    """Return 404 when fetching game with null/empty ID"""
    response = client.get("/api/games/ ")
    assert response.status_code == HTTPStatus.NOT_FOUND

# ===== JOIN GAME TESTS =====

def test_join_a_game_with_an_invalid_id(client, player_1):
    """Return 404 when joining game with invalid game ID"""
    reponse = client.post("/api/games/999/join", json = {
        "player_id" : player_1['player_id']
    })
    assert reponse.status_code == HTTPStatus.NOT_FOUND

def test_join_game_with_max_players(client, game, player_1, player_2):
    """Join game with multiple players and verify state transition to in_progress"""
    # First Player joining the game
    response = client.post(f"/api/games/{game['game_id']}/join", json = {
        "player_id" : player_1['player_id']
    })
    assert response.status_code == HTTPStatus.OK
    game_details = response.json()
    assert game_details['status'] == 'waiting_for_players'
    assert game_details['message'] == 'Game will start when all players join'

    # Second player joining the game
    response = client.post(f"/api/games/{game['game_id']}/join", json = {
        "player_id" : player_2['player_id']
    })
    assert response.status_code == HTTPStatus.OK
    game_details = response.json()
    assert game_details['game_id'] == game['game_id']
    assert game_details['player_id'] == player_2['player_id']
    assert game_details['player_name'] == player_2['player_name']
    assert game_details['position'] == 1
    assert game_details['status'] == 'in_progress'
    assert game_details['message'] == 'Game has started!'

def test_join_a_valid_game_with_an_invalid_player_id(client, game):
    """Return 404 when player ID doesn't exist in database"""
    response = client.post(f"/api/games/{game['game_id']}/join", json={
        "player_id" : "550e8400-e29b-41d4-a716-446655440000"
    })
    assert response.status_code == HTTPStatus.NOT_FOUND

def test_join_a_game_with_more_than_max_players(client, game, player_1, player_2, player_3):
    """Return 409 when third player tries to join game with max_players=2"""
    response = client.post(f"/api/games/{game['game_id']}/join", json={
        "player_id" : player_1['player_id']
    })
    assert response.status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game['game_id']}/join", json={
        "player_id" : player_2['player_id']
    })
    assert response.status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game['game_id']}/join", json={
        "player_id" : player_3['player_id']
    })
    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Game has already started or is completed'

def test_duplicate_player_join_attempt(client, game, player_1):
    """Same player can rejoin game (updates their status in the game)"""
    response1 = client.post(f"/api/games/{game['game_id']}/join", json={
        "player_id": player_1['player_id']
    })
    assert response1.status_code == HTTPStatus.OK

    response2 = client.post(f"/api/games/{game['game_id']}/join", json={
        "player_id": player_1['player_id']
    })
    assert response2.status_code == HTTPStatus.OK

# ===== START HAND AND GAME FLOW TESTS =====

def test_create_game_and_start_hand(client, game, player_1, player_2):
    """Complete game flow: create game, join players, start hand with blinds and hole cards"""
    # Join both players
    assert client.post(f"/api/games/{game['game_id']}/join", json={
        "player_id": player_1['player_id']
    }).status_code == HTTPStatus.OK

    assert client.post(f"/api/games/{game['game_id']}/join", json={
        "player_id": player_2['player_id']
    }).status_code == HTTPStatus.OK

    # Start hand
    response = client.post(f"/api/games/{game['game_id']}/start-hand")
    data = response.json()

    # Validate hand response fields
    expected_hand_fields = {
        'game_id': game['game_id'],
        'hand_number': 1,
        'stage': 'preflop',
        'pot': 15,
        'small_blind_posted': 5,
        'big_blind_posted': 10,
        'current_turn': player_1['player_id'],
        'dealer_position': 0,
        'message': 'Hand #1 started! Blinds posted. Waiting for first action.',
    }
    for key, value in expected_hand_fields.items():
        assert data[key] == value

    assert len(data['players_state']) == 2

    # Validate player states
    expected_players = [
        {'player': player_1, 'position': 0, 'stacks': 995, 'current_bet': 5},
        {'player': player_2, 'position': 1, 'stacks': 990, 'current_bet': 10},
    ]

    for idx, expected in enumerate(expected_players):
        player_state = data['players_state'][idx]
        expected_player = expected['player']

        player_assertions = {
            'player_id': expected_player['player_id'],
            'name': expected_player['player_name'],
            'position': expected['position'],
            'stacks': expected['stacks'],
            'current_bet': expected['current_bet'],
            'status': 'Active',
        }
        for key, value in player_assertions.items():
            assert player_state[key] == value

        assert len(player_state['hole_cards']) == 2

def test_start_hand_without_all_players_joined(client, game, player_1):
    """Cannot start hand until all players join the game"""
    assert client.post(f"/api/games/{game['game_id']}/join", json={
        "player_id": player_1['player_id']
    }).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game['game_id']}/start-hand")
    assert response.status_code == HTTPStatus.CONFLICT

def test_start_hand_twice_same_game(client, game, player_1, player_2):
    """Cannot start same hand twice (hand already in progress)"""
    client.post(f"/api/games/{game['game_id']}/join", json={"player_id": player_1['player_id']})
    client.post(f"/api/games/{game['game_id']}/join", json={"player_id": player_2['player_id']})

    response1 = client.post(f"/api/games/{game['game_id']}/start-hand")
    assert response1.status_code == HTTPStatus.OK
    assert response1.json()['hand_number'] == 1

    response2 = client.post(f"/api/games/{game['game_id']}/start-hand")
    assert response2.status_code == HTTPStatus.CONFLICT

# ===== GAME HISTORY TESTS =====

def test_get_game_history_empty(client, game):
    """Get game history for new game (no hands played yet)"""
    response = client.get(f"/api/games/{game['game_id']}/history")
    assert response.status_code == HTTPStatus.OK
    data = response.json()

    expected_fields = {
        'game_id': game['game_id'],
        'total_hands': 0,
    }
    for key, value in expected_fields.items():
        assert data[key] == value
    assert data['hands'] == []

def test_get_game_history_with_hands(client, game, player_1, player_2):
    """Get game history after hands played in the game"""
    assert client.post(f"/api/games/{game['game_id']}/join", json={
        "player_id": player_1['player_id']
    }).status_code == HTTPStatus.OK

    assert client.post(f"/api/games/{game['game_id']}/join", json={
        "player_id": player_2['player_id']
    }).status_code == HTTPStatus.OK

    response = client.post(f"/api/games/{game['game_id']}/start-hand")
    assert response.status_code == HTTPStatus.OK

    response = client.get(f"/api/games/{game['game_id']}/history")
    assert response.status_code == HTTPStatus.OK
    data = response.json()

    assert data['game_id'] == game['game_id']
    assert data['total_hands'] >= 0
