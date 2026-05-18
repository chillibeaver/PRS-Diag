"""
Level 1 Generator: Basic Movement Rules
Tests basic movement patterns for all 6 piece types
"""

import random
from typing import List, Dict, Tuple


class Level1Generator:
    """Generate Level 1 test cases - basic movement rules"""

    def __init__(self, seed: int = 42):
        """
        Initialize generator

        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        self.files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.ranks = ['1', '2', '3', '4', '5', '6', '7', '8']

        # Piece types to test
        self.piece_types = ['knight', 'bishop',
                            'rook', 'queen', 'king', 'pawn']

    def _random_square(self) -> str:
        """Generate random square"""
        return random.choice(self.files) + random.choice(self.ranks)

    def _square_to_coords(self, square: str) -> Tuple[int, int]:
        """Convert square name to coordinates (0-7, 0-7)"""
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        return (file, rank)

    def _coords_to_square(self, file: int, rank: int) -> str:
        """Convert coordinates to square name"""
        if 0 <= file < 8 and 0 <= rank < 8:
            return chr(ord('a') + file) + str(rank + 1)
        return None

    def _get_random_piece_color(self) -> str:
        """Get random piece color"""
        return random.choice(['white', 'black'])

    def _piece_symbol(self, piece_type: str, color: str) -> str:
        """Get piece symbol"""
        symbols = {
            'knight': 'N' if color == 'white' else 'n',
            'bishop': 'B' if color == 'white' else 'b',
            'rook': 'R' if color == 'white' else 'r',
            'queen': 'Q' if color == 'white' else 'q',
            'king': 'K' if color == 'white' else 'k',
            'pawn': 'P' if color == 'white' else 'p'
        }
        return symbols[piece_type]

    # ===== KNIGHT =====

    def _generate_valid_knight_move(self) -> Tuple[str, str]:
        """Generate valid knight L-shape move"""
        while True:
            start = self._random_square()
            f, r = self._square_to_coords(start)

            # All possible L-shape moves
            moves = [
                (f+2, r+1), (f+2, r-1), (f-2, r+1), (f-2, r-1),
                (f+1, r+2), (f+1, r-2), (f-1, r+2), (f-1, r-2)
            ]

            valid_moves = [(nf, nr)
                           for nf, nr in moves if 0 <= nf < 8 and 0 <= nr < 8]

            if valid_moves:
                end_f, end_r = random.choice(valid_moves)
                end = self._coords_to_square(end_f, end_r)
                return start, end

    def _generate_invalid_knight_move(self) -> Tuple[str, str]:
        """Generate invalid knight move (straight or diagonal)"""
        while True:
            start = self._random_square()
            f, r = self._square_to_coords(start)

            # Choose invalid move type
            move_type = random.choice(['straight_h', 'straight_v', 'diagonal'])

            if move_type == 'straight_h':
                distance = random.randint(1, 5)
                direction = random.choice([-1, 1])
                end_f, end_r = f + direction * distance, r
            elif move_type == 'straight_v':
                distance = random.randint(1, 5)
                direction = random.choice([-1, 1])
                end_f, end_r = f, r + direction * distance
            else:  # diagonal
                distance = random.randint(1, 5)
                dir_f = random.choice([-1, 1])
                dir_r = random.choice([-1, 1])
                end_f, end_r = f + dir_f * distance, r + dir_r * distance

            if 0 <= end_f < 8 and 0 <= end_r < 8:
                end = self._coords_to_square(end_f, end_r)
                if end != start:
                    return start, end

    # ===== BISHOP =====

    def _generate_valid_bishop_move(self) -> Tuple[str, str]:
        """Generate valid bishop diagonal move"""
        while True:
            start = self._random_square()
            f, r = self._square_to_coords(start)

            distance = random.randint(1, 5)
            dir_f = random.choice([-1, 1])
            dir_r = random.choice([-1, 1])

            end_f = f + dir_f * distance
            end_r = r + dir_r * distance

            if 0 <= end_f < 8 and 0 <= end_r < 8:
                end = self._coords_to_square(end_f, end_r)
                return start, end

    def _generate_invalid_bishop_move(self) -> Tuple[str, str]:
        """Generate invalid bishop move (straight line)"""
        while True:
            start = self._random_square()
            f, r = self._square_to_coords(start)

            # Straight line move
            move_type = random.choice(['horizontal', 'vertical'])
            distance = random.randint(1, 6)

            if move_type == 'horizontal':
                direction = random.choice([-1, 1])
                end_f, end_r = f + direction * distance, r
            else:
                direction = random.choice([-1, 1])
                end_f, end_r = f, r + direction * distance

            if 0 <= end_f < 8 and 0 <= end_r < 8:
                end = self._coords_to_square(end_f, end_r)
                return start, end

    # ===== ROOK =====

    def _generate_valid_rook_move(self) -> Tuple[str, str]:
        """Generate valid rook straight line move"""
        while True:
            start = self._random_square()
            f, r = self._square_to_coords(start)

            move_type = random.choice(['horizontal', 'vertical'])
            distance = random.randint(1, 6)
            direction = random.choice([-1, 1])

            if move_type == 'horizontal':
                end_f, end_r = f + direction * distance, r
            else:
                end_f, end_r = f, r + direction * distance

            if 0 <= end_f < 8 and 0 <= end_r < 8:
                end = self._coords_to_square(end_f, end_r)
                return start, end

    def _generate_invalid_rook_move(self) -> Tuple[str, str]:
        """Generate invalid rook move (diagonal)"""
        while True:
            start = self._random_square()
            f, r = self._square_to_coords(start)

            distance = random.randint(2, 5)
            dir_f = random.choice([-1, 1])
            dir_r = random.choice([-1, 1])

            end_f = f + dir_f * distance
            end_r = r + dir_r * distance

            if 0 <= end_f < 8 and 0 <= end_r < 8:
                end = self._coords_to_square(end_f, end_r)
                return start, end

    # ===== QUEEN =====

    def _generate_valid_queen_move(self) -> Tuple[str, str]:
        """Generate valid queen move (straight or diagonal)"""
        move_type = random.choice(['straight', 'diagonal'])
        if move_type == 'straight':
            return self._generate_valid_rook_move()
        else:
            return self._generate_valid_bishop_move()

    def _generate_invalid_queen_move(self) -> Tuple[str, str]:
        """Generate invalid queen move (L-shape)"""
        return self._generate_valid_knight_move()

    # ===== KING =====

    def _generate_valid_king_move(self) -> Tuple[str, str]:
        """Generate valid king move (1 square in any direction)"""
        while True:
            start = self._random_square()
            f, r = self._square_to_coords(start)

            # All 8 directions, 1 square
            directions = [
                (0, 1), (0, -1), (1, 0), (-1, 0),
                (1, 1), (1, -1), (-1, 1), (-1, -1)
            ]

            dir_f, dir_r = random.choice(directions)
            end_f, end_r = f + dir_f, r + dir_r

            if 0 <= end_f < 8 and 0 <= end_r < 8:
                end = self._coords_to_square(end_f, end_r)
                return start, end

    def _generate_invalid_king_move(self) -> Tuple[str, str]:
        """Generate invalid king move (more than 1 square)"""
        while True:
            start = self._random_square()
            f, r = self._square_to_coords(start)

            distance = random.randint(2, 4)
            directions = [
                (0, 1), (0, -1), (1, 0), (-1, 0),
                (1, 1), (1, -1), (-1, 1), (-1, -1)
            ]

            dir_f, dir_r = random.choice(directions)
            end_f, end_r = f + dir_f * distance, r + dir_r * distance

            if 0 <= end_f < 8 and 0 <= end_r < 8:
                end = self._coords_to_square(end_f, end_r)
                return start, end

    # ===== PAWN =====

    def _generate_valid_pawn_move(self, color: str) -> Tuple[str, str]:
        """Generate valid pawn move"""
        while True:
            file = random.choice(self.files)

            if color == 'white':
                # White pawns move up (rank increases)
                # Avoid rank 1 (can't go backward) and rank 8 (would promote)
                start_rank = random.choice(['2', '3', '4', '5', '6', '7'])
                start = file + start_rank
                f, r = self._square_to_coords(start)

                # From rank 2, can move 1 or 2 squares
                if start_rank == '2':
                    distance = random.choice([1, 2])
                else:
                    distance = 1

                end_f, end_r = f, r + distance
            else:
                # Black pawns move down (rank decreases)
                start_rank = random.choice(['7', '6', '5', '4', '3', '2'])
                start = file + start_rank
                f, r = self._square_to_coords(start)

                if start_rank == '7':
                    distance = random.choice([1, 2])
                else:
                    distance = 1

                end_f, end_r = f, r - distance

            if 0 <= end_f < 8 and 0 <= end_r < 8:
                end = self._coords_to_square(end_f, end_r)
                return start, end

    def _generate_invalid_pawn_move(self, color: str) -> Tuple[str, str]:
        """Generate invalid pawn move"""
        invalid_type = random.choice(['backward', 'sideways', 'too_far'])

        while True:
            file = random.choice(self.files)

            if color == 'white':
                start_rank = random.choice(['2', '3', '4', '5', '6', '7'])
            else:
                start_rank = random.choice(['7', '6', '5', '4', '3', '2'])

            start = file + start_rank
            f, r = self._square_to_coords(start)

            if invalid_type == 'backward':
                # Move in wrong direction
                if color == 'white':
                    end_f, end_r = f, r - 1
                else:
                    end_f, end_r = f, r + 1
            elif invalid_type == 'sideways':
                # Horizontal move
                direction = random.choice([-1, 1])
                end_f, end_r = f + direction, r
            else:  # too_far
                # Move 3+ squares
                distance = random.randint(3, 5)
                if color == 'white':
                    end_f, end_r = f, r + distance
                else:
                    end_f, end_r = f, r - distance

            if 0 <= end_f < 8 and 0 <= end_r < 8:
                end = self._coords_to_square(end_f, end_r)
                if end != start:
                    return start, end

    # ===== MAIN GENERATION =====

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """
        Generate all Level 1 test cases

        Args:
            n_cases: Total number of cases

        Returns:
            List of test case dictionaries
        """
        all_cases = []

        # Distribute cases evenly across 6 piece types
        cases_per_piece = n_cases // 6
        remainder = n_cases % 6

        for idx, piece_type in enumerate(self.piece_types):
            n_piece_cases = cases_per_piece + (1 if idx < remainder else 0)

            # 50% valid, 50% invalid
            n_valid = n_piece_cases // 2
            n_invalid = n_piece_cases - n_valid

            print(
                f"Generating {piece_type} tests: {n_valid} valid + {n_invalid} invalid...")

            # Generate valid cases
            for i in range(n_valid):
                color = self._get_random_piece_color()

                if piece_type == 'knight':
                    start, end = self._generate_valid_knight_move()
                elif piece_type == 'bishop':
                    start, end = self._generate_valid_bishop_move()
                elif piece_type == 'rook':
                    start, end = self._generate_valid_rook_move()
                elif piece_type == 'queen':
                    start, end = self._generate_valid_queen_move()
                elif piece_type == 'king':
                    start, end = self._generate_valid_king_move()
                else:  # pawn
                    start, end = self._generate_valid_pawn_move(color)

                piece_symbol = self._piece_symbol(piece_type, color)

                all_cases.append({
                    "case_id": f"L1_{piece_type}_valid_{i+1}",
                    "type": "basic_movement",
                    "subtype": "valid",
                    "piece_type": piece_type,
                    "color": color,
                    "states": [
                        {"pieces": {start: piece_symbol}, "squares": []},
                        {"pieces": {end: piece_symbol}, "squares": []}
                    ],
                    "question": "Is this a legal move according to chess rules?",
                    "expected": "yes"
                })

            # Generate invalid cases
            for i in range(n_invalid):
                color = self._get_random_piece_color()

                if piece_type == 'knight':
                    start, end = self._generate_invalid_knight_move()
                elif piece_type == 'bishop':
                    start, end = self._generate_invalid_bishop_move()
                elif piece_type == 'rook':
                    start, end = self._generate_invalid_rook_move()
                elif piece_type == 'queen':
                    start, end = self._generate_invalid_queen_move()
                elif piece_type == 'king':
                    start, end = self._generate_invalid_king_move()
                else:  # pawn
                    start, end = self._generate_invalid_pawn_move(color)

                piece_symbol = self._piece_symbol(piece_type, color)

                all_cases.append({
                    "case_id": f"L1_{piece_type}_invalid_{i+1}",
                    "type": "basic_movement",
                    "subtype": "invalid",
                    "piece_type": piece_type,
                    "color": color,
                    "states": [
                        {"pieces": {start: piece_symbol}, "squares": []},
                        {"pieces": {end: piece_symbol}, "squares": []}
                    ],
                    "question": "Is this a legal move according to chess rules?",
                    "expected": "no"
                })

        print(f"\n✓ Total generated: {len(all_cases)} Level 1 test cases")
        return all_cases
