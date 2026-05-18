"""
Xiangqi Level 2 Generator: Complex Movement Rules (Explicit Mode)
Explicit version: Shows both before and after states, asks if the move is legal

Tests movement rules for pieces with spatial constraints:
- Knight: L-shape movement with leg blocking
- Bishop: Diagonal movement with eye blocking + river constraint
- King: Orthogonal movement within palace
- Advisor: Diagonal movement within palace

Each piece type tests:
1. Valid movement (path clear, within constraints)
2. Invalid movement (blocked, out of bounds, wrong pattern)
"""

import random
from typing import List, Dict, Tuple, Optional


class Level2Generator:
    """Generate Level 2 test cases - complex movement rules (explicit mode)"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']  # 9 columns
        self.rows = list(range(10))  # 0-9

        # Palace positions
        self.palace_cols = ['d', 'e', 'f']  # columns 3,4,5
        self.red_palace_rows = [0, 1, 2]
        self.black_palace_rows = [7, 8, 9]

        # Piece types to test
        self.piece_types = ['knight', 'bishop', 'king', 'advisor', 'pawn']

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
            'king': 'K' if color == 'red' else 'k',
            'advisor': 'A' if color == 'red' else 'a',
            'pawn': 'P' if color == 'red' else 'p',
            'rook': 'R' if color == 'red' else 'r',
            'cannon': 'C' if color == 'red' else 'c',
        }
        return symbols[piece_type]

    def _opposite_color(self, color: str) -> str:
        return 'black' if color == 'red' else 'red'

    def _is_in_palace(self, col: int, row: int, color: str) -> bool:
        """Check if position is within palace"""
        if color == 'red':
            return 3 <= col <= 5 and 0 <= row <= 2
        else:
            return 3 <= col <= 5 and 7 <= row <= 9

    def _is_own_side(self, row: int, color: str) -> bool:
        """Check if position is on own side of river"""
        if color == 'red':
            return row <= 4
        else:
            return row >= 5

    def _is_across_river(self, row: int, color: str) -> bool:
        """Check if pawn has crossed river (is on enemy side)"""
        if color == 'red':
            return row >= 5  # Red pawn crossed to black side
        else:
            return row <= 4  # Black pawn crossed to red side

    # ==================== KNIGHT ====================

    def _get_knight_moves_with_blocks(self, start: str) -> List[Tuple[str, str]]:
        col, row = self._square_to_coords(start)
        moves = []
        knight_patterns = [
            (1, 2, 0, 1), (1, -2, 0, -1), (-1, 2, 0, 1), (-1, -2, 0, -1),
            (2, 1, 1, 0), (2, -1, 1, 0), (-2, 1, -1, 0), (-2, -1, -1, 0),
        ]
        for dc, dr, bdc, bdr in knight_patterns:
            target = self._coords_to_square(col + dc, row + dr)
            block = self._coords_to_square(col + bdc, row + bdr)
            if target and block:
                moves.append((target, block))
        return moves

    def _generate_knight_valid(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            col = random.randint(1, 7)
            row = random.randint(1, 8)
            start = self._coords_to_square(col, row)
            moves = self._get_knight_moves_with_blocks(start)
            if not moves:
                continue
            target, block_sq = random.choice(moves)
            piece_symbol = self._piece_symbol('knight', color)
            # Explicit mode: State 1 = before, State 2 = after
            return {
                "case_id": f"L2_knight_valid_{case_num}",
                "type": "movement_rule", "subtype": "knight_valid",
                "piece_type": "knight", "color": color,
                "states": [
                    {"pieces": {start: piece_symbol}, "squares": []},
                    {"pieces": {target: piece_symbol}, "squares": []}
                ],
                "question": "Is this a legal move according to Xiangqi rules?",
                "expected": "yes",
                "reasoning": f"Knight moves from {start} to {target}, leg position {block_sq} is clear. Legal move."
            }
        return None

    def _generate_knight_blocked(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        blocker_color = random.choice(['red', 'black'])
        for _ in range(50):
            col = random.randint(1, 7)
            row = random.randint(1, 8)
            start = self._coords_to_square(col, row)
            moves = self._get_knight_moves_with_blocks(start)
            if not moves:
                continue
            target, block_sq = random.choice(moves)
            piece_symbol = self._piece_symbol('knight', color)
            blocker_symbol = self._piece_symbol('pawn', blocker_color)
            # Explicit mode: show the blocked move attempt
            return {
                "case_id": f"L2_knight_blocked_{case_num}",
                "type": "movement_rule", "subtype": "knight_blocked",
                "piece_type": "knight", "color": color,
                "states": [
                    {"pieces": {start: piece_symbol,
                                block_sq: blocker_symbol}, "squares": []},
                    {"pieces": {target: piece_symbol,
                                block_sq: blocker_symbol}, "squares": []}
                ],
                "question": "Is this a legal move according to Xiangqi rules?",
                "expected": "no",
                "reasoning": f"Knight cannot move from {start} to {target}, leg position {block_sq} is blocked."
            }
        return None

    def _generate_knight_invalid_pattern(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            col = random.randint(1, 7)
            row = random.randint(1, 8)
            start = self._coords_to_square(col, row)
            invalid_type = random.choice(['straight', 'diagonal', 'wrong_L'])
            if invalid_type == 'straight':
                dist = random.randint(1, 3)
                dc, dr = random.choice(
                    [(dist, 0), (-dist, 0), (0, dist), (0, -dist)])
            elif invalid_type == 'diagonal':
                dist = random.randint(1, 2)
                dc, dr = random.choice(
                    [(dist, dist), (-dist, dist), (dist, -dist), (-dist, -dist)])
            else:
                dc, dr = random.choice([(3, 1), (1, 3), (-3, 1), (1, -3)])
            target = self._coords_to_square(col + dc, row + dr)
            if not target or target == start:
                continue
            piece_symbol = self._piece_symbol('knight', color)
            return {
                "case_id": f"L2_knight_invalid_{case_num}",
                "type": "movement_rule", "subtype": "knight_invalid_pattern",
                "piece_type": "knight", "color": color,
                "states": [
                    {"pieces": {start: piece_symbol}, "squares": []},
                    {"pieces": {target: piece_symbol}, "squares": []}
                ],
                "question": "Is this a legal move according to Xiangqi rules?",
                "expected": "no",
                "reasoning": f"Knight can only move in L-shape (2+1 pattern). {start} to {target} is not valid."
            }
        return None

    # ==================== BISHOP ====================

    def _get_bishop_moves_with_blocks(self, start: str, color: str) -> List[Tuple[str, str]]:
        col, row = self._square_to_coords(start)
        moves = []
        bishop_patterns = [(2, 2), (2, -2), (-2, 2), (-2, -2)]
        for dc, dr in bishop_patterns:
            new_col, new_row = col + dc, row + dr
            block_col, block_row = col + dc // 2, row + dr // 2
            if not self._is_own_side(new_row, color):
                continue
            target = self._coords_to_square(new_col, new_row)
            block = self._coords_to_square(block_col, block_row)
            if target and block:
                moves.append((target, block))
        return moves

    def _generate_bishop_valid(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            if color == 'red':
                col, row = random.randint(0, 8), random.randint(0, 4)
            else:
                col, row = random.randint(0, 8), random.randint(5, 9)
            start = self._coords_to_square(col, row)
            moves = self._get_bishop_moves_with_blocks(start, color)
            if not moves:
                continue
            target, block_sq = random.choice(moves)
            piece_symbol = self._piece_symbol('bishop', color)
            return {
                "case_id": f"L2_bishop_valid_{case_num}",
                "type": "movement_rule", "subtype": "bishop_valid",
                "piece_type": "bishop", "color": color,
                "states": [
                    {"pieces": {start: piece_symbol}, "squares": []},
                    {"pieces": {target: piece_symbol}, "squares": []}
                ],
                "question": "Is this a legal move according to Xiangqi rules?",
                "expected": "yes",
                "reasoning": f"Bishop moves diagonally 2 steps from {start} to {target}, eye position {block_sq} is clear."
            }
        return None

    def _generate_bishop_blocked(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        blocker_color = random.choice(['red', 'black'])
        for _ in range(50):
            if color == 'red':
                col, row = random.randint(0, 8), random.randint(0, 4)
            else:
                col, row = random.randint(0, 8), random.randint(5, 9)
            start = self._coords_to_square(col, row)
            moves = self._get_bishop_moves_with_blocks(start, color)
            if not moves:
                continue
            target, block_sq = random.choice(moves)
            piece_symbol = self._piece_symbol('bishop', color)
            blocker_symbol = self._piece_symbol('pawn', blocker_color)
            return {
                "case_id": f"L2_bishop_blocked_{case_num}",
                "type": "movement_rule", "subtype": "bishop_blocked",
                "piece_type": "bishop", "color": color,
                "states": [
                    {"pieces": {start: piece_symbol,
                                block_sq: blocker_symbol}, "squares": []},
                    {"pieces": {target: piece_symbol,
                                block_sq: blocker_symbol}, "squares": []}
                ],
                "question": "Is this a legal move according to Xiangqi rules?",
                "expected": "no",
                "reasoning": f"Bishop cannot move from {start} to {target}, eye position {block_sq} is blocked."
            }
        return None

    def _generate_bishop_cross_river(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            if color == 'red':
                col, row = random.randint(0, 8), random.choice([3, 4])
            else:
                col, row = random.randint(0, 8), random.choice([5, 6])
            start = self._coords_to_square(col, row)
            if color == 'red':
                dc, dr = random.choice([2, -2]), 2
            else:
                dc, dr = random.choice([2, -2]), -2
            new_col, new_row = col + dc, row + dr
            target = self._coords_to_square(new_col, new_row)
            if not target or self._is_own_side(new_row, color):
                continue
            piece_symbol = self._piece_symbol('bishop', color)
            return {
                "case_id": f"L2_bishop_river_{case_num}",
                "type": "movement_rule", "subtype": "bishop_cross_river",
                "piece_type": "bishop", "color": color,
                "states": [
                    {"pieces": {start: piece_symbol}, "squares": []},
                    {"pieces": {target: piece_symbol}, "squares": []}
                ],
                "question": "Is this a legal move according to Xiangqi rules?",
                "expected": "no",
                "reasoning": f"Bishop cannot cross the river. {target} is on the opponent's side."
            }
        return None

    def _generate_bishop_invalid_pattern(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            if color == 'red':
                col, row = random.randint(1, 7), random.randint(1, 3)
            else:
                col, row = random.randint(1, 7), random.randint(6, 8)
            start = self._coords_to_square(col, row)
            invalid_type = random.choice(
                ['straight', 'small_diagonal', 'wrong_diagonal'])
            if invalid_type == 'straight':
                dist = random.randint(1, 2)
                dc, dr = random.choice(
                    [(dist, 0), (-dist, 0), (0, dist), (0, -dist)])
            elif invalid_type == 'small_diagonal':
                dc, dr = random.choice([(1, 1), (-1, 1), (1, -1), (-1, -1)])
            else:
                dc, dr = random.choice(
                    [(3, 3), (-3, 3), (3, -3), (-3, -3), (2, 1), (1, 2)])
            new_row = row + dr
            if color == 'red' and new_row > 4:
                dr = -abs(dr)
                new_row = row + dr
            elif color == 'black' and new_row < 5:
                dr = abs(dr)
                new_row = row + dr
            target = self._coords_to_square(col + dc, new_row)
            if not target or target == start:
                continue
            piece_symbol = self._piece_symbol('bishop', color)
            return {
                "case_id": f"L2_bishop_invalid_{case_num}",
                "type": "movement_rule", "subtype": "bishop_invalid_pattern",
                "piece_type": "bishop", "color": color,
                "states": [
                    {"pieces": {start: piece_symbol}, "squares": []},
                    {"pieces": {target: piece_symbol}, "squares": []}
                ],
                "question": "Is this a legal move according to Xiangqi rules?",
                "expected": "no",
                "reasoning": f"Bishop can only move diagonally 2 steps. {start} to {target} is not valid."
            }
        return None

    # ==================== KING ====================

    def _get_palace_positions(self, color: str) -> List[Tuple[int, int]]:
        if color == 'red':
            return [(c, r) for c in range(3, 6) for r in range(0, 3)]
        else:
            return [(c, r) for c in range(3, 6) for r in range(7, 10)]

    def _generate_king_valid(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            positions = self._get_palace_positions(color)
            col, row = random.choice(positions)
            start = self._coords_to_square(col, row)
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            random.shuffle(directions)
            for dc, dr in directions:
                new_col, new_row = col + dc, row + dr
                if self._is_in_palace(new_col, new_row, color):
                    target = self._coords_to_square(new_col, new_row)
                    piece_symbol = self._piece_symbol('king', color)
                    return {
                        "case_id": f"L2_king_valid_{case_num}",
                        "type": "movement_rule", "subtype": "king_valid",
                        "piece_type": "king", "color": color,
                        "states": [
                            {"pieces": {start: piece_symbol}, "squares": []},
                            {"pieces": {target: piece_symbol}, "squares": []}
                        ],
                        "question": "Is this a legal move according to Xiangqi rules?",
                        "expected": "yes",
                        "reasoning": f"King moves one step orthogonally within palace, from {start} to {target}."
                    }
        return None

    def _generate_king_outside_palace(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            if color == 'red':
                edge_positions = [(3, 0), (5, 0), (3, 2),
                                  (5, 2), (4, 0), (4, 2), (3, 1), (5, 1)]
            else:
                edge_positions = [(3, 7), (5, 7), (3, 9),
                                  (5, 9), (4, 7), (4, 9), (3, 8), (5, 8)]
            col, row = random.choice(edge_positions)
            start = self._coords_to_square(col, row)
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            random.shuffle(directions)
            for dc, dr in directions:
                new_col, new_row = col + dc, row + dr
                target = self._coords_to_square(new_col, new_row)
                if target and not self._is_in_palace(new_col, new_row, color):
                    piece_symbol = self._piece_symbol('king', color)
                    return {
                        "case_id": f"L2_king_outside_{case_num}",
                        "type": "movement_rule", "subtype": "king_outside_palace",
                        "piece_type": "king", "color": color,
                        "states": [
                            {"pieces": {start: piece_symbol}, "squares": []},
                            {"pieces": {target: piece_symbol}, "squares": []}
                        ],
                        "question": "Is this a legal move according to Xiangqi rules?",
                        "expected": "no",
                        "reasoning": f"King cannot leave the palace. {target} is outside the palace."
                    }
        return None

    def _generate_king_diagonal(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            positions = self._get_palace_positions(color)
            col, row = random.choice(positions)
            start = self._coords_to_square(col, row)
            dc, dr = random.choice([(1, 1), (-1, 1), (1, -1), (-1, -1)])
            new_col, new_row = col + dc, row + dr
            target = self._coords_to_square(new_col, new_row)
            if target and target != start:
                piece_symbol = self._piece_symbol('king', color)
                return {
                    "case_id": f"L2_king_diagonal_{case_num}",
                    "type": "movement_rule", "subtype": "king_diagonal",
                    "piece_type": "king", "color": color,
                    "states": [
                        {"pieces": {start: piece_symbol}, "squares": []},
                        {"pieces": {target: piece_symbol}, "squares": []}
                    ],
                    "question": "Is this a legal move according to Xiangqi rules?",
                    "expected": "no",
                    "reasoning": f"King can only move orthogonally, not diagonally."
                }
        return None

    def _generate_king_too_far(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            positions = self._get_palace_positions(color)
            col, row = random.choice(positions)
            start = self._coords_to_square(col, row)
            dist = 2
            dc, dr = random.choice(
                [(0, dist), (0, -dist), (dist, 0), (-dist, 0)])
            new_col, new_row = col + dc, row + dr
            target = self._coords_to_square(new_col, new_row)
            if target and target != start:
                piece_symbol = self._piece_symbol('king', color)
                return {
                    "case_id": f"L2_king_far_{case_num}",
                    "type": "movement_rule", "subtype": "king_too_far",
                    "piece_type": "king", "color": color,
                    "states": [
                        {"pieces": {start: piece_symbol}, "squares": []},
                        {"pieces": {target: piece_symbol}, "squares": []}
                    ],
                    "question": "Is this a legal move according to Xiangqi rules?",
                    "expected": "no",
                    "reasoning": f"King can only move one step at a time."
                }
        return None

    # ==================== ADVISOR ====================

    def _get_advisor_valid_positions(self, color: str) -> List[Tuple[int, int]]:
        """Get the 5 valid positions for advisor (corners + center of palace)"""
        if color == 'red':
            # Red palace: d0, f0, e1, d2, f2
            return [(3, 0), (5, 0), (4, 1), (3, 2), (5, 2)]
        else:
            # Black palace: d7, f7, e8, d9, f9
            return [(3, 7), (5, 7), (4, 8), (3, 9), (5, 9)]

    def _get_advisor_valid_moves(self, col: int, row: int, color: str) -> List[Tuple[int, int]]:
        """Get valid diagonal moves for advisor within palace"""
        moves = []
        for dc, dr in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
            new_col, new_row = col + dc, row + dr
            # Must land on a valid advisor position
            if (new_col, new_row) in self._get_advisor_valid_positions(color):
                moves.append((new_col, new_row))
        return moves

    def _generate_advisor_valid(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            # Only start from valid advisor positions (5 points)
            valid_positions = self._get_advisor_valid_positions(color)
            col, row = random.choice(valid_positions)
            moves = self._get_advisor_valid_moves(col, row, color)
            if not moves:
                continue
            new_col, new_row = random.choice(moves)
            start = self._coords_to_square(col, row)
            target = self._coords_to_square(new_col, new_row)
            piece_symbol = self._piece_symbol('advisor', color)
            return {
                "case_id": f"L2_advisor_valid_{case_num}",
                "type": "movement_rule", "subtype": "advisor_valid",
                "piece_type": "advisor", "color": color,
                "states": [
                    {"pieces": {start: piece_symbol}, "squares": []},
                    {"pieces": {target: piece_symbol}, "squares": []}
                ],
                "question": "Is this a legal move according to Xiangqi rules?",
                "expected": "yes",
                "reasoning": f"Advisor moves one step diagonally within palace, from {start} to {target}."
            }
        return None

    def _generate_advisor_orthogonal(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            # Start from valid advisor positions
            valid_positions = self._get_advisor_valid_positions(color)
            col, row = random.choice(valid_positions)
            start = self._coords_to_square(col, row)
            dc, dr = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            new_col, new_row = col + dc, row + dr
            target = self._coords_to_square(new_col, new_row)
            if target and target != start:
                piece_symbol = self._piece_symbol('advisor', color)
                return {
                    "case_id": f"L2_advisor_orthogonal_{case_num}",
                    "type": "movement_rule", "subtype": "advisor_orthogonal",
                    "piece_type": "advisor", "color": color,
                    "states": [
                        {"pieces": {start: piece_symbol}, "squares": []},
                        {"pieces": {target: piece_symbol}, "squares": []}
                    ],
                    "question": "Is this a legal move according to Xiangqi rules?",
                    "expected": "no",
                    "reasoning": f"Advisor can only move diagonally, not orthogonally."
                }
        return None

    def _generate_advisor_outside_palace(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            # Corners of palace that can move outside
            if color == 'red':
                corner_positions = [(3, 0), (5, 0), (3, 2), (5, 2)]
            else:
                corner_positions = [(3, 7), (5, 7), (3, 9), (5, 9)]
            col, row = random.choice(corner_positions)
            start = self._coords_to_square(col, row)
            for dc, dr in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
                new_col, new_row = col + dc, row + dr
                target = self._coords_to_square(new_col, new_row)
                # Check if target is outside valid advisor positions
                if target and (new_col, new_row) not in self._get_advisor_valid_positions(color):
                    piece_symbol = self._piece_symbol('advisor', color)
                    return {
                        "case_id": f"L2_advisor_outside_{case_num}",
                        "type": "movement_rule", "subtype": "advisor_outside_palace",
                        "piece_type": "advisor", "color": color,
                        "states": [
                            {"pieces": {start: piece_symbol}, "squares": []},
                            {"pieces": {target: piece_symbol}, "squares": []}
                        ],
                        "question": "Is this a legal move according to Xiangqi rules?",
                        "expected": "no",
                        "reasoning": f"Advisor cannot leave the palace. {target} is outside the palace."
                    }
        return None

    def _generate_advisor_too_far(self, case_num: int) -> Optional[Dict]:
        color = random.choice(['red', 'black'])
        for _ in range(50):
            valid_positions = self._get_advisor_valid_positions(color)
            col, row = random.choice(valid_positions)
            start = self._coords_to_square(col, row)
            dc, dr = random.choice([(2, 2), (-2, 2), (2, -2), (-2, -2)])
            new_col, new_row = col + dc, row + dr
            target = self._coords_to_square(new_col, new_row)
            if target and target != start:
                piece_symbol = self._piece_symbol('advisor', color)
                return {
                    "case_id": f"L2_advisor_far_{case_num}",
                    "type": "movement_rule", "subtype": "advisor_too_far",
                    "piece_type": "advisor", "color": color,
                    "states": [
                        {"pieces": {start: piece_symbol}, "squares": []},
                        {"pieces": {target: piece_symbol}, "squares": []}
                    ],
                    "question": "Is this a legal move according to Xiangqi rules?",
                    "expected": "no",
                    "reasoning": f"Advisor can only move one step diagonally at a time."
                }
        return None

    # ==================== GENERATE ALL ====================

    def generate_all(self, n_cases: int = 50, verbose: bool = False) -> List[Dict]:
        """Generate all Level 2 test cases (explicit mode)"""
        all_cases = []

        # Distribution ratios (4 piece types, 25% each)
        knight_ratio = 0.25
        bishop_ratio = 0.25
        king_ratio = 0.25
        advisor_ratio = 0.25

        n_knight = int(n_cases * knight_ratio)
        n_bishop = int(n_cases * bishop_ratio)
        n_king = int(n_cases * king_ratio)
        n_advisor = n_cases - n_knight - n_bishop - n_king

        # Knight: 3 subtypes
        n_knight_valid = n_knight // 3
        n_knight_blocked = n_knight // 3
        n_knight_invalid = n_knight - n_knight_valid - n_knight_blocked

        # Bishop: 4 subtypes
        n_bishop_valid = n_bishop // 4
        n_bishop_blocked = n_bishop // 4
        n_bishop_river = n_bishop // 4
        n_bishop_invalid = n_bishop - n_bishop_valid - n_bishop_blocked - n_bishop_river

        # King: 4 subtypes
        n_king_valid = n_king // 4
        n_king_outside = n_king // 4
        n_king_diagonal = n_king // 4
        n_king_far = n_king - n_king_valid - n_king_outside - n_king_diagonal

        # Advisor: 4 subtypes
        n_advisor_valid = n_advisor // 4
        n_advisor_orthogonal = n_advisor // 4
        n_advisor_outside = n_advisor // 4
        n_advisor_far = n_advisor - n_advisor_valid - \
            n_advisor_orthogonal - n_advisor_outside

        generators = [
            (self._generate_knight_valid, n_knight_valid, "knight_valid"),
            (self._generate_knight_blocked, n_knight_blocked, "knight_blocked"),
            (self._generate_knight_invalid_pattern,
             n_knight_invalid, "knight_invalid"),
            (self._generate_bishop_valid, n_bishop_valid, "bishop_valid"),
            (self._generate_bishop_blocked, n_bishop_blocked, "bishop_blocked"),
            (self._generate_bishop_cross_river, n_bishop_river, "bishop_river"),
            (self._generate_bishop_invalid_pattern,
             n_bishop_invalid, "bishop_invalid"),
            (self._generate_king_valid, n_king_valid, "king_valid"),
            (self._generate_king_outside_palace, n_king_outside, "king_outside"),
            (self._generate_king_diagonal, n_king_diagonal, "king_diagonal"),
            (self._generate_king_too_far, n_king_far, "king_far"),
            (self._generate_advisor_valid, n_advisor_valid, "advisor_valid"),
            (self._generate_advisor_orthogonal,
             n_advisor_orthogonal, "advisor_orthogonal"),
            (self._generate_advisor_outside_palace,
             n_advisor_outside, "advisor_outside"),
            (self._generate_advisor_too_far, n_advisor_far, "advisor_far"),
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
                print(f"  ✓ Generated {generated} {name} cases")

        random.shuffle(all_cases)
        if verbose:
            print(
                f"\n✓ Total generated: {len(all_cases)} Level 2 explicit test cases")

        return all_cases
