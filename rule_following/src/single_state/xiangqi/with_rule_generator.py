"""
Automated test case generator for Xiangqi Single State Test 1 (With Rules)
Tests all 7 piece types movement rules
"""

import random
from typing import List, Dict, Tuple, Optional


class XiangqiWithRuleGenerator:
    """Generate xiangqi rule following test cases for all piece types"""

    piece_types = ['rook', 'cannon', 'knight',
                   'bishop', 'advisor', 'king', 'pawn']
    N_TYPES = 7

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
        self.rows = list(range(10))

    def _square_to_coords(self, square: str) -> Tuple[int, int]:
        return ord(square[0]) - ord('a'), int(square[1])

    def _coords_to_square(self, col: int, row: int) -> Optional[str]:
        if 0 <= col < 9 and 0 <= row < 10:
            return chr(ord('a') + col) + str(row)
        return None

    def _random_square(self) -> str:
        return random.choice(self.cols) + str(random.choice(self.rows))

    def _piece_symbol(self, piece_type: str, color: str) -> str:
        symbols = {
            'king': 'K' if color == 'red' else 'k',
            'advisor': 'A' if color == 'red' else 'a',
            'bishop': 'B' if color == 'red' else 'b',
            'knight': 'N' if color == 'red' else 'n',
            'rook': 'R' if color == 'red' else 'r',
            'cannon': 'C' if color == 'red' else 'c',
            'pawn': 'P' if color == 'red' else 'p',
        }
        return symbols[piece_type]

    def _distribute_counts(self, n: int, num_subtypes: int) -> List[int]:
        if n <= 0:
            return [0] * num_subtypes
        base = n // num_subtypes
        remainder = n % num_subtypes
        counts = [base + (1 if i < remainder else 0)
                  for i in range(num_subtypes)]
        return counts

    # ============= ROOK =============
    def generate_rook_tests(self, n: int = 10) -> List[Dict]:
        cases = []
        counts = self._distribute_counts(n, 3)  # clear, blocked, invalid
        n_clear, n_blocked, n_invalid = counts

        generated = 0
        attempts = 0
        while generated < n_clear and attempts < n_clear * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            c, r = random.randint(0, 8), random.randint(0, 9)
            start = self._coords_to_square(c, r)
            if random.choice([True, False]):
                dist = random.randint(1, 5) * random.choice([-1, 1])
                target = self._coords_to_square(
                    c + dist, r) if 0 <= c + dist < 9 else None
            else:
                dist = random.randint(1, 6) * random.choice([-1, 1])
                target = self._coords_to_square(
                    c, r + dist) if 0 <= r + dist < 10 else None
            if target:
                cases.append({
                    "case_id": f"rook_clear_{generated+1}", "type": "rook", "subtype": "clear_path",
                    "pieces": {start: self._piece_symbol('rook', color)}, "squares": [target],
                    "question": f"Can this rook move to highlighted square?",
                    "expected": "yes", "reasoning": "Clear orthogonal path"
                })
                generated += 1

        # Blocked
        generated = 0
        attempts = 0
        while generated < n_blocked and attempts < n_blocked * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            c, r = random.randint(1, 7), random.randint(1, 8)
            start = self._coords_to_square(c, r)
            dist = random.randint(2, 4)
            if random.choice([True, False]):
                target = self._coords_to_square(c + dist, r)
                block = self._coords_to_square(c + dist // 2, r)
            else:
                target = self._coords_to_square(c, r + dist)
                block = self._coords_to_square(c, r + dist // 2)
            if target and block:
                cases.append({
                    "case_id": f"rook_blocked_{generated+1}", "type": "rook", "subtype": "blocked_path",
                    "pieces": {start: self._piece_symbol('rook', color), block: 'P'}, "squares": [target],
                    "question": f"Can this rook move to highlighted square?",
                    "expected": "no", "reasoning": f"Path blocked at {block}"
                })
                generated += 1

        # Invalid (diagonal)
        generated = 0
        attempts = 0
        while generated < n_invalid and attempts < n_invalid * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            c, r = random.randint(1, 7), random.randint(1, 8)
            start = self._coords_to_square(c, r)
            d = random.randint(1, 3)
            dc, dr = random.choice([(d, d), (-d, d), (d, -d), (-d, -d)])
            target = self._coords_to_square(c + dc, r + dr)
            if target:
                cases.append({
                    "case_id": f"rook_invalid_{generated+1}", "type": "rook", "subtype": "invalid_move",
                    "pieces": {start: self._piece_symbol('rook', color)}, "squares": [target],
                    "question": f"Can this rook move to highlighted square?",
                    "expected": "no", "reasoning": "Rook cannot move diagonally"
                })
                generated += 1

        return cases

    # ============= CANNON =============
    def generate_cannon_tests(self, n: int = 10) -> List[Dict]:
        cases = []
        counts = self._distribute_counts(n, 3)
        n_move, n_blocked, n_invalid = counts

        # Clear move
        generated = 0
        attempts = 0
        while generated < n_move and attempts < n_move * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            c, r = random.randint(0, 8), random.randint(0, 9)
            start = self._coords_to_square(c, r)
            dist = random.randint(1, 4) * random.choice([-1, 1])
            if random.choice([True, False]) and 0 <= c + dist < 9:
                target = self._coords_to_square(c + dist, r)
            elif 0 <= r + dist < 10:
                target = self._coords_to_square(c, r + dist)
            else:
                target = None
            if target:
                cases.append({
                    "case_id": f"cannon_move_{generated+1}", "type": "cannon", "subtype": "clear_move",
                    "pieces": {start: self._piece_symbol('cannon', color)}, "squares": [target],
                    "question": f"Can this cannon move to highlighted square?",
                    "expected": "yes", "reasoning": "Clear orthogonal path for movement"
                })
                generated += 1

        # Blocked movement
        generated = 0
        attempts = 0
        while generated < n_blocked and attempts < n_blocked * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            c, r = random.randint(1, 5), random.randint(1, 8)
            start = self._coords_to_square(c, r)
            target = self._coords_to_square(c + 3, r)
            block = self._coords_to_square(c + 1, r)
            if target and block:
                cases.append({
                    "case_id": f"cannon_blocked_{generated+1}", "type": "cannon", "subtype": "blocked_move",
                    "pieces": {start: self._piece_symbol('cannon', color), block: 'P'}, "squares": [target],
                    "question": f"Can this cannon move to highlighted square?",
                    "expected": "no", "reasoning": f"Movement blocked at {block}"
                })
                generated += 1

        # Invalid diagonal
        generated = 0
        attempts = 0
        while generated < n_invalid and attempts < n_invalid * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            c, r = random.randint(1, 7), random.randint(1, 8)
            start = self._coords_to_square(c, r)
            d = random.randint(1, 2)
            target = self._coords_to_square(c + d, r + d)
            if target:
                cases.append({
                    "case_id": f"cannon_invalid_{generated+1}", "type": "cannon", "subtype": "invalid_move",
                    "pieces": {start: self._piece_symbol('cannon', color)}, "squares": [target],
                    "question": f"Can this cannon move to highlighted square?",
                    "expected": "no", "reasoning": "Cannon cannot move diagonally"
                })
                generated += 1

        return cases

    # ============= KNIGHT =============
    def generate_knight_tests(self, n: int = 10) -> List[Dict]:
        cases = []
        counts = self._distribute_counts(n, 3)
        n_valid, n_blocked, n_invalid = counts

        knight_moves = [(1, 2, 0, 1), (1, -2, 0, -1), (-1, 2, 0, 1), (-1, -2, 0, -1),
                        (2, 1, 1, 0), (2, -1, 1, 0), (-2, 1, -1, 0), (-2, -1, -1, 0)]

        # Valid
        generated = 0
        attempts = 0
        while generated < n_valid and attempts < n_valid * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            c, r = random.randint(2, 6), random.randint(2, 7)
            start = self._coords_to_square(c, r)
            dc, dr, bc, br = random.choice(knight_moves)
            target = self._coords_to_square(c + dc, r + dr)
            if target:
                cases.append({
                    "case_id": f"knight_valid_{generated+1}", "type": "knight", "subtype": "valid_move",
                    "pieces": {start: self._piece_symbol('knight', color)}, "squares": [target],
                    "question": f"Can this knight move to highlighted square?",
                    "expected": "yes", "reasoning": "Valid L-shape move, leg clear"
                })
                generated += 1

        # Blocked
        generated = 0
        attempts = 0
        while generated < n_blocked and attempts < n_blocked * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            c, r = random.randint(2, 6), random.randint(2, 7)
            start = self._coords_to_square(c, r)
            dc, dr, bc, br = random.choice(knight_moves)
            target = self._coords_to_square(c + dc, r + dr)
            block = self._coords_to_square(c + bc, r + br)
            if target and block:
                cases.append({
                    "case_id": f"knight_blocked_{generated+1}", "type": "knight", "subtype": "blocked",
                    "pieces": {start: self._piece_symbol('knight', color), block: 'P'}, "squares": [target],
                    "question": f"Can this knight move to highlighted square?",
                    "expected": "no", "reasoning": f"Leg blocked at {block}"
                })
                generated += 1

        # Invalid pattern
        generated = 0
        attempts = 0
        while generated < n_invalid and attempts < n_invalid * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            c, r = random.randint(2, 6), random.randint(2, 7)
            start = self._coords_to_square(c, r)
            dc, dr = random.choice([(2, 0), (0, 2), (1, 1), (3, 1)])
            target = self._coords_to_square(c + dc, r + dr)
            if target:
                cases.append({
                    "case_id": f"knight_invalid_{generated+1}", "type": "knight", "subtype": "invalid_pattern",
                    "pieces": {start: self._piece_symbol('knight', color)}, "squares": [target],
                    "question": f"Can this knight move to highlighted square?",
                    "expected": "no", "reasoning": "Not a valid L-shape move"
                })
                generated += 1

        return cases

    # ============= BISHOP =============
    def generate_bishop_tests(self, n: int = 10) -> List[Dict]:
        cases = []
        counts = self._distribute_counts(n, 4)
        n_valid, n_blocked, n_river, n_invalid = counts

        # Valid
        generated = 0
        attempts = 0
        while generated < n_valid and attempts < n_valid * 30:
            attempts += 1
            color = random.choice(['red', 'black'])
            if color == 'red':
                c, r = random.randint(2, 6), random.randint(0, 2)
            else:
                c, r = random.randint(2, 6), random.randint(7, 9)
            start = self._coords_to_square(c, r)
            dc, dr = random.choice([(2, 2), (2, -2), (-2, 2), (-2, -2)])
            nr = r + dr
            if (color == 'red' and 0 <= nr <= 4) or (color == 'black' and 5 <= nr <= 9):
                target = self._coords_to_square(c + dc, nr)
                if target and 0 <= c + dc < 9:
                    cases.append({
                        "case_id": f"bishop_valid_{generated+1}", "type": "bishop", "subtype": "valid_move",
                        "pieces": {start: self._piece_symbol('bishop', color)}, "squares": [target],
                        "question": f"Can this bishop move to highlighted square?",
                        "expected": "yes", "reasoning": "Valid diagonal 2-step, eye clear"
                    })
                    generated += 1

        # Blocked
        generated = 0
        attempts = 0
        while generated < n_blocked and attempts < n_blocked * 30:
            attempts += 1
            color = random.choice(['red', 'black'])
            if color == 'red':
                c, r = random.randint(2, 6), random.randint(0, 2)
            else:
                c, r = random.randint(2, 6), random.randint(7, 9)
            start = self._coords_to_square(c, r)
            dc, dr = random.choice([(2, 2), (2, -2), (-2, 2), (-2, -2)])
            nr = r + dr
            if (color == 'red' and 0 <= nr <= 4) or (color == 'black' and 5 <= nr <= 9):
                target = self._coords_to_square(c + dc, nr)
                block = self._coords_to_square(c + dc // 2, r + dr // 2)
                if target and block and 0 <= c + dc < 9:
                    cases.append({
                        "case_id": f"bishop_blocked_{generated+1}", "type": "bishop", "subtype": "blocked",
                        "pieces": {start: self._piece_symbol('bishop', color), block: 'P'}, "squares": [target],
                        "question": f"Can this bishop move to highlighted square?",
                        "expected": "no", "reasoning": f"Eye blocked at {block}"
                    })
                    generated += 1

        # Cross river
        generated = 0
        attempts = 0
        while generated < n_river and attempts < n_river * 30:
            attempts += 1
            color = random.choice(['red', 'black'])
            if color == 'red':
                c, r = random.randint(2, 6), random.choice([3, 4])
                dr = 2
            else:
                c, r = random.randint(2, 6), random.choice([5, 6])
                dr = -2
            start = self._coords_to_square(c, r)
            dc = random.choice([2, -2])
            target = self._coords_to_square(c + dc, r + dr)
            if target and 0 <= c + dc < 9:
                cases.append({
                    "case_id": f"bishop_river_{generated+1}", "type": "bishop", "subtype": "cross_river",
                    "pieces": {start: self._piece_symbol('bishop', color)}, "squares": [target],
                    "question": f"Can this bishop move to highlighted square?",
                    "expected": "no", "reasoning": "Bishop cannot cross river"
                })
                generated += 1

        # Invalid pattern
        generated = 0
        attempts = 0
        while generated < n_invalid and attempts < n_invalid * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            c, r = random.randint(2, 6), random.randint(2, 7)
            start = self._coords_to_square(c, r)
            dc, dr = random.choice([(1, 1), (3, 3), (2, 0), (0, 2)])
            target = self._coords_to_square(c + dc, r + dr)
            if target:
                cases.append({
                    "case_id": f"bishop_invalid_{generated+1}", "type": "bishop", "subtype": "invalid_pattern",
                    "pieces": {start: self._piece_symbol('bishop', color)}, "squares": [target],
                    "question": f"Can this bishop move to highlighted square?",
                    "expected": "no", "reasoning": "Bishop must move exactly 2 steps diagonally"
                })
                generated += 1

        return cases

    # ============= ADVISOR =============
    def generate_advisor_tests(self, n: int = 10) -> List[Dict]:
        cases = []
        counts = self._distribute_counts(n, 3)
        n_valid, n_ortho, n_outside = counts

        def get_advisor_positions(color):
            if color == 'red':
                return [(3, 0), (5, 0), (4, 1), (3, 2), (5, 2)]
            return [(3, 7), (5, 7), (4, 8), (3, 9), (5, 9)]

        # Valid
        generated = 0
        attempts = 0
        while generated < n_valid and attempts < n_valid * 30:
            attempts += 1
            color = random.choice(['red', 'black'])
            positions = get_advisor_positions(color)
            c, r = random.choice(positions)
            start = self._coords_to_square(c, r)
            for dc, dr in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
                if (c + dc, r + dr) in positions:
                    target = self._coords_to_square(c + dc, r + dr)
                    cases.append({
                        "case_id": f"advisor_valid_{generated+1}", "type": "advisor", "subtype": "valid_move",
                        "pieces": {start: self._piece_symbol('advisor', color)}, "squares": [target],
                        "question": f"Can this advisor move to highlighted square?",
                        "expected": "yes", "reasoning": "Valid diagonal within palace"
                    })
                    generated += 1
                    break

        # Orthogonal (invalid)
        generated = 0
        attempts = 0
        while generated < n_ortho and attempts < n_ortho * 30:
            attempts += 1
            color = random.choice(['red', 'black'])
            positions = get_advisor_positions(color)
            c, r = random.choice(positions)
            start = self._coords_to_square(c, r)
            dc, dr = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            target = self._coords_to_square(c + dc, r + dr)
            if target:
                cases.append({
                    "case_id": f"advisor_ortho_{generated+1}", "type": "advisor", "subtype": "orthogonal",
                    "pieces": {start: self._piece_symbol('advisor', color)}, "squares": [target],
                    "question": f"Can this advisor move to highlighted square?",
                    "expected": "no", "reasoning": "Advisor can only move diagonally"
                })
                generated += 1

        # Outside palace
        generated = 0
        attempts = 0
        while generated < n_outside and attempts < n_outside * 30:
            attempts += 1
            color = random.choice(['red', 'black'])
            positions = get_advisor_positions(color)
            corners = [(3, 0), (5, 0), (3, 2), (5, 2)] if color == 'red' else [
                (3, 7), (5, 7), (3, 9), (5, 9)]
            c, r = random.choice(corners)
            start = self._coords_to_square(c, r)
            for dc, dr in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
                if (c + dc, r + dr) not in positions:
                    target = self._coords_to_square(c + dc, r + dr)
                    if target:
                        cases.append({
                            "case_id": f"advisor_outside_{generated+1}", "type": "advisor", "subtype": "outside_palace",
                            "pieces": {start: self._piece_symbol('advisor', color)}, "squares": [target],
                            "question": f"Can this advisor move to highlighted square?",
                            "expected": "no", "reasoning": "Advisor cannot leave palace"
                        })
                        generated += 1
                        break

        return cases

    # ============= KING =============
    def generate_king_tests(self, n: int = 10) -> List[Dict]:
        cases = []
        counts = self._distribute_counts(n, 3)
        n_valid, n_diag, n_outside = counts

        def get_palace(color):
            if color == 'red':
                return [(c, r) for c in range(3, 6) for r in range(0, 3)]
            return [(c, r) for c in range(3, 6) for r in range(7, 10)]

        # Valid
        generated = 0
        attempts = 0
        while generated < n_valid and attempts < n_valid * 30:
            attempts += 1
            color = random.choice(['red', 'black'])
            palace = get_palace(color)
            c, r = random.choice(palace)
            start = self._coords_to_square(c, r)
            for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if (c + dc, r + dr) in palace:
                    target = self._coords_to_square(c + dc, r + dr)
                    cases.append({
                        "case_id": f"king_valid_{generated+1}", "type": "king", "subtype": "valid_move",
                        "pieces": {start: self._piece_symbol('king', color)}, "squares": [target],
                        "question": f"Can this king move to highlighted square?",
                        "expected": "yes", "reasoning": "Valid orthogonal within palace"
                    })
                    generated += 1
                    break

        # Diagonal (invalid)
        generated = 0
        attempts = 0
        while generated < n_diag and attempts < n_diag * 30:
            attempts += 1
            color = random.choice(['red', 'black'])
            palace = get_palace(color)
            c, r = random.choice(palace)
            start = self._coords_to_square(c, r)
            dc, dr = random.choice([(1, 1), (-1, 1), (1, -1), (-1, -1)])
            target = self._coords_to_square(c + dc, r + dr)
            if target:
                cases.append({
                    "case_id": f"king_diag_{generated+1}", "type": "king", "subtype": "diagonal",
                    "pieces": {start: self._piece_symbol('king', color)}, "squares": [target],
                    "question": f"Can this king move to highlighted square?",
                    "expected": "no", "reasoning": "King can only move orthogonally"
                })
                generated += 1

        # Outside palace
        generated = 0
        attempts = 0
        while generated < n_outside and attempts < n_outside * 30:
            attempts += 1
            color = random.choice(['red', 'black'])
            palace = get_palace(color)
            edges = [(3, 0), (5, 0), (4, 0), (3, 2), (5, 2), (4, 2)] if color == 'red' else \
                    [(3, 7), (5, 7), (4, 7), (3, 9), (5, 9), (4, 9)]
            c, r = random.choice(edges)
            start = self._coords_to_square(c, r)
            for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                if (c + dc, r + dr) not in palace and 0 <= c + dc < 9 and 0 <= r + dr < 10:
                    target = self._coords_to_square(c + dc, r + dr)
                    cases.append({
                        "case_id": f"king_outside_{generated+1}", "type": "king", "subtype": "outside_palace",
                        "pieces": {start: self._piece_symbol('king', color)}, "squares": [target],
                        "question": f"Can this king move to highlighted square?",
                        "expected": "no", "reasoning": "King cannot leave palace"
                    })
                    generated += 1
                    break

        return cases

    # ============= PAWN =============
    def generate_pawn_tests(self, n: int = 10) -> List[Dict]:
        cases = []
        counts = self._distribute_counts(n, 3)
        n_valid, n_back, n_side = counts

        # Valid forward
        generated = 0
        attempts = 0
        while generated < n_valid and attempts < n_valid * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            if color == 'red':
                c, r = random.randint(0, 8), random.randint(3, 8)
                dr = 1
            else:
                c, r = random.randint(0, 8), random.randint(1, 6)
                dr = -1
            start = self._coords_to_square(c, r)
            target = self._coords_to_square(c, r + dr)
            if target:
                king_pos = 'e1' if color == 'red' else 'e8'
                cases.append({
                    "case_id": f"pawn_valid_{generated+1}", "type": "pawn", "subtype": "valid_forward",
                    "pieces": {
                        start: self._piece_symbol('pawn', color),
                        king_pos: self._piece_symbol('king', color)
                    },
                    "squares": [target],
                    "question": f"Can this pawn move to highlighted square?",
                    "expected": "yes", "reasoning": "Valid forward move"
                })
                generated += 1

        # Backward (invalid)
        generated = 0
        attempts = 0
        while generated < n_back and attempts < n_back * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            if color == 'red':
                c, r = random.randint(0, 8), random.randint(1, 9)
                dr = -1
            else:
                c, r = random.randint(0, 8), random.randint(0, 8)
                dr = 1
            start = self._coords_to_square(c, r)
            target = self._coords_to_square(c, r + dr)
            if target:
                king_pos = 'e1' if color == 'red' else 'e8'
                cases.append({
                    "case_id": f"pawn_back_{generated+1}", "type": "pawn", "subtype": "backward",
                    "pieces": {
                        start: self._piece_symbol('pawn', color),
                        king_pos: self._piece_symbol('king', color)
                    },
                    "squares": [target],
                    "question": f"Can this pawn move to highlighted square?",
                    "expected": "no", "reasoning": "Pawn cannot move backward"
                })
                generated += 1

        # Sideways before river (invalid)
        generated = 0
        attempts = 0
        while generated < n_side and attempts < n_side * 20:
            attempts += 1
            color = random.choice(['red', 'black'])
            if color == 'red':
                c, r = random.randint(1, 7), random.randint(0, 4)
            else:
                c, r = random.randint(1, 7), random.randint(5, 9)
            start = self._coords_to_square(c, r)
            dc = random.choice([-1, 1])
            target = self._coords_to_square(c + dc, r)
            if target:
                king_pos = 'e1' if color == 'red' else 'e8'
                cases.append({
                    "case_id": f"pawn_side_{generated+1}", "type": "pawn", "subtype": "sideways_own_side",
                    "pieces": {
                        start: self._piece_symbol('pawn', color),
                        king_pos: self._piece_symbol('king', color)
                    },
                    "squares": [target],
                    "question": f"Can this pawn move to highlighted square?",
                    "expected": "no", "reasoning": "Pawn cannot move sideways before crossing river"
                })
                generated += 1

        return cases

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """
        Generate comprehensive test suite for all 7 piece types.
        Cases are distributed proportionally across piece types.
        """
        all_cases = []

        cases_per_type = n_cases // self.N_TYPES
        remainder = n_cases % self.N_TYPES

        type_counts = {}
        for i, piece_type in enumerate(self.piece_types):
            type_counts[piece_type] = cases_per_type + \
                (1 if i < remainder else 0)

        print(
            f"Generating {n_cases} total cases across {self.N_TYPES} piece types...")
        print(f"Distribution: {type_counts}")

        print(f"Generating Rook tests ({type_counts['rook']})...")
        all_cases.extend(self.generate_rook_tests(type_counts['rook']))

        print(f"Generating Cannon tests ({type_counts['cannon']})...")
        all_cases.extend(self.generate_cannon_tests(type_counts['cannon']))

        print(f"Generating Knight tests ({type_counts['knight']})...")
        all_cases.extend(self.generate_knight_tests(type_counts['knight']))

        print(f"Generating Bishop tests ({type_counts['bishop']})...")
        all_cases.extend(self.generate_bishop_tests(type_counts['bishop']))

        print(f"Generating Advisor tests ({type_counts['advisor']})...")
        all_cases.extend(self.generate_advisor_tests(type_counts['advisor']))

        print(f"Generating King tests ({type_counts['king']})...")
        all_cases.extend(self.generate_king_tests(type_counts['king']))

        print(f"Generating Pawn tests ({type_counts['pawn']})...")
        all_cases.extend(self.generate_pawn_tests(type_counts['pawn']))

        print(f"\n✓ Total generated: {len(all_cases)} test cases")
        return all_cases
