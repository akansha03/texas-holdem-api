"""PokerGame Service - Core game logic and orchestration"""
from typing import List, Dict, Optional, Tuple
from app.core.game_logic.card import PokerCard
from app.core.game_logic.deck import PokerDeck
from app.core.game_logic.hand import PokerHand
from app.core.game_logic.player import Player


class PokerGame:
    """Manages a single poker game session"""

    def __init__(self, small_blind: int = 5, big_blind: int = 10, max_players: int = 2):
        """
        Initialize a poker game

        Args:
            small_blind: Small blind amount
            big_blind: Big blind amount
            max_players: Maximum number of players

        Raises:
            ValueError: If blind values are invalid
        """
        # Validate blinds
        if small_blind <= 0:
            raise ValueError("Small blind must be greater than 0")
        if big_blind <= 0:
            raise ValueError("Big blind must be greater than 0")
        if big_blind <= small_blind:
            raise ValueError(
                f"Big blind ({big_blind}) must be greater than small blind ({small_blind}). "
                f"Typical ratio is 1:2"
            )
        if max_players < 2 or max_players>10:
            raise ValueError("Max Players must be between 2 and 10")
        
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.max_players = max_players

        self.players: List[Player] = []
        self.deck: Optional[PokerDeck] = None
        self.hand_evaluator = PokerHand()

        # Game state
        self.stage = "preflop"  # preflop, flop, turn, river, showdown
        self.pot = 0
        self.community_cards: List[PokerCard] = []
        self.current_player_index = 0
        self.dealer_position = 0
        self.hand_number = 0
        self.betting_round_active = False
        self.highest_bet_in_round = 0
        self.players_acted_this_round: set = set()  # Track who has acted

    def add_player(self, player: Player) -> bool:
        """Add player to game"""
        if len(self.players) >= self.max_players:
            return False
        player.position = len(self.players)
        self.players.append(player)
        return True

    def get_player(self, player_id: str) -> Optional[Player]:
        """Get player by ID"""
        for p in self.players:
            if p.player_id == player_id:
                return p
        return None

    def start_new_hand(self):
        """Initialize a new hand"""
        self.hand_number += 1
        self.stage = "preflop"
        self.pot = 0
        self.community_cards = []
        self.current_player_index = 0
        self.highest_bet_in_round = 0
        self.betting_round_active = True
        self.players_acted_this_round = set()

        # Reset player state
        for player in self.players:
            if player.get_stacks() > 0: 
                player.reset_for_new_hand()

        # Create and shuffle deck
        self.deck = PokerDeck()
        self.deck.shuffle_cards()

        # Deal hole cards
        hole_cards = self.deck.distribute_hole_cards(len(self.players))
        for i, player in enumerate(self.players):
            card1, card2 = hole_cards[i]
            player.receive_hole_cards(card1, card2)

    def post_blinds(self):
        """Post small and big blinds"""
        if len(self.players) < 2:
            raise ValueError("Need at least 2 players to post blinds")

        # In 2-player, dealer is small blind
        sb_position = self.dealer_position
        bb_position = (self.dealer_position + 1) % len(self.players)

        # Post small blind
        sb_player = self.players[sb_position]
        sb_amount = min(self.small_blind, sb_player.get_stacks())
        sb_player.deduct_chips(sb_amount)
        self.pot += sb_amount

        # Post big blind
        bb_player = self.players[bb_position]
        bb_amount = min(self.big_blind, bb_player.get_stacks())
        bb_player.deduct_chips(bb_amount)
        self.pot += bb_amount

        self.highest_bet_in_round = bb_amount

        # First to act is after big blind (UTG in preflop)
        self.current_player_index = (bb_position + 1) % len(self.players)

    def get_current_player(self) -> Optional[Player]:
        """Get player whose turn it is"""
        if not self.players or self.current_player_index >= len(self.players):
            return None
        return self.players[self.current_player_index]

    def is_betting_round_complete(self) -> bool:
        """
        Check if the current betting round is complete.

        Betting round ends when:
        1. Only 1 active player left (rest folded)
        2. All active players have acted AND all have same bet (or all-in)

        Returns: True if betting round should end, False otherwise
        """
        active_players = self.get_active_players()

        # If only 1 player left, hand is over
        if len(active_players) <= 1:
            return True

        # Check if all active players have acted at least once
        for player in active_players:
            if player.player_id not in self.players_acted_this_round:
                return False

        # Check if all active players have matched the highest bet (or are all-in)
        for player in active_players:
            if player.current_bet < self.highest_bet_in_round and player.get_stacks() > 0:
                return False

        return True

    def advance_to_next_player(self):
        """Move to next player who can act"""
        if not self.players:
            return

        start_index = self.current_player_index
        loop_count = 0

        while loop_count < len(self.players):
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            current = self.players[self.current_player_index]

            # Can this player act?
            if current.can_act():
                return

            loop_count += 1

        # No active players
        self.current_player_index = start_index

    def player_fold(self, player_id: str) -> bool:
        """Player folds"""
        player = self.get_player(player_id)
        if not player:
            return False

        player.fold()

        # Check if only one player remains (everyone else folded)
        active = self.get_active_players()
        if len(active) == 1:
            # Hand ends immediately - remaining player wins
            self.stage = "showdown"
            self.betting_round_active = False
            return True

        self.advance_to_next_player()
        return True

    def player_check(self, player_id: str) -> bool:
        """Player checks"""
        player = self.get_player(player_id)
        if not player:
            return False

        # Can only check if no one has bet
        if player.current_bet < self.highest_bet_in_round:
            return False

        # Track that this player has acted
        self.players_acted_this_round.add(player_id)

        # Check if betting round is complete
        if self.is_betting_round_complete():
            self.betting_round_active = False
            # Auto-advance to next stage if not at showdown
            if self.stage != "river":
                self.advance_stage()
            elif self.stage == "river":
                self.stage = "showdown"
            return True

        self.advance_to_next_player()
        return True

    def player_call(self, player_id: str) -> bool:
        """Player calls current bet"""
        player = self.get_player(player_id)
        if not player:
            return False

        amount_needed = self.highest_bet_in_round - player.current_bet
        if amount_needed <= 0:
            return self.player_check(player_id)

        if not player.deduct_chips(amount_needed):
            return False  # Insufficient chips

        self.pot += amount_needed

        # Track that this player has acted
        self.players_acted_this_round.add(player_id)

        # Check if betting round is complete
        if self.is_betting_round_complete():
            self.betting_round_active = False
            # Auto-advance to next stage if not at showdown
            if self.stage != "river":
                self.advance_stage()
            elif self.stage == "river":
                self.stage = "showdown"
            return True

        self.advance_to_next_player()
        return True

    def player_raise(self, player_id: str, raise_to: int) -> bool:
        """Player raises to amount"""
        player = self.get_player(player_id)
        if not player:
            return False

        if raise_to <= self.highest_bet_in_round:
            return False  # Raise must be higher than current

        amount_needed = raise_to - player.current_bet
        if amount_needed > player.get_stacks():
            return False  # Insufficient chips

        if not player.deduct_chips(amount_needed):
            return False

        self.pot += amount_needed
        self.highest_bet_in_round = raise_to

        # Track that this player has acted (but clear others since they need to respond)
        self.players_acted_this_round.clear()
        self.players_acted_this_round.add(player_id)

        self.advance_to_next_player()
        return True

    def player_all_in(self, player_id: str) -> bool:
        """Player goes all-in"""
        player = self.get_player(player_id)
        if not player:
            return False

        amount = player.all_in()
        self.pot += amount

        # If this is more than current bet, it's a raise
        if player.current_bet > self.highest_bet_in_round:
            self.highest_bet_in_round = player.current_bet
            # Clear others since they need to respond to the raise
            self.players_acted_this_round.clear()

        # Track that this player has acted
        self.players_acted_this_round.add(player_id)

        # Check if betting round is complete
        if self.is_betting_round_complete():
            self.betting_round_active = False
            # Auto-advance to next stage if not at showdown
            if self.stage != "river":
                self.advance_stage()
            elif self.stage == "river":
                self.stage = "showdown"
            return True

        self.advance_to_next_player()
        return True

    def advance_stage(self):
        """Advance to next stage (flop/turn/river)"""
        if self.stage == "preflop":
            self.stage = "flop"
            self.community_cards.extend(self.deck.deal_community_cards("flop"))
        elif self.stage == "flop":
            self.stage = "turn"
            self.community_cards.extend(self.deck.deal_community_cards("turn"))
        elif self.stage == "turn":
            self.stage = "river"
            self.community_cards.extend(self.deck.deal_community_cards("river"))
        elif self.stage == "river":
            self.stage = "showdown"
            return

        # Reset for new betting round
        self.highest_bet_in_round = 0
        self.players_acted_this_round = set()
        for player in self.players:
            if not player.has_folded:
                player.reset_current_bet()

    def get_active_players(self) -> List[Player]:
        """Get players still in the hand"""
        return [p for p in self.players if not p.has_folded]

    def determine_winner(self) -> Tuple[List[Player], int]:
        """
        Determine winner(s) at showdown

        Returns:
            Tuple: (list of winner(s), winning hand rank)
        """
        active = self.get_active_players()

        if len(active) == 1:
            # Everyone else folded
            return (active, -1)

        # Evaluate all active players
        best_hand = None
        winners = []

        for player in active:
            all_cards = player.hole_cards + self.community_cards
            hand = self.hand_evaluator.evaluate_hand(all_cards)

            if best_hand is None:
                best_hand = hand
                winners = [player]
            else:
                comparison = self.hand_evaluator.compare_hands(hand, best_hand)
                if comparison > 0:
                    best_hand = hand
                    winners = [player]
                elif comparison == 0:
                    winners.append(player)

        return (winners, best_hand[0] if best_hand else -1)

    def distribute_pot(self) -> bool:
        """
        Distribute pot to winner(s).
        Returns True if distribution was successful.
        """
        winners, _ = self.determine_winner()
        if not winners:
            return False

        # Split pot equally among winners
        chips_per_winner = self.pot // len(winners)
        remainder = self.pot % len(winners)

        for i, winner in enumerate(winners):
            chips_to_award = chips_per_winner
            # Give remainder chips to first winner(s)
            if i < remainder:
                chips_to_award += 1
            winner.add_chips(chips_to_award)

        # Reset pot
        self.pot = 0
        return True

    def get_game_state(self) -> dict:
        """Get current game state for API"""
        return {
            "stage": self.stage,
            "pot": self.pot,
            "community_cards": [str(c) for c in self.community_cards],
            "dealer_position": self.dealer_position,
            "current_player_index": self.current_player_index,
            "hand_number": self.hand_number,
            "highest_bet_in_round": self.highest_bet_in_round,
            "active_players_count": len(self.get_active_players()),
        }

    def get_players_state(self) -> List[dict]:
        """Get all players' state"""
        return [player.to_dict() for player in self.players]
