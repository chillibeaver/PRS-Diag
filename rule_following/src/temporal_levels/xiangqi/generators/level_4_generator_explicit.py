"""
Xiangqi Level 4 Generator: Flying General Constraint (Explicit Mode)
Explicit version: Shows both before and after states, asks if the move is legal

Rule: The two Kings cannot face each other directly on the same file with no pieces between them.
If a piece is the only blocker between the two Kings, it cannot move to a position that would
expose the Kings to face each other (even if the move is otherwise legal).

Test cases:
1. Valid: Piece moves but another piece still blocks the Kings
2. Valid: Piece moves along the same file (still blocking)
3. Invalid: Piece is the only blocker and moves away, causing flying general
4. Pawn river crossing tests
"""

import random
from typing import List, Dict, Tuple, Optional, Set


class Level4Generator:
    """Generate Level 4 test cases - flying general constraint (explicit mode)"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
        self.rows = list(range(10))

        # Palace columns where Kings can be
        self.palace_cols = ['d', 'e', 'f']

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
            'king': 'K' if color == 'red' else 'k',
            'advisor': 'A' if color == 'red' else 'a',
            'bishop': 'B' if color == 'red' else 'b',
            'knight': 'N' if color == 'red' else 'n',
            'rook': 'R' if color == 'red' else 'r',
            'cannon': 'C' if color == 'red' else 'c',
            'pawn': 'P' if color == 'red' else 'p',
        }
        return symbols[piece_type]

    def _opposite_color(self, color: str) -> str:
        return 'black' if color == 'red' else 'red'

    def _get_squares_between(self, col: int, row1: int, row2: int) -> List[str]:
        """Get all squares between two rows on the same column (exclusive)"""
        min_row, max_row = min(row1, row2), max(row1, row2)
        squares = []
        for r in range(min_row + 1, max_row):
            sq = self._coords_to_square(col, r)
            if sq:
                squares.append(sq)
        return squares

    def _get_rook_moves(self, start: str, occupied: Set[str], same_col_ok: bool = False) -> List[str]:
        """Get valid rook moves, optionally excluding moves on same column"""
        col, row = self._square_to_coords(start)
        moves = []

        # Horizontal moves
        for c in range(9):
            if c != col:
                sq = self._coords_to_square(c, row)
                if sq and sq not in occupied:
                    clear = True
                    for cc in range(min(c, col) + 1, max(c, col)):
                        if self._coords_to_square(cc, row) in occupied:
                            clear = False
                            break
                    if clear:
                        moves.append(sq)

        # Vertical moves
        for r in range(10):
            if r != row:
                sq = self._coords_to_square(col, r)
                if sq and sq not in occupied:
                    clear = True
                    for rr in range(min(r, row) + 1, max(r, row)):
                        if self._coords_to_square(col, rr) in occupied:
                            clear = False
                            break
                    if clear:
                        if same_col_ok or True:
                            moves.append(sq)

        return moves

    def _get_cannon_moves(self, start: str, occupied: Set[str]) -> List[str]:
        """Get valid cannon moves (movement only, not capture)"""
        return self._get_rook_moves(start, occupied)

    def _get_knight_moves(self, start: str, occupied: Set[str]) -> List[str]:
        """Get valid knight moves with blocking check"""
        col, row = self._square_to_coords(start)
        moves = []

        knight_patterns = [
            (1, 2, 0, 1), (1, -2, 0, -1), (-1, 2, 0, 1), (-1, -2, 0, -1),
            (2, 1, 1, 0), (2, -1, 1, 0), (-2, 1, -1, 0), (-2, -1, -1, 0),
        ]

        for dc, dr, bdc, bdr in knight_patterns:
            target = self._coords_to_square(col + dc, row + dr)
            block = self._coords_to_square(col + bdc, row + bdr)
            if target and target not in occupied:
                if block and block not in occupied:
                    moves.append(target)

        return moves

    def _get_pawn_moves(self, start: str, color: str, occupied: Set[str]) -> List[str]:
        """Get valid pawn moves"""
        col, row = self._square_to_coords(start)
        moves = []

        if color == 'red':
            fwd = self._coords_to_square(col, row + 1)
            if fwd and fwd not in occupied:
                moves.append(fwd)
            if row >= 5:
                for dc in [-1, 1]:
                    side = self._coords_to_square(col + dc, row)
                    if side and side not in occupied:
                        moves.append(side)
        else:
            fwd = self._coords_to_square(col, row - 1)
            if fwd and fwd not in occupied:
                moves.append(fwd)
            if row <= 4:
                for dc in [-1, 1]:
                    side = self._coords_to_square(col + dc, row)
                    if side and side not in occupied:
                        moves.append(side)

        return moves

    # ==================== CASE GENERATION ====================

    def _generate_invalid_case(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: Single blocker moves away, causing flying general
        """
        king_col_char = random.choice(self.palace_cols)
        king_col = ord(king_col_char) - ord('a')

        red_king_row = random.randint(0, 2)
        black_king_row = random.randint(7, 9)

        red_king_sq = self._coords_to_square(king_col, red_king_row)
        black_king_sq = self._coords_to_square(king_col, black_king_row)

        between_squares = self._get_squares_between(
            king_col, red_king_row, black_king_row)
        if not between_squares:
            return None

        blocker_sq = random.choice(between_squares)
        blocker_col, blocker_row = self._square_to_coords(blocker_sq)

        blocker_color = random.choice(['red', 'black'])
        blocker_type = random.choice(['rook', 'cannon', 'pawn'])

        if blocker_type == 'pawn':
            if blocker_color == 'red' and blocker_row < 3:
                blocker_type = 'rook'
            elif blocker_color == 'black' and blocker_row > 6:
                blocker_type = 'rook'

        blocker_symbol = self._piece_symbol(blocker_type, blocker_color)

        pieces_before = {
            red_king_sq: 'K',
            black_king_sq: 'k',
            blocker_sq: blocker_symbol,
        }
        occupied = set(pieces_before.keys())

        if blocker_type == 'rook':
            all_moves = self._get_rook_moves(blocker_sq, occupied)
        elif blocker_type == 'cannon':
            all_moves = self._get_cannon_moves(blocker_sq, occupied)
        else:
            all_moves = self._get_pawn_moves(
                blocker_sq, blocker_color, occupied)

        leaving_moves = [m for m in all_moves if m[0] != king_col_char]

        if not leaving_moves:
            return None

        target = random.choice(leaving_moves)

        # State 2: after move (blocker moved away)
        pieces_after = {
            red_king_sq: 'K',
            black_king_sq: 'k',
            target: blocker_symbol,
        }

        return {
            "case_id": f"L4_flying_general_invalid_{case_num}",
            "type": "flying_general",
            "subtype": "single_blocker_leaves",
            "piece_type": blocker_type,
            "color": blocker_color,
            "states": [
                {"pieces": pieces_before, "squares": []},
                {"pieces": pieces_after, "squares": []}
            ],
            "question": "Is this a legal move according to Xiangqi rules?",
            "expected": "no",
            "reasoning": f"The {blocker_type.capitalize()} is the only piece between the two Kings. Moving away would cause Flying General (Kings facing each other), which is illegal."
        }

    def _generate_valid_same_column_case(self, case_num: int) -> Optional[Dict]:
        """
        Valid: Blocker moves along the same column (still blocking)
        """
        king_col_char = random.choice(self.palace_cols)
        king_col = ord(king_col_char) - ord('a')

        red_king_row = random.randint(0, 2)
        black_king_row = random.randint(7, 9)

        red_king_sq = self._coords_to_square(king_col, red_king_row)
        black_king_sq = self._coords_to_square(king_col, black_king_row)

        between_squares = self._get_squares_between(
            king_col, red_king_row, black_king_row)
        if len(between_squares) < 2:
            return None

        blocker_sq = random.choice(between_squares)
        blocker_color = random.choice(['red', 'black'])
        blocker_type = 'rook'

        blocker_symbol = self._piece_symbol(blocker_type, blocker_color)

        pieces_before = {
            red_king_sq: 'K',
            black_king_sq: 'k',
            blocker_sq: blocker_symbol,
        }
        occupied = set(pieces_before.keys())

        same_col_moves = []
        for sq in between_squares:
            if sq != blocker_sq and sq not in occupied:
                same_col_moves.append(sq)

        if not same_col_moves:
            return None

        target = random.choice(same_col_moves)

        pieces_after = {
            red_king_sq: 'K',
            black_king_sq: 'k',
            target: blocker_symbol,
        }

        return {
            "case_id": f"L4_flying_general_valid_same_col_{case_num}",
            "type": "flying_general",
            "subtype": "blocker_stays_on_column",
            "piece_type": blocker_type,
            "color": blocker_color,
            "states": [
                {"pieces": pieces_before, "squares": []},
                {"pieces": pieces_after, "squares": []}
            ],
            "question": "Is this a legal move according to Xiangqi rules?",
            "expected": "yes",
            "reasoning": f"The {blocker_type.capitalize()} remains on the same column after moving, still blocking the Kings from facing each other. Legal move."
        }

    def _generate_valid_multiple_blockers_case(self, case_num: int) -> Optional[Dict]:
        """
        Valid: Multiple blockers, one moves away but another still blocks
        """
        king_col_char = random.choice(self.palace_cols)
        king_col = ord(king_col_char) - ord('a')

        red_king_row = random.randint(0, 2)
        black_king_row = random.randint(7, 9)

        red_king_sq = self._coords_to_square(king_col, red_king_row)
        black_king_sq = self._coords_to_square(king_col, black_king_row)

        between_squares = self._get_squares_between(
            king_col, red_king_row, black_king_row)
        if len(between_squares) < 2:
            return None

        blocker_squares = random.sample(between_squares, 2)
        moving_blocker_sq = blocker_squares[0]
        staying_blocker_sq = blocker_squares[1]

        moving_color = random.choice(['red', 'black'])
        staying_color = random.choice(['red', 'black'])
        moving_type = random.choice(['rook', 'cannon'])
        staying_type = random.choice(['rook', 'cannon', 'pawn'])

        staying_row = self._square_to_coords(staying_blocker_sq)[1]
        if staying_type == 'pawn':
            if staying_color == 'red' and staying_row < 3:
                staying_type = 'cannon'
            elif staying_color == 'black' and staying_row > 6:
                staying_type = 'cannon'

        moving_symbol = self._piece_symbol(moving_type, moving_color)
        staying_symbol = self._piece_symbol(staying_type, staying_color)

        pieces_before = {
            red_king_sq: 'K',
            black_king_sq: 'k',
            moving_blocker_sq: moving_symbol,
            staying_blocker_sq: staying_symbol,
        }
        occupied = set(pieces_before.keys())

        if moving_type == 'rook':
            all_moves = self._get_rook_moves(moving_blocker_sq, occupied)
        else:
            all_moves = self._get_cannon_moves(moving_blocker_sq, occupied)

        leaving_moves = [m for m in all_moves if m[0] != king_col_char]

        if not leaving_moves:
            return None

        target = random.choice(leaving_moves)

        pieces_after = {
            red_king_sq: 'K',
            black_king_sq: 'k',
            target: moving_symbol,
            staying_blocker_sq: staying_symbol,
        }

        return {
            "case_id": f"L4_flying_general_valid_multi_{case_num}",
            "type": "flying_general",
            "subtype": "multiple_blockers",
            "piece_type": moving_type,
            "color": moving_color,
            "states": [
                {"pieces": pieces_before, "squares": []},
                {"pieces": pieces_after, "squares": []}
            ],
            "question": "Is this a legal move according to Xiangqi rules?",
            "expected": "yes",
            "reasoning": f"Although the {moving_type.capitalize()} moves away, another piece at {staying_blocker_sq} still blocks the Kings. No Flying General occurs. Legal move."
        }

    def _generate_pawn_crossed_river_case(self, case_num: int, is_valid: bool) -> Optional[Dict]:
        """
        Test pawn movement after crossing the river
        Valid: Pawn that has crossed river moves sideways
        Invalid: Pawn that has NOT crossed river tries to move sideways
        """
        red_king_col = random.choice([3, 4, 5])
        black_king_col = random.choice([3, 4, 5])
        red_king_row = random.randint(0, 2)
        black_king_row = random.randint(7, 9)

        red_king_sq = self._coords_to_square(red_king_col, red_king_row)
        black_king_sq = self._coords_to_square(black_king_col, black_king_row)

        if red_king_col == black_king_col:
            black_king_col = (black_king_col + 1) % 3 + 3
            black_king_sq = self._coords_to_square(
                black_king_col, black_king_row)

        pawn_color = random.choice(['red', 'black'])

        if is_valid:
            if pawn_color == 'red':
                pawn_row = random.randint(5, 8)
            else:
                pawn_row = random.randint(1, 4)
        else:
            if pawn_color == 'red':
                pawn_row = random.randint(3, 4)
            else:
                pawn_row = random.randint(5, 6)

        pawn_col = random.randint(1, 7)
        pawn_sq = self._coords_to_square(pawn_col, pawn_row)

        if pawn_sq in [red_king_sq, black_king_sq]:
            pawn_col = (pawn_col + 1) % 7 + 1
            pawn_sq = self._coords_to_square(pawn_col, pawn_row)

        direction = random.choice([-1, 1])
        target_col = pawn_col + direction
        target_sq = self._coords_to_square(target_col, pawn_row)

        if not target_sq or target_sq in [red_king_sq, black_king_sq]:
            return None

        pawn_symbol = self._piece_symbol('pawn', pawn_color)

        pieces_before = {
            red_king_sq: 'K',
            black_king_sq: 'k',
            pawn_sq: pawn_symbol,
        }

        pieces_after = {
            red_king_sq: 'K',
            black_king_sq: 'k',
            target_sq: pawn_symbol,
        }

        if is_valid:
            return {
                "case_id": f"L4_pawn_crossed_valid_{case_num}",
                "type": "pawn_river_crossing",
                "subtype": "crossed_river_sideways",
                "piece_type": "pawn",
                "color": pawn_color,
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []}
                ],
                "question": "Is this a legal move according to Xiangqi rules?",
                "expected": "yes",
                "reasoning": f"The Pawn has crossed the river (on opponent's side), so it can move sideways."
            }
        else:
            return {
                "case_id": f"L4_pawn_not_crossed_invalid_{case_num}",
                "type": "pawn_river_crossing",
                "subtype": "not_crossed_river_sideways",
                "piece_type": "pawn",
                "color": pawn_color,
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []}
                ],
                "question": "Is this a legal move according to Xiangqi rules?",
                "expected": "no",
                "reasoning": f"The Pawn has not crossed the river yet, so it can only move forward, not sideways."
            }

    def _generate_valid_not_blocking_case(self, case_num: int) -> Optional[Dict]:
        """
        Valid: Kings are not on the same column, piece can move freely
        """
        cols = random.sample(self.palace_cols, 2)
        red_king_col = ord(cols[0]) - ord('a')
        black_king_col = ord(cols[1]) - ord('a')

        red_king_row = random.randint(0, 2)
        black_king_row = random.randint(7, 9)

        red_king_sq = self._coords_to_square(red_king_col, red_king_row)
        black_king_sq = self._coords_to_square(black_king_col, black_king_row)

        piece_color = random.choice(['red', 'black'])
        piece_type = random.choice(['rook', 'cannon'])

        for _ in range(50):
            piece_col = random.randint(0, 8)
            piece_row = random.randint(3, 6)
            piece_sq = self._coords_to_square(piece_col, piece_row)

            if piece_sq not in [red_king_sq, black_king_sq]:
                break
        else:
            return None

        piece_symbol = self._piece_symbol(piece_type, piece_color)

        pieces_before = {
            red_king_sq: 'K',
            black_king_sq: 'k',
            piece_sq: piece_symbol,
        }
        occupied = set(pieces_before.keys())

        if piece_type == 'rook':
            all_moves = self._get_rook_moves(piece_sq, occupied)
        else:
            all_moves = self._get_cannon_moves(piece_sq, occupied)

        if not all_moves:
            return None

        target = random.choice(all_moves)

        pieces_after = {
            red_king_sq: 'K',
            black_king_sq: 'k',
            target: piece_symbol,
        }

        return {
            "case_id": f"L4_flying_general_valid_free_{case_num}",
            "type": "flying_general",
            "subtype": "kings_different_columns",
            "piece_type": piece_type,
            "color": piece_color,
            "states": [
                {"pieces": pieces_before, "squares": []},
                {"pieces": pieces_after, "squares": []}
            ],
            "question": "Is this a legal move according to Xiangqi rules?",
            "expected": "yes",
            "reasoning": f"The two Kings are not on the same column, so there is no Flying General concern. The {piece_type.capitalize()} can move freely."
        }

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """Generate all Level 4 test cases (explicit mode)"""
        all_cases = []

        # Distribution:
        # Flying general: 60% (24% invalid, 36% valid)
        # Pawn river crossing: 40% (20% invalid, 20% valid)

        n_flying_general = int(n_cases * 0.60)
        n_pawn_crossing = n_cases - n_flying_general

        n_fg_invalid = int(n_flying_general * 0.40)
        n_fg_valid = n_flying_general - n_fg_invalid
        n_same_col = n_fg_valid // 3
        n_multi_blocker = n_fg_valid // 3
        n_free = n_fg_valid - n_same_col - n_multi_blocker

        n_pawn_valid = n_pawn_crossing // 2
        n_pawn_invalid = n_pawn_crossing - n_pawn_valid

        print(f"Generating flying general - invalid cases...")
        count = 0
        for _ in range(n_fg_invalid * 10):
            if count >= n_fg_invalid:
                break
            case = self._generate_invalid_case(count + 1)
            if case:
                all_cases.append(case)
                count += 1
        print(f"  ✓ Generated {count} flying general invalid cases")

        print(f"Generating flying general - valid (same column)...")
        count = 0
        for _ in range(n_same_col * 10):
            if count >= n_same_col:
                break
            case = self._generate_valid_same_column_case(count + 1)
            if case:
                all_cases.append(case)
                count += 1
        print(f"  ✓ Generated {count} same-column cases")

        print(f"Generating flying general - valid (multiple blockers)...")
        count = 0
        for _ in range(n_multi_blocker * 10):
            if count >= n_multi_blocker:
                break
            case = self._generate_valid_multiple_blockers_case(count + 1)
            if case:
                all_cases.append(case)
                count += 1
        print(f"  ✓ Generated {count} multiple-blocker cases")

        print(f"Generating flying general - valid (different columns)...")
        count = 0
        for _ in range(n_free * 10):
            if count >= n_free:
                break
            case = self._generate_valid_not_blocking_case(count + 1)
            if case:
                all_cases.append(case)
                count += 1
        print(f"  ✓ Generated {count} free-move cases")

        print(f"Generating pawn crossing - valid (crossed river, sideways)...")
        count = 0
        for _ in range(n_pawn_valid * 10):
            if count >= n_pawn_valid:
                break
            case = self._generate_pawn_crossed_river_case(
                count + 1, is_valid=True)
            if case:
                all_cases.append(case)
                count += 1
        print(f"  ✓ Generated {count} pawn crossed river valid cases")

        print(f"Generating pawn crossing - invalid (not crossed, sideways)...")
        count = 0
        for _ in range(n_pawn_invalid * 10):
            if count >= n_pawn_invalid:
                break
            case = self._generate_pawn_crossed_river_case(
                count + 1, is_valid=False)
            if case:
                all_cases.append(case)
                count += 1
        print(f"  ✓ Generated {count} pawn not crossed invalid cases")

        random.shuffle(all_cases)
        print(
            f"\n✓ Total generated: {len(all_cases)} Level 4 explicit test cases")
        return all_cases
