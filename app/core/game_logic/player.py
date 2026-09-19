"""Player Service - Manages individual player state"""
from typing import List, Optional
from app.core.game_logic.card import PokerCard


class Player:
    """Represents a single player in the game"""

    def __init__(self, player_id: str, player_name: str, starting_chips: int, position: int = 0):
        """
        Create a player

        Args:
            player_id: Unique identifier (e.g., "p1", "user_123")
            player_name: Player's name
            starting_chips: Initial chip count
            position: Seat position at table (0 = dealer, 1 = small blind, etc)
        """
        self.player_id = player_id
        self.player_name = player_name
        self.starting_chips = starting_chips
        self.position = position

        # State
        self.stacks = starting_chips
        self.hole_cards: List[PokerCard] = []
        self.current_bet = 0
        self.status = "Active"  # Active, Folded, All-in
        self.has_folded = False

    def receive_hole_cards(self, card1: PokerCard, card2: PokerCard):
        """Receive 2 hole cards"""
        self.hole_cards = [card1, card2]

    def get_hole_cards(self) -> List[PokerCard]:
        """Get player's hole cards"""
        return self.hole_cards

    def get_stacks(self) -> int:
        """Get remaining chips"""
        return self.stacks

    def deduct_chips(self, amount: int) -> bool:
        """
        Deduct chips (for bets)

        Args:
            amount: Chips to deduct

        Returns:
            True if successful, False if insufficient chips
        """
        if amount < 0 or amount > self.stacks:
            return False

        self.stacks -= amount
        self.current_bet += amount

        if self.stacks == 0:
            self.status = "All-in"

        return True

    def add_chips(self, amount: int):
        """Add chips (from pot, winnings)"""
        self.stacks += amount
        if self.stacks > 0:
            self.status = "Active"

    def fold(self):
        """Player folds"""
        self.has_folded = True
        self.status = "Folded"

    def reset_for_new_hand(self):
        """Reset player state for a new hand"""
        self.hole_cards = []
        self.current_bet = 0
        self.has_folded = False

        # Only reset status to Active if player still has chips
        if self.stacks > 0:
            self.status = "Active"
        elif self.stacks == 0:
            self.status = "All-in"

    def all_in(self, amount: Optional[int] = None) -> int:
        """
        Push all remaining chips to pot

        Args:
            amount: Optional max amount (if less than stack)

        Returns:
            Amount actually pushed
        """
        if amount is None:
            amount_to_push = self.stacks
        else:
            amount_to_push = min(amount, self.stacks)

        self.stacks -= amount_to_push
        self.current_bet += amount_to_push
        self.status = "All-in"

        return amount_to_push

    def can_act(self) -> bool:
        """Can player take an action?"""
        return self.status == "Active" and not self.has_folded and self.stacks > 0

    def reset_current_bet(self):
        """Reset current bet for new betting round"""
        self.current_bet = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "position": self.position,
            "stacks": self.stacks,
            "current_bet": self.current_bet,
            "status": self.status,
            "has_folded": self.has_folded,
            "hole_cards_count": len(self.hole_cards),
        }
