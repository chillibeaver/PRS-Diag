"""
Xiangqi Level 3 Generator: Capture Rules with Blocking
Tests capture logic for pieces with special rules:
- Knight: L-shape capture, can be blocked at the "leg" position
- Bishop: Diagonal capture, can be blocked at the "eye" position  
- Cannon: Must jump over exactly one piece to capture
- Pawn: Forward capture (always), sideways capture (only after crossing river)

Each piece type tests:
1. Valid capture (path clear / has screen piece / correct direction)
2. Invalid capture (blocked / no screen piece / wrong direction)

Note: King is placed on board to indicate which side is which color.
"""

import random
from typing import List, Dict, Tuple, Optional, Set


class Level3Generator:
    """Generate Level 3 test cases - capture rules with blocking"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']  # 9 columns
        self.rows = list(range(10))  # 0-9

        # Piece types to test
        self.piece_types = ['knight', 'bishop', 'cannon', 'pawn']

    def _random_square(self) -> str:
        return random.choice(self.cols) + str(random.choice(self.rows))

    def _square_to_coords(self, square: str) -> Tuple[int, int]:
        col = ord(square[0]) - ord('a')
        row = int(square[1])
        return (col, row)

    def _coords_to_square(self, col: int, row: int) -> Optional[str]:
        if 0 <= col < 9 and 0 <= row < 10:
            return chr(ord('a') + col) + str(row)
        return None

    def _piece_symbol(self, piece_type: str, color: str) -> str:
        symbols = {
            'knight': 'N' if color == 'red' else 'n',
            'bishop': 'B' if color == 'red' else 'b',
            'cannon': 'C' if color == 'red' else 'c',
            'pawn': 'P' if color == 'red' else 'p',
            'king': 'K' if color == 'red' else 'k',
        }
        return symbols[piece_type]

    def _opposite_color(self, color: str) -> str:
        return 'black' if color == 'red' else 'red'

    def _get_king_position(self, color: str) -> Tuple[str, int, int]:
        """Get a random king position in the palace"""
        col = random.choice([3, 4, 5])
        if color == 'red':
            row = random.choice([0, 1, 2])
        else:
            row = random.choice([7, 8, 9])
        return self._coords_to_square(col, row), col, row

    def _is_across_river(self, row: int, color: str) -> bool:
        """Check if pawn has crossed river (is on enemy side)"""
        if color == 'red':
            return row >= 5  # Red pawn crossed to black side
        else:
            return row <= 4  # Black pawn crossed to red side

    # ==================== KNIGHT ====================

    def _get_knight_move_and_block(self, start: str) -> List[Tuple[str, str]]:
        col, row = self._square_to_coords(start)
        moves = []
        knight_moves = [
            (1, 2, 0, 1), (1, -2, 0, -1), (-1, 2, 0, 1), (-1, -2, 0, -1),
            (2, 1, 1, 0), (2, -1, 1, 0), (-2, 1, -1, 0), (-2, -1, -1, 0),
        ]
        for dc, dr, bdc, bdr in knight_moves:
            target = self._coords_to_square(col + dc, row + dr)
            block = self._coords_to_square(col + bdc, row + bdr)
            if target and block:
                moves.append((target, block))
        return moves

    def _generate_knight_capture_valid(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)
        for _ in range(50):
            col = random.randint(1, 7)
            row = random.randint(1, 8)
            start = self._coords_to_square(col, row)
            moves = self._get_knight_move_and_block(start)
            if not moves:
                continue
            target, block_sq = random.choice(moves)
            pieces = {
                start: self._piece_symbol('knight', color),
                target: self._piece_symbol('pawn', enemy_color),
            }
            return {
                "case_id": f"L3_knight_valid_{case_num}",
                "type": "capture_rule", "subtype": "knight_capture_valid",
                "piece_type": "knight", "color": color,
                "states": [{"pieces": pieces, "squares": []}],
                "question": f"Can the Knight at {start} capture the piece at {target}?",
                "expected": "yes",
                "reasoning": f"Knight captures from {start} to {target}, leg position {block_sq} is clear. Valid capture."
            }
        return None

    def _generate_knight_capture_blocked(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)
        blocker_color = random.choice(['red', 'black'])
        for _ in range(50):
            col = random.randint(1, 7)
            row = random.randint(1, 8)
            start = self._coords_to_square(col, row)
            moves = self._get_knight_move_and_block(start)
            if not moves:
                continue
            target, block_sq = random.choice(moves)
            pieces = {
                start: self._piece_symbol('knight', color),
                target: self._piece_symbol('pawn', enemy_color),
                block_sq: self._piece_symbol('pawn', blocker_color),
            }
            return {
                "case_id": f"L3_knight_blocked_{case_num}",
                "type": "capture_rule", "subtype": "knight_capture_blocked",
                "piece_type": "knight", "color": color,
                "states": [{"pieces": pieces, "squares": []}],
                "question": f"Can the Knight at {start} capture the piece at {target}?",
                "expected": "no",
                "reasoning": f"Knight cannot capture from {start} to {target}, leg position {block_sq} is blocked."
            }
        return None

    # ==================== BISHOP ====================

    def _get_bishop_move_and_block(self, start: str, color: str) -> List[Tuple[str, str]]:
        col, row = self._square_to_coords(start)
        moves = []
        bishop_moves = [(2, 2), (2, -2), (-2, 2), (-2, -2)]
        for dc, dr in bishop_moves:
            new_col, new_row = col + dc, row + dr
            block_col, block_row = col + dc // 2, row + dr // 2
            if color == 'red' and new_row > 4:
                continue
            if color == 'black' and new_row < 5:
                continue
            target = self._coords_to_square(new_col, new_row)
            block = self._coords_to_square(block_col, block_row)
            if target and block:
                moves.append((target, block))
        return moves

    def _generate_bishop_capture_valid(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)
        for _ in range(50):
            if color == 'red':
                col, row = random.randint(0, 8), random.randint(0, 4)
            else:
                col, row = random.randint(0, 8), random.randint(5, 9)
            start = self._coords_to_square(col, row)
            moves = self._get_bishop_move_and_block(start, color)
            if not moves:
                continue
            target, block_sq = random.choice(moves)
            pieces = {
                start: self._piece_symbol('bishop', color),
                target: self._piece_symbol('pawn', enemy_color),
            }
            return {
                "case_id": f"L3_bishop_valid_{case_num}",
                "type": "capture_rule", "subtype": "bishop_capture_valid",
                "piece_type": "bishop", "color": color,
                "states": [{"pieces": pieces, "squares": []}],
                "question": f"Can the Bishop at {start} capture the piece at {target}?",
                "expected": "yes",
                "reasoning": f"Bishop captures from {start} to {target}, eye position {block_sq} is clear. Valid capture."
            }
        return None

    def _generate_bishop_capture_blocked(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)
        blocker_color = random.choice(['red', 'black'])
        for _ in range(50):
            if color == 'red':
                col, row = random.randint(0, 8), random.randint(0, 4)
            else:
                col, row = random.randint(0, 8), random.randint(5, 9)
            start = self._coords_to_square(col, row)
            moves = self._get_bishop_move_and_block(start, color)
            if not moves:
                continue
            target, block_sq = random.choice(moves)
            pieces = {
                start: self._piece_symbol('bishop', color),
                target: self._piece_symbol('pawn', enemy_color),
                block_sq: self._piece_symbol('pawn', blocker_color),
            }
            return {
                "case_id": f"L3_bishop_blocked_{case_num}",
                "type": "capture_rule", "subtype": "bishop_capture_blocked",
                "piece_type": "bishop", "color": color,
                "states": [{"pieces": pieces, "squares": []}],
                "question": f"Can the Bishop at {start} capture the piece at {target}?",
                "expected": "no",
                "reasoning": f"Bishop cannot capture from {start} to {target}, eye position {block_sq} is blocked."
            }
        return None

    # ==================== CANNON ====================

    def _generate_cannon_capture_valid(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)
        screen_color = random.choice(['red', 'black'])
        for _ in range(50):
            col = random.randint(0, 8)
            row = random.randint(0, 9)
            start = self._coords_to_square(col, row)
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            random.shuffle(directions)
            for dc, dr in directions:
                screen_dist = random.randint(1, 3)
                target_dist = screen_dist + random.randint(1, 3)
                screen_sq = self._coords_to_square(
                    col + dc * screen_dist, row + dr * screen_dist)
                target_sq = self._coords_to_square(
                    col + dc * target_dist, row + dr * target_dist)
                if screen_sq and target_sq:
                    pieces = {
                        start: self._piece_symbol('cannon', color),
                        screen_sq: self._piece_symbol('pawn', screen_color),
                        target_sq: self._piece_symbol('pawn', enemy_color),
                    }
                    return {
                        "case_id": f"L3_cannon_valid_{case_num}",
                        "type": "capture_rule", "subtype": "cannon_capture_valid",
                        "piece_type": "cannon", "color": color,
                        "states": [{"pieces": pieces, "squares": []}],
                        "question": f"Can the Cannon at {start} capture the piece at {target_sq}?",
                        "expected": "yes",
                        "reasoning": f"Cannon captures from {start} to {target_sq}, with exactly one screen piece at {screen_sq}. Valid capture."
                    }
        return None

    def _generate_cannon_capture_no_screen(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)
        for _ in range(50):
            col = random.randint(0, 8)
            row = random.randint(0, 9)
            start = self._coords_to_square(col, row)
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            random.shuffle(directions)
            for dc, dr in directions:
                target_dist = random.randint(2, 5)
                target_sq = self._coords_to_square(
                    col + dc * target_dist, row + dr * target_dist)
                if target_sq:
                    pieces = {
                        start: self._piece_symbol('cannon', color),
                        target_sq: self._piece_symbol('pawn', enemy_color),
                    }
                    return {
                        "case_id": f"L3_cannon_no_screen_{case_num}",
                        "type": "capture_rule", "subtype": "cannon_no_screen",
                        "piece_type": "cannon", "color": color,
                        "states": [{"pieces": pieces, "squares": []}],
                        "question": f"Can the Cannon at {start} capture the piece at {target_sq}?",
                        "expected": "no",
                        "reasoning": f"Cannon cannot capture from {start} to {target_sq}, no screen piece between them."
                    }
        return None

    def _generate_cannon_capture_two_screens(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)
        screen1_color = random.choice(['red', 'black'])
        screen2_color = random.choice(['red', 'black'])
        for _ in range(50):
            col = random.randint(0, 8)
            row = random.randint(0, 9)
            start = self._coords_to_square(col, row)
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            random.shuffle(directions)
            for dc, dr in directions:
                screen1_dist = random.randint(1, 2)
                screen2_dist = screen1_dist + random.randint(1, 2)
                target_dist = screen2_dist + random.randint(1, 2)
                screen1_sq = self._coords_to_square(
                    col + dc * screen1_dist, row + dr * screen1_dist)
                screen2_sq = self._coords_to_square(
                    col + dc * screen2_dist, row + dr * screen2_dist)
                target_sq = self._coords_to_square(
                    col + dc * target_dist, row + dr * target_dist)
                if screen1_sq and screen2_sq and target_sq:
                    pieces = {
                        start: self._piece_symbol('cannon', color),
                        screen1_sq: self._piece_symbol('pawn', screen1_color),
                        screen2_sq: self._piece_symbol('pawn', screen2_color),
                        target_sq: self._piece_symbol('pawn', enemy_color),
                    }
                    return {
                        "case_id": f"L3_cannon_two_screens_{case_num}",
                        "type": "capture_rule", "subtype": "cannon_two_screens",
                        "piece_type": "cannon", "color": color,
                        "states": [{"pieces": pieces, "squares": []}],
                        "question": f"Can the Cannon at {start} capture the piece at {target_sq}?",
                        "expected": "no",
                        "reasoning": f"Cannon cannot capture from {start} to {target_sq}, two pieces between ({screen1_sq}, {screen2_sq}). Requires exactly one screen."
                    }
        return None

    # ==================== PAWN ====================

    def _generate_pawn_capture_forward_after_river(self, case_num: int) -> Optional[Dict]:
        """Pawn captures forward after crossing river (valid)"""
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)

        for _ in range(50):
            col = random.randint(0, 8)

            if color == 'red':
                # Red pawn crossed river (row 5-8), captures forward (row+1)
                row = random.randint(5, 8)
                target_row = row + 1
            else:
                # Black pawn crossed river (row 1-4), captures forward (row-1)
                row = random.randint(1, 4)
                target_row = row - 1

            start = self._coords_to_square(col, row)
            target = self._coords_to_square(col, target_row)
            king_sq, king_col, king_row = self._get_king_position(color)

            # Ensure no overlap
            if start == king_sq or target == king_sq:
                continue

            pieces = {
                start: self._piece_symbol('pawn', color),
                target: self._piece_symbol('pawn', enemy_color),
                king_sq: self._piece_symbol('king', color),
            }

            return {
                "case_id": f"L3_pawn_forward_after_{case_num}",
                "type": "capture_rule", "subtype": "pawn_capture_forward_after",
                "piece_type": "pawn", "color": color,
                "states": [{"pieces": pieces, "squares": []}],
                "question": f"Can the Pawn at {start} capture the piece at {target}?",
                "expected": "yes",
                "reasoning": f"Pawn captures forward from {start} to {target} after crossing river. Valid capture."
            }
        return None

    def _generate_pawn_capture_sideways_after_river(self, case_num: int) -> Optional[Dict]:
        """Pawn captures sideways after crossing river (valid)"""
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)

        for _ in range(50):
            col = random.randint(1, 7)  # Avoid edges

            if color == 'red':
                # Red pawn crossed river (row 5-9)
                row = random.randint(5, 9)
            else:
                # Black pawn crossed river (row 0-4)
                row = random.randint(0, 4)

            dc = random.choice([-1, 1])
            start = self._coords_to_square(col, row)
            target = self._coords_to_square(col + dc, row)
            king_sq, king_col, king_row = self._get_king_position(color)

            if start == king_sq or target == king_sq:
                continue

            pieces = {
                start: self._piece_symbol('pawn', color),
                target: self._piece_symbol('pawn', enemy_color),
                king_sq: self._piece_symbol('king', color),
            }

            return {
                "case_id": f"L3_pawn_sideways_after_{case_num}",
                "type": "capture_rule", "subtype": "pawn_capture_sideways_after",
                "piece_type": "pawn", "color": color,
                "states": [{"pieces": pieces, "squares": []}],
                "question": f"Can the Pawn at {start} capture the piece at {target}?",
                "expected": "yes",
                "reasoning": f"Pawn captures sideways from {start} to {target} after crossing river. Valid capture."
            }
        return None

    def _generate_pawn_capture_forward_before_river(self, case_num: int) -> Optional[Dict]:
        """Pawn captures forward before crossing river (valid)"""
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)

        for _ in range(50):
            col = random.randint(0, 8)

            if color == 'red':
                # Red pawn on own side (row 0-3), captures forward (row+1)
                row = random.randint(0, 3)
                target_row = row + 1
            else:
                # Black pawn on own side (row 6-9), captures forward (row-1)
                row = random.randint(6, 9)
                target_row = row - 1

            start = self._coords_to_square(col, row)
            target = self._coords_to_square(col, target_row)
            king_sq, king_col, king_row = self._get_king_position(color)

            if start == king_sq or target == king_sq:
                continue

            pieces = {
                start: self._piece_symbol('pawn', color),
                target: self._piece_symbol('pawn', enemy_color),
                king_sq: self._piece_symbol('king', color),
            }

            return {
                "case_id": f"L3_pawn_forward_before_{case_num}",
                "type": "capture_rule", "subtype": "pawn_capture_forward_before",
                "piece_type": "pawn", "color": color,
                "states": [{"pieces": pieces, "squares": []}],
                "question": f"Can the Pawn at {start} capture the piece at {target}?",
                "expected": "yes",
                "reasoning": f"Pawn captures forward from {start} to {target} before crossing river. Valid capture."
            }
        return None

    def _generate_pawn_capture_sideways_before_river(self, case_num: int) -> Optional[Dict]:
        """Pawn tries to capture sideways before crossing river (invalid)"""
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)

        for _ in range(50):
            col = random.randint(1, 7)

            if color == 'red':
                # Red pawn on own side (row 0-4)
                row = random.randint(0, 4)
            else:
                # Black pawn on own side (row 5-9)
                row = random.randint(5, 9)

            dc = random.choice([-1, 1])
            start = self._coords_to_square(col, row)
            target = self._coords_to_square(col + dc, row)
            king_sq, king_col, king_row = self._get_king_position(color)

            if start == king_sq or target == king_sq:
                continue

            pieces = {
                start: self._piece_symbol('pawn', color),
                target: self._piece_symbol('pawn', enemy_color),
                king_sq: self._piece_symbol('king', color),
            }

            return {
                "case_id": f"L3_pawn_sideways_before_{case_num}",
                "type": "capture_rule", "subtype": "pawn_capture_sideways_before",
                "piece_type": "pawn", "color": color,
                "states": [{"pieces": pieces, "squares": []}],
                "question": f"Can the Pawn at {start} capture the piece at {target}?",
                "expected": "no",
                "reasoning": f"Pawn cannot capture sideways before crossing river. {start} is still on own side (King at {king_sq})."
            }
        return None

    def _generate_pawn_capture_backward(self, case_num: int) -> Optional[Dict]:
        """Pawn tries to capture backward (invalid)"""
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)

        for _ in range(50):
            col = random.randint(0, 8)

            if color == 'red':
                # Red pawn, trying to capture backward (row-1)
                row = random.randint(1, 9)
                target_row = row - 1
            else:
                # Black pawn, trying to capture backward (row+1)
                row = random.randint(0, 8)
                target_row = row + 1

            start = self._coords_to_square(col, row)
            target = self._coords_to_square(col, target_row)
            king_sq, king_col, king_row = self._get_king_position(color)

            if start == king_sq or target == king_sq:
                continue

            pieces = {
                start: self._piece_symbol('pawn', color),
                target: self._piece_symbol('pawn', enemy_color),
                king_sq: self._piece_symbol('king', color),
            }

            return {
                "case_id": f"L3_pawn_backward_{case_num}",
                "type": "capture_rule", "subtype": "pawn_capture_backward",
                "piece_type": "pawn", "color": color,
                "states": [{"pieces": pieces, "squares": []}],
                "question": f"Can the Pawn at {start} capture the piece at {target}?",
                "expected": "no",
                "reasoning": f"Pawn cannot capture backward. {start} to {target} is a backward move (King at {king_sq} marks own side)."
            }
        return None

    def _generate_pawn_capture_diagonal(self, case_num: int) -> Optional[Dict]:
        """Pawn tries to capture diagonally (invalid)"""
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)

        for _ in range(50):
            col = random.randint(1, 7)
            row = random.randint(1, 8)

            dc, dr = random.choice([(1, 1), (-1, 1), (1, -1), (-1, -1)])
            start = self._coords_to_square(col, row)
            target = self._coords_to_square(col + dc, row + dr)
            king_sq, king_col, king_row = self._get_king_position(color)

            if not target or start == king_sq or target == king_sq:
                continue

            pieces = {
                start: self._piece_symbol('pawn', color),
                target: self._piece_symbol('pawn', enemy_color),
                king_sq: self._piece_symbol('king', color),
            }

            return {
                "case_id": f"L3_pawn_diagonal_{case_num}",
                "type": "capture_rule", "subtype": "pawn_capture_diagonal",
                "piece_type": "pawn", "color": color,
                "states": [{"pieces": pieces, "squares": []}],
                "question": f"Can the Pawn at {start} capture the piece at {target}?",
                "expected": "no",
                "reasoning": f"Pawn cannot capture diagonally."
            }
        return None

    # ==================== GENERATE ALL ====================

    def generate_all(self, n_cases: int = 50, verbose: bool = False) -> List[Dict]:
        """Generate all Level 3 test cases"""
        all_cases = []

        # Distribute cases among piece types
        knight_ratio = 0.20  # Knight 20%
        bishop_ratio = 0.25  # Bishop 25%
        cannon_ratio = 0.20  # Cannon 20%
        pawn_ratio = 0.35    # Pawn 35%

        n_knight = int(n_cases * knight_ratio)
        n_bishop = int(n_cases * bishop_ratio)
        n_cannon = int(n_cases * cannon_ratio)
        n_pawn = n_cases - n_knight - n_bishop - n_cannon

        # Knight: 2 subtypes
        n_knight_valid = n_knight // 2
        n_knight_blocked = n_knight - n_knight_valid

        # Bishop: 2 subtypes
        n_bishop_valid = n_bishop // 2
        n_bishop_blocked = n_bishop - n_bishop_valid

        # Cannon: 3 subtypes
        n_cannon_valid = n_cannon // 3
        n_cannon_no_screen = n_cannon // 3
        n_cannon_two_screens = n_cannon - n_cannon_valid - n_cannon_no_screen

        # Pawn: 6 subtypes
        n_pawn_per_subtype = n_pawn // 6
        n_pawn_remainder = n_pawn % 6

        generators = [
            # Knight
            (self._generate_knight_capture_valid, n_knight_valid, "knight_valid"),
            (self._generate_knight_capture_blocked,
             n_knight_blocked, "knight_blocked"),
            # Bishop
            (self._generate_bishop_capture_valid, n_bishop_valid, "bishop_valid"),
            (self._generate_bishop_capture_blocked,
             n_bishop_blocked, "bishop_blocked"),
            # Cannon
            (self._generate_cannon_capture_valid, n_cannon_valid, "cannon_valid"),
            (self._generate_cannon_capture_no_screen,
             n_cannon_no_screen, "cannon_no_screen"),
            (self._generate_cannon_capture_two_screens,
             n_cannon_two_screens, "cannon_two_screens"),
            # Pawn
            (self._generate_pawn_capture_forward_after_river,
             n_pawn_per_subtype + (1 if n_pawn_remainder > 0 else 0), "pawn_forward_after"),
            (self._generate_pawn_capture_sideways_after_river,
             n_pawn_per_subtype + (1 if n_pawn_remainder > 1 else 0), "pawn_sideways_after"),
            (self._generate_pawn_capture_forward_before_river,
             n_pawn_per_subtype + (1 if n_pawn_remainder > 2 else 0), "pawn_forward_before"),
            (self._generate_pawn_capture_sideways_before_river,
             n_pawn_per_subtype + (1 if n_pawn_remainder > 3 else 0), "pawn_sideways_before"),
            (self._generate_pawn_capture_backward,
             n_pawn_per_subtype + (1 if n_pawn_remainder > 4 else 0), "pawn_backward"),
            (self._generate_pawn_capture_diagonal,
             n_pawn_per_subtype, "pawn_diagonal"),
        ]

        for gen_func, count, name in generators:
            generated = 0
            for _ in range(count * 10):
                if generated >= count:
                    break
                case = gen_func(generated + 1)
                if case:
                    all_cases.append(case)
                    generated += 1
            if verbose:
                print(f"  Generated {generated} {name} cases")

        random.shuffle(all_cases)
        if verbose:
            print(f"\nTotal generated: {len(all_cases)} Level 3 test cases")

        return all_cases
