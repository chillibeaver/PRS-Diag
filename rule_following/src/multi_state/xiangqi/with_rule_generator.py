"""
Xiangqi With-Rule Multi-State Test Generator (Revised)
Only includes tests with TRUE temporal dependency:
- Move Inference: What move was made from State 1 to State 2?
- Move Legality: Is the transition from State 1 to State 2 legal?
- Perpetual Check: 6-state check sequence
- Perpetual Chase: 6-state chase sequence
"""

import random
from typing import List, Dict, Tuple, Optional


class XiangqiWithRuleGenerator:
    """Generate Xiangqi rule-based multi-state test cases with true temporal dependency"""

    PERPETUAL_RULES = """Note: In Xiangqi, Perpetual Check is illegal after 3 consecutive checks."""

    ANSWER_FORMAT = """- Answer 'yes' if the answer is affirmative
- Answer 'no' if the answer is negative
- Answer 'unknown' if you cannot determine"""

    PIECE_NAMES = {
        'K': 'Red King', 'k': 'Black King',
        'A': 'Red Advisor', 'a': 'Black Advisor',
        'B': 'Red Bishop', 'b': 'Black Bishop',
        'N': 'Red Knight', 'n': 'Black Knight',
        'R': 'Red Rook', 'r': 'Black Rook',
        'C': 'Red Cannon', 'c': 'Black Cannon',
        'P': 'Red Pawn', 'p': 'Black Pawn',
    }

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
        self.rows = list(range(10))
        self.palace_cols = ['d', 'e', 'f']
        self.palace_col_indices = [3, 4, 5]

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

    def _get_piece_name(self, symbol: str) -> str:
        return self.PIECE_NAMES.get(symbol, 'Unknown')

    def _get_squares_between(self, col: int, row1: int, row2: int) -> List[str]:
        """Get all squares between two rows on the same column (exclusive)"""
        min_row, max_row = min(row1, row2), max(row1, row2)
        squares = []
        for r in range(min_row + 1, max_row):
            sq = self._coords_to_square(col, r)
            if sq:
                squares.append(sq)
        return squares

    def _distribute_counts(self, total: int, n_slots: int) -> List[int]:
        """Distribute total count as evenly as possible into n_slots"""
        base = total // n_slots
        remainder = total % n_slots
        return [base + (1 if i < remainder else 0) for i in range(n_slots)]

    # ============= Type 1: Move Legality =============

    def generate_move_legality_tests(self, n_cases: int = 10) -> List[Dict]:
        """Generate move legality tests - must understand State 1 to judge if transition is legal"""
        cases = []
        subtypes = [
            ('knight_blocked', self._gen_move_legality_knight_blocked),
            ('knight_legal', self._gen_move_legality_knight_legal),
            ('bishop_blocked', self._gen_move_legality_bishop_blocked),
            ('bishop_legal', self._gen_move_legality_bishop_legal),
            ('cannon_capture_valid', self._gen_move_legality_cannon_valid),
            ('cannon_capture_invalid', self._gen_move_legality_cannon_invalid),
            ('flying_general_violation', self._gen_move_legality_flying_general),
            ('flying_general_safe', self._gen_move_legality_no_flying_general),
            ('flying_general_same_col',
             self._gen_move_legality_flying_general_same_col),
            ('flying_general_diff_col',
             self._gen_move_legality_flying_general_diff_col),
            ('rook_path_blocked', self._gen_move_legality_rook_blocked),
            ('rook_path_clear', self._gen_move_legality_rook_clear),
        ]

        # Distribute n_cases evenly among subtypes
        counts = self._distribute_counts(n_cases, len(subtypes))

        case_idx = 1
        for i, (subtype_name, method) in enumerate(subtypes):
            count = counts[i]
            for _ in range(count):
                case = method(case_idx)
                if case:
                    cases.append(case)
                    case_idx += 1

        return cases

    def _gen_move_legality_knight_blocked(self, case_num: int) -> Optional[Dict]:
        """Knight move is illegal because leg is blocked in State 1"""
        color = random.choice(['red', 'black'])
        for _ in range(50):
            knight_col = random.randint(1, 7)
            knight_row = random.randint(1, 8)
            knight_sq = self._coords_to_square(knight_col, knight_row)

            # Knight moves: (dc, dr, block_dc, block_dr)
            moves = [
                (1, 2, 0, 1), (2, 1, 1, 0), (-1, 2, 0, 1), (-2, 1, -1, 0),
                (1, -2, 0, -1), (2, -1, 1, 0), (-1, -2, 0, -1), (-2, -1, -1, 0)
            ]
            dc, dr, bdc, bdr = random.choice(moves)

            target_sq = self._coords_to_square(
                knight_col + dc, knight_row + dr)
            block_sq = self._coords_to_square(
                knight_col + bdc, knight_row + bdr)

            if not target_sq or not block_sq:
                continue

            blocker_symbol = self._piece_symbol(
                'pawn', random.choice(['red', 'black']))
            knight_symbol = self._piece_symbol('knight', color)

            pieces_before = {knight_sq: knight_symbol,
                             block_sq: blocker_symbol}
            pieces_after = {target_sq: knight_symbol, block_sq: blocker_symbol}

            return {
                "case_id": f"move_legality_knight_blocked_{case_num}",
                "type": "move_legality",
                "subtype": "knight_blocked",
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []},
                ],
                "question": f"Is the transition from State 1 to State 2 a legal move?\n{self.ANSWER_FORMAT}",
                "expected": "no",
                "reasoning": f"Knight attempts {knight_sq}→{target_sq}, but piece at {block_sq} blocks the knight's leg."
            }
        return None

    def _gen_move_legality_knight_legal(self, case_num: int) -> Optional[Dict]:
        """Knight move is legal - leg is clear"""
        color = random.choice(['red', 'black'])
        for _ in range(50):
            knight_col = random.randint(1, 7)
            knight_row = random.randint(1, 8)
            knight_sq = self._coords_to_square(knight_col, knight_row)

            moves = [
                (1, 2, 0, 1), (2, 1, 1, 0), (-1, 2, 0, 1), (-2, 1, -1, 0),
                (1, -2, 0, -1), (2, -1, 1, 0), (-1, -2, 0, -1), (-2, -1, -1, 0)
            ]
            dc, dr, bdc, bdr = random.choice(moves)

            target_sq = self._coords_to_square(
                knight_col + dc, knight_row + dr)
            block_sq = self._coords_to_square(
                knight_col + bdc, knight_row + bdr)

            if not target_sq or not block_sq:
                continue

            # Put blocker somewhere else (not blocking)
            other_col = (knight_col + bdc + 2) % 9
            other_sq = self._coords_to_square(other_col, knight_row + bdr)
            if not other_sq or other_sq == knight_sq or other_sq == target_sq:
                continue

            blocker_symbol = self._piece_symbol(
                'pawn', random.choice(['red', 'black']))
            knight_symbol = self._piece_symbol('knight', color)

            pieces_before = {knight_sq: knight_symbol,
                             other_sq: blocker_symbol}
            pieces_after = {target_sq: knight_symbol, other_sq: blocker_symbol}

            return {
                "case_id": f"move_legality_knight_legal_{case_num}",
                "type": "move_legality",
                "subtype": "knight_legal",
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []},
                ],
                "question": f"Is the transition from State 1 to State 2 a legal move?\n{self.ANSWER_FORMAT}",
                "expected": "yes",
                "reasoning": f"Knight moves {knight_sq}→{target_sq}. The leg position {block_sq} is clear."
            }
        return None

    def _gen_move_legality_bishop_blocked(self, case_num: int) -> Optional[Dict]:
        """Bishop move is illegal - eye is blocked"""
        color = random.choice(['red', 'black'])
        for _ in range(50):
            if color == 'red':
                valid_starts = [(2, 0), (6, 0), (2, 4),
                                (6, 4), (0, 2), (4, 2), (8, 2)]
                valid_rows = range(0, 5)
            else:
                valid_starts = [(2, 9), (6, 9), (2, 5),
                                (6, 5), (0, 7), (4, 7), (8, 7)]
                valid_rows = range(5, 10)

            bishop_col, bishop_row = random.choice(valid_starts)
            bishop_sq = self._coords_to_square(bishop_col, bishop_row)

            moves = [(2, 2, 1, 1), (2, -2, 1, -1),
                     (-2, 2, -1, 1), (-2, -2, -1, -1)]
            dc, dr, bdc, bdr = random.choice(moves)

            target_col, target_row = bishop_col + dc, bishop_row + dr
            block_col, block_row = bishop_col + bdc, bishop_row + bdr

            if not (0 <= target_col <= 8) or target_row not in valid_rows:
                continue

            target_sq = self._coords_to_square(target_col, target_row)
            block_sq = self._coords_to_square(block_col, block_row)

            if not target_sq or not block_sq:
                continue

            blocker_symbol = self._piece_symbol(
                'pawn', random.choice(['red', 'black']))
            bishop_symbol = self._piece_symbol('bishop', color)

            pieces_before = {bishop_sq: bishop_symbol,
                             block_sq: blocker_symbol}
            pieces_after = {target_sq: bishop_symbol, block_sq: blocker_symbol}

            return {
                "case_id": f"move_legality_bishop_blocked_{case_num}",
                "type": "move_legality",
                "subtype": "bishop_blocked",
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []},
                ],
                "question": f"Is the transition from State 1 to State 2 a legal move?\n{self.ANSWER_FORMAT}",
                "expected": "no",
                "reasoning": f"Bishop attempts {bishop_sq}→{target_sq}, but piece at {block_sq} blocks the bishop's eye."
            }
        return None

    def _gen_move_legality_bishop_legal(self, case_num: int) -> Optional[Dict]:
        """Bishop move is legal - eye is clear"""
        color = random.choice(['red', 'black'])
        for _ in range(50):
            if color == 'red':
                valid_starts = [(2, 0), (6, 0), (2, 4),
                                (6, 4), (0, 2), (4, 2), (8, 2)]
                valid_rows = range(0, 5)
            else:
                valid_starts = [(2, 9), (6, 9), (2, 5),
                                (6, 5), (0, 7), (4, 7), (8, 7)]
                valid_rows = range(5, 10)

            bishop_col, bishop_row = random.choice(valid_starts)
            bishop_sq = self._coords_to_square(bishop_col, bishop_row)

            moves = [(2, 2, 1, 1), (2, -2, 1, -1),
                     (-2, 2, -1, 1), (-2, -2, -1, -1)]
            dc, dr, bdc, bdr = random.choice(moves)

            target_col, target_row = bishop_col + dc, bishop_row + dr
            block_col, block_row = bishop_col + bdc, bishop_row + bdr

            if not (0 <= target_col <= 8) or target_row not in valid_rows:
                continue

            target_sq = self._coords_to_square(target_col, target_row)
            block_sq = self._coords_to_square(block_col, block_row)

            if not target_sq or not block_sq:
                continue

            bishop_symbol = self._piece_symbol('bishop', color)
            pieces_before = {bishop_sq: bishop_symbol}
            pieces_after = {target_sq: bishop_symbol}

            return {
                "case_id": f"move_legality_bishop_legal_{case_num}",
                "type": "move_legality",
                "subtype": "bishop_legal",
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []},
                ],
                "question": f"Is the transition from State 1 to State 2 a legal move?\n{self.ANSWER_FORMAT}",
                "expected": "yes",
                "reasoning": f"Bishop moves {bishop_sq}→{target_sq}. The eye position {block_sq} is clear."
            }
        return None

    def _gen_move_legality_cannon_valid(self, case_num: int) -> Optional[Dict]:
        """Cannon capture is valid - exactly one screen piece"""
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)

        for _ in range(50):
            cannon_col = random.randint(0, 4)
            cannon_row = random.randint(2, 7)
            cannon_sq = self._coords_to_square(cannon_col, cannon_row)

            screen_col = cannon_col + random.randint(2, 3)
            target_col = screen_col + random.randint(2, 3)

            if target_col > 8:
                continue

            screen_sq = self._coords_to_square(screen_col, cannon_row)
            target_sq = self._coords_to_square(target_col, cannon_row)

            cannon_symbol = self._piece_symbol('cannon', color)
            screen_symbol = self._piece_symbol(
                'pawn', random.choice(['red', 'black']))
            target_symbol = self._piece_symbol('rook', enemy_color)

            pieces_before = {cannon_sq: cannon_symbol,
                             screen_sq: screen_symbol, target_sq: target_symbol}
            pieces_after = {target_sq: cannon_symbol, screen_sq: screen_symbol}

            return {
                "case_id": f"move_legality_cannon_valid_{case_num}",
                "type": "move_legality",
                "subtype": "cannon_capture_valid",
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []},
                ],
                "question": f"Is the transition from State 1 to State 2 a legal move?\n{self.ANSWER_FORMAT}",
                "expected": "yes",
                "reasoning": f"Cannon captures {cannon_sq}→{target_sq} by jumping over screen at {screen_sq}. Legal."
            }
        return None

    def _gen_move_legality_cannon_invalid(self, case_num: int) -> Optional[Dict]:
        """Cannon capture is invalid - no screen piece"""
        color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(color)

        for _ in range(50):
            cannon_col = random.randint(0, 4)
            cannon_row = random.randint(2, 7)
            cannon_sq = self._coords_to_square(cannon_col, cannon_row)

            target_col = cannon_col + random.randint(3, 5)
            if target_col > 8:
                continue

            target_sq = self._coords_to_square(target_col, cannon_row)

            cannon_symbol = self._piece_symbol('cannon', color)
            target_symbol = self._piece_symbol('rook', enemy_color)

            pieces_before = {cannon_sq: cannon_symbol,
                             target_sq: target_symbol}
            pieces_after = {target_sq: cannon_symbol}

            return {
                "case_id": f"move_legality_cannon_invalid_{case_num}",
                "type": "move_legality",
                "subtype": "cannon_capture_invalid",
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []},
                ],
                "question": f"Is the transition from State 1 to State 2 a legal move?\n{self.ANSWER_FORMAT}",
                "expected": "no",
                "reasoning": f"Cannon attempts capture {cannon_sq}→{target_sq} but has no screen piece to jump over."
            }
        return None

    def _gen_move_legality_flying_general(self, case_num: int) -> Optional[Dict]:
        """Move causes Flying General - illegal"""
        for _ in range(50):
            king_col = random.choice(self.palace_col_indices)
            red_king_row = random.randint(0, 2)
            black_king_row = random.randint(7, 9)

            red_king_sq = self._coords_to_square(king_col, red_king_row)
            black_king_sq = self._coords_to_square(king_col, black_king_row)

            between = self._get_squares_between(
                king_col, red_king_row, black_king_row)
            if not between:
                continue

            blocker_sq = random.choice(between)
            blocker_row = self._square_to_coords(blocker_sq)[1]
            blocker_color = random.choice(['red', 'black'])
            blocker_symbol = self._piece_symbol('rook', blocker_color)

            new_col = random.choice([c for c in range(9) if c != king_col])
            new_sq = self._coords_to_square(new_col, blocker_row)

            pieces_before = {red_king_sq: 'K',
                             black_king_sq: 'k', blocker_sq: blocker_symbol}
            pieces_after = {red_king_sq: 'K',
                            black_king_sq: 'k', new_sq: blocker_symbol}

            return {
                "case_id": f"move_legality_flying_general_{case_num}",
                "type": "move_legality",
                "subtype": "flying_general_violation",
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []},
                ],
                "question": f"Is the transition from State 1 to State 2 a legal move?\n{self.ANSWER_FORMAT}",
                "expected": "no",
                "reasoning": f"Moving {blocker_sq}→{new_sq} exposes Kings facing each other (Flying General)."
            }
        return None

    def _gen_move_legality_no_flying_general(self, case_num: int) -> Optional[Dict]:
        """Move doesn't cause Flying General - another piece still blocks"""
        for _ in range(50):
            king_col = random.choice(self.palace_col_indices)
            red_king_row = random.randint(0, 2)
            black_king_row = random.randint(7, 9)

            red_king_sq = self._coords_to_square(king_col, red_king_row)
            black_king_sq = self._coords_to_square(king_col, black_king_row)

            between = self._get_squares_between(
                king_col, red_king_row, black_king_row)
            if len(between) < 2:
                continue

            blockers = random.sample(between, 2)
            moving_sq, staying_sq = blockers[0], blockers[1]
            moving_row = self._square_to_coords(moving_sq)[1]

            moving_symbol = self._piece_symbol(
                'rook', random.choice(['red', 'black']))
            staying_symbol = self._piece_symbol(
                'cannon', random.choice(['red', 'black']))

            new_col = random.choice([c for c in range(9) if c != king_col])
            new_sq = self._coords_to_square(new_col, moving_row)

            pieces_before = {red_king_sq: 'K', black_king_sq: 'k',
                             moving_sq: moving_symbol, staying_sq: staying_symbol}
            pieces_after = {red_king_sq: 'K', black_king_sq: 'k',
                            new_sq: moving_symbol, staying_sq: staying_symbol}

            return {
                "case_id": f"move_legality_no_flying_general_{case_num}",
                "type": "move_legality",
                "subtype": "flying_general_safe",
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []},
                ],
                "question": f"Is the transition from State 1 to State 2 a legal move?\n{self.ANSWER_FORMAT}",
                "expected": "yes",
                "reasoning": f"Move {moving_sq}→{new_sq} is legal. Piece at {staying_sq} still blocks Kings."
            }
        return None

    def _gen_move_legality_flying_general_same_col(self, case_num: int) -> Optional[Dict]:
        """Blocker moves along same column - still blocking, legal"""
        for _ in range(50):
            king_col = random.choice(self.palace_col_indices)
            red_king_row = random.randint(0, 2)
            black_king_row = random.randint(7, 9)

            red_king_sq = self._coords_to_square(king_col, red_king_row)
            black_king_sq = self._coords_to_square(king_col, black_king_row)

            between = self._get_squares_between(
                king_col, red_king_row, black_king_row)
            if len(between) < 2:
                continue

            blocker_sq = random.choice(between)
            blocker_color = random.choice(['red', 'black'])
            blocker_symbol = self._piece_symbol('rook', blocker_color)

            # Find another square on same column (still between kings)
            same_col_targets = [sq for sq in between if sq != blocker_sq]
            if not same_col_targets:
                continue

            target_sq = random.choice(same_col_targets)

            pieces_before = {red_king_sq: 'K',
                             black_king_sq: 'k', blocker_sq: blocker_symbol}
            pieces_after = {red_king_sq: 'K',
                            black_king_sq: 'k', target_sq: blocker_symbol}

            return {
                "case_id": f"move_legality_flying_general_same_col_{case_num}",
                "type": "move_legality",
                "subtype": "flying_general_same_col",
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []},
                ],
                "question": f"Is the transition from State 1 to State 2 a legal move?\n{self.ANSWER_FORMAT}",
                "expected": "yes",
                "reasoning": f"Rook moves {blocker_sq}→{target_sq} along same column, still blocking Kings. Legal."
            }
        return None

    def _gen_move_legality_flying_general_diff_col(self, case_num: int) -> Optional[Dict]:
        """Kings on different columns - piece can move freely, legal"""
        for _ in range(50):
            # Put kings on different columns
            king_cols = random.sample(self.palace_col_indices, 2)
            red_king_col, black_king_col = king_cols[0], king_cols[1]

            red_king_row = random.randint(0, 2)
            black_king_row = random.randint(7, 9)

            red_king_sq = self._coords_to_square(red_king_col, red_king_row)
            black_king_sq = self._coords_to_square(
                black_king_col, black_king_row)

            # Place a piece anywhere
            piece_col = random.randint(0, 8)
            piece_row = random.randint(3, 6)
            piece_sq = self._coords_to_square(piece_col, piece_row)

            if piece_sq in [red_king_sq, black_king_sq]:
                continue

            piece_color = random.choice(['red', 'black'])
            piece_symbol = self._piece_symbol('rook', piece_color)

            # Move to any valid square
            new_col = random.randint(0, 8)
            new_row = piece_row  # horizontal move
            new_sq = self._coords_to_square(new_col, new_row)

            if new_sq == piece_sq or new_sq in [red_king_sq, black_king_sq]:
                continue

            pieces_before = {red_king_sq: 'K',
                             black_king_sq: 'k', piece_sq: piece_symbol}
            pieces_after = {red_king_sq: 'K',
                            black_king_sq: 'k', new_sq: piece_symbol}

            return {
                "case_id": f"move_legality_flying_general_diff_col_{case_num}",
                "type": "move_legality",
                "subtype": "flying_general_diff_col",
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []},
                ],
                "question": f"Is the transition from State 1 to State 2 a legal move?\n{self.ANSWER_FORMAT}",
                "expected": "yes",
                "reasoning": f"Kings are on different columns ({self.cols[red_king_col]} and {self.cols[black_king_col]}), no Flying General concern. Legal."
            }
        return None

    def _gen_move_legality_rook_blocked(self, case_num: int) -> Optional[Dict]:
        """Rook move is illegal - path is blocked"""
        color = random.choice(['red', 'black'])
        for _ in range(50):
            rook_col = random.randint(0, 4)
            rook_row = random.randint(2, 7)
            rook_sq = self._coords_to_square(rook_col, rook_row)

            target_col = rook_col + random.randint(3, 5)
            if target_col > 8:
                continue

            block_col = rook_col + random.randint(1, 2)
            target_sq = self._coords_to_square(target_col, rook_row)
            block_sq = self._coords_to_square(block_col, rook_row)

            rook_symbol = self._piece_symbol('rook', color)
            blocker_symbol = self._piece_symbol(
                'pawn', random.choice(['red', 'black']))

            pieces_before = {rook_sq: rook_symbol, block_sq: blocker_symbol}
            pieces_after = {target_sq: rook_symbol, block_sq: blocker_symbol}

            return {
                "case_id": f"move_legality_rook_blocked_{case_num}",
                "type": "move_legality",
                "subtype": "rook_path_blocked",
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []},
                ],
                "question": f"Is the transition from State 1 to State 2 a legal move?\n{self.ANSWER_FORMAT}",
                "expected": "no",
                "reasoning": f"Rook attempts {rook_sq}→{target_sq}, but piece at {block_sq} blocks the path."
            }
        return None

    def _gen_move_legality_rook_clear(self, case_num: int) -> Optional[Dict]:
        """Rook move is legal - path is clear"""
        color = random.choice(['red', 'black'])
        for _ in range(50):
            rook_col = random.randint(0, 4)
            rook_row = random.randint(2, 7)
            rook_sq = self._coords_to_square(rook_col, rook_row)

            target_col = rook_col + random.randint(2, 4)
            if target_col > 8:
                continue

            target_sq = self._coords_to_square(target_col, rook_row)
            rook_symbol = self._piece_symbol('rook', color)

            # Add piece that doesn't block
            other_sq = self._coords_to_square(rook_col, rook_row + 1)
            if not other_sq:
                continue
            other_symbol = self._piece_symbol(
                'pawn', random.choice(['red', 'black']))

            pieces_before = {rook_sq: rook_symbol, other_sq: other_symbol}
            pieces_after = {target_sq: rook_symbol, other_sq: other_symbol}

            return {
                "case_id": f"move_legality_rook_clear_{case_num}",
                "type": "move_legality",
                "subtype": "rook_path_clear",
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []},
                ],
                "question": f"Is the transition from State 1 to State 2 a legal move?\n{self.ANSWER_FORMAT}",
                "expected": "yes",
                "reasoning": f"Rook moves {rook_sq}→{target_sq}. Path is clear."
            }
        return None

    # ============= Type 2: Perpetual Check =============

    def generate_perpetual_check_tests(self, n_cases: int = 10) -> List[Dict]:
        """Generate perpetual check tests (6 states) - requires full history"""
        cases = []

        # Distribute n_cases between violation (no) and broken (yes)
        # We try to keep it 50/50
        n_violation = n_cases // 2
        n_broken = n_cases - n_violation

        for i in range(n_violation):
            case = self._generate_perpetual_check_violation(i + 1)
            if case:
                cases.append(case)

        for i in range(n_broken):
            case = self._generate_perpetual_check_broken(i + 1)
            if case:
                cases.append(case)

        return cases

    def _generate_perpetual_check_violation(self, case_num: int) -> Optional[Dict]:
        """Rook checks King 3 times, 4th would be perpetual check"""
        attacker_color = random.choice(['red', 'black'])
        defender_color = self._opposite_color(attacker_color)

        for _ in range(100):
            king_col = random.choice(self.palace_col_indices)
            if defender_color == 'red':
                king_row_a, king_row_b = 0, 1
            else:
                king_row_a, king_row_b = 9, 8

            king_sq_a = self._coords_to_square(king_col, king_row_a)
            king_sq_b = self._coords_to_square(king_col, king_row_b)

            att_col = random.choice([c for c in range(9) if c != king_col])
            att_sq_a = self._coords_to_square(att_col, king_row_a)
            att_sq_b = self._coords_to_square(att_col, king_row_b)

            if attacker_color == 'red':
                att_king_sq = self._coords_to_square(4, 1)
            else:
                att_king_sq = self._coords_to_square(4, 8)

            all_sqs = {king_sq_a, king_sq_b, att_sq_a, att_sq_b, att_king_sq}
            if len(all_sqs) < 5:
                continue

            att_symbol = self._piece_symbol('rook', attacker_color)
            def_king_symbol = self._piece_symbol('king', defender_color)
            base = {att_king_sq: self._piece_symbol('king', attacker_color)}

            # 6 states showing the check pattern
            states = [
                {"pieces": {**base, att_sq_a: att_symbol,
                            king_sq_a: def_king_symbol}, "squares": []},  # Check 1
                {"pieces": {**base, att_sq_a: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},  # King escapes
                {"pieces": {**base, att_sq_b: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},  # Check 2
                {"pieces": {**base, att_sq_b: att_symbol,
                            king_sq_a: def_king_symbol}, "squares": []},  # King escapes
                {"pieces": {**base, att_sq_a: att_symbol,
                            king_sq_a: def_king_symbol}, "squares": []},  # Check 3
                {"pieces": {**base, att_sq_a: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},  # King escapes
            ]

            return {
                "case_id": f"perpetual_check_violation_{case_num}",
                "type": "perpetual_check",
                "subtype": "violation",
                "states": states,
                "question": f"{self.PERPETUAL_RULES}\nCan the Rook move to {att_sq_b}?\n{self.ANSWER_FORMAT}",
                "expected": "no",
                "reasoning": "The Rook has already given check 3 times. A 4th check would be perpetual check (illegal)."
            }
        return None

    def _generate_perpetual_check_broken(self, case_num: int) -> Optional[Dict]:
        """Check pattern was broken, checking again is legal"""
        attacker_color = random.choice(['red', 'black'])
        defender_color = self._opposite_color(attacker_color)

        for _ in range(100):
            king_col = random.choice(self.palace_col_indices)
            if defender_color == 'red':
                king_row_a, king_row_b = 0, 1
            else:
                king_row_a, king_row_b = 9, 8

            king_sq_a = self._coords_to_square(king_col, king_row_a)
            king_sq_b = self._coords_to_square(king_col, king_row_b)

            att_col = random.choice([c for c in range(9) if c != king_col])
            att_sq_a = self._coords_to_square(att_col, king_row_a)
            att_sq_b = self._coords_to_square(att_col, king_row_b)
            att_sq_c = self._coords_to_square(
                att_col, 5)  # Non-checking position

            if attacker_color == 'red':
                att_king_sq = self._coords_to_square(4, 0)
            else:
                att_king_sq = self._coords_to_square(4, 9)

            all_sqs = {king_sq_a, king_sq_b, att_sq_a,
                       att_sq_b, att_sq_c, att_king_sq}
            if len(all_sqs) < 6:
                continue

            att_symbol = self._piece_symbol('rook', attacker_color)
            def_king_symbol = self._piece_symbol('king', defender_color)
            base = {att_king_sq: self._piece_symbol('king', attacker_color)}

            states = [
                {"pieces": {**base, att_sq_a: att_symbol,
                            king_sq_a: def_king_symbol}, "squares": []},  # Check 1
                {"pieces": {**base, att_sq_a: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},
                {"pieces": {**base, att_sq_b: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},  # Check 2
                {"pieces": {**base, att_sq_b: att_symbol,
                            king_sq_a: def_king_symbol}, "squares": []},
                {"pieces": {**base, att_sq_c: att_symbol,
                            king_sq_a: def_king_symbol}, "squares": []},  # Pattern broken!
                {"pieces": {**base, att_sq_c: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},
            ]

            return {
                "case_id": f"perpetual_check_broken_{case_num}",
                "type": "perpetual_check",
                "subtype": "pattern_broken",
                "states": states,
                "question": f"{self.PERPETUAL_RULES}\nCan the Rook move to {att_sq_b}?\n{self.ANSWER_FORMAT}",
                "expected": "yes",
                "reasoning": f"Pattern was broken when Rook moved to {att_sq_c} (not a check). This would be the 3rd check which is still legal."
            }
        return None

    # ============= Helper Methods =============

    def _gen_rook_move(self) -> Optional[Tuple[str, str]]:
        """Generate a valid rook move (horizontal or vertical)"""
        col = random.randint(0, 8)
        row = random.randint(0, 9)
        from_sq = self._coords_to_square(col, row)

        if random.choice([True, False]):  # Horizontal
            new_col = random.choice([c for c in range(9) if c != col])
            to_sq = self._coords_to_square(new_col, row)
        else:  # Vertical
            new_row = random.choice([r for r in range(10) if r != row])
            to_sq = self._coords_to_square(col, new_row)

        return (from_sq, to_sq) if to_sq else None

    def _gen_cannon_move(self) -> Optional[Tuple[str, str]]:
        """Generate a valid cannon move (no capture)"""
        return self._gen_rook_move()  # Same movement pattern

    def _gen_cannon_capture_move(self) -> Optional[Tuple[str, str, str]]:
        """Generate a valid cannon capture move with screen"""
        for _ in range(20):
            col = random.randint(0, 4)
            row = random.randint(2, 7)
            from_sq = self._coords_to_square(col, row)

            screen_col = col + random.randint(2, 3)
            target_col = screen_col + random.randint(1, 2)

            if target_col > 8:
                continue

            screen_sq = self._coords_to_square(screen_col, row)
            to_sq = self._coords_to_square(target_col, row)

            return (from_sq, to_sq, screen_sq)
        return None

    def _gen_knight_move(self) -> Optional[Tuple[str, str]]:
        """Generate a valid knight move"""
        col = random.randint(2, 6)
        row = random.randint(2, 7)
        from_sq = self._coords_to_square(col, row)

        moves = [(1, 2), (2, 1), (-1, 2), (-2, 1),
                 (1, -2), (2, -1), (-1, -2), (-2, -1)]
        dc, dr = random.choice(moves)

        to_sq = self._coords_to_square(col + dc, row + dr)
        return (from_sq, to_sq) if to_sq else None

    def _gen_bishop_move(self, color: str) -> Optional[Tuple[str, str]]:
        """Generate a valid bishop move"""
        if color == 'red':
            valid_positions = [(2, 0), (6, 0), (2, 4),
                               (6, 4), (0, 2), (4, 2), (8, 2)]
        else:
            valid_positions = [(2, 9), (6, 9), (2, 5),
                               (6, 5), (0, 7), (4, 7), (8, 7)]

        col, row = random.choice(valid_positions)
        from_sq = self._coords_to_square(col, row)

        moves = [(2, 2), (2, -2), (-2, 2), (-2, -2)]
        for dc, dr in random.sample(moves, len(moves)):
            new_col, new_row = col + dc, row + dr
            if color == 'red' and 0 <= new_row <= 4 and 0 <= new_col <= 8:
                return (from_sq, self._coords_to_square(new_col, new_row))
            elif color == 'black' and 5 <= new_row <= 9 and 0 <= new_col <= 8:
                return (from_sq, self._coords_to_square(new_col, new_row))
        return None

    def _gen_pawn_move(self, color: str) -> Optional[Tuple[str, str]]:
        """Generate a valid pawn move"""
        col = random.randint(0, 8)
        if color == 'red':
            row = random.randint(3, 8)
            new_row = row + 1
        else:
            row = random.randint(1, 6)
            new_row = row - 1

        from_sq = self._coords_to_square(col, row)
        to_sq = self._coords_to_square(col, new_row)
        return (from_sq, to_sq) if to_sq else None

    def _gen_random_static_pieces(self, exclude: List[str], count: int) -> Dict[str, str]:
        """Generate random pieces that don't move"""
        pieces = {}
        attempts = 0
        while len(pieces) < count and attempts < 50:
            sq = self._random_square()
            if sq not in exclude and sq not in pieces:
                piece_type = random.choice(['pawn', 'advisor', 'knight'])
                color = random.choice(['red', 'black'])
                pieces[sq] = self._piece_symbol(piece_type, color)
            attempts += 1
        return pieces

    # ============= Main Generation =============

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """Generate all test cases with true temporal dependency"""
        all_cases = []

        # Determine how many cases for each main type
        # We have Move Legality (12 subtypes) and Perpetual Check (2 subtypes)
        # Total distinct scenarios = 14

        total_subtypes = 14
        counts = self._distribute_counts(n_cases, total_subtypes)

        # First 12 counts go to Move Legality
        n_legality = sum(counts[:12])
        # Last 2 counts go to Perpetual Check
        n_perpetual = sum(counts[12:])

        print(f"Generating Move Legality tests ({n_legality} cases)...")
        ml_cases = self.generate_move_legality_tests(n_legality)
        all_cases.extend(ml_cases)

        print(f"Generating Perpetual Check tests ({n_perpetual} cases)...")
        pc_cases = self.generate_perpetual_check_tests(n_perpetual)
        all_cases.extend(pc_cases)

        print(
            f"\n✓ Total: {len(all_cases)} test cases (all with true temporal dependency)")
        return all_cases
