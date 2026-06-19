"""CRUD Operations for Database"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Player, GameSession, GameParticipant, Hand, HandResult
from datetime import datetime


# ============ PLAYER CRUD ============

def get_player(db: Session, player_id: str) -> Player:
    """Get a player by ID"""
    return db.query(Player).filter(Player.player_id == player_id).first()


def get_player_by_name(db: Session, player_name: str) -> Player:
    """Get a player by name"""
    return db.query(Player).filter(Player.player_name == player_name).first()


def get_all_players(db: Session) -> list[Player]:
    """Get all players"""
    return db.query(Player).all()


def create_player(db: Session, player_name: str, email: str = None) -> Player:
    """Create a new player - player_id is auto-generated"""
    player = Player(
        player_name=player_name,
        email=email,
        total_chips=1000
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


def update_player_chips(db: Session, player_id: str, chips: float) -> Player:
    """Update player's total chips"""
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if player:
        player.total_chips = chips
        player.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(player)
    return player


def update_player_stats(db: Session, player_id: str, games: int = 0, wins: int = 0) -> Player:
    """Update player's game statistics"""
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if player:
        if games != 0:
            player.total_games += games
        if wins != 0:
            player.total_wins += wins
        player.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(player)
    return player


def delete_player(db: Session, player_id: str) -> bool:
    """Delete a player"""
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if player:
        db.delete(player)
        db.commit()
        return True
    return False


# ============ GAME SESSION CRUD ============

def get_game_session(db: Session, game_id: str) -> GameSession:
    """Get a game session by ID"""
    return db.query(GameSession).filter(GameSession.game_id == game_id).first()


def get_all_games(db: Session) -> list[GameSession]:
    """Get all game sessions"""
    return db.query(GameSession).all()


def get_active_games(db: Session) -> list[GameSession]:
    """Get all active game sessions"""
    from app.db.models import GameStatus
    return db.query(GameSession).filter(
        GameSession.status.in_([GameStatus.WAITING, GameStatus.IN_PROGRESS])
    ).all()


def create_game_session(db: Session, game_id: str, game_name: str, small_blind: int,
                       big_blind: int, max_players: int = 6) -> GameSession:
    """Create a new game session"""
    game = GameSession(
        game_id=game_id,
        game_name=game_name,
        small_blind=small_blind,
        big_blind=big_blind,
        max_players=max_players
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


def update_game_status(db: Session, game_id: str, status: str) -> GameSession:
    """Update game status"""
    game = db.query(GameSession).filter(GameSession.game_id == game_id).first()
    if game:
        from app.db.models import GameStatus
        game.status = GameStatus(status)
        if status == "completed":
            game.completed_at = datetime.utcnow()
        game.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(game)
    return game


def update_game_stage(db: Session, game_id: str, stage: str) -> GameSession:
    """Update game's current stage"""
    game = db.query(GameSession).filter(GameSession.game_id == game_id).first()
    if game:
        game.current_stage = stage
        game.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(game)
    return game


def update_game_pot(db: Session, game_id: str, pot: float) -> GameSession:
    """Update game's pot amount"""
    game = db.query(GameSession).filter(GameSession.game_id == game_id).first()
    if game:
        game.pot = pot
        game.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(game)
    return game


def delete_game_session(db: Session, game_id: str) -> bool:
    """Delete a game session"""
    game = db.query(GameSession).filter(GameSession.game_id == game_id).first()
    if game:
        db.delete(game)
        db.commit()
        return True
    return False


# ============ GAME PARTICIPANT CRUD ============

def add_game_participant(db: Session, game_id: str, player_id: str,
                        starting_chips: float, position: int = None) -> GameParticipant:
    """Add a player to a game"""
    participant = GameParticipant(
        game_id=game_id,
        player_id=player_id,
        starting_chips=starting_chips,
        current_chips=starting_chips,
        position=position
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def get_game_participants(db: Session, game_id: str) -> list[GameParticipant]:
    """Get all participants in a game"""
    return db.query(GameParticipant).filter(GameParticipant.game_id == game_id).all()


def get_game_participant(db: Session, game_id: str, player_id: str) -> GameParticipant:
    """Get a specific participant in a game"""
    return db.query(GameParticipant).filter(
        GameParticipant.game_id == game_id,
        GameParticipant.player_id == player_id
    ).first()


def update_participant_chips(db: Session, game_id: str, player_id: str, chips: float) -> GameParticipant:
    """Update participant's chip count"""
    participant = get_game_participant(db, game_id, player_id)
    if participant:
        participant.current_chips = chips
        db.commit()
        db.refresh(participant)
    return participant


def update_participant_active(db: Session, game_id: str, player_id: str, is_active: bool) -> GameParticipant:
    """Update participant's active status"""
    participant = get_game_participant(db, game_id, player_id)
    if participant:
        participant.is_active = is_active
        db.commit()
        db.refresh(participant)
    return participant


def remove_game_participant(db: Session, game_id: str, player_id: str) -> bool:
    """Remove a player from a game"""
    participant = get_game_participant(db, game_id, player_id)
    if participant:
        db.delete(participant)
        db.commit()
        return True
    return False


# ============ HAND CRUD ============

def create_hand(db: Session, game_id: str, hand_number: int) -> Hand:
    """Create a new hand"""
    hand = Hand(
        game_id=game_id,
        hand_number=hand_number
    )
    db.add(hand)
    db.commit()
    db.refresh(hand)
    return hand


def get_hand(db: Session, hand_id: int) -> Hand:
    """Get a hand by ID"""
    return db.query(Hand).filter(Hand.id == hand_id).first()


def get_game_hands(db: Session, game_id: str) -> list[Hand]:
    """Get all hands in a game"""
    return db.query(Hand).filter(Hand.game_id == game_id).all()


def update_hand_community_cards(db: Session, hand_id: int, cards: str) -> Hand:
    """Update hand's community cards"""
    hand = get_hand(db, hand_id)
    if hand:
        hand.community_cards = cards
        db.commit()
        db.refresh(hand)
    return hand


def complete_hand(db: Session, hand_id: int) -> Hand:
    """Mark hand as completed"""
    hand = get_hand(db, hand_id)
    if hand:
        hand.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(hand)
    return hand


# ============ HAND RESULT CRUD ============

def create_hand_result(db: Session, hand_id: int, player_id: str,
                      hole_cards: str = None, final_hand: str = None,
                      hand_rank: str = None, amount_won: float = 0,
                      is_winner: bool = False, folded: bool = False) -> HandResult:
    """Create a hand result"""
    result = HandResult(
        hand_id=hand_id,
        player_id=player_id,
        hole_cards=hole_cards,
        final_hand=final_hand,
        hand_rank=hand_rank,
        amount_won=amount_won,
        is_winner=is_winner,
        folded=folded
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_hand_results(db: Session, hand_id: int) -> list[HandResult]:
    """Get all results for a hand"""
    return db.query(HandResult).filter(HandResult.hand_id == hand_id).all()


def get_player_hand_result(db: Session, hand_id: int, player_id: str) -> HandResult:
    """Get a player's result for a specific hand"""
    return db.query(HandResult).filter(
        HandResult.hand_id == hand_id,
        HandResult.player_id == player_id
    ).first()


def get_player_statistics(db: Session, player_id: str) -> dict:
    """Get comprehensive player statistics"""
    player = get_player(db, player_id)
    if not player:
        return None

    # Get hand results
    hand_results = db.query(HandResult).filter(HandResult.player_id == player_id).all()

    total_games = len(set(h.hand.game_id for h in hand_results)) if hand_results else 0
    wins = len([h for h in hand_results if h.is_winner]) if hand_results else 0
    total_won = sum(h.amount_won for h in hand_results) if hand_results else 0

    return {
        "player_id": player_id,
        "player_name": player.player_name,
        "total_games": total_games,
        "total_wins": wins,
        "win_rate": (wins / total_games * 100) if total_games > 0 else 0,
        "total_chips": player.total_chips,
        "total_won": total_won
    }
