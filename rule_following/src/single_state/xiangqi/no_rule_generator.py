"""
Automated test case generator for Xiangqi Single State Test 0 (No Rules)
Pure spatial reasoning on 9x10 board without xiangqi rules
"""

import random
from typing import List, Dict, Tuple


class XiangqiNoRuleGenerator:
    """Generate spatial reasoning test cases for xiangqi board"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']  # 9 columns
        self.rows = [str(i) for i in range(10)]  # 0-9

        self.test_types = [
            'same_file', 'same_rank', 'diagonal', 'direction',
            'river_position', 'path_clear'
        ]

    def _square_to_coords(self, square: str) -> Tuple[int, int]:
        col = ord(square[0]) - ord('a')
        row = int(square[1])
        return (col, row)

    def _coords_to_square(self, col: int, row: int) -> str:
        return chr(ord('a') + col) + str(row)

    def _random_square(self) -> str:
        return random.choice(self.cols) + random.choice(self.rows)

    def _random_square_pair(self) -> Tuple[str, str]:
        sq1 = self._random_square()
        sq2 = self._random_square()
        while sq1 == sq2:
            sq2 = self._random_square()
        return sq1, sq2

    # ============= Type 1: Same Line =============

    def generate_same_file_tests(self, n_pos: int = 5, n_neg: int = 5) -> List[Dict]:
        """Generate same file (vertical line) tests"""
        cases = []
        for i in range(n_pos):
            col = random.choice(self.cols)
            r1, r2 = random.sample(self.rows, 2)
            sq1, sq2 = col + r1, col + r2
            cases.append({
                "case_id": f"same_file_pos_{i+1}", "type": "same_line", "subtype": "same_file",
                "pieces": {}, "squares": [sq1, sq2],
                "question": "Are the highlighted squares on the same file (vertical line)?",
                "expected": "yes", "reasoning": f"Both on file {col}"
            })
        for i in range(n_neg):
            sq1, sq2 = self._random_square_pair()
            while sq1[0] == sq2[0]:
                sq2 = self._random_square()
            cases.append({
                "case_id": f"same_file_neg_{i+1}", "type": "same_line", "subtype": "same_file",
                "pieces": {}, "squares": [sq1, sq2],
                "question": "Are the highlighted squares on the same file (vertical line)?",
                "expected": "no", "reasoning": f"Different files: {sq1[0]} vs {sq2[0]}"
            })
        return cases

    def generate_same_rank_tests(self, n_pos: int = 5, n_neg: int = 5) -> List[Dict]:
        """Generate same rank (horizontal line) tests"""
        cases = []
        for i in range(n_pos):
            row = random.choice(self.rows)
            c1, c2 = random.sample(self.cols, 2)
            sq1, sq2 = c1 + row, c2 + row
            cases.append({
                "case_id": f"same_rank_pos_{i+1}", "type": "same_line", "subtype": "same_rank",
                "pieces": {}, "squares": [sq1, sq2],
                "question": "Are the highlighted squares on the same rank (horizontal line)?",
                "expected": "yes", "reasoning": f"Both on rank {row}"
            })
        for i in range(n_neg):
            sq1, sq2 = self._random_square_pair()
            while sq1[1:] == sq2[1:]:
                sq2 = self._random_square()
            cases.append({
                "case_id": f"same_rank_neg_{i+1}", "type": "same_line", "subtype": "same_rank",
                "pieces": {}, "squares": [sq1, sq2],
                "question": "Are the highlighted squares on the same rank (horizontal line)?",
                "expected": "no", "reasoning": f"Different ranks: {sq1[1:]} vs {sq2[1:]}"
            })
        return cases

    # ============= Type 2: Diagonal =============

    def _on_same_diagonal(self, sq1: str, sq2: str) -> bool:
        c1, r1 = self._square_to_coords(sq1)
        c2, r2 = self._square_to_coords(sq2)
        return abs(c1 - c2) == abs(r1 - r2) and sq1 != sq2

    def generate_diagonal_tests(self, n_pos: int = 5, n_neg: int = 5) -> List[Dict]:
        """Generate diagonal tests"""
        cases = []
        attempts = 0
        while len([c for c in cases if c['expected'] == 'yes']) < n_pos and attempts < 1000:
            sq1, sq2 = self._random_square_pair()
            if self._on_same_diagonal(sq1, sq2):
                cases.append({
                    "case_id": f"diagonal_pos_{len([c for c in cases if c['expected']=='yes'])+1}",
                    "type": "diagonal", "pieces": {}, "squares": [sq1, sq2],
                    "question": "Are the highlighted squares on the same diagonal?",
                    "expected": "yes", "reasoning": "On same diagonal"
                })
            attempts += 1
        attempts = 0
        while len([c for c in cases if c['expected'] == 'no']) < n_neg and attempts < 1000:
            sq1, sq2 = self._random_square_pair()
            if not self._on_same_diagonal(sq1, sq2):
                cases.append({
                    "case_id": f"diagonal_neg_{len([c for c in cases if c['expected']=='no'])+1}",
                    "type": "diagonal", "pieces": {}, "squares": [sq1, sq2],
                    "question": "Are the highlighted squares on the same diagonal?",
                    "expected": "no", "reasoning": "Not on same diagonal"
                })
            attempts += 1
        return cases

    # ============= Type 3: Relative Position =============

    def _get_direction(self, from_sq: str, to_sq: str) -> str:
        c1, r1 = self._square_to_coords(from_sq)
        c2, r2 = self._square_to_coords(to_sq)
        dc, dr = c2 - c1, r2 - r1
        if dc == 0 and dr > 0:
            return "north"
        if dc > 0 and dr > 0:
            return "northeast"
        if dc > 0 and dr == 0:
            return "east"
        if dc > 0 and dr < 0:
            return "southeast"
        if dc == 0 and dr < 0:
            return "south"
        if dc < 0 and dr < 0:
            return "southwest"
        if dc < 0 and dr == 0:
            return "west"
        if dc < 0 and dr > 0:
            return "northwest"
        return "same"

    def _has_direction_component(self, actual_dir: str, target_dir: str) -> bool:
        """Check if actual direction contains any component of target direction"""
        north_dirs = ["north", "northeast", "northwest"]
        south_dirs = ["south", "southeast", "southwest"]
        east_dirs = ["east", "northeast", "southeast"]
        west_dirs = ["west", "northwest", "southwest"]

        direction_map = {
            "north": north_dirs,
            "south": south_dirs,
            "east": east_dirs,
            "west": west_dirs,
            "northeast": ["northeast"],
            "southeast": ["southeast"],
            "southwest": ["southwest"],
            "northwest": ["northwest"],
        }
        return actual_dir in direction_map.get(target_dir, [])

    def generate_direction_tests(self, n_cases: int = 16) -> List[Dict]:
        """Generate relative position tests with total case count"""
        cases = []
        directions = ["north", "northeast", "east", "southeast",
                      "south", "southwest", "west", "northwest"]

        n_per_dir = n_cases // 8
        remainder = n_cases % 8

        for idx, direction in enumerate(directions):

            dir_cases = n_per_dir + (1 if idx < remainder else 0)
            n_pos = dir_cases // 2
            n_neg = dir_cases - n_pos

            # Positive cases: exact match
            pos_count, attempts = 0, 0
            while pos_count < n_pos and attempts < 200:
                sq1, sq2 = self._random_square_pair()
                if self._get_direction(sq1, sq2) == direction:
                    cases.append({
                        "case_id": f"dir_{direction}_pos_{pos_count+1}",
                        "type": "relative_position", "pieces": {}, "squares": [sq1, sq2],
                        "question": f"Is {sq2} {direction} of the other highlighted square?",
                        "expected": "yes", "reasoning": f"{sq2} is {direction} of {sq1}"
                    })
                    pos_count += 1
                attempts += 1
            # Negative cases
            neg_count, attempts = 0, 0
            while neg_count < n_neg and attempts < 200:
                sq1, sq2 = self._random_square_pair()
                actual = self._get_direction(sq1, sq2)
                if actual != "same" and not self._has_direction_component(actual, direction):
                    cases.append({
                        "case_id": f"dir_{direction}_neg_{neg_count+1}",
                        "type": "relative_position", "pieces": {}, "squares": [sq1, sq2],
                        "question": f"Is {sq2} {direction} of the other highlighted square?",
                        "expected": "no", "reasoning": f"{sq2} is {actual} of {sq1}, no {direction} component"
                    })
                    neg_count += 1
                attempts += 1
        return cases

    # ============= Type 4: River Position =============

    def generate_river_tests(self, n_pos: int = 5, n_neg: int = 5) -> List[Dict]:
        """Test if square is on specific side of river (xiangqi-specific spatial)"""
        cases = []
        for i in range(n_pos):
            row = random.randint(5, 9)
            col = random.choice(self.cols)
            sq = col + str(row)
            cases.append({
                "case_id": f"river_north_pos_{i+1}", "type": "river_position",
                "pieces": {}, "squares": [sq],
                "question": f"Is {sq} on the north side of the river (rows 5-9)?",
                "expected": "yes", "reasoning": f"Row {row} >= 5"
            })
        for i in range(n_neg):
            row = random.randint(0, 4)
            col = random.choice(self.cols)
            sq = col + str(row)
            cases.append({
                "case_id": f"river_north_neg_{i+1}", "type": "river_position",
                "pieces": {}, "squares": [sq],
                "question": f"Is {sq} on the north side of the river (rows 5-9)?",
                "expected": "no", "reasoning": f"Row {row} < 5"
            })
        return cases

    # ============= Type 5: Path Clear =============

    def generate_path_clear_tests(self, n_pos: int = 5, n_neg: int = 5) -> List[Dict]:
        """Generate path clearance tests"""
        cases = []
        for i in range(n_pos):
            if random.choice([True, False]):
                col = random.choice(self.cols)
                rows = sorted(random.sample([int(r) for r in self.rows], 2))
                sq1, sq2 = col + str(rows[0]), col + str(rows[1])
            else:
                row = random.choice(self.rows)
                cols = sorted(random.sample(self.cols, 2))
                sq1, sq2 = cols[0] + row, cols[1] + row
            pieces = {}
            for _ in range(random.randint(1, 2)):
                p_sq = self._random_square()
                c, r = self._square_to_coords(p_sq)
                c1, r1 = self._square_to_coords(sq1)
                c2, r2 = self._square_to_coords(sq2)
                if not ((c1 == c2 == c and min(r1, r2) < r < max(r1, r2)) or
                        (r1 == r2 == r and min(c1, c2) < c < max(c1, c2))):
                    pieces[p_sq] = 'P'
            cases.append({
                "case_id": f"path_clear_pos_{i+1}", "type": "path_clear",
                "pieces": pieces, "squares": [sq1, sq2],
                "question": "Is the path between the two highlighted squares clear?",
                "expected": "yes", "reasoning": "No pieces block the path"
            })
        for i in range(n_neg):
            if random.choice([True, False]):
                col = random.choice(self.cols)
                rows = sorted(random.sample(
                    [int(r) for r in self.rows if int(r) < 8], 2))
                if rows[1] - rows[0] <= 1:
                    rows[1] = rows[0] + 2
                block_row = random.randint(rows[0]+1, rows[1]-1)
                sq1, sq2 = col + str(rows[0]), col + str(rows[1])
                block_sq = col + str(block_row)
            else:
                row = random.choice(self.rows)
                col_indices = sorted(random.sample(range(7), 2))
                if col_indices[1] - col_indices[0] <= 1:
                    col_indices[1] = col_indices[0] + 2
                block_idx = random.randint(col_indices[0]+1, col_indices[1]-1)
                sq1 = self.cols[col_indices[0]] + row
                sq2 = self.cols[col_indices[1]] + row
                block_sq = self.cols[block_idx] + row
            pieces = {block_sq: 'P'}
            cases.append({
                "case_id": f"path_clear_neg_{i+1}", "type": "path_clear",
                "pieces": pieces, "squares": [sq1, sq2],
                "question": "Is the path between the two highlighted squares clear?",
                "expected": "no", "reasoning": f"Path blocked by piece at {block_sq}"
            })
        return cases

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """
        Generate comprehensive test suite with total case count.
        Cases are distributed proportionally across 6 test types.
        """
        all_cases = []

        n_types = 6
        cases_per_type = n_cases // n_types
        remainder = n_cases % n_types

        type_counts = []
        for i in range(n_types):
            count = cases_per_type + (1 if i < remainder else 0)
            type_counts.append(count)

        print(f"Generating {n_cases} total cases across {n_types} types...")
        print(f"Distribution: {type_counts}")

        # Type 0: same_file
        n = type_counts[0]
        n_pos, n_neg = n // 2, n - n // 2
        print(f"Generating same file tests ({n_pos} pos + {n_neg} neg)...")
        all_cases.extend(self.generate_same_file_tests(n_pos, n_neg))

        # Type 1: same_rank
        n = type_counts[1]
        n_pos, n_neg = n // 2, n - n // 2
        print(f"Generating same rank tests ({n_pos} pos + {n_neg} neg)...")
        all_cases.extend(self.generate_same_rank_tests(n_pos, n_neg))

        # Type 2: diagonal
        n = type_counts[2]
        n_pos, n_neg = n // 2, n - n // 2
        print(f"Generating diagonal tests ({n_pos} pos + {n_neg} neg)...")
        all_cases.extend(self.generate_diagonal_tests(n_pos, n_neg))

        # Type 3: direction (8 directions)
        n = type_counts[3]
        print(f"Generating direction tests ({n} total)...")
        all_cases.extend(self.generate_direction_tests(n))

        # Type 4: river_position
        n = type_counts[4]
        n_pos, n_neg = n // 2, n - n // 2
        print(
            f"Generating river position tests ({n_pos} pos + {n_neg} neg)...")
        all_cases.extend(self.generate_river_tests(n_pos, n_neg))

        # Type 5: path_clear
        n = type_counts[5]
        n_pos, n_neg = n // 2, n - n // 2
        print(f"Generating path clear tests ({n_pos} pos + {n_neg} neg)...")
        all_cases.extend(self.generate_path_clear_tests(n_pos, n_neg))

        print(f"\n✓ Total generated: {len(all_cases)} test cases")
        return all_cases
