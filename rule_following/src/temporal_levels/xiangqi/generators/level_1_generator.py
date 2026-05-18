"""
Xiangqi Level 1 Generator: Basic Movement Rules
Predictive version: Shows current state, asks if piece can move to target position

Tests basic movement rules for 2 piece types:
- Rook: Any distance orthogonally
- Cannon: Any distance orthogonally (movement only, not capture)
"""

import random
from typing import List, Dict, Tuple, Optional


class Level1Generator:
    """Generate Level 1 test cases - basic movement rules"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']  # 9 columns
        self.rows = list(range(10))  # 0-9

        # Piece types to test (2 types: rook, cannon)
        self.piece_types = ['rook', 'cannon']

    def _random_square(self) -> str:
        """Generate random square"""
        return random.choice(self.cols) + str(random.choice(self.rows))

    def _square_to_coords(self, square: str) -> Tuple[int, int]:
        """Convert 'e4' to (col_idx, row_idx)"""
        col = ord(square[0]) - ord('a')
        row = int(square[1])
        return (col, row)

    def _coords_to_square(self, col: int, row: int) -> Optional[str]:
        """Convert (col_idx, row_idx) to 'e4'"""
        if 0 <= col < 9 and 0 <= row < 10:
            return chr(ord('a') + col) + str(row)
        return None

    def _piece_symbol(self, piece_type: str, color: str) -> str:
        """Get piece symbol"""
        symbols = {
            'rook': 'R' if color == 'red' else 'r',
            'cannon': 'C' if color == 'red' else 'c',
        }
        return symbols[piece_type]

    # ==================== VALID MOVES ====================

    def _generate_valid_rook_move(self, color: str) -> Optional[Tuple[str, str]]:
        """Generate valid rook move (straight line any distance)"""
        for _ in range(50):
            col = random.randint(0, 8)
            row = random.randint(0, 9)
            start = self._coords_to_square(col, row)

            if random.choice([True, False]):
                # Horizontal
                dist = random.randint(1, 6) * random.choice([-1, 1])
                new_col = col + dist
                if 0 <= new_col < 9:
                    return start, self._coords_to_square(new_col, row)
            else:
                # Vertical
                dist = random.randint(1, 7) * random.choice([-1, 1])
                new_row = row + dist
                if 0 <= new_row < 10:
                    return start, self._coords_to_square(col, new_row)
        return None

    def _generate_valid_cannon_move(self, color: str) -> Optional[Tuple[str, str]]:
        """Generate valid cannon move (same as rook for movement)"""
        return self._generate_valid_rook_move(color)

    # ==================== INVALID MOVES ====================

    def _generate_invalid_rook_move(self, color: str) -> Optional[Tuple[str, str]]:
        """Generate invalid rook move (diagonal)"""
        col = random.randint(1, 7)
        row = random.randint(1, 8)
        start = self._coords_to_square(col, row)

        dist = random.randint(1, 3)
        dc, dr = random.choice(
            [(dist, dist), (-dist, dist), (dist, -dist), (-dist, -dist)])
        target = self._coords_to_square(col + dc, row + dr)
        if target:
            return start, target
        return None

    def _generate_invalid_cannon_move(self, color: str) -> Optional[Tuple[str, str]]:
        """Generate invalid cannon move (diagonal)"""
        return self._generate_invalid_rook_move(color)

    # ==================== CASE GENERATION ====================

    def _generate_case(self, piece_type: str, is_valid: bool, case_num: int) -> Optional[Dict]:
        """Generate a single test case"""
        color = random.choice(['red', 'black'])

        for _ in range(100):
            if is_valid:
                if piece_type == 'rook':
                    result = self._generate_valid_rook_move(color)
                else:  # cannon
                    result = self._generate_valid_cannon_move(color)
            else:
                if piece_type == 'rook':
                    result = self._generate_invalid_rook_move(color)
                else:  # cannon
                    result = self._generate_invalid_cannon_move(color)

            if result:
                start, target = result
                if start != target:
                    break
        else:
            return None

        piece_symbol = self._piece_symbol(piece_type, color)
        subtype = "valid" if is_valid else "invalid"

        # Build pieces dict - just the piece being tested
        pieces = {start: piece_symbol}

        return {
            "case_id": f"L1_{piece_type}_{subtype}_{case_num}",
            "type": "basic_movement",
            "subtype": subtype,
            "piece_type": piece_type,
            "color": color,
            "start": start,
            "target": target,
            "states": [
                {"pieces": pieces, "squares": []}
            ],
            "question": f"Can the {piece_type.capitalize()} move from {start} to {target}?",
            "expected": "yes" if is_valid else "no",
            "reasoning": self._get_reasoning(piece_type, start, target, is_valid, color)
        }

    def _get_reasoning(self, piece_type: str, start: str, target: str,
                       is_valid: bool, color: str) -> str:
        """Generate reasoning explanation"""
        if is_valid:
            patterns = {
                'rook': f"Rook moves orthogonally from {start} to {target}. Legal move.",
                'cannon': f"Cannon moves orthogonally from {start} to {target} (no capture). Legal move.",
            }
        else:
            patterns = {
                'rook': f"Rook can only move orthogonally, not diagonally.",
                'cannon': f"Cannon can only move orthogonally, not diagonally.",
            }
        return patterns.get(piece_type, "Movement rule check.")

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """Generate all Level 1 test cases"""
        all_cases = []

        cases_per_piece = n_cases // 2
        remainder = n_cases % 2

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
                f"  Generated {valid_count} valid + {invalid_count} invalid")

        random.shuffle(all_cases)
        print(f"\nTotal generated: {len(all_cases)} Level 1 test cases")
        return all_cases
