"""
Level 1 Generator: Basic Movement Rules
Predictive version: Only shows current state, asks if piece can move to target position
- Does not directly show movement result
- Model needs to reason whether piece can reach target
"""

import random
from typing import List, Dict, Tuple, Optional


class Level1Generator:
    """Generate Level 1 test cases - basic movement rules"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.ranks = ['1', '2', '3', '4', '5', '6', '7', '8']
        self.piece_types = ['knight', 'bishop',
                            'rook', 'queen', 'king', 'pawn']

    def _random_square(self) -> str:
        return random.choice(self.files) + random.choice(self.ranks)

    def _square_to_coords(self, square: str) -> Tuple[int, int]:
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        return (file, rank)

    def _coords_to_square(self, file: int, rank: int) -> Optional[str]:
        if 0 <= file < 8 and 0 <= rank < 8:
            return chr(ord('a') + file) + str(rank + 1)
        return None

    def _piece_symbol(self, piece_type: str, color: str) -> str:
        symbols = {
            'knight': 'N' if color == 'white' else 'n',
            'bishop': 'B' if color == 'white' else 'b',
            'rook': 'R' if color == 'white' else 'r',
            'queen': 'Q' if color == 'white' else 'q',
            'king': 'K' if color == 'white' else 'k',
            'pawn': 'P' if color == 'white' else 'p'
        }
        return symbols[piece_type]

    def _piece_name(self, piece_type: str) -> str:
        return piece_type.capitalize()

    # ==================== VALID MOVES ====================

    def _generate_valid_knight_target(self, start: str) -> Optional[str]:
        f, r = self._square_to_coords(start)
        moves = [(f+2, r+1), (f+2, r-1), (f-2, r+1), (f-2, r-1),
                 (f+1, r+2), (f+1, r-2), (f-1, r+2), (f-1, r-2)]
        valid = [(nf, nr) for nf, nr in moves if 0 <= nf < 8 and 0 <= nr < 8]
        if valid:
            end_f, end_r = random.choice(valid)
            return self._coords_to_square(end_f, end_r)
        return None

    def _generate_valid_bishop_target(self, start: str) -> Optional[str]:
        f, r = self._square_to_coords(start)
        distance = random.randint(1, 5)
        dir_f, dir_r = random.choice([(1, 1), (1, -1), (-1, 1), (-1, -1)])
        end_f, end_r = f + dir_f * distance, r + dir_r * distance
        return self._coords_to_square(end_f, end_r)

    def _generate_valid_rook_target(self, start: str) -> Optional[str]:
        f, r = self._square_to_coords(start)
        if random.choice([True, False]):  # horizontal
            distance = random.randint(1, 6) * random.choice([-1, 1])
            return self._coords_to_square(f + distance, r)
        else:  # vertical
            distance = random.randint(1, 6) * random.choice([-1, 1])
            return self._coords_to_square(f, r + distance)

    def _generate_valid_queen_target(self, start: str) -> Optional[str]:
        if random.choice([True, False]):
            return self._generate_valid_rook_target(start)
        return self._generate_valid_bishop_target(start)

    def _generate_valid_king_target(self, start: str) -> Optional[str]:
        f, r = self._square_to_coords(start)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0),
                      (1, 1), (1, -1), (-1, 1), (-1, -1)]
        dir_f, dir_r = random.choice(directions)
        return self._coords_to_square(f + dir_f, r + dir_r)

    def _generate_valid_pawn_target(self, start: str, color: str) -> Optional[str]:
        f, r = self._square_to_coords(start)
        if color == 'white':
            if r == 1:  # rank 2, can move 1 or 2
                distance = random.choice([1, 2])
            else:
                distance = 1
            return self._coords_to_square(f, r + distance)
        else:
            if r == 6:  # rank 7, can move 1 or 2
                distance = random.choice([1, 2])
            else:
                distance = 1
            return self._coords_to_square(f, r - distance)

    # ==================== INVALID MOVES ====================

    def _generate_invalid_knight_target(self, start: str) -> Optional[str]:
        f, r = self._square_to_coords(start)
        invalid_type = random.choice(['straight', 'diagonal'])
        if invalid_type == 'straight':
            dist = random.randint(1, 4)
            if random.choice([True, False]):
                return self._coords_to_square(f + dist * random.choice([-1, 1]), r)
            return self._coords_to_square(f, r + dist * random.choice([-1, 1]))
        else:
            dist = random.randint(1, 4)
            df, dr = random.choice([(1, 1), (1, -1), (-1, 1), (-1, -1)])
            return self._coords_to_square(f + df*dist, r + dr*dist)

    def _generate_invalid_bishop_target(self, start: str) -> Optional[str]:
        f, r = self._square_to_coords(start)
        dist = random.randint(1, 5)
        if random.choice([True, False]):
            return self._coords_to_square(f + dist * random.choice([-1, 1]), r)
        return self._coords_to_square(f, r + dist * random.choice([-1, 1]))

    def _generate_invalid_rook_target(self, start: str) -> Optional[str]:
        f, r = self._square_to_coords(start)
        dist = random.randint(2, 4)
        df, dr = random.choice([(1, 1), (1, -1), (-1, 1), (-1, -1)])
        return self._coords_to_square(f + df*dist, r + dr*dist)

    def _generate_invalid_queen_target(self, start: str) -> Optional[str]:
        # Queen can't move in L-shape
        f, r = self._square_to_coords(start)
        l_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                   (1, 2), (1, -2), (-1, 2), (-1, -2)]
        df, dr = random.choice(l_moves)
        return self._coords_to_square(f + df, r + dr)

    def _generate_invalid_king_target(self, start: str) -> Optional[str]:
        f, r = self._square_to_coords(start)
        dist = random.randint(2, 4)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0),
                      (1, 1), (1, -1), (-1, 1), (-1, -1)]
        df, dr = random.choice(directions)
        return self._coords_to_square(f + df*dist, r + dr*dist)

    def _generate_invalid_pawn_target(self, start: str, color: str) -> Optional[str]:
        f, r = self._square_to_coords(start)
        invalid_type = random.choice(['backward', 'sideways', 'too_far'])

        if invalid_type == 'backward':
            if color == 'white':
                return self._coords_to_square(f, r - 1)
            return self._coords_to_square(f, r + 1)
        elif invalid_type == 'sideways':
            return self._coords_to_square(f + random.choice([-1, 1]), r)
        else:  # too_far
            dist = random.randint(3, 5)
            if color == 'white':
                return self._coords_to_square(f, r + dist)
            return self._coords_to_square(f, r - dist)

    # ==================== CASE GENERATION ====================

    def _generate_case(self, piece_type: str, is_valid: bool, case_num: int) -> Optional[Dict]:
        """Generate a single test case - predictive version"""
        color = random.choice(['white', 'black'])

        for _ in range(100):
            # Choose appropriate starting position for pawn
            if piece_type == 'pawn':
                file = random.choice(self.files)
                if color == 'white':
                    rank = random.choice(['2', '3', '4', '5', '6'])
                else:
                    rank = random.choice(['3', '4', '5', '6', '7'])
                start = file + rank
            else:
                start = self._random_square()

            # Generate target position
            if is_valid:
                if piece_type == 'knight':
                    target = self._generate_valid_knight_target(start)
                elif piece_type == 'bishop':
                    target = self._generate_valid_bishop_target(start)
                elif piece_type == 'rook':
                    target = self._generate_valid_rook_target(start)
                elif piece_type == 'queen':
                    target = self._generate_valid_queen_target(start)
                elif piece_type == 'king':
                    target = self._generate_valid_king_target(start)
                else:  # pawn
                    target = self._generate_valid_pawn_target(start, color)
            else:
                if piece_type == 'knight':
                    target = self._generate_invalid_knight_target(start)
                elif piece_type == 'bishop':
                    target = self._generate_invalid_bishop_target(start)
                elif piece_type == 'rook':
                    target = self._generate_invalid_rook_target(start)
                elif piece_type == 'queen':
                    target = self._generate_invalid_queen_target(start)
                elif piece_type == 'king':
                    target = self._generate_invalid_king_target(start)
                else:  # pawn
                    target = self._generate_invalid_pawn_target(start, color)

            if target and target != start:
                break
        else:
            return None

        piece_symbol = self._piece_symbol(piece_type, color)
        piece_name = self._piece_name(piece_type)
        subtype = "valid" if is_valid else "invalid"

        return {
            "case_id": f"L1_{piece_type}_{subtype}_{case_num}",
            "type": "basic_movement_predictive",
            "subtype": subtype,
            "piece_type": piece_type,
            "color": color,
            "states": [
                {"pieces": {start: piece_symbol}, "squares": [target]}
            ],
            "question": f"Can the {piece_name} at {start} move to {target}?",
            "expected": "yes" if is_valid else "no",
            "reasoning": self._get_reasoning(piece_type, start, target, is_valid)
        }

    def _get_reasoning(self, piece_type: str, start: str, target: str, is_valid: bool) -> str:
        """Generate reasoning explanation"""
        if is_valid:
            patterns = {
                'knight': f"Valid L-shape move from {start} to {target}",
                'bishop': f"Valid diagonal move from {start} to {target}",
                'rook': f"Valid straight line move from {start} to {target}",
                'queen': f"Valid queen move from {start} to {target}",
                'king': f"Valid one-square move from {start} to {target}",
                'pawn': f"Valid pawn advance from {start} to {target}"
            }
        else:
            patterns = {
                'knight': f"Knight cannot move in straight/diagonal line",
                'bishop': f"Bishop cannot move in straight line",
                'rook': f"Rook cannot move diagonally",
                'queen': f"Queen cannot move in L-shape",
                'king': f"King can only move one square at a time",
                'pawn': f"Invalid pawn movement pattern"
            }
        return patterns.get(piece_type, "Movement pattern check")

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """Generate all Level 1 predictive test cases"""
        all_cases = []

        cases_per_piece = n_cases // 6
        remainder = n_cases % 6

        for idx, piece_type in enumerate(self.piece_types):
            n_piece_cases = cases_per_piece + (1 if idx < remainder else 0)
            n_valid = n_piece_cases // 2
            n_invalid = n_piece_cases - n_valid

            print(
                f"Generating {piece_type} tests: {n_valid} valid + {n_invalid} invalid...")

            # Valid cases
            valid_count = 0
            for _ in range(n_valid * 10):
                if valid_count >= n_valid:
                    break
                case = self._generate_case(piece_type, True, valid_count + 1)
                if case:
                    all_cases.append(case)
                    valid_count += 1

            # Invalid cases
            invalid_count = 0
            for _ in range(n_invalid * 10):
                if invalid_count >= n_invalid:
                    break
                case = self._generate_case(
                    piece_type, False, invalid_count + 1)
                if case:
                    all_cases.append(case)
                    invalid_count += 1

            print(
                f"  ✓ Generated {valid_count} valid + {invalid_count} invalid")

        random.shuffle(all_cases)
        print(
            f"\n✓ Total generated: {len(all_cases)} Level 1 predictive test cases")
        return all_cases
