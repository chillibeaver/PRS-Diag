"""
Automated test case generator for Xiangqi No-Rule Multi-State Test
Pure temporal reasoning without Xiangqi rules - automatically generated
"""

import random
from typing import List, Dict


class XiangqiNoRuleGenerator:
    """Automatically generate Xiangqi multi-state reasoning test cases (No Rules)"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']  # 9 columns
        self.rows = list(range(10))  # 0-9

    def _random_square(self) -> str:
        col = random.choice(self.cols)
        row = random.choice(self.rows)
        return col + str(row)

    def _random_piece(self) -> str:
        pieces = ['K', 'A', 'B', 'N', 'R', 'C',
                  'P', 'k', 'a', 'b', 'n', 'r', 'c', 'p']
        return random.choice(pieces)

    def _get_different_square(self, square: str) -> str:
        new_square = self._random_square()
        while new_square == square:
            new_square = self._random_square()
        return new_square

    def _distribute_counts(self, total: int, n_slots: int) -> List[int]:
        """Distribute total count as evenly as possible into n_slots"""
        base = total // n_slots
        remainder = total % n_slots
        return [base + (1 if i < remainder else 0) for i in range(n_slots)]

    # ============= Type 1: Movement Detection =============

    def generate_movement_detection_tests(self, n_positive: int = 5, n_negative: int = 5) -> List[Dict]:
        cases = []

        # Positive cases
        for i in range(n_positive):
            piece = self._random_piece()
            start_sq = self._random_square()
            end_sq = self._get_different_square(start_sq)

            question = f"""Between these two states, did the piece move from {start_sq} to {end_sq}?
- Answer 'yes' if the piece moved from {start_sq} to {end_sq}
- Answer 'no' if the piece moved to a different location
- Answer 'unknown' if you cannot determine"""

            cases.append({
                "case_id": f"movement_pos_{i+1}",
                "type": "movement_detection",
                "subtype": "moved_to_target",
                "states": [
                    {"pieces": {start_sq: piece}, "squares": []},
                    {"pieces": {end_sq: piece}, "squares": []}
                ],
                "label": "These are two consecutive board states.",
                "question": question,
                "expected": "yes",
                "reasoning": f"Piece moved from {start_sq} to {end_sq}"
            })

        # Negative cases
        for i in range(n_negative):
            piece = self._random_piece()
            start_sq = self._random_square()
            actual_end_sq = self._get_different_square(start_sq)
            asked_sq = self._get_different_square(start_sq)
            while asked_sq == actual_end_sq:
                asked_sq = self._get_different_square(start_sq)

            question = f"""Between these two states, did the piece move from {start_sq} to {asked_sq}?
- Answer 'yes' if the piece moved from {start_sq} to {asked_sq}
- Answer 'no' if the piece moved to a different location
- Answer 'unknown' if you cannot determine"""

            cases.append({
                "case_id": f"movement_neg_{i+1}",
                "type": "movement_detection",
                "subtype": "moved_elsewhere",
                "states": [
                    {"pieces": {start_sq: piece}, "squares": []},
                    {"pieces": {actual_end_sq: piece}, "squares": []}
                ],
                "label": "These are two consecutive board states.",
                "question": question,
                "expected": "no",
                "reasoning": f"Piece moved to {actual_end_sq}, not {asked_sq}"
            })

        return cases

    # ============= Type 2: Sequence Order =============

    def generate_sequence_order_tests(self, n_positive: int = 5, n_negative: int = 5) -> List[Dict]:
        cases = []

        # Positive cases
        for i in range(n_positive):
            piece = self._random_piece()
            sq_a = self._random_square()
            sq_b = self._get_different_square(sq_a)
            sq_c = self._get_different_square(sq_b)
            while sq_c == sq_a:
                sq_c = self._get_different_square(sq_b)

            question = f"""Did the piece move to {sq_b} before moving to {sq_c}?
- Answer 'yes' if the sequence shows movement to {sq_b} before {sq_c}
- Answer 'no' if this is not the order shown
- Answer 'unknown' if you cannot determine"""

            cases.append({
                "case_id": f"sequence_pos_{i+1}",
                "type": "sequence_order",
                "subtype": "correct_order",
                "states": [
                    {"pieces": {sq_a: piece}, "squares": []},
                    {"pieces": {sq_b: piece}, "squares": []},
                    {"pieces": {sq_c: piece}, "squares": []}
                ],
                "label": "States are shown in chronological order (1 → 2 → 3).",
                "question": question,
                "expected": "yes",
                "reasoning": f"Sequence is {sq_a} → {sq_b} → {sq_c}"
            })

        # Negative cases
        for i in range(n_negative):
            piece = self._random_piece()
            sq_a = self._random_square()
            sq_b = self._get_different_square(sq_a)
            sq_c = self._get_different_square(sq_b)
            while sq_c == sq_a:
                sq_c = self._get_different_square(sq_b)

            question = f"""Did the piece move to {sq_c} before moving to {sq_b}?
- Answer 'yes' if the sequence shows movement to {sq_c} before {sq_b}
- Answer 'no' if this is not the order shown
- Answer 'unknown' if you cannot determine"""

            cases.append({
                "case_id": f"sequence_neg_{i+1}",
                "type": "sequence_order",
                "subtype": "wrong_order",
                "states": [
                    {"pieces": {sq_a: piece}, "squares": []},
                    {"pieces": {sq_b: piece}, "squares": []},
                    {"pieces": {sq_c: piece}, "squares": []}
                ],
                "label": "States are shown in chronological order (1 → 2 → 3).",
                "question": question,
                "expected": "no",
                "reasoning": f"Sequence is {sq_a} → {sq_b} → {sq_c}, not to {sq_c} before {sq_b}"
            })

        return cases

    # ============= Type 3: State Comparison =============

    def generate_state_comparison_tests(self, n_positive: int = 5, n_negative: int = 5) -> List[Dict]:
        cases = []

        # Positive cases: piece returns
        for i in range(n_positive):
            piece = self._random_piece()
            start_sq = self._random_square()
            middle_sq = self._get_different_square(start_sq)

            question = f"""Did the piece return to its starting position?
- Answer 'yes' if the piece is at the same position in State 3 as in State 1
- Answer 'no' if the piece is at a different position
- Answer 'unknown' if you cannot determine"""

            cases.append({
                "case_id": f"comparison_pos_{i+1}",
                "type": "state_comparison",
                "subtype": "returned",
                "states": [
                    {"pieces": {start_sq: piece}, "squares": []},
                    {"pieces": {middle_sq: piece}, "squares": []},
                    {"pieces": {start_sq: piece}, "squares": []}
                ],
                "label": "States are shown in chronological order (1 → 2 → 3).",
                "question": question,
                "expected": "yes",
                "reasoning": f"Piece started at {start_sq} and returned to {start_sq}"
            })

        # Negative cases
        for i in range(n_negative):
            piece = self._random_piece()
            sq_a = self._random_square()
            sq_b = self._get_different_square(sq_a)
            sq_c = self._get_different_square(sq_a)
            while sq_c == sq_b:
                sq_c = self._get_different_square(sq_a)

            question = f"""Did the piece return to its starting position?
- Answer 'yes' if the piece is at the same position in State 3 as in State 1
- Answer 'no' if the piece is at a different position
- Answer 'unknown' if you cannot determine"""

            cases.append({
                "case_id": f"comparison_neg_{i+1}",
                "type": "state_comparison",
                "subtype": "not_returned",
                "states": [
                    {"pieces": {sq_a: piece}, "squares": []},
                    {"pieces": {sq_b: piece}, "squares": []},
                    {"pieces": {sq_c: piece}, "squares": []}
                ],
                "label": "States are shown in chronological order (1 → 2 → 3).",
                "question": question,
                "expected": "no",
                "reasoning": f"Piece started at {sq_a} but ended at {sq_c}"
            })

        return cases

    # ============= Type 4: Position Tracking =============

    def generate_position_tracking_tests(self, n_positive: int = 5, n_negative: int = 5) -> List[Dict]:
        cases = []

        # Positive cases
        for i in range(n_positive):
            piece = self._random_piece()
            sq_a = self._random_square()
            sq_b = self._get_different_square(sq_a)
            sq_c = self._get_different_square(sq_b)
            while sq_c == sq_a:
                sq_c = self._get_different_square(sq_b)

            visited_state = random.choice([1, 2, 3])
            ask_sq = [sq_a, sq_b, sq_c][visited_state - 1]

            question = f"""At any point in the sequence, was the piece at {ask_sq}?
- Answer 'yes' if the piece was at {ask_sq} in any of the shown states
- Answer 'no' if the piece was never at {ask_sq}
- Answer 'unknown' if you cannot determine"""

            cases.append({
                "case_id": f"tracking_pos_{i+1}",
                "type": "position_tracking",
                "subtype": "was_there",
                "states": [
                    {"pieces": {sq_a: piece}, "squares": []},
                    {"pieces": {sq_b: piece}, "squares": []},
                    {"pieces": {sq_c: piece}, "squares": []}
                ],
                "label": "States are shown in chronological order (1 → 2 → 3).",
                "question": question,
                "expected": "yes",
                "reasoning": f"Piece was at {ask_sq} in State {visited_state}"
            })

        # Negative cases
        for i in range(n_negative):
            piece = self._random_piece()
            sq_a = self._random_square()
            sq_b = self._get_different_square(sq_a)
            sq_c = self._get_different_square(sq_b)
            while sq_c == sq_a:
                sq_c = self._get_different_square(sq_b)

            never_visited = self._random_square()
            while never_visited in [sq_a, sq_b, sq_c]:
                never_visited = self._random_square()

            question = f"""At any point in the sequence, was the piece at {never_visited}?
- Answer 'yes' if the piece was at {never_visited} in any of the shown states
- Answer 'no' if the piece was never at {never_visited}
- Answer 'unknown' if you cannot determine"""

            cases.append({
                "case_id": f"tracking_neg_{i+1}",
                "type": "position_tracking",
                "subtype": "was_not_there",
                "states": [
                    {"pieces": {sq_a: piece}, "squares": []},
                    {"pieces": {sq_b: piece}, "squares": []},
                    {"pieces": {sq_c: piece}, "squares": []}
                ],
                "label": "States are shown in chronological order (1 → 2 → 3).",
                "question": question,
                "expected": "no",
                "reasoning": f"Piece was never at {never_visited} (visited {sq_a}, {sq_b}, {sq_c})"
            })

        return cases

    # ============= Main Generation Method =============

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """
        Generate test cases for all no-rule categories.

        Args:
            n_cases: Total number of cases to generate
        """
        all_cases = []

        # We have 4 main types. Distribute n_cases among them.
        types_counts = self._distribute_counts(n_cases, 4)

        # Order: Movement, Sequence, Comparison, Tracking

        # 1. Movement Detection
        count = types_counts[0]
        n_pos = count // 2
        n_neg = count - n_pos
        print(f"Generating movement detection tests ({count} cases)...")
        all_cases.extend(self.generate_movement_detection_tests(n_pos, n_neg))

        # 2. Sequence Order
        count = types_counts[1]
        n_pos = count // 2
        n_neg = count - n_pos
        print(f"Generating sequence order tests ({count} cases)...")
        all_cases.extend(self.generate_sequence_order_tests(n_pos, n_neg))

        # 3. State Comparison
        count = types_counts[2]
        n_pos = count // 2
        n_neg = count - n_pos
        print(f"Generating state comparison tests ({count} cases)...")
        all_cases.extend(self.generate_state_comparison_tests(n_pos, n_neg))

        # 4. Position Tracking
        count = types_counts[3]
        n_pos = count // 2
        n_neg = count - n_pos
        print(f"Generating position tracking tests ({count} cases)...")
        all_cases.extend(self.generate_position_tracking_tests(n_pos, n_neg))

        print(f"\n✓ Total generated: {len(all_cases)} test cases")
        return all_cases
