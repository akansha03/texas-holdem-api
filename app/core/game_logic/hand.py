"""PokerHand Service - Evaluates poker hand rankings"""
from typing import List, Tuple
from itertools import combinations
from app.core.game_logic.card import PokerCard


class PokerHand:
    """Evaluates poker hand rankings and determines winners"""

    HAND_RANKINGS = {
        8: "Royal Flush",
        7: "Straight Flush",
        6: "Four of a Kind",
        5: "Full House",
        4: "Flush",
        3: "Straight",
        2: "Three of a Kind",
        1: "Two Pair",
        0: "Pair",
        -1: "High Card"
    }

    def evaluate_hand(self, cards: List[PokerCard]) -> Tuple[int, list]:
        """
        Evaluate a hand of 5-7 cards and return the best 5-card ranking

        Args:
            cards: List of 5-7 PokerCard objects

        Returns:
            Tuple: (hand_rank, kicker_values)
            - hand_rank: -1 (high card) to 8 (royal flush)
            - kicker_values: list of card values for tiebreaking
        """
        if len(cards) < 5:
            raise ValueError(f"Need at least 5 cards, got {len(cards)}")

        if len(cards) == 5:
            return self._evaluate_five_cards(cards)

        # Try all 5-card combinations and return the best
        best_rank = (-2, [])  # Start worse than worst hand

        for combo in combinations(cards, 5):
            combo_list = list(combo)
            rank, kickers = self._evaluate_five_cards(combo_list)
            score = (rank, kickers)

            if score > best_rank:
                best_rank = score

        return best_rank

    def _evaluate_five_cards(self, cards: List[PokerCard]) -> Tuple[int, list]:
        """
        Evaluate exactly 5 cards

        Returns: (rank, kickers)
        """
        values = sorted([card.get_numeric_value() for card in cards], reverse=True)
        suits = [card.suit for card in cards]

        # Check for flush
        is_flush = len(set(suits)) == 1

        # Check for straight
        is_straight, straight_high = self._check_straight(values)

        # Check for groups (pairs, three of a kind, etc)
        groups = self._get_groups(values)

        # Royal Flush: A-K-Q-J-10, same suit
        if is_flush and is_straight and values == [14, 13, 12, 11, 10]:
            return (8, [14])

        # Straight Flush
        if is_flush and is_straight:
            return (7, [straight_high])

        # Four of a Kind
        if self._has_n_of_a_kind(groups, 4):
            quads = [v for v, count in groups.items() if count == 4][0]
            kicker = [v for v in values if v != quads][0]
            return (6, [quads, kicker])

        # Full House
        if self._has_n_of_a_kind(groups, 3) and self._has_n_of_a_kind(groups, 2):
            trips = [v for v, count in groups.items() if count == 3][0]
            pair = [v for v, count in groups.items() if count == 2][0]
            return (5, [trips, pair])

        # Flush
        if is_flush:
            return (4, values)

        # Straight
        if is_straight:
            return (3, [straight_high])

        # Three of a Kind
        if self._has_n_of_a_kind(groups, 3):
            trips = [v for v, count in groups.items() if count == 3][0]
            kickers = sorted([v for v in values if v != trips], reverse=True)
            return (2, [trips] + kickers)

        # Two Pair
        pairs = [v for v, count in groups.items() if count == 2]
        if len(pairs) == 2:
            pairs = sorted(pairs, reverse=True)
            kicker = [v for v in values if v not in pairs][0]
            return (1, pairs + [kicker])

        # Pair
        if self._has_n_of_a_kind(groups, 2):
            pair = [v for v, count in groups.items() if count == 2][0]
            kickers = sorted([v for v in values if v != pair], reverse=True)
            return (0, [pair] + kickers)

        # High Card
        return (-1, values)

    def _check_straight(self, values: list) -> Tuple[bool, int]:
        """Check if values form a straight and return high card"""
        # Regular straight
        if values[0] - values[4] == 4 and len(set(values)) == 5:
            return (True, values[0])

        # Wheel straight (A-2-3-4-5, A is high)
        if values == [14, 5, 4, 3, 2]:
            return (True, 5)  # In a wheel, 5 is high card

        return (False, 0)

    def _get_groups(self, values: list) -> dict:
        """Count occurrences of each value"""
        groups = {}
        for v in values:
            groups[v] = groups.get(v, 0) + 1
        return groups

    def _has_n_of_a_kind(self, groups: dict, n: int) -> bool:
        """Check if groups contain n-of-a-kind"""
        return any(count == n for count in groups.values())

    def get_hand_name(self, rank: int) -> str:
        """Get readable name for hand rank"""
        return self.HAND_RANKINGS.get(rank, "Unknown")

    def compare_hands(self, hand1: Tuple[int, list], hand2: Tuple[int, list]) -> int:
        """
        Compare two hands

        Args:
            hand1: (rank, kickers)
            hand2: (rank, kickers)

        Returns:
            1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        rank1, kickers1 = hand1
        rank2, kickers2 = hand2

        # Compare ranks first
        if rank1 > rank2:
            return 1
        elif rank1 < rank2:
            return -1

        # Same rank - compare kickers
        for k1, k2 in zip(kickers1, kickers2):
            if k1 > k2:
                return 1
            elif k1 < k2:
                return -1

        # Identical hands
        return 0
