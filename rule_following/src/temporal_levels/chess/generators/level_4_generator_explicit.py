"""
Level 4 Generator: En Passant + Constraints (Explicit/Non-Predictive Version)
Aligned with Predictive version - tests en passant timing and check constraints

Shows N+1 states (predictive shows N):
- valid: 3 states (was 2)
- missed_timing: 4 states (was 3)
- causes_check_pin: 3 states (was 2)
- already_in_check: 3 states (was 2)

Question: "Is this en passant capture legal?"
"""

import random
from typing import List, Dict, Tuple, Optional


class Level4Generator:
    """Generate Level 4 test cases - en passant with constraints (Explicit version)"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.ranks = ['1', '2', '3', '4', '5', '6', '7', '8']

    def _random_square(self) -> str:
        return random.choice(self.files) + random.choice(self.ranks)

    def _adjacent_files(self, file: str) -> List[str]:
        file_idx = self.files.index(file)
        adjacent = []
        if file_idx > 0:
            adjacent.append(self.files[file_idx - 1])
        if file_idx < 7:
            adjacent.append(self.files[file_idx + 1])
        return adjacent

    def _get_safe_extra_pieces(self, occupied_squares: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """Get 2 random squares for extra pieces"""
        available = [f + r for f in self.files for r in self.ranks
                     if f + r not in occupied_squares]
        if len(available) >= 2:
            return tuple(random.sample(available, 2))
        return None, None

    # ==================== VALID CASES ====================

    def _generate_valid_cases(self, n_cases: int) -> List[Dict]:
        """
        Generate valid en passant cases with extra pieces
        State 1: Initial position (black pawn at start)
        State 2: Black pawn double-stepped
        State 3: En passant capture completed
        """
        cases = []

        valid_combinations = []
        for black_file in ['b', 'c', 'd', 'e', 'f', 'g']:
            black_start = black_file + '7'
            black_end = black_file + '5'
            ep_target = black_file + '6'

            adjacent = self._adjacent_files(black_file)
            for white_file in adjacent:
                white_sq = white_file + '5'
                valid_combinations.append({
                    'white_sq': white_sq,
                    'black_start': black_start,
                    'black_end': black_end,
                    'ep_target': ep_target
                })

        for i in range(n_cases):
            combo = random.choice(valid_combinations)
            white_sq = combo['white_sq']
            black_start = combo['black_start']
            black_end = combo['black_end']
            ep_target = combo['ep_target']

            occupied = [white_sq, black_start, black_end, ep_target]
            extra1, extra2 = self._get_safe_extra_pieces(occupied)

            if extra1 and extra2:
                extra_piece_1 = random.choice(['N', 'B', 'n', 'b'])
                extra_piece_2 = random.choice(['N', 'B', 'n', 'b'])

                # State 1: Initial
                state1 = {
                    white_sq: 'P',
                    black_start: 'p',
                    extra1: extra_piece_1,
                    extra2: extra_piece_2
                }

                # State 2: Black pawn double-stepped
                state2 = {
                    white_sq: 'P',
                    black_end: 'p',
                    extra1: extra_piece_1,
                    extra2: extra_piece_2
                }

                # State 3: En passant completed
                state3 = {
                    ep_target: 'P',  # White pawn at capture square
                    # Black pawn removed
                    extra1: extra_piece_1,
                    extra2: extra_piece_2
                }

                cases.append({
                    "case_id": f"L4_valid_{i+1}",
                    "type": "en_passant_constraint_explicit",
                    "subtype": "valid",
                    "states": [
                        {"pieces": state1, "squares": []},
                        {"pieces": state2, "squares": []},
                        {"pieces": state3, "squares": []}
                    ],
                    "question": "Is this en passant capture legal?",
                    "expected": "yes",
                    "reasoning": "All conditions met, no constraints violated"
                })

        return cases

    # ==================== SCENARIO A: MISSED TIMING ====================

    def _generate_scenario_a_missed_timing(self, n_cases: int) -> List[Dict]:
        """
        Scenario A: Missed timing (4 states instead of 3)
        State 1: Initial
        State 2: Black pawn double-stepped
        State 3: White moves another piece (not en passant) - timing missed
        State 4: Attempted en passant (illegal)
        """
        cases = []

        for i in range(n_cases):
            black_file = random.choice(['b', 'c', 'd', 'e', 'f', 'g'])
            adjacent = self._adjacent_files(black_file)
            white_file = random.choice(adjacent)

            black_start = black_file + '7'
            black_end = black_file + '5'
            white_sq = white_file + '5'
            ep_target = black_file + '6'

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

            occupied = [white_sq, black_start, black_end, ep_target,
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

                    # State 1: Initial
                    state1 = {
                        white_sq: 'P',
                        black_start: 'p',
                        moving_piece_start: moving_piece_symbol,
                        extra_sq: extra_piece
                    }

                    # State 2: Black pawn double-stepped
                    state2 = {
                        white_sq: 'P',
                        black_end: 'p',
                        moving_piece_start: moving_piece_symbol,
                        extra_sq: extra_piece
                    }

                    # State 3: White moved another piece (missed timing)
                    state3 = {
                        white_sq: 'P',
                        black_end: 'p',
                        moving_piece_end: moving_piece_symbol,
                        extra_sq: extra_piece
                    }

                    # State 4: Attempted en passant (illegal)
                    state4 = {
                        ep_target: 'P',
                        # black_end pawn removed - but this is illegal
                        moving_piece_end: moving_piece_symbol,
                        extra_sq: extra_piece
                    }

                    cases.append({
                        "case_id": f"L4_scenario_a_{i+1}",
                        "type": "en_passant_constraint_explicit",
                        "subtype": "missed_timing",
                        "states": [
                            {"pieces": state1, "squares": []},
                            {"pieces": state2, "squares": []},
                            {"pieces": state3, "squares": []},
                            {"pieces": state4, "squares": []}
                        ],
                        "question": "Is this en passant capture legal?",
                        "expected": "no",
                        "reasoning": f"White moved {piece_type} instead of capturing en passant, timing window closed"
                    })

        return cases

    # ==================== SCENARIO B: CAUSES CHECK (PIN) ====================

    def _generate_scenario_b_causes_check(self, n_cases: int) -> List[Dict]:
        """
        Scenario B: En passant would expose King to check (Absolute Pin)
        State 1: Initial (black pawn at start)
        State 2: Black pawn double-stepped
        State 3: Attempted en passant (illegal - would expose king)
        """
        cases = []

        pin_configs = [
            # Vertical Pins
            {'king': 'e1', 'white': 'e5', 'attacker': 'e8', 'attacker_type': 'r',
             'black_start': 'd7', 'black_end': 'd5', 'ep_target': 'd6'},
            {'king': 'e1', 'white': 'e5', 'attacker': 'e8', 'attacker_type': 'q',
             'black_start': 'f7', 'black_end': 'f5', 'ep_target': 'f6'},
            {'king': 'd1', 'white': 'd5', 'attacker': 'd8', 'attacker_type': 'r',
             'black_start': 'c7', 'black_end': 'c5', 'ep_target': 'c6'},
            {'king': 'd1', 'white': 'd5', 'attacker': 'd8', 'attacker_type': 'q',
             'black_start': 'e7', 'black_end': 'e5', 'ep_target': 'e6'},

            # Horizontal Pins
            {'king': 'a5', 'white': 'd5', 'attacker': 'h5', 'attacker_type': 'r',
             'black_start': 'e7', 'black_end': 'e5', 'ep_target': 'e6'},
            {'king': 'h5', 'white': 'f5', 'attacker': 'a5', 'attacker_type': 'q',
             'black_start': 'e7', 'black_end': 'e5', 'ep_target': 'e6'},
        ]

        for i in range(n_cases):
            config = random.choice(pin_configs)

            # State 1: Initial
            state1 = {
                config['white']: 'P',
                config['black_start']: 'p',
                config['king']: 'K',
                config['attacker']: config['attacker_type']
            }

            # State 2: Black pawn double-stepped
            state2 = {
                config['white']: 'P',
                config['black_end']: 'p',
                config['king']: 'K',
                config['attacker']: config['attacker_type']
            }

            # State 3: Attempted en passant (illegal)
            state3 = {
                config['ep_target']: 'P',
                # Black pawn removed - but this exposes king
                config['king']: 'K',
                config['attacker']: config['attacker_type']
            }

            cases.append({
                "case_id": f"L4_scenario_b_{i+1}",
                "type": "en_passant_constraint_explicit",
                "subtype": "causes_check_pin",
                "states": [
                    {"pieces": state1, "squares": []},
                    {"pieces": state2, "squares": []},
                    {"pieces": state3, "squares": []}
                ],
                "question": "Is this en passant capture legal?",
                "expected": "no",
                "reasoning": f"White pawn is pinned by {config['attacker_type']} at {config['attacker']}, capturing would expose King to check"
            })

        return cases

    # ==================== SCENARIO C: ALREADY IN CHECK ====================

    def _generate_scenario_c_in_check(self, n_cases: int) -> List[Dict]:
        """
        Scenario C: King is ALREADY in check.
        En passant does not resolve the check.
        State 1: Initial (black pawn at start)
        State 2: Black pawn double-stepped (king now in check from another piece)
        State 3: Attempted en passant (illegal - doesn't resolve check)
        """
        cases = []

        configs = [
            # Distant Rank Check
            {'king': 'a1', 'attacker': 'h1', 'attacker_type': 'r',
             'white': 'd5', 'black_start': 'e7', 'black_end': 'e5', 'ep_target': 'e6'},

            # Close File Check
            {'king': 'e1', 'attacker': 'e2', 'attacker_type': 'q',
             'white': 'a5', 'black_start': 'b7', 'black_end': 'b5', 'ep_target': 'b6'},

            # Diagonal Check
            {'king': 'e1', 'attacker': 'h4', 'attacker_type': 'b',
             'white': 'b5', 'black_start': 'c7', 'black_end': 'c5', 'ep_target': 'c6'},

            # Knight Check (cannot be blocked)
            {'king': 'e1', 'attacker': 'c2', 'attacker_type': 'n',
             'white': 'g5', 'black_start': 'h7', 'black_end': 'h5', 'ep_target': 'h6'},
        ]

        for i in range(n_cases):
            config = random.choice(configs)

            # State 1: Initial
            state1 = {
                config['white']: 'P',
                config['black_start']: 'p',
                config['king']: 'K',
                config['attacker']: config['attacker_type']
            }

            # State 2: Black pawn double-stepped (king in check)
            state2 = {
                config['white']: 'P',
                config['black_end']: 'p',
                config['king']: 'K',
                config['attacker']: config['attacker_type']
            }

            # State 3: Attempted en passant (doesn't resolve check)
            state3 = {
                config['ep_target']: 'P',
                config['king']: 'K',
                config['attacker']: config['attacker_type']
            }

            cases.append({
                "case_id": f"L4_scenario_c_{i+1}",
                "type": "en_passant_constraint_explicit",
                "subtype": "already_in_check",
                "states": [
                    {"pieces": state1, "squares": []},
                    {"pieces": state2, "squares": []},
                    {"pieces": state3, "squares": []}
                ],
                "question": "Is this en passant capture legal?",
                "expected": "no",
                "reasoning": f"King at {config['king']} is in check from {config['attacker']}, en passant does not resolve the check"
            })

        return cases

    # ==================== GENERATE ALL ====================

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """Generate all Level 4 test cases"""
        all_cases = []

        n_valid = int(n_cases * 0.20)
        n_invalid = n_cases - n_valid

        n_scenario_a = n_invalid // 3
        n_scenario_b = n_invalid // 3
        n_scenario_c = n_invalid - n_scenario_a - n_scenario_b

        print(f"Generating valid en passant cases...")
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

        random.shuffle(all_cases)

        print(f"\n✓ Total generated: {len(all_cases)} Level 4 test cases")
        print(
            f"  Valid: {len(valid_cases)} ({len(valid_cases)/len(all_cases)*100:.1f}%)")
        print(
            f"  Invalid: {len(all_cases) - len(valid_cases)} ({(len(all_cases) - len(valid_cases))/len(all_cases)*100:.1f}%)")

        return all_cases
