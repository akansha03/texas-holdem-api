import uuid
import pytest
from http import HTTPStatus

def test_create_a_player_with_unique_email_id(client):
    # Verify player creation with both name and email
    response = client.post("/api/players", json={
        "player_name" : "Jane Doe",
        "email" : "jane_doe@email.com"
    })
    assert response.status_code == HTTPStatus.CREATED
    player_profile = response.json()
    assert player_profile['player_name'] == 'Jane Doe'
    assert player_profile['email'] == 'jane_doe@email.com'
    assert player_profile['total_games'] == 0
    assert player_profile['total_wins'] == 0
    assert player_profile['total_chips_won'] == 0

@pytest.mark.parametrize(
        "player_name,email",
        [
            ("Johnny Bravo", "abc"),
            ("Jane",123),
            ("Han", '1@3'),
            (" ", " ")
        ]
)
def test_create_a_player_with_invalid_parameters(client, player_name, email):
    # Verify validation rejects invalid name/email formats
    response = client.post("/api/players", json={
        "player_name" : player_name,
        "email" : email
    })
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_create_two_players_with_same_email_should_return_in_conflict(client, player_1):
    # Verify duplicate email is rejected (unique constraint)
    response = client.post("/api/players", json={
        "player_name" : "John",
        "email" : "john_doe@gmail.com"
    })

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()['detail'] == 'Email john_doe@gmail.com is already registered'

def test_create_a_player_with_only_name(client):
    # Verify player can be created with just name (email optional)
    assert client.post("/api/players", json={
        "player_name" : "Alice"
    }).status_code == HTTPStatus.CREATED

def test_create_a_player_with_only_email(client):
    # Verify player_name is mandatory
    assert client.post("/api/players", json={
        "email" : "abc@email.com"
    }).status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_create_and_get_a_player(client, player_1):
    # Verify retrieval of existing player with correct fields
    response = client.get(f"/api/players/{player_1['player_id']}")
    assert response.status_code == HTTPStatus.OK
    player_profile = response.json()

    assert player_profile['player_name'] == 'John Doe'
    assert player_profile['email'] == 'john_doe@gmail.com'
    assert player_profile['total_games'] == 0
    assert player_profile['total_wins'] == 0
    assert player_profile['total_chips_won'] == 0

def test_get_an_invalid_player(client):
    # Verify 404 for non-existent player_id
    assert client.get(f"/api/players/{str(uuid.uuid4())}").status_code == HTTPStatus.NOT_FOUND

def test_update_an_existing_player_name(client, player_1):
    # Verify player name update succeeds
    response = client.put(f"/api/players/{player_1['player_id']}", json = {
        "player_name" : "Johny Doe"
    })
    assert response.status_code == HTTPStatus.OK

@pytest.mark.parametrize(
        "player_name, email",
        [
            ("", ""),
            (None, None),
            ("Alice", " "),
            ("", "alison@gmail.com")
        ]
)
def test_update_a_player_with_valid_parameters(client, player_1, player_name, email):
    # Verify update accepts optional name/email fields
    assert client.put(f"/api/players/{player_1['player_id']}", json={
        "player_name" : player_name,
        "email" : email
    }).status_code == HTTPStatus.OK

def test_create_and_delete_a_player(client):
    # Verify full CRUD cycle: create, retrieve, delete, verify deletion
    response = client.post("/api/players", json={
        "player_name" : "Jason Doe",
        "email" : "jason_doe@gmail.com"
    })

    assert response.status_code == HTTPStatus.CREATED
    player_detail = response.json()

    assert client.get(f"/api/players/{player_detail['player_id']}").status_code == HTTPStatus.OK

    assert client.delete(f"/api/players/{player_detail['player_id']}").status_code == HTTPStatus.NO_CONTENT

    assert client.get(f"/api/players/{player_detail['player_id']}").status_code == HTTPStatus.NOT_FOUND

def test_delete_an_invalid_player(client):
    # Verify 404 when deleting non-existent player
    assert client.delete(f"/api/players/{str(uuid.uuid4())}").status_code == HTTPStatus.NOT_FOUND

def test_get_stats_of_valid_player(client, player_1):
    # Verify stats endpoint returns correct initial values
    player_stats = client.get(f"/api/players/{player_1['player_id']}/stats").json()
    print(player_stats)
    assert player_stats['total_games'] == 0
    assert player_stats['total_wins'] == 0
    assert player_stats['win_rate'] == 0
    assert player_stats['total_chips'] == 1000
    assert player_stats['total_won'] == 0

def test_create_multiple_players_without_email(client):
    # Verify multiple players can be created without email (mobile app scenario)
    player1 = client.post("/api/players", json={"player_name": "Player One"}).json()
    player2 = client.post("/api/players", json={"player_name": "Player Two"}).json()

    assert player1['email'] is None
    assert player2['email'] is None
    assert player1['player_id'] != player2['player_id']

def test_update_player_to_add_email(client):
    # Verify adding email to a player created without one
    create_resp = client.post("/api/players", json={"player_name": "NoEmail Player"})
    player_id = create_resp.json()['player_id']

    update_resp = client.put(f"/api/players/{player_id}", json={"email": "newemail@test.com"})
    assert update_resp.status_code == HTTPStatus.OK
    assert update_resp.json()['email'] == 'newemail@test.com'

def test_update_player_to_remove_email(client):
    # Verify removing email from player (clear to null)
    create_resp = client.post("/api/players", json={
        "player_name": "Has Email",
        "email": "hasemail@test.com"
    })
    player_id = create_resp.json()['player_id']

    update_resp = client.put(f"/api/players/{player_id}", json={"email": None})
    assert update_resp.status_code == HTTPStatus.OK
    assert update_resp.json()['email'] is None

def test_list_all_players(client):
    # Verify list endpoint returns all players with correct count
    client.post("/api/players", json={"player_name": "ListPlayer1"})
    client.post("/api/players", json={"player_name": "ListPlayer2"})

    response = client.get("/api/players").json()
    assert response['total_count'] >= 2
    assert len(response['players']) >= 2

def test_player_name_minimum_length(client):
    # Verify player_name must be at least 2 characters
    response = client.post("/api/players", json={"player_name": "A"})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

def test_player_name_maximum_length(client):
    # Verify player_name cannot exceed 100 characters
    long_name = "A" * 101
    response = client.post("/api/players", json={"player_name": long_name})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY