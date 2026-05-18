"""
Automated test case generator for Single State Test 0 (No Rules)
"""

import random
from typing import List, Dict, Tuple


class ChessNoRuleGenerator:
    """Automatically generate spatial reasoning test cases"""

    TEST_TYPES = ['same_file', 'same_rank',
                  'diagonal', 'direction', 'path_clear']
    N_TYPES = 5

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.ranks = ['1', '2', '3', '4', '5', '6', '7', '8']

    def _square_to_coords(self, square: str) -> Tuple[int, int]:
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        return (file, rank)

    def _coords_to_square(self, file: int, rank: int) -> str:
        return chr(ord('a') + file) + str(rank + 1)

    def _random_square(self) -> str:
        file = random.choice(self.files)
        rank = random.choice(self.ranks)
        return file + rank

    def _random_square_pair(self) -> Tuple[str, str]:
        sq1 = self._random_square()
        sq2 = self._random_square()
        while sq1 == sq2:
            sq2 = self._random_square()
        return sq1, sq2

    # ============= Type 1: Same File =============

    def generate_same_file_tests(self, n_positive: int = 5, n_negative: int = 5) -> List[Dict]:
        cases = []
        for i in range(n_positive):
            file = random.choice(self.files)
            rank1, rank2 = random.sample(self.ranks, 2)
            sq1, sq2 = file + rank1, file + rank2
            cases.append({
                "case_id": f"same_file_pos_{i+1}", "type": "same_line", "subtype": "same_file",
                "squares": [sq1, sq2],
                "question": f"Are the highlighted squares on the same file (vertical line)?",
                "expected": "yes", "reasoning": f"Both on file {file}"
            })
        for i in range(n_negative):
            sq1, sq2 = self._random_square_pair()
            while sq1[0] == sq2[0]:
                sq2 = self._random_square()
            cases.append({
                "case_id": f"same_file_neg_{i+1}", "type": "same_line", "subtype": "same_file",
                "squares": [sq1, sq2],
                "question": f"Are the highlighted squares on the same file (vertical line)?",
                "expected": "no", "reasoning": f"Different files: {sq1[0]} vs {sq2[0]}"
            })
        return cases

    # ============= Type 2: Same Rank =============

    def generate_same_rank_tests(self, n_positive: int = 5, n_negative: int = 5) -> List[Dict]:
        cases = []
        for i in range(n_positive):
            rank = random.choice(self.ranks)
            file1, file2 = random.sample(self.files, 2)
            sq1, sq2 = file1 + rank, file2 + rank
            cases.append({
                "case_id": f"same_rank_pos_{i+1}", "type": "same_line", "subtype": "same_rank",
                "squares": [sq1, sq2],
                "question": f"Are the highlighted squares on the same rank (horizontal line)?",
                "expected": "yes", "reasoning": f"Both on rank {rank}"
            })
        for i in range(n_negative):
            sq1, sq2 = self._random_square_pair()
            while sq1[1] == sq2[1]:
                sq2 = self._random_square()
            cases.append({
                "case_id": f"same_rank_neg_{i+1}", "type": "same_line", "subtype": "same_rank",
                "squares": [sq1, sq2],
                "question": f"Are the highlighted squares on the same rank (horizontal line)?",
                "expected": "no", "reasoning": f"Different ranks: {sq1[1]} vs {sq2[1]}"
            })
        return cases

    # ============= Type 3: Diagonal =============

    def _on_same_diagonal(self, sq1: str, sq2: str) -> bool:
        f1, r1 = self._square_to_coords(sq1)
        f2, r2 = self._square_to_coords(sq2)
        return abs(f1 - f2) == abs(r1 - r2) and sq1 != sq2

    def generate_diagonal_tests(self, n_positive: int = 5, n_negative: int = 5) -> List[Dict]:
        cases = []
        attempts = 0
        while len(cases) < n_positive and attempts < 1000:
            sq1, sq2 = self._random_square_pair()
            if self._on_same_diagonal(sq1, sq2):
                cases.append({
                    "case_id": f"diagonal_pos_{len(cases)+1}", "type": "diagonal",
                    "squares": [sq1, sq2],
                    "question": f"Are the highlighted squares on the same diagonal?",
                    "expected": "yes", "reasoning": "On same diagonal"
                })
            attempts += 1

        attempts = 0
        neg_count = 0
        while neg_count < n_negative and attempts < 1000:
            sq1, sq2 = self._random_square_pair()
            if not self._on_same_diagonal(sq1, sq2):
                cases.append({
                    "case_id": f"diagonal_neg_{neg_count+1}", "type": "diagonal",
                    "squares": [sq1, sq2],
                    "question": f"Are the highlighted squares on the same diagonal?",
                    "expected": "no", "reasoning": "Not on same diagonal"
                })
                neg_count += 1
            attempts += 1
        return cases

    # ============= Type 4: Direction =============

    def _get_direction(self, from_sq: str, to_sq: str) -> str:
        f1, r1 = self._square_to_coords(from_sq)
        f2, r2 = self._square_to_coords(to_sq)
        df, dr = f2 - f1, r2 - r1

        if df == 0 and dr > 0:
            return "north"
        elif df > 0 and dr > 0:
            return "northeast"
        elif df > 0 and dr == 0:
            return "east"
        elif df > 0 and dr < 0:
            return "southeast"
        elif df == 0 and dr < 0:
            return "south"
        elif df < 0 and dr < 0:
            return "southwest"
        elif df < 0 and dr == 0:
            return "west"
        elif df < 0 and dr > 0:
            return "northwest"
        return "same"

    def _has_component_of(self, actual_dir: str, target_dir: str) -> bool:
        direction_map = {
            "north": ["north", "northeast", "northwest"],
            "south": ["south", "southeast", "southwest"],
            "east": ["east", "northeast", "southeast"],
            "west": ["west", "northwest", "southwest"],
            "northeast": ["northeast"], "southeast": ["southeast"],
            "southwest": ["southwest"], "northwest": ["northwest"],
        }
        return actual_dir in direction_map.get(target_dir, [])

    def generate_direction_tests(self, n_cases: int = 16) -> List[Dict]:
        cases = []
        directions = ["north", "northeast", "east", "southeast",
                      "south", "southwest", "west", "northwest"]

        n_per_dir = n_cases // 8
        remainder = n_cases % 8

        for idx, direction in enumerate(directions):
            dir_cases = n_per_dir + (1 if idx < remainder else 0)
            n_pos = dir_cases // 2
            n_neg = dir_cases - n_pos

            pos_count, attempts = 0, 0
            while pos_count < n_pos and attempts < 200:
                sq1, sq2 = self._random_square_pair()
                if self._get_direction(sq1, sq2) == direction:
                    cases.append({
                        "case_id": f"dir_{direction}_pos_{pos_count+1}",
                        "type": "relative_position", "squares": [sq1, sq2],
                        "question": f"Is {sq2} {direction} of the other highlighted square?",
                        "expected": "yes", "reasoning": f"{sq2} is indeed {direction} of {sq1}"
                    })
                    pos_count += 1
                attempts += 1

            neg_count, attempts = 0, 0
            while neg_count < n_neg and attempts < 200:
                sq1, sq2 = self._random_square_pair()
                actual_dir = self._get_direction(sq1, sq2)
                if actual_dir != "same" and not self._has_component_of(actual_dir, direction):
                    cases.append({
                        "case_id": f"dir_{direction}_neg_{neg_count+1}",
                        "type": "relative_position", "squares": [sq1, sq2],
                        "question": f"Is {sq2} {direction} of the other highlighted square?",
                        "expected": "no",
                        "reasoning": f"{sq2} is {actual_dir} of {sq1}, no {direction} component"
                    })
                    neg_count += 1
                attempts += 1
        return cases

    # ============= Type 5: Path Clear =============

    def generate_path_clear_tests(self, n_positive: int = 5, n_negative: int = 5) -> List[Dict]:
        cases = []

        for i in range(n_positive):
            if random.choice([True, False]):
                file = random.choice(self.files)
                ranks = sorted(random.sample([int(r) for r in self.ranks], 2))
                pieces = {}
                for _ in range(random.randint(1, 3)):
                    piece_file = random.choice(
                        [f for f in self.files if f != file])
                    piece_rank = str(random.randint(1, 8))
                    pieces[piece_file + piece_rank] = "P"
                sq1 = file + str(ranks[0])
                sq2 = file + str(ranks[1])
            else:
                rank = random.choice(self.ranks)
                files = sorted(random.sample(self.files, 2))
                pieces = {}
                for _ in range(random.randint(1, 3)):
                    piece_file = random.choice(self.files)
                    piece_rank = random.choice(
                        [r for r in self.ranks if r != rank])
                    pieces[piece_file + piece_rank] = "P"
                sq1 = files[0] + rank
                sq2 = files[1] + rank

            cases.append({
                "case_id": f"path_clear_pos_{i+1}", "type": "path_clear",
                "pieces": pieces, "squares": [sq1, sq2],
                "question": f"Is the path between the two highlighted squares clear (no pieces blocking)?",
                "expected": "yes", "reasoning": "No pieces block the path"
            })

        for i in range(n_negative):
            if random.choice([True, False]):
                file = random.choice(self.files)
                ranks = sorted(random.sample([int(r) for r in self.ranks], 2))
                if ranks[1] - ranks[0] > 1:
                    blocking_rank = random.randint(ranks[0] + 1, ranks[1] - 1)
                else:
                    blocking_rank = ranks[0]
                pieces = {file + str(blocking_rank): "P"}
                sq1 = file + str(ranks[0])
                sq2 = file + str(ranks[1])
            else:
                rank = random.choice(self.ranks)
                files = sorted(random.sample(self.files, 2))
                file_idx1 = self.files.index(files[0])
                file_idx2 = self.files.index(files[1])
                if file_idx2 - file_idx1 > 1:
                    blocking_idx = random.randint(file_idx1 + 1, file_idx2 - 1)
                else:
                    blocking_idx = file_idx1
                blocking_file = self.files[blocking_idx]
                pieces = {blocking_file + rank: "P"}
                sq1 = files[0] + rank
                sq2 = files[1] + rank

            cases.append({
                "case_id": f"path_clear_neg_{i+1}", "type": "path_clear",
                "pieces": pieces, "squares": [sq1, sq2],
                "question": f"Is the path between the two highlighted squares clear (no pieces blocking)?",
                "expected": "no", "reasoning": f"Path blocked by piece at {list(pieces.keys())[0]}"
            })
        return cases

    # ============= Main Generation Method =============

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """
        Generate comprehensive test suite with total case count.
        Cases are distributed proportionally across 5 test types.
        """
        all_cases = []

        cases_per_type = n_cases // self.N_TYPES
        remainder = n_cases % self.N_TYPES

        type_counts = [cases_per_type +
                       (1 if i < remainder else 0) for i in range(self.N_TYPES)]

        print(
            f"Generating {n_cases} total cases across {self.N_TYPES} types...")
        print(f"Distribution: {dict(zip(self.TEST_TYPES, type_counts))}")

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

        # Type 4: path_clear
        n = type_counts[4]
        n_pos, n_neg = n // 2, n - n // 2
        print(f"Generating path clear tests ({n_pos} pos + {n_neg} neg)...")
        all_cases.extend(self.generate_path_clear_tests(n_pos, n_neg))

        print(f"\n✓ Total generated: {len(all_cases)} test cases")
        return all_cases
