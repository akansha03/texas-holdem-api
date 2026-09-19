import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.game_logic.game import PokerGame
from app.db.models import Base
from app.db import get_db
from app.config import settings
from fastapi.testclient import TestClient
from app.main import app
from http import HTTPStatus

def advance_stage(client, game_id):
    """Helper to advance game stage with admin token"""
    return client.post(f"/api/games/{game_id}/advance-stage",
                      params={"admin_token": settings.admin_token}).json()

SQLALCHEMY_DATABASE_URL = f'postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}_test'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture()
def game(client):
    response = client.post("/api/games", json={
        "game_name" : "Texas Poker Game"
    })
    assert response.status_code == HTTPStatus.CREATED

    new_game = response.json()
    return new_game

@pytest.fixture
def player_1(client):
    response = client.post("/api/players", json= {
        "player_name" : "John Doe",
        "email" : "john_doe@gmail.com"
    })
    assert response.status_code == HTTPStatus.CREATED
    return response.json()

@pytest.fixture
def player_2(client):
    response = client.post("/api/players", json= {
        "player_name" : "Jane Doe",
        "email" : "jane_doe@gmail.com"
    })
    assert response.status_code == HTTPStatus.CREATED
    return response.json()

@pytest.fixture
def player_3(client):
    response = client.post("/api/players", json= {
        "player_name" : "Scooby Doo"
    })
    assert response.status_code == HTTPStatus.CREATED
    return response.json()

@pytest.fixture
def players_join_game(client, game, player_1, player_2):

    players = [player_1, player_2]
    for player in players:
        response = client.post(f"/api/games/{game['game_id']}/join", json={
            "player_id" : player['player_id']
        })
        assert response.status_code == HTTPStatus.OK
    return response.json()

@pytest.fixture
def game_at_preflop(client, game, players_join_game):
    assert players_join_game['status'] == 'in_progress'

    response = client.get(f"/api/games/{game['game_id']}/state")
    assert response.status_code == HTTPStatus.OK

    hand_data = client.post(f"/api/games/{game['game_id']}/start-hand").json()
    assert hand_data['stage'] == 'preflop'
    return hand_data

@pytest.fixture
def game_at_flop(client, game, game_at_preflop):
    assert game_at_preflop['stage'] == 'preflop'
    data = advance_stage(client, game['game_id'])
    assert data['stage'] == 'flop'
    return data

@pytest.fixture
def game_at_turn(client, game, game_at_flop):
    assert game_at_flop['stage'] == 'flop'
    data = advance_stage(client, game['game_id'])
    assert data['stage'] == 'turn'
    return data

@pytest.fixture
def game_at_river(client, game, game_at_turn):
    assert game_at_turn['stage'] == 'turn'
    data = advance_stage(client, game['game_id'])
    assert data['stage'] == 'river'
    return data