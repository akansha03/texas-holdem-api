"""PokerDeck Service - Manages a deck of 52 playing cards"""
import random
from typing import List
from app.core.game_logic.card import PokerCard


class PokerDeck:
    """Manages a deck of 52 poker cards"""

    def __init__(self):
        """Initialize deck with all 52 cards"""
        self.cards: List[PokerCard] = []
        self._initialize_deck()

    def _initialize_deck(self):
        """Create a fresh deck with all 52 cards"""
        suits = ["S", "H", "D", "C"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

        for suit in suits:
            for rank in ranks:
                self.cards.append(PokerCard(suit, rank))

    def shuffle_cards(self):
        """Randomize deck order"""
        random.shuffle(self.cards)

    def burn_card(self) -> PokerCard:
        """Remove and return top card (discarded before dealing community cards)"""
        if not self.cards:
            raise ValueError("Cannot burn card - deck is empty")
        return self.cards.pop(0) 

    def deal_card(self) -> PokerCard:
        """Deal and return the top card"""
        if not self.cards:
            raise ValueError("Cannot deal card - deck is empty")
        return self.cards.pop(0)

    def distribute_hole_cards(self, num_players: int = 2) -> dict:
        """
        Distribute 2 hole cards to each player

        Args:
            num_players: Number of players in game

        Returns:
            Dictionary: {player_number: [card1, card2]}
        """
        if num_players * 2 > len(self.cards):
            raise ValueError(f"Not enough cards to deal {num_players} players")

        player_cards = {}
        for player_num in range(num_players):
            player_cards[player_num] = [self.deal_card(), self.deal_card()]

        return player_cards

    def deal_community_cards(self, stage: str) -> List[PokerCard]:
        """
        Deal community cards for each stage

        Args:
            stage: 'flop' (3 cards), 'turn' (1 card), 'river' (1 card)

        Returns:
            List of cards dealt
        """
        if stage == "flop":
            self.burn_card()  # Burn before flop
            return [self.deal_card(), self.deal_card(), self.deal_card()]
        elif stage == "turn":
            self.burn_card()  # Burn before turn
            return [self.deal_card()]
        elif stage == "river":
            self.burn_card()  # Burn before river
            return [self.deal_card()]
        else:
            raise ValueError(f"Invalid stage: {stage}. Must be 'flop', 'turn', or 'river'")

    def cards_remaining(self) -> int:
        """Return number of cards left in deck"""
        return len(self.cards)

    def reset_deck(self):
        """Reset to fresh 52-card deck"""
        self.cards = []
        self._initialize_deck()
