"""
Automated test case generator for Single State Test 1
Chess rule following: All 6 piece types + Castling
"""

import random
from typing import List, Dict, Tuple


class ChessWithRuleGenerator:
    """Generate chess rule following test cases for all piece types"""

    TEST_TYPES = ['king', 'queen', 'rook', 'bishop', 'knight', 'pawn',
                  'castling_through_check', 'castling_in_check']

    N_TYPES = 8

    def __init__(self, seed: int = 42):
        """
        Initialize generator

        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        self.files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.ranks = ['1', '2', '3', '4', '5', '6', '7', '8']

    def _square_to_coords(self, square: str) -> Tuple[int, int]:
        """Convert square name to coordinates (0-7, 0-7)"""
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        return (file, rank)

    def _coords_to_square(self, file: int, rank: int) -> str:
        """Convert coordinates to square name"""
        if 0 <= file <= 7 and 0 <= rank <= 7:
            return chr(ord('a') + file) + str(rank + 1)
        return None

    def _random_square(self) -> str:
        """Generate random square"""
        file = random.choice(self.files)
        rank = random.choice(self.ranks)
        return file + rank

    def _is_valid_knight_move(self, from_sq: str, to_sq: str) -> bool:
        """Check if move is valid L-shape knight move"""
        f1, r1 = self._square_to_coords(from_sq)
        f2, r2 = self._square_to_coords(to_sq)

        df = abs(f2 - f1)
        dr = abs(r2 - r1)

        return (df == 2 and dr == 1) or (df == 1 and dr == 2)

    def _is_on_diagonal(self, from_sq: str, to_sq: str) -> bool:
        """Check if two squares are on same diagonal"""
        f1, r1 = self._square_to_coords(from_sq)
        f2, r2 = self._square_to_coords(to_sq)

        return abs(f2 - f1) == abs(r2 - r1) and from_sq != to_sq

    def _is_on_straight_line(self, from_sq: str, to_sq: str) -> bool:
        """Check if two squares are on same rank or file"""
        f1, r1 = self._square_to_coords(from_sq)
        f2, r2 = self._square_to_coords(to_sq)

        return (f1 == f2 or r1 == r2) and from_sq != to_sq

    def _get_squares_between(self, from_sq: str, to_sq: str) -> List[str]:
        """Get all squares between two squares (for blocking check)"""
        f1, r1 = self._square_to_coords(from_sq)
        f2, r2 = self._square_to_coords(to_sq)

        squares = []

        # Calculate direction
        df = 0 if f1 == f2 else (1 if f2 > f1 else -1)
        dr = 0 if r1 == r2 else (1 if r2 > r1 else -1)

        # Move step by step
        f, r = f1 + df, r1 + dr
        while (f, r) != (f2, r2):
            sq = self._coords_to_square(f, r)
            if sq:
                squares.append(sq)
            f += df
            r += dr

        return squares

    # ============= King Tests =============

    def generate_king_tests(self, n_per_type: int = 10) -> List[Dict]:
        """Generate king movement tests - can move one square in any direction"""
        cases = []
        n_pos = n_per_type // 2
        n_neg = n_per_type - n_pos

        # Positive cases: valid one-square moves
        attempts = 0
        while len([c for c in cases if c['expected'] == 'yes']) < n_pos and attempts < 1000:
            from_sq = self._random_square()
            f1, r1 = self._square_to_coords(from_sq)

            # Pick a random adjacent square
            directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                          (0, 1), (1, -1), (1, 0), (1, 1)]
            df, dr = random.choice(directions)
            to_sq = self._coords_to_square(f1 + df, r1 + dr)

            if to_sq:
                cases.append({
                    'case_id': f'king_pos_{len([c for c in cases if c["expected"] == "yes"])+1}',
                    'type': 'king',
                    'subtype': 'valid_move',
                    'pieces': {from_sq: 'K'},
                    'squares': [to_sq],
                    'question': f'Can this king move to highlighted square?',
                    'expected': 'yes',
                    'reasoning': f'King can move one square in any direction'
                })
            attempts += 1

        # Negative cases: moves more than one square
        attempts = 0
        while len([c for c in cases if c['expected'] == 'no']) < n_neg and attempts < 1000:
            from_sq = self._random_square()
            to_sq = self._random_square()

            f1, r1 = self._square_to_coords(from_sq)
            f2, r2 = self._square_to_coords(to_sq)

            if abs(f2 - f1) > 1 or abs(r2 - r1) > 1:
                cases.append({
                    'case_id': f'king_neg_{len([c for c in cases if c["expected"] == "no"])+1}',
                    'type': 'king',
                    'subtype': 'too_far',
                    'pieces': {from_sq: 'K'},
                    'squares': [to_sq],
                    'question': f'Can this king move to highlighted square?',
                    'expected': 'no',
                    'reasoning': 'King can only move one square at a time'
                })
            attempts += 1

        return cases

    # ============= Queen Tests =============

    def generate_queen_tests(self, n_per_type: int = 10) -> List[Dict]:
        """Generate queen movement tests - combines rook and bishop movement"""
        cases = []
        n_clear = n_per_type // 3
        n_blocked = n_per_type // 3
        n_invalid = n_per_type - n_clear - n_blocked

        # Type 1: Clear path (diagonal or straight)
        attempts = 0
        while len([c for c in cases if c.get('subtype') == 'clear_path']) < n_clear and attempts < 1000:
            from_sq = self._random_square()
            to_sq = self._random_square()

            if self._is_on_diagonal(from_sq, to_sq) or self._is_on_straight_line(from_sq, to_sq):
                path_type = 'diagonal' if self._is_on_diagonal(
                    from_sq, to_sq) else 'straight'
                cases.append({
                    'case_id': f'queen_clear_{len([c for c in cases if c.get("subtype") == "clear_path"])+1}',
                    'type': 'queen',
                    'subtype': 'clear_path',
                    'pieces': {from_sq: 'Q'},
                    'squares': [to_sq],
                    'question': f'Can this queen move to highlighted square?',
                    'expected': 'yes',
                    'reasoning': f'Queen can move on clear {path_type} path'
                })
            attempts += 1

        # Type 2: Blocked path
        attempts = 0
        while len([c for c in cases if c.get('subtype') == 'blocked_path']) < n_blocked and attempts < 1000:
            from_sq = self._random_square()
            to_sq = self._random_square()

            if self._is_on_diagonal(from_sq, to_sq) or self._is_on_straight_line(from_sq, to_sq):
                between = self._get_squares_between(from_sq, to_sq)
                if between:
                    blocking_sq = random.choice(between)
                    cases.append({
                        'case_id': f'queen_blocked_{len([c for c in cases if c.get("subtype") == "blocked_path"])+1}',
                        'type': 'queen',
                        'subtype': 'blocked_path',
                        'pieces': {
                            from_sq: 'Q',
                            blocking_sq: 'P'
                        },
                        'squares': [to_sq],
                        'question': f'Can this queen move to highlighted square?',
                        'expected': 'no',
                        'reasoning': f'Path blocked by piece at {blocking_sq}'
                    })
            attempts += 1

        # Type 3: Invalid move (not diagonal or straight)
        attempts = 0
        while len([c for c in cases if c.get('subtype') == 'invalid_move']) < n_invalid and attempts < 1000:
            from_sq = self._random_square()
            to_sq = self._random_square()

            if not self._is_on_diagonal(from_sq, to_sq) and not self._is_on_straight_line(from_sq, to_sq) and from_sq != to_sq:
                cases.append({
                    'case_id': f'queen_invalid_{len([c for c in cases if c.get("subtype") == "invalid_move"])+1}',
                    'type': 'queen',
                    'subtype': 'invalid_move',
                    'pieces': {from_sq: 'Q'},
                    'squares': [to_sq],
                    'question': f'Can this queen move to highlighted square?',
                    'expected': 'no',
                    'reasoning': 'Queen only moves diagonally or straight'
                })
            attempts += 1

        return cases

    # ============= Rook Tests =============

    def generate_rook_tests(self, n_per_type: int = 10) -> List[Dict]:
        """Generate rook movement tests"""
        cases = []
        n_clear = n_per_type // 3
        n_blocked = n_per_type // 3
        n_invalid = n_per_type - n_clear - n_blocked

        # Type 1: Clear straight path (positive)
        attempts = 0
        while len([c for c in cases if c.get('subtype') == 'clear_path']) < n_clear and attempts < 1000:
            from_sq = self._random_square()
            to_sq = self._random_square()

            if self._is_on_straight_line(from_sq, to_sq):
                cases.append({
                    'case_id': f'rook_clear_{len([c for c in cases if c.get("subtype") == "clear_path"])+1}',
                    'type': 'rook',
                    'subtype': 'clear_path',
                    'pieces': {from_sq: 'R'},
                    'squares': [to_sq],
                    'question': f'Can this rook move to highlighted square?',
                    'expected': 'yes',
                    'reasoning': 'Rook on clear straight path'
                })
            attempts += 1

        # Type 2: Blocked straight path (negative)
        attempts = 0
        while len([c for c in cases if c.get('subtype') == 'blocked_path']) < n_blocked and attempts < 1000:
            from_sq = self._random_square()
            to_sq = self._random_square()

            if self._is_on_straight_line(from_sq, to_sq):
                between = self._get_squares_between(from_sq, to_sq)
                if between:
                    blocking_sq = random.choice(between)
                    cases.append({
                        'case_id': f'rook_blocked_{len([c for c in cases if c.get("subtype") == "blocked_path"])+1}',
                        'type': 'rook',
                        'subtype': 'blocked_path',
                        'pieces': {
                            from_sq: 'R',
                            blocking_sq: 'P'
                        },
                        'squares': [to_sq],
                        'question': f'Can this rook move to highlighted square?',
                        'expected': 'no',
                        'reasoning': f'Path blocked by piece at {blocking_sq}'
                    })
            attempts += 1

        # Type 3: Not on straight line (negative)
        attempts = 0
        while len([c for c in cases if c.get('subtype') == 'not_straight']) < n_invalid and attempts < 1000:
            from_sq = self._random_square()
            to_sq = self._random_square()

            if not self._is_on_straight_line(from_sq, to_sq) and from_sq != to_sq:
                cases.append({
                    'case_id': f'rook_invalid_{len([c for c in cases if c.get("subtype") == "not_straight"])+1}',
                    'type': 'rook',
                    'subtype': 'not_straight',
                    'pieces': {from_sq: 'R'},
                    'squares': [to_sq],
                    'question': f'Can this rook move to highlighted square?',
                    'expected': 'no',
                    'reasoning': 'Not on straight line - rook only moves straight'
                })
            attempts += 1

        return cases

    # ============= Bishop Tests =============

    def generate_bishop_tests(self, n_per_type: int = 10) -> List[Dict]:
        """Generate bishop movement tests"""
        cases = []
        n_clear = n_per_type // 3
        n_blocked = n_per_type // 3
        n_invalid = n_per_type - n_clear - n_blocked

        # Type 1: Clear diagonal path (positive)
        attempts = 0
        while len([c for c in cases if c.get('subtype') == 'clear_path']) < n_clear and attempts < 1000:
            from_sq = self._random_square()
            to_sq = self._random_square()

            if self._is_on_diagonal(from_sq, to_sq):
                cases.append({
                    'case_id': f'bishop_clear_{len([c for c in cases if c.get("subtype") == "clear_path"])+1}',
                    'type': 'bishop',
                    'subtype': 'clear_path',
                    'pieces': {from_sq: 'B'},
                    'squares': [to_sq],
                    'question': f'Can this bishop move to highlighted square?',
                    'expected': 'yes',
                    'reasoning': 'Bishop on clear diagonal path'
                })
            attempts += 1

        # Type 2: Blocked diagonal path (negative)
        attempts = 0
        while len([c for c in cases if c.get('subtype') == 'blocked_path']) < n_blocked and attempts < 1000:
            from_sq = self._random_square()
            to_sq = self._random_square()

            if self._is_on_diagonal(from_sq, to_sq):
                between = self._get_squares_between(from_sq, to_sq)
                if between:
                    blocking_sq = random.choice(between)
                    cases.append({
                        'case_id': f'bishop_blocked_{len([c for c in cases if c.get("subtype") == "blocked_path"])+1}',
                        'type': 'bishop',
                        'subtype': 'blocked_path',
                        'pieces': {
                            from_sq: 'B',
                            blocking_sq: 'P'
                        },
                        'squares': [to_sq],
                        'question': f'Can this bishop move to highlighted square?',
                        'expected': 'no',
                        'reasoning': f'Path blocked by piece at {blocking_sq}'
                    })
            attempts += 1

        # Type 3: Not on diagonal (negative)
        attempts = 0
        while len([c for c in cases if c.get('subtype') == 'not_diagonal']) < n_invalid and attempts < 1000:
            from_sq = self._random_square()
            to_sq = self._random_square()

            if not self._is_on_diagonal(from_sq, to_sq) and from_sq != to_sq:
                cases.append({
                    'case_id': f'bishop_invalid_{len([c for c in cases if c.get("subtype") == "not_diagonal"])+1}',
                    'type': 'bishop',
                    'subtype': 'not_diagonal',
                    'pieces': {from_sq: 'B'},
                    'squares': [to_sq],
                    'question': f'Can this bishop move to highlighted square?',
                    'expected': 'no',
                    'reasoning': 'Not on diagonal - bishop only moves diagonally'
                })
            attempts += 1

        return cases

    # ============= Knight Tests =============

    def generate_knight_tests(self, n_per_type: int = 10) -> List[Dict]:
        """Generate knight movement tests"""
        cases = []
        n_pos = n_per_type // 2
        n_neg = n_per_type - n_pos

        # Positive cases: valid L-shape moves
        attempts = 0
        while len([c for c in cases if c['expected'] == 'yes']) < n_pos and attempts < 1000:
            from_sq = self._random_square()
            to_sq = self._random_square()

            if self._is_valid_knight_move(from_sq, to_sq):
                cases.append({
                    'case_id': f'knight_pos_{len([c for c in cases if c["expected"] == "yes"])+1}',
                    'type': 'knight',
                    'subtype': 'valid_move',
                    'pieces': {from_sq: 'N'},
                    'squares': [to_sq],
                    'question': f'Can this knight move to highlighted square?',
                    'expected': 'yes',
                    'reasoning': f'Valid L-shape move from {from_sq} to {to_sq}'
                })
            attempts += 1

        # Negative cases: invalid moves
        attempts = 0
        while len([c for c in cases if c['expected'] == 'no']) < n_neg and attempts < 1000:
            from_sq = self._random_square()
            to_sq = self._random_square()

            if not self._is_valid_knight_move(from_sq, to_sq) and from_sq != to_sq:
                f1, r1 = self._square_to_coords(from_sq)
                f2, r2 = self._square_to_coords(to_sq)

                subtype = 'invalid_move'
                if f1 == f2 or r1 == r2:
                    subtype = 'straight_line'
                elif abs(f2 - f1) == abs(r2 - r1):
                    subtype = 'diagonal'

                cases.append({
                    'case_id': f'knight_neg_{len([c for c in cases if c["expected"] == "no"])+1}',
                    'type': 'knight',
                    'subtype': subtype,
                    'pieces': {from_sq: 'N'},
                    'squares': [to_sq],
                    'question': f'Can this knight move to highlighted square?',
                    'expected': 'no',
                    'reasoning': f'Invalid knight move: {subtype}'
                })
            attempts += 1

        return cases

    # ============= Pawn Tests =============

    def generate_pawn_tests(self, n_per_type: int = 10) -> List[Dict]:
        """Generate pawn movement tests - forward one square (or two from start)"""
        cases = []
        n_pos = n_per_type // 2
        n_neg = n_per_type - n_pos

        # Positive cases: valid forward moves
        pos_count = 0
        attempts = 0
        while pos_count < n_pos and attempts < 1000:
            # White pawn (moves up, rank increases)
            from_rank = random.choice(['2', '3', '4', '5', '6', '7'])
            from_file = random.choice(self.files)
            from_sq = from_file + from_rank

            # Can move one square forward
            if random.random() < 0.7:  # 70% one square
                to_sq = from_file + str(int(from_rank) + 1)
                reasoning = 'Pawn can move one square forward'
            else:  # 30% two squares from starting position
                if from_rank == '2':
                    to_sq = from_file + '4'
                    reasoning = 'Pawn can move two squares from starting position'
                else:
                    to_sq = from_file + str(int(from_rank) + 1)
                    reasoning = 'Pawn can move one square forward'

            # Make sure to_sq is valid
            if to_sq[1] in self.ranks:
                cases.append({
                    'case_id': f'pawn_pos_{pos_count+1}',
                    'type': 'pawn',
                    'subtype': 'valid_forward',
                    'pieces': {from_sq: 'P'},
                    'squares': [to_sq],
                    'question': f'Can this pawn move to highlighted square?',
                    'expected': 'yes',
                    'reasoning': reasoning
                })
                pos_count += 1
            attempts += 1

        # Negative cases: invalid moves
        neg_count = 0
        attempts = 0
        while neg_count < n_neg and attempts < 1000:
            from_rank = random.choice(['2', '3', '4', '5', '6', '7'])
            from_file = random.choice(self.files)
            from_sq = from_file + from_rank

            # Generate invalid moves
            invalid_type = random.choice(
                ['backward', 'sideways', 'diagonal_no_capture', 'too_far'])

            if invalid_type == 'backward':
                to_sq = from_file + str(int(from_rank) - 1)
                reasoning = 'Pawn cannot move backward'
            elif invalid_type == 'sideways':
                new_file = random.choice(
                    [f for f in self.files if f != from_file])
                to_sq = new_file + from_rank
                reasoning = 'Pawn cannot move sideways'
            elif invalid_type == 'diagonal_no_capture':
                # Diagonal move without capture piece
                file_idx = self.files.index(from_file)
                if file_idx > 0:
                    new_file = self.files[file_idx - 1]
                else:
                    new_file = self.files[file_idx + 1]
                to_sq = new_file + str(int(from_rank) + 1)
                reasoning = 'Pawn can only move diagonally when capturing'
            else:  # too_far
                if from_rank != '2':
                    to_sq = from_file + str(int(from_rank) + 2)
                    reasoning = 'Pawn can only move two squares from starting position'
                else:
                    to_sq = from_file + str(int(from_rank) + 3)
                    reasoning = 'Pawn cannot move three squares'

            # Make sure to_sq is valid
            if to_sq[1] in self.ranks:
                cases.append({
                    'case_id': f'pawn_neg_{neg_count+1}',
                    'type': 'pawn',
                    'subtype': invalid_type,
                    'pieces': {from_sq: 'P'},
                    'squares': [to_sq],
                    'question': f'Can this pawn move to highlighted square?',
                    'expected': 'no',
                    'reasoning': reasoning
                })
                neg_count += 1
            attempts += 1

        return cases

    # ============= Helper Methods for Castling =============

    def _can_piece_attack_square(self, piece_type: str, from_sq: str, to_sq: str, all_pieces: Dict[str, str]) -> bool:
        """
        Check if a piece at from_sq can attack to_sq

        Args:
            piece_type: 'K', 'Q', 'R', 'B', 'N', 'P' (or lowercase for black)
            from_sq: Square where piece is located
            to_sq: Target square to check if it can be attacked
            all_pieces: All pieces on board (for blocking check)

        Returns:
            True if piece can attack the square
        """
        piece_upper = piece_type.upper()

        if piece_upper == 'K':
            # King attacks adjacent squares
            f1, r1 = self._square_to_coords(from_sq)
            f2, r2 = self._square_to_coords(to_sq)
            return abs(f2 - f1) <= 1 and abs(r2 - r1) <= 1 and from_sq != to_sq

        elif piece_upper == 'Q':
            # Queen attacks like rook + bishop
            if self._is_on_straight_line(from_sq, to_sq):
                between = self._get_squares_between(from_sq, to_sq)
                return all(sq not in all_pieces for sq in between)
            elif self._is_on_diagonal(from_sq, to_sq):
                between = self._get_squares_between(from_sq, to_sq)
                return all(sq not in all_pieces for sq in between)
            return False

        elif piece_upper == 'R':
            # Rook attacks straight lines
            if self._is_on_straight_line(from_sq, to_sq):
                between = self._get_squares_between(from_sq, to_sq)
                return all(sq not in all_pieces for sq in between)
            return False

        elif piece_upper == 'B':
            # Bishop attacks diagonals
            if self._is_on_diagonal(from_sq, to_sq):
                between = self._get_squares_between(from_sq, to_sq)
                return all(sq not in all_pieces for sq in between)
            return False

        elif piece_upper == 'N':
            # Knight attacks L-shape (jumps, no blocking)
            return self._is_valid_knight_move(from_sq, to_sq)

        elif piece_upper == 'P':
            # Pawn attacks diagonal forward (one square)
            f1, r1 = self._square_to_coords(from_sq)
            f2, r2 = self._square_to_coords(to_sq)

            # White pawn (uppercase) attacks diagonally upward
            if piece_type.isupper():
                return abs(f2 - f1) == 1 and r2 == r1 + 1
            # Black pawn (lowercase) attacks diagonally downward
            else:
                return abs(f2 - f1) == 1 and r2 == r1 - 1

        return False

    def _is_square_under_attack(self, square: str, by_color: str, all_pieces: Dict[str, str]) -> bool:
        """
        Check if a square is under attack by pieces of a given color

        Args:
            square: Square to check
            by_color: 'white' or 'black' - color of attacking pieces
            all_pieces: Dictionary of all pieces on board {square: piece_symbol}

        Returns:
            True if square is under attack
        """
        for piece_sq, piece_symbol in all_pieces.items():
            # Check if piece is of the attacking color
            is_white = piece_symbol.isupper()
            piece_color = 'white' if is_white else 'black'

            if piece_color == by_color:
                if self._can_piece_attack_square(piece_symbol, piece_sq, square, all_pieces):
                    return True

        return False

    # ============= Castling Tests =============

    def generate_castling_through_check_tests(self, n_per_type: int = 10) -> List[Dict]:
        """
        Generate castling through check tests

        Test whether the model understands that:
        - King cannot castle THROUGH a square that is under attack
        - Even if the king's starting and ending positions are safe

        Args:
            n_per_type: Number of cases (split between positive and negative)
        """
        cases = []
        n_pos = n_per_type // 2
        n_neg = n_per_type - n_pos

        # Positive cases: Can castle (king not in check, path is not under attack, destination safe)
        pos_count = 0
        attempts = 0
        while pos_count < n_pos and attempts < 500:
            attempts += 1

            # Randomly choose white or black, kingside or queenside
            is_white = random.choice([True, False])
            is_kingside = random.choice([True, False])

            if is_white:
                king_sq = 'e1'
                if is_kingside:
                    rook_sq = 'h1'
                    # King passes through f1, ends at g1
                    path_squares = ['f1', 'g1']
                    target_sq = 'g1'
                    castle_type = 'kingside'
                else:
                    rook_sq = 'a1'
                    # King passes through d1, ends at c1
                    path_squares = ['d1', 'c1']
                    target_sq = 'c1'
                    castle_type = 'queenside'
                king_piece = 'K'
                rook_piece = 'R'
                opponent_color = 'black'
                opponent_piece = random.choice(['q', 'r', 'b', 'n'])
            else:
                king_sq = 'e8'
                if is_kingside:
                    rook_sq = 'h8'
                    path_squares = ['f8', 'g8']
                    target_sq = 'g8'
                    castle_type = 'kingside'
                else:
                    rook_sq = 'a8'
                    path_squares = ['d8', 'c8']
                    target_sq = 'c8'
                    castle_type = 'queenside'
                king_piece = 'k'
                rook_piece = 'r'
                opponent_color = 'white'
                opponent_piece = random.choice(['Q', 'R', 'B', 'N'])

            # Place opponent piece that doesn't attack king, path, or destination
            pieces = {king_sq: king_piece, rook_sq: rook_piece}

            # Try to place opponent piece randomly
            opponent_sq = self._random_square()
            # Avoid placing on important squares
            avoid_squares = [king_sq, rook_sq] + path_squares

            if opponent_sq not in avoid_squares:
                pieces[opponent_sq] = opponent_piece

                # Check ALL castling requirements:
                # 1. King is NOT currently in check
                # 2. Path squares are NOT under attack
                # 3. Destination is NOT under attack
                all_safe = True

                # Check king's current position
                if self._is_square_under_attack(king_sq, opponent_color, pieces):
                    all_safe = False

                # Check path and destination
                if all_safe:
                    for sq in path_squares:
                        if self._is_square_under_attack(sq, opponent_color, pieces):
                            all_safe = False
                            break

                if all_safe:
                    cases.append({
                        'case_id': f'castling_through_pos_{pos_count+1}',
                        'type': 'castling',
                        'subtype': 'through_check_safe',
                        'pieces': pieces,
                        'squares': [],
                        'question': f'Can the {"white" if is_white else "black"} king castle {castle_type}?',
                        'expected': 'yes',
                        'reasoning': f'King is not in check and castling path is safe'
                    })
                    pos_count += 1

        # Negative cases: Cannot castle (path IS under attack)
        neg_count = 0
        attempts = 0
        while neg_count < n_neg and attempts < 500:
            attempts += 1

            is_white = random.choice([True, False])
            is_kingside = random.choice([True, False])

            if is_white:
                king_sq = 'e1'
                if is_kingside:
                    rook_sq = 'h1'
                    path_squares = ['f1', 'g1']
                    target_sq = 'g1'
                    castle_type = 'kingside'
                else:
                    rook_sq = 'a1'
                    path_squares = ['d1', 'c1']
                    target_sq = 'c1'
                    castle_type = 'queenside'
                king_piece = 'K'
                rook_piece = 'R'
                opponent_color = 'black'
            else:
                king_sq = 'e8'
                if is_kingside:
                    rook_sq = 'h8'
                    path_squares = ['f8', 'g8']
                    target_sq = 'g8'
                    castle_type = 'kingside'
                else:
                    rook_sq = 'a8'
                    path_squares = ['d8', 'c8']
                    target_sq = 'c8'
                    castle_type = 'queenside'
                king_piece = 'k'
                rook_piece = 'r'
                opponent_color = 'white'

            pieces = {king_sq: king_piece, rook_sq: rook_piece}

            # Choose which square in path to attack
            attacked_square = random.choice(path_squares)

            # Place attacking piece based on type
            piece_type = random.choice(['rook', 'bishop', 'queen', 'knight'])

            if piece_type == 'rook':
                # Place rook on same rank or file as attacked square
                opponent_piece = 'r' if opponent_color == 'black' else 'R'
                if random.choice([True, False]):
                    # Same rank
                    opponent_sq = random.choice(
                        self.files) + attacked_square[1]
                else:
                    # Same file
                    opponent_sq = attacked_square[0] + \
                        random.choice(self.ranks)

            elif piece_type == 'bishop':
                # Place bishop on diagonal to attacked square
                opponent_piece = 'b' if opponent_color == 'black' else 'B'
                f, r = self._square_to_coords(attacked_square)
                # Try diagonal positions
                offsets = [(-2, -2), (-2, 2), (2, -2), (2, 2),
                           (-3, -3), (-3, 3), (3, -3), (3, 3)]
                random.shuffle(offsets)
                opponent_sq = None
                for df, dr in offsets:
                    sq = self._coords_to_square(f + df, r + dr)
                    if sq and sq not in [king_sq, rook_sq]:
                        opponent_sq = sq
                        break

            elif piece_type == 'queen':
                # Queen can attack from anywhere on rank/file/diagonal
                opponent_piece = 'q' if opponent_color == 'black' else 'Q'
                opponent_sq = random.choice(self.files) + attacked_square[1]

            else:  # knight
                # Place knight at L-shape distance
                opponent_piece = 'n' if opponent_color == 'black' else 'N'
                f, r = self._square_to_coords(attacked_square)
                knight_offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                                  (1, -2), (1, 2), (2, -1), (2, 1)]
                random.shuffle(knight_offsets)
                opponent_sq = None
                for df, dr in knight_offsets:
                    sq = self._coords_to_square(f + df, r + dr)
                    if sq and sq not in [king_sq, rook_sq]:
                        opponent_sq = sq
                        break

            if opponent_sq and opponent_sq not in [king_sq, rook_sq]:
                pieces[opponent_sq] = opponent_piece

                # Verify that the path IS under attack
                if self._is_square_under_attack(attacked_square, opponent_color, pieces):
                    cases.append({
                        'case_id': f'castling_through_neg_{neg_count+1}',
                        'type': 'castling',
                        'subtype': 'through_check_blocked',
                        'pieces': pieces,
                        'squares': [],
                        'question': f'Can the {"white" if is_white else "black"} king castle {castle_type}?',
                        'expected': 'no',
                        'reasoning': f'Cannot castle through attacked square {attacked_square}'
                    })
                    neg_count += 1

        return cases

    def generate_castling_in_check_tests(self, n_per_type: int = 10) -> List[Dict]:
        """
        Generate castling in check tests

        Test whether the model understands that:
        - King cannot castle when currently in check

        Args:
            n_per_type: Number of cases (split between positive and negative)
        """
        cases = []
        n_pos = n_per_type // 2
        n_neg = n_per_type - n_pos

        # Positive cases: Can castle (king is NOT in check)
        pos_count = 0
        attempts = 0
        while pos_count < n_pos and attempts < 500:
            attempts += 1

            is_white = random.choice([True, False])
            is_kingside = random.choice([True, False])

            if is_white:
                king_sq = 'e1'
                if is_kingside:
                    rook_sq = 'h1'
                    path_squares = ['f1', 'g1']  # Squares king passes through
                    target_sq = 'g1'
                    castle_type = 'kingside'
                else:
                    rook_sq = 'a1'
                    path_squares = ['d1', 'c1']  # Squares king passes through
                    target_sq = 'c1'
                    castle_type = 'queenside'
                king_piece = 'K'
                rook_piece = 'R'
                opponent_color = 'black'
                opponent_piece = random.choice(['q', 'r', 'b', 'n'])
            else:
                king_sq = 'e8'
                if is_kingside:
                    rook_sq = 'h8'
                    path_squares = ['f8', 'g8']
                    target_sq = 'g8'
                    castle_type = 'kingside'
                else:
                    rook_sq = 'a8'
                    path_squares = ['d8', 'c8']
                    target_sq = 'c8'
                    castle_type = 'queenside'
                king_piece = 'k'
                rook_piece = 'r'
                opponent_color = 'white'
                opponent_piece = random.choice(['Q', 'R', 'B', 'N'])

            pieces = {king_sq: king_piece, rook_sq: rook_piece}

            # Place opponent piece that does NOT attack the king, path, or destination
            opponent_sq = self._random_square()
            avoid_squares = [king_sq, rook_sq] + path_squares

            if opponent_sq not in avoid_squares:
                pieces[opponent_sq] = opponent_piece

                # Check ALL castling conditions:
                # 1. King is NOT currently under attack
                # 2. King does NOT pass through attacked squares
                # 3. King's destination is NOT under attack
                all_safe = True

                # Check current king position
                if self._is_square_under_attack(king_sq, opponent_color, pieces):
                    all_safe = False

                # Check all squares in castling path (including destination)
                for sq in path_squares:
                    if self._is_square_under_attack(sq, opponent_color, pieces):
                        all_safe = False
                        break

                if all_safe:
                    cases.append({
                        'case_id': f'castling_in_check_pos_{pos_count+1}',
                        'type': 'castling',
                        'subtype': 'not_in_check',
                        'pieces': pieces,
                        'squares': [],
                        'question': f'Can the {"white" if is_white else "black"} king castle {castle_type}?',
                        'expected': 'yes',
                        'reasoning': f'King is not in check and castling path is safe'
                    })
                    pos_count += 1

        # Negative cases: Cannot castle (king IS in check)
        neg_count = 0
        attempts = 0
        while neg_count < n_neg and attempts < 500:
            attempts += 1

            is_white = random.choice([True, False])
            is_kingside = random.choice([True, False])

            if is_white:
                king_sq = 'e1'
                rook_sq = 'h1' if is_kingside else 'a1'
                target_sq = 'g1' if is_kingside else 'c1'
                castle_type = 'kingside' if is_kingside else 'queenside'
                king_piece = 'K'
                rook_piece = 'R'
                opponent_color = 'black'
            else:
                king_sq = 'e8'
                rook_sq = 'h8' if is_kingside else 'a8'
                target_sq = 'g8' if is_kingside else 'c8'
                castle_type = 'kingside' if is_kingside else 'queenside'
                king_piece = 'k'
                rook_piece = 'r'
                opponent_color = 'white'

            pieces = {king_sq: king_piece, rook_sq: rook_piece}

            # Place attacking piece based on type
            piece_type = random.choice(['rook', 'bishop', 'queen', 'knight'])

            if piece_type == 'rook':
                opponent_piece = 'r' if opponent_color == 'black' else 'R'
                # Place on same rank or file as king
                if random.choice([True, False]):
                    opponent_sq = random.choice(
                        [f for f in self.files if f != king_sq[0]]) + king_sq[1]
                else:
                    opponent_sq = king_sq[0] + \
                        random.choice(
                            [r for r in self.ranks if r != king_sq[1]])

            elif piece_type == 'bishop':
                opponent_piece = 'b' if opponent_color == 'black' else 'B'
                f, r = self._square_to_coords(king_sq)
                offsets = [(-2, -2), (-2, 2), (2, -2), (2, 2),
                           (-3, -3), (-3, 3), (3, -3), (3, 3)]
                random.shuffle(offsets)
                opponent_sq = None
                for df, dr in offsets:
                    sq = self._coords_to_square(f + df, r + dr)
                    if sq and sq != rook_sq:
                        opponent_sq = sq
                        break

            elif piece_type == 'queen':
                opponent_piece = 'q' if opponent_color == 'black' else 'Q'
                opponent_sq = random.choice(
                    [f for f in self.files if f != king_sq[0]]) + king_sq[1]

            else:  # knight
                opponent_piece = 'n' if opponent_color == 'black' else 'N'
                f, r = self._square_to_coords(king_sq)
                knight_offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                                  (1, -2), (1, 2), (2, -1), (2, 1)]
                random.shuffle(knight_offsets)
                opponent_sq = None
                for df, dr in knight_offsets:
                    sq = self._coords_to_square(f + df, r + dr)
                    if sq and sq != rook_sq:
                        opponent_sq = sq
                        break

            if opponent_sq and opponent_sq != rook_sq:
                pieces[opponent_sq] = opponent_piece

                # Verify that king IS under attack
                if self._is_square_under_attack(king_sq, opponent_color, pieces):
                    cases.append({
                        'case_id': f'castling_in_check_neg_{neg_count+1}',
                        'type': 'castling',
                        'subtype': 'in_check',
                        'pieces': pieces,
                        'squares': [],
                        'question': f'Can the {"white" if is_white else "black"} king castle {castle_type}?',
                        'expected': 'no',
                        'reasoning': f'Cannot castle while in check'
                    })
                    neg_count += 1

        return cases

    # ============= Main Generation Method =============

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """
        Generate comprehensive Test 1 suite for all 6 piece types + 2 castling types.
        Cases are distributed proportionally across 8 test types.
        """
        all_cases = []

        cases_per_type = n_cases // self.N_TYPES
        remainder = n_cases % self.N_TYPES

        type_counts = {}
        for i, test_type in enumerate(self.TEST_TYPES):
            type_counts[test_type] = cases_per_type + \
                (1 if i < remainder else 0)

        print(
            f"Generating {n_cases} total cases across {self.N_TYPES} types...")
        print(f"Distribution: {type_counts}")

        print(f"Generating King tests ({type_counts['king']})...")
        king_cases = self.generate_king_tests(n_per_type=type_counts['king'])
        all_cases.extend(king_cases)

        print(f"Generating Queen tests ({type_counts['queen']})...")
        queen_cases = self.generate_queen_tests(
            n_per_type=type_counts['queen'])
        all_cases.extend(queen_cases)

        print(f"Generating Rook tests ({type_counts['rook']})...")
        rook_cases = self.generate_rook_tests(n_per_type=type_counts['rook'])
        all_cases.extend(rook_cases)

        print(f"Generating Bishop tests ({type_counts['bishop']})...")
        bishop_cases = self.generate_bishop_tests(
            n_per_type=type_counts['bishop'])
        all_cases.extend(bishop_cases)

        print(f"Generating Knight tests ({type_counts['knight']})...")
        knight_cases = self.generate_knight_tests(
            n_per_type=type_counts['knight'])
        all_cases.extend(knight_cases)

        print(f"Generating Pawn tests ({type_counts['pawn']})...")
        pawn_cases = self.generate_pawn_tests(n_per_type=type_counts['pawn'])
        all_cases.extend(pawn_cases)

        print(
            f"Generating Castling Through Check tests ({type_counts['castling_through_check']})...")
        castling_through_cases = self.generate_castling_through_check_tests(
            n_per_type=type_counts['castling_through_check'])
        all_cases.extend(castling_through_cases)

        print(
            f"Generating Castling In Check tests ({type_counts['castling_in_check']})...")
        castling_in_cases = self.generate_castling_in_check_tests(
            n_per_type=type_counts['castling_in_check'])
        all_cases.extend(castling_in_cases)

        print(f"\n✓ Total generated: {len(all_cases)} test cases")
        return all_cases
