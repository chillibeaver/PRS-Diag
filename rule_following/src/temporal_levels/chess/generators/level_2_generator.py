"""
Level 2 Generator: En Passant Basic (Temporal Version)
Tests the 3 basic conditions for en passant capture:
1. The captured pawn starts from its initial position
2. The captured pawn makes a double-step move
3. The two pawns are adjacent

Added temporal tracking elements:
- Distractor piece movements
- Multiple pawn confusion
"""

import random
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict


class Level2Generator:
    """Generate Level 2 test cases - en passant with temporal tracking"""

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
                # Ensure knight has somewhere to move
                moves = self._get_knight_moves(sq, forbidden)
                if moves:
                    return sq
        return None

    # ==================== VALID: ALL CONDITIONS MET ====================

    def _generate_valid_case(self, case_num: int) -> Optional[Dict]:
        """
        Valid: All conditions met, with distractor knight
        State 1: White pawn in position, black pawn at starting position, white knight somewhere
        State 2: White knight moves (white's turn)
        State 3: Black pawn double-steps (black's turn)
        Answer: Yes (white's turn, can capture en passant)

        Fixes:
        1. Protect en passant target square (Rank 6)
        2. Force use of white knight to ensure correct move order (white -> black -> white asks)
        """
        black_file = random.choice(['b', 'c', 'd', 'e', 'f', 'g'])
        black_start = black_file + '7'
        black_end = black_file + '5'

        # Fix 1: Calculate en passant landing square (Rank 6)
        ep_target_sq = black_file + '6'

        adjacent = self._adjacent_files(black_file)
        white_file = random.choice(adjacent)
        white_sq = white_file + '5'

        # Fix 2: Add landing square to forbidden
        forbidden = {white_sq, black_start, black_end, ep_target_sq}

        # Fix 3: Force use of white knight to ensure move order: white knight moves -> black pawn moves -> white's turn to ask
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

        return {
            "case_id": f"L2_valid_{case_num}",
            "type": "en_passant_temporal",
            "subtype": "all_conditions_met",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []}
            ],
            "question": f"Can white capture the black pawn at {black_end} en passant?",
            "expected": "yes",
            "reasoning": f"Black pawn just moved 2 squares from {black_start} to {black_end}, white pawn at {white_sq} is adjacent, capture square {ep_target_sq} is clear"
        }

    # ==================== INVALID: NOT FROM START ====================

    def _generate_not_from_start_case(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: Black pawn not from starting position
        State 1: Black pawn at rank 6 (not 7), white knight somewhere
        State 2: White knight moves
        State 3: Black pawn moves to rank 5
        Answer: No (not a double-step from starting position)
        """
        black_file = random.choice(['b', 'c', 'd', 'e', 'f', 'g'])
        # Starting from rank 6 (not starting position)
        black_start = black_file + '6'
        black_end = black_file + '5'

        # Although invalid, still protect target square
        # Note: overlaps with black_start, but conceptually is the target square
        ep_target_sq = black_file + '6'

        adjacent = self._adjacent_files(black_file)
        white_file = random.choice(adjacent)
        white_sq = white_file + '5'

        forbidden = {white_sq, black_start, black_end}

        # Use white knight to ensure correct move order
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

        return {
            "case_id": f"L2_not_from_start_{case_num}",
            "type": "en_passant_temporal",
            "subtype": "not_from_start",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []}
            ],
            "question": f"Can white capture the black pawn at {black_end} en passant?",
            "expected": "no",
            "reasoning": f"Black pawn was not on starting rank (started from {black_start}, not rank 7)"
        }

    # ==================== INVALID: MOVED ONE SQUARE ====================

    def _generate_moved_one_square_case(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: Black pawn only moved 1 square
        State 1: Black pawn at rank 7, white knight somewhere
        State 2: White knight moves
        State 3: Black pawn only moves to rank 6 (not 5)
        Answer: No (only moved 1 square)
        """
        black_file = random.choice(['b', 'c', 'd', 'e', 'f', 'g'])
        black_start = black_file + '7'
        black_end = black_file + '6'  # Only moved 1 square

        # Protect target square (although this is an invalid case)
        ep_target_sq = black_file + '6'

        adjacent = self._adjacent_files(black_file)
        white_file = random.choice(adjacent)
        white_sq = white_file + '5'

        # black_end and ep_target_sq overlap, so forbidden includes it
        forbidden = {white_sq, black_start, black_end}

        # Use white knight
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

        return {
            "case_id": f"L2_one_square_{case_num}",
            "type": "en_passant_temporal",
            "subtype": "moved_one_square",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []}
            ],
            "question": f"Can white capture the black pawn at {black_end} en passant?",
            "expected": "no",
            "reasoning": f"Black pawn only moved 1 square from {black_start} to {black_end}"
        }

    # ==================== INVALID: NOT ADJACENT ====================

    def _generate_not_adjacent_case(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: White pawn and black pawn not adjacent
        State 1: Black pawn at rank 7, white pawn on non-adjacent file, white knight somewhere
        State 2: White knight moves
        State 3: Black pawn double-steps
        Answer: No (not adjacent)
        """
        black_file = random.choice(['a', 'b', 'c', 'd'])
        black_start = black_file + '7'
        black_end = black_file + '5'

        # Protect target square
        ep_target_sq = black_file + '6'

        # Choose non-adjacent file
        black_file_idx = self.files.index(black_file)
        non_adjacent = [f for i, f in enumerate(
            self.files) if abs(i - black_file_idx) >= 2]

        if not non_adjacent:
            return None

        white_file = random.choice(non_adjacent)
        white_sq = white_file + '5'

        forbidden = {white_sq, black_start, black_end, ep_target_sq}

        # Use white knight
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

        return {
            "case_id": f"L2_not_adjacent_{case_num}",
            "type": "en_passant_temporal",
            "subtype": "not_adjacent",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []}
            ],
            "question": f"Can white capture the black pawn at {black_end} en passant?",
            "expected": "no",
            "reasoning": f"White pawn at {white_sq} is not adjacent to black pawn at {black_end}"
        }

    # ==================== INVALID: MULTI-PAWN CONFUSION ====================

    def _generate_multi_pawn_confusion_case(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: Multiple pawn confusion - the pawn that double-stepped and the pawn being asked about are different

        Fixed move order:
        State 1: Black pawn A already at c5 (implies historical double-step, but that was "before"), black pawn B at e6, white knight somewhere
        State 2: White knight moves (white's turn)
        State 3: Black pawn B moves to e5 (black's turn, only moves 1 square)

        Question: Can capture black pawn B (at e5)? -> No (black pawn B only moved 1 square)

        Note: Although pawn A double-stepped before, that right has already expired since many moves have passed
        """
        white_file = random.choice(['c', 'd', 'e', 'f'])
        white_sq = white_file + '5'

        adjacent = self._adjacent_files(white_file)
        if len(adjacent) < 2:
            return None

        # Black pawn A: already at c5 (historically double-stepped, but right expired)
        pawn_a_file = adjacent[0]
        pawn_a_sq = pawn_a_file + '5'  # Already at rank 5

        # Black pawn A's target square (if capturing), needs protection
        ep_target_a = pawn_a_file + '6'

        # Black pawn B: moves from e6 to e5 (only 1 square, this is what we ask about)
        pawn_b_file = adjacent[1]
        pawn_b_start = pawn_b_file + '6'
        pawn_b_end = pawn_b_file + '5'

        # Black pawn B's target square
        ep_target_b = pawn_b_file + '6'  # Overlaps with pawn_b_start

        forbidden = {white_sq, pawn_a_sq,
                     pawn_b_start, pawn_b_end, ep_target_a}

        # White knight
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

        return {
            "case_id": f"L2_confusion_{case_num}",
            "type": "en_passant_temporal",
            "subtype": "multi_pawn_confusion",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []}
            ],
            "question": f"Can white capture the black pawn at {pawn_b_end} en passant?",
            "expected": "no",
            "reasoning": f"The pawn at {pawn_b_end} only moved 1 square from {pawn_b_start}; en passant requires a double-step move"
        }

    # ==================== INVALID: WRONG PAWN DOUBLE STEPPED ====================

    def _generate_wrong_pawn_case(self, case_num: int) -> Optional[Dict]:
        """
        Invalid: Asking about the pawn that didn't just double-step

        State 1: White pawn at d5, black pawn A at c7, black pawn B at e5 (already there), white knight
        State 2: White knight moves (white's turn)
        State 3: Black pawn A double-steps to c5 (black's turn)

        Question: Can capture black pawn B (at e5)? -> No (black pawn B didn't just double-step)

        Move order: white -> black -> white's turn to ask
        """
        white_file = random.choice(['c', 'd', 'e', 'f'])
        white_sq = white_file + '5'

        adjacent = self._adjacent_files(white_file)
        if len(adjacent) < 2:
            return None

        # Black pawn A: double-steps (this one just moved, can be captured, but we don't ask about this one)
        pawn_a_file = adjacent[0]
        pawn_a_start = pawn_a_file + '7'
        pawn_a_end = pawn_a_file + '5'
        ep_target_a = pawn_a_file + '6'

        # Black pawn B: already at e5 (we ask about this one, answer is No)
        pawn_b_file = adjacent[1]
        pawn_b_sq = pawn_b_file + '5'
        ep_target_b = pawn_b_file + '6'

        forbidden = {white_sq, pawn_a_start, pawn_a_end,
                     pawn_b_sq, ep_target_a, ep_target_b}

        # White knight
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

        return {
            "case_id": f"L2_wrong_pawn_{case_num}",
            "type": "en_passant_temporal",
            "subtype": "wrong_pawn_asked",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []}
            ],
            "question": f"Can white capture the black pawn at {pawn_b_sq} en passant?",
            "expected": "no",
            "reasoning": f"The pawn at {pawn_b_sq} did not just make a double-step move; the pawn at {pawn_a_end} did"
        }

    # ==================== VALID: CORRECT PAWN IDENTIFIED ====================

    def _generate_correct_pawn_case(self, case_num: int) -> Optional[Dict]:
        """
        Valid: Multiple pawns present, but asking about the correct one (the one that just double-stepped)

        State 1: White pawn at d5, black pawn A at c7, black pawn B at e5 (already there), white knight
        State 2: White knight moves (white's turn)
        State 3: Black pawn A double-steps to c5 (black's turn)

        Question: Can capture black pawn A (at c5)? -> Yes (black pawn A just double-stepped)
        """
        white_file = random.choice(['c', 'd', 'e', 'f'])
        white_sq = white_file + '5'

        adjacent = self._adjacent_files(white_file)
        if len(adjacent) < 2:
            return None

        # Black pawn A: double-steps (we ask about this one, answer is Yes)
        pawn_a_file = adjacent[0]
        pawn_a_start = pawn_a_file + '7'
        pawn_a_end = pawn_a_file + '5'
        ep_target_a = pawn_a_file + '6'

        # Black pawn B: already at e5 (distractor)
        pawn_b_file = adjacent[1]
        pawn_b_sq = pawn_b_file + '5'
        ep_target_b = pawn_b_file + '6'

        forbidden = {white_sq, pawn_a_start, pawn_a_end,
                     pawn_b_sq, ep_target_a, ep_target_b}

        # White knight
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

        return {
            "case_id": f"L2_correct_pawn_{case_num}",
            "type": "en_passant_temporal",
            "subtype": "correct_pawn_identified",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []}
            ],
            "question": f"Can white capture the black pawn at {pawn_a_end} en passant?",
            "expected": "yes",
            "reasoning": f"The pawn at {pawn_a_end} just moved 2 squares from {pawn_a_start}; capture square {ep_target_a} is clear"
        }

    # ==================== GENERATE ALL ====================

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """Generate all Level 2 test cases"""
        all_cases = []

        # Distribution ratio
        # Valid: 30% (basic valid + correct pawn identified)
        # Invalid: 70%
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

        # Not from start
        not_start_count = 0
        for _ in range(n_not_from_start * 10):
            if not_start_count >= n_not_from_start:
                break
            case = self._generate_not_from_start_case(not_start_count + 1)
            if case:
                all_cases.append(case)
                not_start_count += 1
        print(f"  ✓ Generated {not_start_count} not_from_start cases")

        # Moved one square
        one_sq_count = 0
        for _ in range(n_one_square * 10):
            if one_sq_count >= n_one_square:
                break
            case = self._generate_moved_one_square_case(one_sq_count + 1)
            if case:
                all_cases.append(case)
                one_sq_count += 1
        print(f"  ✓ Generated {one_sq_count} moved_one_square cases")

        # Not adjacent
        not_adj_count = 0
        for _ in range(n_not_adjacent * 10):
            if not_adj_count >= n_not_adjacent:
                break
            case = self._generate_not_adjacent_case(not_adj_count + 1)
            if case:
                all_cases.append(case)
                not_adj_count += 1
        print(f"  ✓ Generated {not_adj_count} not_adjacent cases")

        # Multi-pawn confusion
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

        # Wrong pawn asked
        wrong_count = 0
        for _ in range(n_wrong_pawn * 10):
            if wrong_count >= n_wrong_pawn:
                break
            case = self._generate_wrong_pawn_case(wrong_count + 1)
            if case:
                all_cases.append(case)
                wrong_count += 1
        print(f"  ✓ Generated {wrong_count} wrong_pawn_asked cases")

        # Shuffle order
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
