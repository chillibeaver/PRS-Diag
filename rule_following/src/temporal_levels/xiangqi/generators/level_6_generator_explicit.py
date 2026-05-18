"""
Xiangqi Level 6 Generator: Perpetual Check and Perpetual Chase Detection (Explicit Mode)
Explicit version: Shows all states including the final move, asks if the sequence is legal

Rules clarification:
1. Perpetual Check: Continuously checking the King in a repeating pattern is illegal.
   The checking side must change their move after 3 consecutive checks.

2. Perpetual Chase: Continuously chasing a piece in a repeating pattern 
   is illegal after 3 consecutive chases.

Test format (7 states for explicit mode):
- States 1-6: Same as predictive mode (showing the chase/check pattern)
- State 7: The final position after the 4th chase/check move
- Question: Is this move sequence legal according to Xiangqi rules?
"""

import random
from typing import List, Dict, Tuple, Optional, Set


class Level6Generator:
    """Generate Level 6 test cases - perpetual check and chase detection (explicit mode)"""

    # Rule explanation to include in questions
    PERPETUAL_RULES = """Note: In Xiangqi, Perpetual Check and Perpetual Chase are illegal after 3 consecutive occurrences."""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
        self.rows = list(range(10))
        self.palace_col_indices = [3, 4, 5]

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

    def _is_in_palace(self, square: str, color: str) -> bool:
        col, row = self._square_to_coords(square)
        if col not in self.palace_col_indices:
            return False
        if color == 'red':
            return 0 <= row <= 2
        else:
            return 7 <= row <= 9

    def _can_rook_attack(self, rook_sq: str, target_sq: str, occupied: Set[str]) -> bool:
        """Check if Rook can attack target (straight line, no blocking)"""
        col1, row1 = self._square_to_coords(rook_sq)
        col2, row2 = self._square_to_coords(target_sq)

        if col1 != col2 and row1 != row2:
            return False

        if col1 == col2:
            min_r, max_r = min(row1, row2), max(row1, row2)
            for r in range(min_r + 1, max_r):
                sq = self._coords_to_square(col1, r)
                if sq in occupied:
                    return False
        else:
            min_c, max_c = min(col1, col2), max(col1, col2)
            for c in range(min_c + 1, max_c):
                sq = self._coords_to_square(c, row1)
                if sq in occupied:
                    return False
        return True

    def _can_rook_move_to(self, from_sq: str, to_sq: str, occupied: Set[str]) -> bool:
        """Check if Rook can legally move from from_sq to to_sq."""
        col1, row1 = self._square_to_coords(from_sq)
        col2, row2 = self._square_to_coords(to_sq)

        if col1 != col2 and row1 != row2:
            return False

        if to_sq in occupied:
            return False

        if col1 == col2:
            min_r, max_r = min(row1, row2), max(row1, row2)
            for r in range(min_r + 1, max_r):
                sq = self._coords_to_square(col1, r)
                if sq in occupied:
                    return False
        else:
            min_c, max_c = min(col1, col2), max(col1, col2)
            for c in range(min_c + 1, max_c):
                sq = self._coords_to_square(c, row1)
                if sq in occupied:
                    return False
        return True

    def _get_cannon_legal_moves(self, cannon_sq: str, occupied: Set[str],
                                forbidden: Set[str] = None) -> List[str]:
        """Get all legal non-capture moves for a cannon."""
        if forbidden is None:
            forbidden = set()

        col, row = self._square_to_coords(cannon_sq)
        moves = []

        for c in range(9):
            if c == col:
                continue
            sq = self._coords_to_square(c, row)
            if sq and sq not in forbidden and sq not in occupied:
                min_c, max_c = min(col, c), max(col, c)
                blocked = False
                for cc in range(min_c + 1, max_c):
                    if self._coords_to_square(cc, row) in occupied:
                        blocked = True
                        break
                if not blocked:
                    moves.append(sq)

        for r in range(10):
            if r == row:
                continue
            sq = self._coords_to_square(col, r)
            if sq and sq not in forbidden and sq not in occupied:
                min_r, max_r = min(row, r), max(row, r)
                blocked = False
                for rr in range(min_r + 1, max_r):
                    if self._coords_to_square(col, rr) in occupied:
                        blocked = True
                        break
                if not blocked:
                    moves.append(sq)

        return moves

    # ==================== PERPETUAL CHECK ====================

    def _generate_perpetual_check_invalid(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: Rook checks King 3 times, 4th check shown explicitly.
        Shows 7 states: 6 states of the pattern + final state after 4th check.
        """
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

            if not self._is_in_palace(king_sq_a, defender_color):
                continue
            if not self._is_in_palace(king_sq_b, defender_color):
                continue

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

            test_occupied_a = {att_sq_a, att_king_sq}
            test_occupied_b = {att_sq_b, att_king_sq}

            if not self._can_rook_attack(att_sq_a, king_sq_a, test_occupied_a):
                continue
            if not self._can_rook_attack(att_sq_b, king_sq_b, test_occupied_b):
                continue

            if not self._can_rook_move_to(att_sq_a, att_sq_b, {att_king_sq, king_sq_b}):
                continue

            att_symbol = self._piece_symbol('rook', attacker_color)
            def_king_symbol = self._piece_symbol('king', defender_color)
            base_pieces = {att_king_sq: self._piece_symbol(
                'king', attacker_color)}

            # 7 states: 6 showing the pattern + 1 final state after 4th check
            states = [
                {"pieces": {**base_pieces, att_sq_a: att_symbol,
                            king_sq_a: def_king_symbol}, "squares": []},
                {"pieces": {**base_pieces, att_sq_a: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},
                {"pieces": {**base_pieces, att_sq_b: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},
                {"pieces": {**base_pieces, att_sq_b: att_symbol,
                            king_sq_a: def_king_symbol}, "squares": []},
                {"pieces": {**base_pieces, att_sq_a: att_symbol,
                            king_sq_a: def_king_symbol}, "squares": []},
                {"pieces": {**base_pieces, att_sq_a: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},
                # State 7: After the 4th check move (Rook moves to att_sq_b)
                {"pieces": {**base_pieces, att_sq_b: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},
            ]

            return {
                "case_id": f"L6_perpetual_check_invalid_{case_num}",
                "type": "perpetual_check",
                "subtype": "perpetual_check_violation",
                "piece_type": "rook",
                "attacker_color": attacker_color,
                "states": states,
                "question": f"{self.PERPETUAL_RULES}\nIs this move sequence legal according to Xiangqi rules?",
                "expected": "no",
                "reasoning": f"The Rook has checked the King 3 times in a repeating pattern. The 4th check (shown in State 7) constitutes perpetual check, which is illegal."
            }
        return None

    def _generate_perpetual_check_valid_broken(self, case_num: int) -> Optional[Dict]:
        """
        Valid: Check pattern was broken, then resumes.
        Shows 7 states where the pattern is broken mid-sequence.
        """
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
            base_pieces = {att_king_sq: self._piece_symbol(
                'king', attacker_color)}

            # 7 states: pattern broken at state 5, then new check at state 7
            states = [
                {"pieces": {**base_pieces, att_sq_a: att_symbol,
                            king_sq_a: def_king_symbol}, "squares": []},
                {"pieces": {**base_pieces, att_sq_a: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},
                {"pieces": {**base_pieces, att_sq_b: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},
                {"pieces": {**base_pieces, att_sq_b: att_symbol,
                            king_sq_a: def_king_symbol}, "squares": []},
                # Pattern broken: Rook moves to non-checking position
                {"pieces": {**base_pieces, att_sq_c: att_symbol,
                            king_sq_a: def_king_symbol}, "squares": []},
                {"pieces": {**base_pieces, att_sq_c: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},
                # New check after pattern break (this is legal - counter reset)
                {"pieces": {**base_pieces, att_sq_a: att_symbol,
                            king_sq_b: def_king_symbol}, "squares": []},
            ]

            return {
                "case_id": f"L6_perpetual_check_valid_broken_{case_num}",
                "type": "perpetual_check",
                "subtype": "pattern_broken",
                "piece_type": "rook",
                "attacker_color": attacker_color,
                "states": states,
                "question": f"{self.PERPETUAL_RULES}\nIs this move sequence legal according to Xiangqi rules?",
                "expected": "yes",
                "reasoning": f"The perpetual check pattern was broken when Rook moved to {att_sq_c} (a non-checking position in State 5). The cycle was interrupted, so the check in State 7 is legal - the counter has reset."
            }
        return None

    # ==================== PERPETUAL CHASE ====================

    def _generate_perpetual_chase_invalid(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: Rook chasing Cannon for 3 times, 4th chase shown explicitly.
        Shows 7 states: 6 states of chase pattern + final state after 4th chase.
        """
        attacker_color = random.choice(['red', 'black'])
        defender_color = self._opposite_color(attacker_color)

        for _ in range(500):
            # Initial rook position
            rook_col_1 = random.randint(1, 7)
            rook_row_1 = random.randint(3, 6)
            rook_sq_1 = self._coords_to_square(rook_col_1, rook_row_1)

            # Initial cannon position: same row as rook
            cannon_col_1 = random.choice(
                [c for c in range(9) if c != rook_col_1 and abs(c - rook_col_1) >= 2])
            cannon_row_1 = rook_row_1
            cannon_sq_1 = self._coords_to_square(cannon_col_1, cannon_row_1)

            if not cannon_sq_1:
                continue

            if not self._can_rook_attack(rook_sq_1, cannon_sq_1, set()):
                continue

            # === State 2: Cannon escapes ===
            escape_row_2 = cannon_row_1 + random.choice([2, 3, -2, -3])
            if not (0 <= escape_row_2 <= 9):
                escape_row_2 = cannon_row_1 + (3 if cannon_row_1 < 5 else -3)
            if not (0 <= escape_row_2 <= 9):
                continue

            cannon_sq_2 = self._coords_to_square(cannon_col_1, escape_row_2)
            if not cannon_sq_2 or cannon_sq_2 == rook_sq_1:
                continue

            cannon_moves_1 = self._get_cannon_legal_moves(
                cannon_sq_1, {rook_sq_1})
            if cannon_sq_2 not in cannon_moves_1:
                continue

            cannon_col_2, cannon_row_2 = self._square_to_coords(cannon_sq_2)

            # === State 3: Rook chases ===
            rook_sq_2_option_a = self._coords_to_square(
                rook_col_1, cannon_row_2)
            rook_sq_2_option_b = self._coords_to_square(
                cannon_col_2, rook_row_1)

            rook_sq_2 = None
            occupied_2 = {cannon_sq_2}

            for opt in [rook_sq_2_option_a, rook_sq_2_option_b]:
                if not opt or opt == cannon_sq_2:
                    continue
                if self._can_rook_move_to(rook_sq_1, opt, occupied_2):
                    if self._can_rook_attack(opt, cannon_sq_2, set()):
                        rook_sq_2 = opt
                        break

            if not rook_sq_2:
                continue

            rook_col_2, rook_row_2 = self._square_to_coords(rook_sq_2)

            # === State 4: Cannon escapes again ===
            cannon_moves_3 = self._get_cannon_legal_moves(
                cannon_sq_2, {rook_sq_2})

            valid_escapes_3 = []
            for sq in cannon_moves_3:
                c, r = self._square_to_coords(sq)
                if c != rook_col_2 and r != rook_row_2:
                    valid_escapes_3.append(sq)

            if not valid_escapes_3:
                continue
            cannon_sq_3 = random.choice(valid_escapes_3)
            cannon_col_3, cannon_row_3 = self._square_to_coords(cannon_sq_3)

            # === State 5: Rook chases again ===
            rook_sq_3_option_a = self._coords_to_square(
                rook_col_2, cannon_row_3)
            rook_sq_3_option_b = self._coords_to_square(
                cannon_col_3, rook_row_2)

            rook_sq_3 = None
            occupied_4 = {cannon_sq_3}

            for opt in [rook_sq_3_option_a, rook_sq_3_option_b]:
                if not opt or opt == cannon_sq_3:
                    continue
                if self._can_rook_move_to(rook_sq_2, opt, occupied_4):
                    if self._can_rook_attack(opt, cannon_sq_3, set()):
                        rook_sq_3 = opt
                        break

            if not rook_sq_3:
                continue

            rook_col_3, rook_row_3 = self._square_to_coords(rook_sq_3)

            # === State 6: Cannon escapes again ===
            cannon_moves_5 = self._get_cannon_legal_moves(
                cannon_sq_3, {rook_sq_3})

            valid_escapes_5 = []
            for sq in cannon_moves_5:
                c, r = self._square_to_coords(sq)
                if c != rook_col_3 and r != rook_row_3:
                    valid_escapes_5.append(sq)

            if not valid_escapes_5:
                continue
            cannon_sq_4 = random.choice(valid_escapes_5)
            cannon_col_4, cannon_row_4 = self._square_to_coords(cannon_sq_4)

            # === State 7: Final position after 4th chase ===
            rook_sq_4_option_a = self._coords_to_square(
                rook_col_3, cannon_row_4)
            rook_sq_4_option_b = self._coords_to_square(
                cannon_col_4, rook_row_3)

            rook_sq_4 = None
            occupied_6 = {cannon_sq_4}

            for opt in [rook_sq_4_option_a, rook_sq_4_option_b]:
                if not opt or opt == cannon_sq_4:
                    continue
                if self._can_rook_move_to(rook_sq_3, opt, occupied_6):
                    if self._can_rook_attack(opt, cannon_sq_4, set()):
                        rook_sq_4 = opt
                        break

            if not rook_sq_4:
                continue

            # Build states (7 states for explicit mode)
            rook_symbol = self._piece_symbol('rook', attacker_color)
            cannon_symbol = self._piece_symbol('cannon', defender_color)

            states = [
                {"pieces": {rook_sq_1: rook_symbol,
                            cannon_sq_1: cannon_symbol}, "squares": []},
                {"pieces": {rook_sq_1: rook_symbol,
                            cannon_sq_2: cannon_symbol}, "squares": []},
                {"pieces": {rook_sq_2: rook_symbol,
                            cannon_sq_2: cannon_symbol}, "squares": []},
                {"pieces": {rook_sq_2: rook_symbol,
                            cannon_sq_3: cannon_symbol}, "squares": []},
                {"pieces": {rook_sq_3: rook_symbol,
                            cannon_sq_3: cannon_symbol}, "squares": []},
                {"pieces": {rook_sq_3: rook_symbol,
                            cannon_sq_4: cannon_symbol}, "squares": []},
                # State 7: After the 4th chase move
                {"pieces": {rook_sq_4: rook_symbol,
                            cannon_sq_4: cannon_symbol}, "squares": []},
            ]

            return {
                "case_id": f"L6_perpetual_chase_invalid_{case_num}",
                "type": "perpetual_chase",
                "subtype": "perpetual_chase_violation",
                "piece_type": "rook",
                "target_type": "cannon",
                "attacker_color": attacker_color,
                "states": states,
                "question": f"{self.PERPETUAL_RULES}\nIs this move sequence legal according to Xiangqi rules?",
                "expected": "no",
                "reasoning": f"The Rook has been chasing the Cannon for 3 consecutive moves. The 4th chase (shown in State 7) constitutes perpetual chase, which is illegal."
            }

        return None

    # ==================== GENERATE ALL ====================

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """Generate all Level 6 test cases (explicit mode)"""
        all_cases = []

        # Distribution matching predictive mode exactly
        n_check_invalid = int(n_cases * 0.40)
        n_check_valid = int(n_cases * 0.20)
        n_chase_invalid = n_cases - n_check_invalid - n_check_valid

        generators = [
            ("perpetual check (invalid)", n_check_invalid,
             self._generate_perpetual_check_invalid),
            ("perpetual check (valid - broken)", n_check_valid,
             self._generate_perpetual_check_valid_broken),
            ("perpetual chase (invalid)", n_chase_invalid,
             self._generate_perpetual_chase_invalid),
        ]

        for name, target_count, gen_func in generators:
            print(f"Generating {name} cases...")
            count = 0
            for _ in range(target_count * 100):
                if count >= target_count:
                    break
                case = gen_func(count + 1)
                if case:
                    all_cases.append(case)
                    count += 1
            print(f"  ✓ Generated {count} {name} cases")

        random.shuffle(all_cases)

        valid_count = sum(1 for c in all_cases if c['expected'] == 'yes')
        invalid_count = sum(1 for c in all_cases if c['expected'] == 'no')

        print(
            f"\n✓ Total generated: {len(all_cases)} Level 6 explicit test cases")
        print(
            f"  Valid (yes): {valid_count} ({valid_count/len(all_cases)*100:.1f}%)")
        print(
            f"  Invalid (no): {invalid_count} ({invalid_count/len(all_cases)*100:.1f}%)")

        return all_cases
