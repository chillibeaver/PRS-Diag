"""
Level 2 Generator: En Passant Basic (Explicit/Non-Predictive Version)
Aligned with Predictive version - tests en passant with temporal tracking

Shows 4 states (predictive shows 3):
- State 1: White pawn in position, black pawn at starting position, white knight somewhere
- State 2: White knight moves (white's turn)
- State 3: Black pawn double-steps (black's turn)
- State 4: En passant capture result (white pawn at capture square, black pawn removed)

Question: "Is this en passant capture legal?"
"""

import random
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict


class Level2Generator:
    """Generate Level 2 test cases - en passant with temporal tracking (Explicit version)"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.ranks = ['1', '2', '3', '4', '5', '6', '7', '8']

    def _adjacent_files(self, file: str) -> List[str]:
        """Get adjacent files"""
        file_idx = self.files.index(file)
        adjacent = []
        if file_idx > 0:
            adjacent.append(self.files[file_idx - 1])
        if file_idx < 7:
            adjacent.append(self.files[file_idx + 1])
        return adjacent

    def _get_knight_moves(self, square: str, forbidden: Set[str]) -> List[str]:
        """Get all legal knight move targets"""
        f = ord(square[0]) - ord('a')
        r = int(square[1]) - 1
        moves = []
        for df, dr in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
            new_f, new_r = f + df, r + dr
            if 0 <= new_f < 8 and 0 <= new_r < 8:
                sq = chr(ord('a') + new_f) + str(new_r + 1)
                if sq not in forbidden:
                    moves.append(sq)
        return moves

    def _get_safe_knight_position(self, forbidden: Set[str]) -> Optional[str]:
        """Find a safe knight position"""
        for _ in range(100):
            f = random.choice(self.files)
            r = random.choice(self.ranks)
            sq = f + r
            if sq not in forbidden:
                moves = self._get_knight_moves(sq, forbidden)
                if moves:
                    return sq
        return None

    # ==================== VALID: ALL CONDITIONS MET ====================

    def _generate_valid_case(self, case_num: int) -> Optional[Dict]:
        """
        Valid: All en passant conditions met
        State 1: White pawn in position, black pawn at starting position, white knight somewhere
        State 2: White knight moves (white's turn)
        State 3: Black pawn double-steps (black's turn)
        State 4: En passant capture completed (white pawn at c6, black pawn removed)
        Answer: Yes
        """
        black_file = random.choice(['b', 'c', 'd', 'e', 'f', 'g'])
        black_start = black_file + '7'
        black_end = black_file + '5'

        # En passant landing square (rank 6)
        ep_target_sq = black_file + '6'

        adjacent = self._adjacent_files(black_file)
        white_file = random.choice(adjacent)
        white_sq = white_file + '5'

        forbidden = {white_sq, black_start, black_end, ep_target_sq}

        # White knight for move order
        knight_symbol = 'N'
        knight_start = self._get_safe_knight_position(forbidden)
        if not knight_start:
            return None

        forbidden.add(knight_start)
        knight_moves = self._get_knight_moves(knight_start, forbidden)
        if not knight_moves:
            return None

        knight_end = random.choice(knight_moves)

        # Build 4 states
        state1 = {
            white_sq: 'P',
            black_start: 'p',
            knight_start: knight_symbol
        }

        state2 = {
            white_sq: 'P',
            black_start: 'p',
            knight_end: knight_symbol
        }

        state3 = {
            white_sq: 'P',
            black_end: 'p',
            knight_end: knight_symbol
        }

        # State 4: En passant completed
        state4 = {
            ep_target_sq: 'P',  # White pawn moved to capture square
            # Black pawn removed (not in state4)
            knight_end: knight_symbol
        }

        return {
            "case_id": f"L2_valid_{case_num}",
            "type": "en_passant_temporal_explicit",
            "subtype": "all_conditions_met",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []},
                {"pieces": state4, "squares": []}
            ],
            "question": f"Is this en passant capture legal?",
            "expected": "yes",
            "reasoning": f"Black pawn moved 2 squares from {black_start} to {black_end}, white pawn at {white_sq} is adjacent, capture to {ep_target_sq} is valid"
        }

    # ==================== INVALID: NOT FROM START ====================

    def _generate_not_from_start_case(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: Black pawn not from starting position
        State 1: Black pawn at rank 6 (not 7)
        State 2: White knight moves
        State 3: Black pawn moves to rank 5
        State 4: Attempted en passant
        Answer: No
        """
        black_file = random.choice(['b', 'c', 'd', 'e', 'f', 'g'])
        black_start = black_file + '6'  # Not starting position
        black_end = black_file + '5'
        ep_target_sq = black_file + '6'

        adjacent = self._adjacent_files(black_file)
        white_file = random.choice(adjacent)
        white_sq = white_file + '5'

        forbidden = {white_sq, black_start, black_end}

        knight_symbol = 'N'
        knight_start = self._get_safe_knight_position(forbidden)
        if not knight_start:
            return None

        forbidden.add(knight_start)
        knight_moves = self._get_knight_moves(knight_start, forbidden)
        if not knight_moves:
            return None

        knight_end = random.choice(knight_moves)

        state1 = {
            white_sq: 'P',
            black_start: 'p',
            knight_start: knight_symbol
        }

        state2 = {
            white_sq: 'P',
            black_start: 'p',
            knight_end: knight_symbol
        }

        state3 = {
            white_sq: 'P',
            black_end: 'p',
            knight_end: knight_symbol
        }

        # State 4: Attempted en passant (illegal)
        state4 = {
            ep_target_sq: 'P',
            knight_end: knight_symbol
        }

        return {
            "case_id": f"L2_not_from_start_{case_num}",
            "type": "en_passant_temporal_explicit",
            "subtype": "not_from_start",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []},
                {"pieces": state4, "squares": []}
            ],
            "question": f"Is this en passant capture legal?",
            "expected": "no",
            "reasoning": f"Black pawn was not on starting rank (started from {black_start}, not rank 7)"
        }

    # ==================== INVALID: MOVED ONE SQUARE ====================

    def _generate_moved_one_square_case(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: Black pawn only moved 1 square
        State 1: Black pawn at rank 7
        State 2: White knight moves
        State 3: Black pawn only moves to rank 6 (not 5)
        State 4: Attempted en passant
        Answer: No
        """
        black_file = random.choice(['b', 'c', 'd', 'e', 'f', 'g'])
        black_start = black_file + '7'
        black_end = black_file + '6'  # Only moved 1 square

        # Where white pawn would try to capture
        ep_target_sq = black_file + '7'  # Would need to go backwards - invalid anyway

        adjacent = self._adjacent_files(black_file)
        white_file = random.choice(adjacent)
        white_sq = white_file + '5'

        forbidden = {white_sq, black_start, black_end}

        knight_symbol = 'N'
        knight_start = self._get_safe_knight_position(forbidden)
        if not knight_start:
            return None

        forbidden.add(knight_start)
        knight_moves = self._get_knight_moves(knight_start, forbidden)
        if not knight_moves:
            return None

        knight_end = random.choice(knight_moves)

        state1 = {
            white_sq: 'P',
            black_start: 'p',
            knight_start: knight_symbol
        }

        state2 = {
            white_sq: 'P',
            black_start: 'p',
            knight_end: knight_symbol
        }

        state3 = {
            white_sq: 'P',
            black_end: 'p',
            knight_end: knight_symbol
        }

        # State 4: Attempted en passant to rank 7 (illegal move shown)
        # White pawn tries to capture diagonally to where black pawn was
        attempted_capture_sq = black_file + '6'
        state4 = {
            attempted_capture_sq: 'P',
            knight_end: knight_symbol
        }

        return {
            "case_id": f"L2_one_square_{case_num}",
            "type": "en_passant_temporal_explicit",
            "subtype": "moved_one_square",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []},
                {"pieces": state4, "squares": []}
            ],
            "question": f"Is this en passant capture legal?",
            "expected": "no",
            "reasoning": f"Black pawn only moved 1 square from {black_start} to {black_end}, en passant requires double-step"
        }

    # ==================== INVALID: NOT ADJACENT ====================

    def _generate_not_adjacent_case(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: White pawn and black pawn not adjacent
        Answer: No
        """
        black_file = random.choice(['a', 'b', 'c', 'd'])
        black_start = black_file + '7'
        black_end = black_file + '5'
        ep_target_sq = black_file + '6'

        # Non-adjacent file
        black_file_idx = self.files.index(black_file)
        non_adjacent = [f for i, f in enumerate(
            self.files) if abs(i - black_file_idx) >= 2]
        if not non_adjacent:
            return None

        white_file = random.choice(non_adjacent)
        white_sq = white_file + '5'

        forbidden = {white_sq, black_start, black_end, ep_target_sq}

        knight_symbol = 'N'
        knight_start = self._get_safe_knight_position(forbidden)
        if not knight_start:
            return None

        forbidden.add(knight_start)
        knight_moves = self._get_knight_moves(knight_start, forbidden)
        if not knight_moves:
            return None

        knight_end = random.choice(knight_moves)

        state1 = {
            white_sq: 'P',
            black_start: 'p',
            knight_start: knight_symbol
        }

        state2 = {
            white_sq: 'P',
            black_start: 'p',
            knight_end: knight_symbol
        }

        state3 = {
            white_sq: 'P',
            black_end: 'p',
            knight_end: knight_symbol
        }

        state4 = {
            ep_target_sq: 'P',
            knight_end: knight_symbol
        }

        return {
            "case_id": f"L2_not_adjacent_{case_num}",
            "type": "en_passant_temporal_explicit",
            "subtype": "not_adjacent",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []},
                {"pieces": state4, "squares": []}
            ],
            "question": f"Is this en passant capture legal?",
            "expected": "no",
            "reasoning": f"White pawn at {white_sq} is not adjacent to black pawn at {black_end}"
        }

    # ==================== INVALID: MULTI-PAWN CONFUSION ====================

    def _generate_multi_pawn_confusion_case(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: Multiple pawn confusion - asking about wrong pawn
        Pawn A already at c5 (historical), Pawn B moves from e6 to e5 (only 1 square)
        Question asks about Pawn B
        Answer: No
        """
        white_file = random.choice(['c', 'd', 'e', 'f'])
        white_sq = white_file + '5'

        adjacent = self._adjacent_files(white_file)
        if len(adjacent) < 2:
            return None

        pawn_a_file = adjacent[0]
        pawn_a_sq = pawn_a_file + '5'

        pawn_b_file = adjacent[1]
        pawn_b_start = pawn_b_file + '6'
        pawn_b_end = pawn_b_file + '5'
        ep_target_b = pawn_b_file + '6'

        forbidden = {white_sq, pawn_a_sq, pawn_b_start, pawn_b_end}

        knight_symbol = 'N'
        knight_start = self._get_safe_knight_position(forbidden)
        if not knight_start:
            return None

        forbidden.add(knight_start)
        knight_moves = self._get_knight_moves(knight_start, forbidden)
        if not knight_moves:
            return None

        knight_end = random.choice(knight_moves)

        state1 = {
            white_sq: 'P',
            pawn_a_sq: 'p',
            pawn_b_start: 'p',
            knight_start: knight_symbol
        }

        state2 = {
            white_sq: 'P',
            pawn_a_sq: 'p',
            pawn_b_start: 'p',
            knight_end: knight_symbol
        }

        state3 = {
            white_sq: 'P',
            pawn_a_sq: 'p',
            pawn_b_end: 'p',
            knight_end: knight_symbol
        }

        # Attempted capture of pawn B
        state4 = {
            ep_target_b: 'P',
            pawn_a_sq: 'p',
            knight_end: knight_symbol
        }

        return {
            "case_id": f"L2_confusion_{case_num}",
            "type": "en_passant_temporal_explicit",
            "subtype": "multi_pawn_confusion",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []},
                {"pieces": state4, "squares": []}
            ],
            "question": f"Is this en passant capture legal?",
            "expected": "no",
            "reasoning": f"The captured pawn at {pawn_b_end} only moved 1 square from {pawn_b_start}; en passant requires a double-step move"
        }

    # ==================== INVALID: WRONG PAWN ASKED ====================

    def _generate_wrong_pawn_case(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: Pawn A double-steps, but capture shown is against Pawn B (which didn't move)
        Answer: No
        """
        white_file = random.choice(['c', 'd', 'e', 'f'])
        white_sq = white_file + '5'

        adjacent = self._adjacent_files(white_file)
        if len(adjacent) < 2:
            return None

        pawn_a_file = adjacent[0]
        pawn_a_start = pawn_a_file + '7'
        pawn_a_end = pawn_a_file + '5'

        pawn_b_file = adjacent[1]
        pawn_b_sq = pawn_b_file + '5'
        ep_target_b = pawn_b_file + '6'

        forbidden = {white_sq, pawn_a_start,
                     pawn_a_end, pawn_b_sq, ep_target_b}

        knight_symbol = 'N'
        knight_start = self._get_safe_knight_position(forbidden)
        if not knight_start:
            return None

        forbidden.add(knight_start)
        knight_moves = self._get_knight_moves(knight_start, forbidden)
        if not knight_moves:
            return None

        knight_end = random.choice(knight_moves)

        state1 = {
            white_sq: 'P',
            pawn_a_start: 'p',
            pawn_b_sq: 'p',
            knight_start: knight_symbol
        }

        state2 = {
            white_sq: 'P',
            pawn_a_start: 'p',
            pawn_b_sq: 'p',
            knight_end: knight_symbol
        }

        state3 = {
            white_sq: 'P',
            pawn_a_end: 'p',
            pawn_b_sq: 'p',
            knight_end: knight_symbol
        }

        # Capture against pawn B (wrong pawn)
        state4 = {
            ep_target_b: 'P',
            pawn_a_end: 'p',
            knight_end: knight_symbol
        }

        return {
            "case_id": f"L2_wrong_pawn_{case_num}",
            "type": "en_passant_temporal_explicit",
            "subtype": "wrong_pawn_asked",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []},
                {"pieces": state4, "squares": []}
            ],
            "question": f"Is this en passant capture legal?",
            "expected": "no",
            "reasoning": f"The pawn at {pawn_b_sq} did not just make a double-step move; the pawn at {pawn_a_end} did"
        }

    # ==================== VALID: CORRECT PAWN IDENTIFIED ====================

    def _generate_correct_pawn_case(self, case_num: int) -> Optional[Dict]:
        """
        Valid: Multiple pawns present, capture shown is against correct pawn (just double-stepped)
        Answer: Yes
        """
        white_file = random.choice(['c', 'd', 'e', 'f'])
        white_sq = white_file + '5'

        adjacent = self._adjacent_files(white_file)
        if len(adjacent) < 2:
            return None

        pawn_a_file = adjacent[0]
        pawn_a_start = pawn_a_file + '7'
        pawn_a_end = pawn_a_file + '5'
        ep_target_a = pawn_a_file + '6'

        pawn_b_file = adjacent[1]
        pawn_b_sq = pawn_b_file + '5'

        forbidden = {white_sq, pawn_a_start,
                     pawn_a_end, pawn_b_sq, ep_target_a}

        knight_symbol = 'N'
        knight_start = self._get_safe_knight_position(forbidden)
        if not knight_start:
            return None

        forbidden.add(knight_start)
        knight_moves = self._get_knight_moves(knight_start, forbidden)
        if not knight_moves:
            return None

        knight_end = random.choice(knight_moves)

        state1 = {
            white_sq: 'P',
            pawn_a_start: 'p',
            pawn_b_sq: 'p',
            knight_start: knight_symbol
        }

        state2 = {
            white_sq: 'P',
            pawn_a_start: 'p',
            pawn_b_sq: 'p',
            knight_end: knight_symbol
        }

        state3 = {
            white_sq: 'P',
            pawn_a_end: 'p',
            pawn_b_sq: 'p',
            knight_end: knight_symbol
        }

        # Correct capture against pawn A
        state4 = {
            ep_target_a: 'P',
            pawn_b_sq: 'p',
            knight_end: knight_symbol
        }

        return {
            "case_id": f"L2_correct_pawn_{case_num}",
            "type": "en_passant_temporal_explicit",
            "subtype": "correct_pawn_identified",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []},
                {"pieces": state4, "squares": []}
            ],
            "question": f"Is this en passant capture legal?",
            "expected": "yes",
            "reasoning": f"The pawn at {pawn_a_end} just moved 2 squares from {pawn_a_start}; capture to {ep_target_a} is valid"
        }

    # ==================== GENERATE ALL ====================

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """Generate all Level 2 test cases"""
        all_cases = []

        # Distribution: 30% valid, 70% invalid (matching predictive version)
        n_valid_basic = int(n_cases * 0.15)
        n_valid_correct = int(n_cases * 0.15)
        n_invalid = n_cases - n_valid_basic - n_valid_correct

        # Invalid distribution
        n_not_from_start = n_invalid // 5
        n_one_square = n_invalid // 5
        n_not_adjacent = n_invalid // 5
        n_confusion = n_invalid // 5
        n_wrong_pawn = n_invalid - n_not_from_start - \
            n_one_square - n_not_adjacent - n_confusion

        print(f"Generating valid cases (basic)...")
        valid_basic_count = 0
        for _ in range(n_valid_basic * 10):
            if valid_basic_count >= n_valid_basic:
                break
            case = self._generate_valid_case(valid_basic_count + 1)
            if case:
                all_cases.append(case)
                valid_basic_count += 1
        print(f"  ✓ Generated {valid_basic_count} valid basic cases")

        print(f"Generating valid cases (correct pawn)...")
        valid_correct_count = 0
        for _ in range(n_valid_correct * 10):
            if valid_correct_count >= n_valid_correct:
                break
            case = self._generate_correct_pawn_case(valid_correct_count + 1)
            if case:
                all_cases.append(case)
                valid_correct_count += 1
        print(f"  ✓ Generated {valid_correct_count} correct pawn cases")

        print(f"Generating invalid cases...")

        not_start_count = 0
        for _ in range(n_not_from_start * 10):
            if not_start_count >= n_not_from_start:
                break
            case = self._generate_not_from_start_case(not_start_count + 1)
            if case:
                all_cases.append(case)
                not_start_count += 1
        print(f"  ✓ Generated {not_start_count} not_from_start cases")

        one_sq_count = 0
        for _ in range(n_one_square * 10):
            if one_sq_count >= n_one_square:
                break
            case = self._generate_moved_one_square_case(one_sq_count + 1)
            if case:
                all_cases.append(case)
                one_sq_count += 1
        print(f"  ✓ Generated {one_sq_count} moved_one_square cases")

        not_adj_count = 0
        for _ in range(n_not_adjacent * 10):
            if not_adj_count >= n_not_adjacent:
                break
            case = self._generate_not_adjacent_case(not_adj_count + 1)
            if case:
                all_cases.append(case)
                not_adj_count += 1
        print(f"  ✓ Generated {not_adj_count} not_adjacent cases")

        confusion_count = 0
        for _ in range(n_confusion * 10):
            if confusion_count >= n_confusion:
                break
            case = self._generate_multi_pawn_confusion_case(
                confusion_count + 1)
            if case:
                all_cases.append(case)
                confusion_count += 1
        print(f"  ✓ Generated {confusion_count} multi_pawn_confusion cases")

        wrong_count = 0
        for _ in range(n_wrong_pawn * 10):
            if wrong_count >= n_wrong_pawn:
                break
            case = self._generate_wrong_pawn_case(wrong_count + 1)
            if case:
                all_cases.append(case)
                wrong_count += 1
        print(f"  ✓ Generated {wrong_count} wrong_pawn_asked cases")

        random.shuffle(all_cases)

        # Statistics
        stats = defaultdict(int)
        for case in all_cases:
            stats[case['subtype']] += 1

        total_valid = valid_basic_count + valid_correct_count
        total_invalid = len(all_cases) - total_valid

        print(f"\n✓ Total generated: {len(all_cases)} Level 2 test cases")
        print(
            f"  Valid: {total_valid} ({total_valid/len(all_cases)*100:.1f}%)")
        print(
            f"  Invalid: {total_invalid} ({total_invalid/len(all_cases)*100:.1f}%)")
        print(f"  Breakdown:")
        for subtype, count in sorted(stats.items()):
            print(f"    {subtype}: {count} ({count/len(all_cases)*100:.1f}%)")

        return all_cases
