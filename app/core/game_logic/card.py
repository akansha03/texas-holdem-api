"""PokerCard Service - Represents a single playing card"""


class PokerCard:
    """A single poker card with suit and rank"""

    VALID_SUITS = {"S", "H", "D", "C"}  # Spades, Hearts, Diamonds, Clubs
    VALID_RANKS = {"2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"}

    # Rank to numeric value mapping (for comparison)
    RANK_VALUES = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
        "J": 11, "Q": 12, "K": 13, "A": 14
    }

    def __init__(self, suit: str, rank: str):
        """
        Create a poker card

        Args:
            suit: One of S (spades), H (hearts), D (diamonds), C (clubs)
            rank: One of 2-10, J, Q, K, A
        """
        suit = suit.upper()
        rank = str(rank).upper()

        if suit not in self.VALID_SUITS:
            raise ValueError(f"Invalid suit: {suit}. Must be one of {self.VALID_SUITS}")

        if rank not in self.VALID_RANKS:
            raise ValueError(f"Invalid rank: {rank}. Must be one of {self.VALID_RANKS}")

        self.suit = suit
        self.rank = rank

    def get_numeric_value(self) -> int:
        """Return numeric value of rank (2-14)"""
        return self.RANK_VALUES[self.rank]

    def __str__(self) -> str:
        """String representation: AS (Ace of Spades), 2H (Two of Hearts), etc."""
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:
        """For debugging"""
        return f"PokerCard({self.rank}{self.suit})"

    def __eq__(self, other) -> bool:
        """Compare two cards"""
        if not isinstance(other, PokerCard):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self) -> int:
        """Allow card to be used in sets/dicts"""
        return hash((self.suit, self.rank))
