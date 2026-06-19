"""Game Manager - Manages multiple concurrent game sessions"""
from typing import Dict, Optional
from datetime import datetime
import uuid
from app.core.game_logic.game import PokerGame
from app.core.game_logic.player import Player

class GameSession:
    """Represents a single poker game session"""

    def __init__(
        self,
        game_id: str,
        game_name: str,
        small_blind: int,
        big_blind: int,
        max_players: int,
        starting_chips: int
    ):
        self.game_id = game_id
        self.game_name = game_name
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.max_players = max_players
        self.starting_chips = starting_chips
        self.created_at = datetime.utcnow()

        self.players: Dict[str, Player] = {}  # {player_id: Player service instance}
        self.status = "waiting_for_players"  # waiting_for_players, in_progress, completed
        self.current_hand = 0
        self.hand_history = []  # List of completed hands

        # Initialize PokerGame instance with service layer
        self.game = PokerGame(
            small_blind=small_blind,
            big_blind=big_blind,
            max_players=max_players
        )

    def add_player(self, player_id: str, player_name: str) -> bool:
        """Add player to game session"""
        if len(self.players) >= self.max_players:
            return False

        # Create Player service instance
        player = Player(
            player_id=player_id,
            player_name=player_name,
            starting_chips=self.starting_chips,
            position=len(self.players)
        )
        self.players[player_id] = player

        # Add to PokerGame service
        self.game.add_player(player)

        # Start game when all players joined
        if len(self.players) == self.max_players:
            self.status = "in_progress"

        return True

    def get_player(self, player_id: str) -> Optional[Player]:
        """Get player by ID"""
        return self.players.get(player_id)

    def get_players(self) -> list:
        """Get all players in session"""
        return list(self.players.values())

    def get_players_state(self) -> list:
        """Get all players' state as dicts for API response"""
        return [player.to_dict() for player in self.players.values()]


class GameManager:
    """Manages all active game sessions"""

    def __init__(self):
        self.games: Dict[str, GameSession] = {}

    def create_game(
        self,
        game_name: str,
        small_blind: int,
        big_blind: int,
        max_players: int = 2,
        starting_chips: int = 1000
    ) -> GameSession:
        """Create a new game session"""
        game_id = f"game_{uuid.uuid4().hex[:12]}"

        game = GameSession(
            game_id=game_id,
            game_name=game_name,
            small_blind=small_blind,
            big_blind=big_blind,
            max_players=max_players,
            starting_chips=starting_chips
        )

        self.games[game_id] = game
        return game

    def get_game(self, game_id: str) -> Optional[GameSession]:
        """Get game session by ID"""
        return self.games.get(game_id)

    def join_game(self, game_id: str, player_id: str, player_name: str) -> bool:
        """Add player to game"""
        game = self.get_game(game_id)
        if not game:
            return False
        return game.add_player(player_id, player_name)

    def delete_game(self, game_id: str) -> bool:
        """Remove completed game"""
        if game_id in self.games:
            del self.games[game_id]
            return True
        return False

    def get_all_games(self) -> list:
        """Get all active games"""
        return list(self.games.values())

# Global game manager instance
game_manager = GameManager()
