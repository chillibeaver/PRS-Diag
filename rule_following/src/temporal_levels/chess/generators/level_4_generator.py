"""
Level 4 Generator: En Passant + Constraints
Tests en passant timing and check constraints
"""

import random
from typing import List, Dict, Tuple


class Level4Generator:
    """Generate Level 4 test cases - en passant with constraints"""

    def __init__(self, seed: int = 42):
        """
        Initialize generator

        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        self.files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.ranks = ['1', '2', '3', '4', '5', '6', '7', '8']

    def _random_square(self) -> str:
        """Generate random square"""
        return random.choice(self.files) + random.choice(self.ranks)

    def _adjacent_files(self, file: str) -> List[str]:
        """Get adjacent files"""
        file_idx = self.files.index(file)
        adjacent = []
        if file_idx > 0:
            adjacent.append(self.files[file_idx - 1])
        if file_idx < 7:
            adjacent.append(self.files[file_idx + 1])
        return adjacent

    def _is_square_blocking_check(self, king_sq: str, attacker_sq: str, blocker_sq: str) -> bool:
        """
        Check if a square blocks the line between king and attacker
        """
        if blocker_sq == king_sq or blocker_sq == attacker_sq:
            return False

        king_f, king_r = ord(king_sq[0]) - ord('a'), int(king_sq[1]) - 1
        att_f, att_r = ord(attacker_sq[0]) - ord('a'), int(attacker_sq[1]) - 1
        block_f, block_r = ord(
            blocker_sq[0]) - ord('a'), int(blocker_sq[1]) - 1

        # Check if on same file (vertical line)
        if king_f == att_f == block_f:
            min_r, max_r = sorted([king_r, att_r])
            return min_r < block_r < max_r

        # Check if on same rank (horizontal line)
        if king_r == att_r == block_r:
            min_f, max_f = sorted([king_f, att_f])
            return min_f < block_f < max_f

        # Check if on diagonal
        if abs(att_f - king_f) == abs(att_r - king_r):
            if abs(block_f - king_f) == abs(block_r - king_r):
                if king_f < att_f:
                    return king_f < block_f < att_f
                else:
                    return att_f < block_f < king_f

        return False

    def _get_safe_extra_pieces(self, occupied_squares: List[str]) -> Tuple[str, str]:
        """Get 2 random squares for extra pieces"""
        available = [f + r for f in self.files for r in self.ranks
                     if f + r not in occupied_squares]

        if len(available) >= 2:
            return random.sample(available, 2)
        return None, None

    def _generate_valid_cases(self, n_cases: int) -> List[Dict]:
        """Generate valid en passant cases with extra pieces"""
        cases = []

        valid_combinations = []
        for black_file in ['b', 'c', 'd', 'e', 'f', 'g']:
            black_start = black_file + '7'
            black_end = black_file + '5'

            adjacent = self._adjacent_files(black_file)
            for white_file in adjacent:
                white_sq = white_file + '5'
                valid_combinations.append({
                    'white_sq': white_sq,
                    'black_start': black_start,
                    'black_end': black_end
                })

        for i in range(n_cases):
            combo = random.choice(valid_combinations)
            white_sq = combo['white_sq']
            black_start = combo['black_start']
            black_end = combo['black_end']

            occupied = [white_sq, black_start, black_end]
            extra1, extra2 = self._get_safe_extra_pieces(occupied)

            if extra1 and extra2:
                extra_piece_1 = random.choice(['N', 'B', 'n', 'b'])
                extra_piece_2 = random.choice(['N', 'B', 'n', 'b'])

                cases.append({
                    "case_id": f"L4_valid_{i+1}",
                    "type": "en_passant_constraint",
                    "subtype": "valid",
                    "states": [
                        {
                            "pieces": {
                                white_sq: 'P',
                                black_start: 'p',
                                extra1: extra_piece_1,
                                extra2: extra_piece_2
                            },
                            "squares": []
                        },
                        {
                            "pieces": {
                                white_sq: 'P',
                                black_end: 'p',
                                extra1: extra_piece_1,
                                extra2: extra_piece_2
                            },
                            "squares": []
                        }
                    ],
                    "question": "Can white capture the black pawn en passant?",
                    "expected": "yes",
                    "reasoning": "All conditions met, no constraints violated"
                })

        return cases

    def _generate_scenario_a_missed_timing(self, n_cases: int) -> List[Dict]:
        """Scenario A: Missed timing (3 images)"""
        cases = []

        for i in range(n_cases):
            black_file = random.choice(['b', 'c', 'd', 'e', 'f', 'g'])
            adjacent = self._adjacent_files(black_file)
            white_file = random.choice(adjacent)

            black_start = black_file + '7'
            black_mid = black_file + '5'
            white_sq = white_file + '5'

            piece_type = random.choice(['rook', 'knight'])

            if piece_type == 'rook':
                move_type = random.choice(['horizontal', 'vertical'])

                if move_type == 'horizontal':
                    start_file = random.choice(['a', 'h'])
                    start_rank = random.choice(['1', '8'])
                    moving_piece_start = start_file + start_rank
                    end_file = random.choice(['c', 'd', 'e'])
                    moving_piece_end = end_file + start_rank
                else:
                    start_file = random.choice(['a', 'h'])
                    moving_piece_start = start_file + '1'
                    moving_piece_end = start_file + '3'

                moving_piece_symbol = random.choice(['R', 'r'])

            else:
                knight_moves = [
                    ('b1', 'c3'), ('g1', 'f3'), ('b1', 'a3'), ('g1', 'h3'),
                    ('b8', 'c6'), ('g8', 'f6'), ('b8', 'a6'), ('g8', 'h6'),
                    ('a1', 'c2'), ('h1', 'f2'), ('a8', 'c7'), ('h8', 'f7')
                ]

                moving_piece_start, moving_piece_end = random.choice(
                    knight_moves)
                moving_piece_symbol = random.choice(['N', 'n'])

            occupied = [white_sq, black_start, black_mid,
                        moving_piece_start, moving_piece_end]

            if len(occupied) == len(set(occupied)):
                extra_sq = None
                for _ in range(50):
                    candidate = self._random_square()
                    if candidate not in occupied:
                        extra_sq = candidate
                        break

                if extra_sq:
                    extra_piece = random.choice(['N', 'B', 'n', 'b'])

                    cases.append({
                        "case_id": f"L4_scenario_a_{i+1}",
                        "type": "en_passant_constraint",
                        "subtype": "missed_timing",
                        "states": [
                            {
                                "pieces": {
                                    white_sq: 'P',
                                    black_start: 'p',
                                    moving_piece_start: moving_piece_symbol,
                                    extra_sq: extra_piece
                                },
                                "squares": []
                            },
                            {
                                "pieces": {
                                    white_sq: 'P',
                                    black_mid: 'p',
                                    moving_piece_start: moving_piece_symbol,
                                    extra_sq: extra_piece
                                },
                                "squares": []
                            },
                            {
                                "pieces": {
                                    white_sq: 'P',
                                    black_mid: 'p',
                                    moving_piece_end: moving_piece_symbol,
                                    extra_sq: extra_piece
                                },
                                "squares": []
                            }
                        ],
                        "question": "Can white capture the black pawn en passant in the position shown in State 3?",
                        "expected": "no",
                        "reasoning": f"White moved {piece_type} instead, timing window closed"
                    })

        return cases

    def _generate_scenario_b_causes_check(self, n_cases: int) -> List[Dict]:
        """
        Scenario B: En passant would expose King to check (Absolute Pin)
        Fixed logic: ONLY Horizontal and Vertical pins to avoid geometric loopholes.
        """
        cases = []

        # Configurations where White Pawn is pinned
        # STRICTLY Vertical or Horizontal

        pin_configs = [
            # --- Vertical Pins (File Open) ---
            # King e1, White P e5, Black R/Q e8.
            # Black P moves d7->d5. White P (e5) captures d5 (lands on d6).
            # e-file opens (e5 is now empty). King e1 exposed to e8. -> Illegal.
            {'king': 'e1', 'white': 'e5', 'attacker': 'e8', 'attacker_type': 'r',
             'black_start': 'd7', 'black_end': 'd5'},
            {'king': 'e1', 'white': 'e5', 'attacker': 'e8', 'attacker_type': 'q',
             'black_start': 'f7', 'black_end': 'f5'},

            # King d1, White P d5, Black R/Q d8.
            # Black P moves c7->c5. White P (d5) captures c5 (lands c6).
            # d-file opens (d5 is empty). King d1 exposed to d8. -> Illegal.
            {'king': 'd1', 'white': 'd5', 'attacker': 'd8', 'attacker_type': 'r',
             'black_start': 'c7', 'black_end': 'c5'},
            {'king': 'd1', 'white': 'd5', 'attacker': 'd8', 'attacker_type': 'q',
             'black_start': 'e7', 'black_end': 'e5'},

            # --- Horizontal Pins (Rank Open) ---
            # King a5, White P d5, Black R/Q h5.
            # Black P moves e7->e5. White P (d5) captures e5 (lands e6).
            # Rank 5 opens (d5 is empty). King a5 exposed to h5. -> Illegal.
            {'king': 'a5', 'white': 'd5', 'attacker': 'h5', 'attacker_type': 'r',
             'black_start': 'e7', 'black_end': 'e5'},

            # King h5, White P f5, Black R/Q a5.
            # Black P moves e7->e5. White P (f5) captures e5 (lands e6).
            # Rank 5 opens (f5 is empty). King h5 exposed to a5. -> Illegal.
            {'king': 'h5', 'white': 'f5', 'attacker': 'a5', 'attacker_type': 'q',
             'black_start': 'e7', 'black_end': 'e5'},
        ]

        for i in range(n_cases):
            config = random.choice(pin_configs)

            cases.append({
                "case_id": f"L4_scenario_b_{i+1}",
                "type": "en_passant_constraint",
                "subtype": "causes_check_pin",
                "states": [
                    {
                        "pieces": {
                            config['white']: 'P',
                            config['black_start']: 'p',
                            config['king']: 'K',
                            config['attacker']: config['attacker_type']
                        },
                        "squares": []
                    },
                    {
                        "pieces": {
                            config['white']: 'P',
                            config['black_end']: 'p',
                            config['king']: 'K',
                            config['attacker']: config['attacker_type']
                        },
                        "squares": []
                    }
                ],
                "question": "Can white capture the black pawn en passant?",
                "expected": "no",
                "reasoning": f"White pawn is pinned by {config['attacker_type']} at {config['attacker']}, capturing would expose King to check"
            })

        return cases

    def _generate_scenario_c_in_check(self, n_cases: int) -> List[Dict]:
        """
        Scenario C: King is ALREADY in check.
        White must resolve the check. En Passant does not resolve it.
        """
        cases = []

        # Configurations where White King is ALREADY in check
        # and the En Passant move happens elsewhere and doesn't block the check.

        configs = [
            # 1. Distant Rank Check (Attacker on h1, King a1)
            # En passant happening in the middle (d/e file) irrelevant to Rank 1.
            {'king': 'a1', 'attacker': 'h1', 'attacker_type': 'r',
             'white': 'd5', 'black_start': 'e7', 'black_end': 'e5'},

            # 2. Close File Check (Attacker e2, King e1)
            # En passant on a/b files (far left), cannot block e-file check.
            {'king': 'e1', 'attacker': 'e2', 'attacker_type': 'q',
             'white': 'a5', 'black_start': 'b7', 'black_end': 'b5'},

            # 3. Distant Diagonal Check (Attacker h4, King e1)
            # En passant on b5/c5 (far left), cannot block e1-h4 diagonal.
            {'king': 'e1', 'attacker': 'h4', 'attacker_type': 'b',
             'white': 'b5', 'black_start': 'c7', 'black_end': 'c5'},

            # 4. Knight Check (Cannot be blocked)
            # Knight c2 checks King e1. En Passant happens at g5/h5.
            {'king': 'e1', 'attacker': 'c2', 'attacker_type': 'n',
             'white': 'g5', 'black_start': 'h7', 'black_end': 'h5'},
        ]

        for i in range(n_cases):
            config = random.choice(configs)

            cases.append({
                "case_id": f"L4_scenario_c_{i+1}",
                "type": "en_passant_constraint",
                "subtype": "already_in_check",
                "states": [
                    {
                        "pieces": {
                            config['white']: 'P',
                            config['black_start']: 'p',
                            config['king']: 'K',
                            config['attacker']: config['attacker_type']
                        },
                        "squares": []
                    },
                    {
                        "pieces": {
                            config['white']: 'P',
                            config['black_end']: 'p',
                            config['king']: 'K',
                            config['attacker']: config['attacker_type']
                        },
                        "squares": []
                    }
                ],
                "question": "Can white capture the black pawn en passant?",
                "expected": "no",
                "reasoning": f"King at {config['king']} is currently in check from {config['attacker']}, en passant does not resolve the check"
            })

        return cases

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """Generate all Level 4 test cases"""
        all_cases = []

        n_valid = int(n_cases * 0.20)
        n_invalid = n_cases - n_valid

        n_scenario_a = n_invalid // 3
        n_scenario_b = n_invalid // 3
        n_scenario_c = n_invalid - n_scenario_a - n_scenario_b

        print(f"Generating valid en passant cases with extra pieces...")
        valid_cases = self._generate_valid_cases(n_valid)
        all_cases.extend(valid_cases)
        print(f"  ✓ Generated {len(valid_cases)} valid cases")

        print(f"Generating constraint violations...")

        scenario_a = self._generate_scenario_a_missed_timing(n_scenario_a)
        all_cases.extend(scenario_a)
        print(f"  ✓ Generated {len(scenario_a)} scenario A (missed timing)")

        scenario_b = self._generate_scenario_b_causes_check(n_scenario_b)
        all_cases.extend(scenario_b)
        print(
            f"  ✓ Generated {len(scenario_b)} scenario B (causes check - pin)")

        scenario_c = self._generate_scenario_c_in_check(n_scenario_c)
        all_cases.extend(scenario_c)
        print(f"  ✓ Generated {len(scenario_c)} scenario C (already in check)")

        print(f"\n✓ Total generated: {len(all_cases)} Level 4 test cases")
        print(
            f"  Valid: {len(valid_cases)} ({len(valid_cases)/len(all_cases)*100:.1f}%)")
        print(
            f"  Invalid: {len(all_cases) - len(valid_cases)} ({(len(all_cases) - len(valid_cases))/len(all_cases)*100:.1f}%)")

        return all_cases
