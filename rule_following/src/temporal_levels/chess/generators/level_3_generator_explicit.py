"""
Level 3 Generator: Path Blocked Capture (Explicit/Non-Predictive Version)
Aligned with Predictive version - tests temporal changes in path blocking

Shows 3 states (predictive shows 2):
- State 1: Blocking piece on path
- State 2: Blocking piece moves (away or stays on path or new piece enters)
- State 3: Capture result (attacker at target position, target removed)

Question: "Is this capture legal?" (based on State 2 board position)
"""

import random
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict


class Level3Generator:
    """Generate Level 3 test cases - path blocked capture with temporal changes (Explicit version)"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.ranks = ['1', '2', '3', '4', '5', '6', '7', '8']
        self.piece_types = ['rook', 'bishop', 'queen']

    def _random_square(self) -> str:
        return random.choice(self.files) + random.choice(self.ranks)

    def _square_to_coords(self, square: str) -> Tuple[int, int]:
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        return (file, rank)

    def _coords_to_square(self, file: int, rank: int) -> Optional[str]:
        if 0 <= file < 8 and 0 <= rank < 8:
            return chr(ord('a') + file) + str(rank + 1)
        return None

    def _piece_symbol(self, piece_type: str, color: str) -> str:
        symbols = {
            ('rook', 'white'): 'R', ('rook', 'black'): 'r',
            ('bishop', 'white'): 'B', ('bishop', 'black'): 'b',
            ('queen', 'white'): 'Q', ('queen', 'black'): 'q',
            ('knight', 'white'): 'N', ('knight', 'black'): 'n',
            ('pawn', 'white'): 'P', ('pawn', 'black'): 'p',
        }
        return symbols.get((piece_type, color), 'P')

    def _get_opposite_color(self, color: str) -> str:
        return 'black' if color == 'white' else 'white'

    def _get_path_squares(self, start: str, end: str) -> List[str]:
        """Get all squares between two points (excluding endpoints)"""
        start_f, start_r = self._square_to_coords(start)
        end_f, end_r = self._square_to_coords(end)

        df = end_f - start_f
        dr = end_r - start_r

        step_f = 0 if df == 0 else (1 if df > 0 else -1)
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)

        if not ((df == 0 and dr != 0) or (dr == 0 and df != 0) or (abs(df) == abs(dr) and df != 0)):
            return []

        path = []
        curr_f, curr_r = start_f + step_f, start_r + step_r

        while (curr_f, curr_r) != (end_f, end_r):
            sq = self._coords_to_square(curr_f, curr_r)
            if sq:
                path.append(sq)
            curr_f += step_f
            curr_r += step_r

        return path

    def _is_valid_move_for_piece(self, start: str, end: str, piece_type: str) -> bool:
        """Check if move follows piece rules"""
        start_f, start_r = self._square_to_coords(start)
        end_f, end_r = self._square_to_coords(end)

        df = abs(end_f - start_f)
        dr = abs(end_r - start_r)

        if piece_type == 'rook':
            return (df == 0 and dr > 0) or (dr == 0 and df > 0)
        elif piece_type == 'bishop':
            return df == dr and df > 0
        elif piece_type == 'queen':
            return (df == 0 and dr > 0) or (dr == 0 and df > 0) or (df == dr and df > 0)
        elif piece_type == 'knight':
            return (df == 2 and dr == 1) or (df == 1 and dr == 2)
        return False

    def _get_knight_moves(self, square: str, forbidden: Set[str]) -> List[str]:
        """Get all legal knight move targets"""
        f, r = self._square_to_coords(square)
        moves = []
        for df, dr in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
            sq = self._coords_to_square(f + df, r + dr)
            if sq and sq not in forbidden:
                moves.append(sq)
        return moves

    def _generate_attack_setup(self, piece_type: str) -> Optional[Dict]:
        """Generate basic setup for attacker and target"""
        for _ in range(100):
            attacker_sq = self._random_square()
            attacker_f, attacker_r = self._square_to_coords(attacker_sq)

            if piece_type == 'rook':
                move_type = random.choice(['horizontal', 'vertical'])
                distance = random.randint(4, 6)
                direction = random.choice([-1, 1])

                if move_type == 'horizontal':
                    target_f = attacker_f + direction * distance
                    target_r = attacker_r
                else:
                    target_f = attacker_f
                    target_r = attacker_r + direction * distance

            elif piece_type == 'bishop':
                distance = random.randint(4, 6)
                dir_f = random.choice([-1, 1])
                dir_r = random.choice([-1, 1])
                target_f = attacker_f + dir_f * distance
                target_r = attacker_r + dir_r * distance

            else:  # queen
                move_like = random.choice(['rook', 'bishop'])
                if move_like == 'rook':
                    move_type = random.choice(['horizontal', 'vertical'])
                    distance = random.randint(4, 6)
                    direction = random.choice([-1, 1])
                    if move_type == 'horizontal':
                        target_f = attacker_f + direction * distance
                        target_r = attacker_r
                    else:
                        target_f = attacker_f
                        target_r = attacker_r + direction * distance
                else:
                    distance = random.randint(4, 6)
                    dir_f = random.choice([-1, 1])
                    dir_r = random.choice([-1, 1])
                    target_f = attacker_f + dir_f * distance
                    target_r = attacker_r + dir_r * distance

            if 0 <= target_f < 8 and 0 <= target_r < 8:
                target_sq = self._coords_to_square(target_f, target_r)
                path = self._get_path_squares(attacker_sq, target_sq)

                if len(path) >= 2:
                    return {
                        'attacker_sq': attacker_sq,
                        'target_sq': target_sq,
                        'path': path
                    }

        return None

    # ==================== VALID: PATH CLEARED ====================

    def _generate_path_cleared_case(self, piece_type: str, case_num: int) -> Optional[Dict]:
        """
        Valid: Blocking piece moves away, path opens
        State 1: Blocking piece on path
        State 2: Blocking piece moves away (knight jumps away)
        State 3: Capture completed (attacker at target position)
        Answer: Yes
        """
        setup = self._generate_attack_setup(piece_type)
        if not setup:
            return None

        attacker_sq = setup['attacker_sq']
        target_sq = setup['target_sq']
        path = setup['path']

        attacker_color = random.choice(['white', 'black'])
        target_color = self._get_opposite_color(attacker_color)
        blocker_color = random.choice(['white', 'black'])

        blocker_start = random.choice(path)
        forbidden = {attacker_sq, target_sq, blocker_start}

        knight_moves = self._get_knight_moves(blocker_start, forbidden)
        valid_moves = [sq for sq in knight_moves if sq not in path]

        if not valid_moves:
            return None

        blocker_end = random.choice(valid_moves)

        attacker_symbol = self._piece_symbol(piece_type, attacker_color)
        target_symbol = self._piece_symbol('pawn', target_color)
        blocker_symbol = self._piece_symbol('knight', blocker_color)

        piece_name = piece_type.capitalize()

        # State 1: Blocker on path
        state1 = {
            attacker_sq: attacker_symbol,
            target_sq: target_symbol,
            blocker_start: blocker_symbol
        }

        # State 2: Blocker moved away
        state2 = {
            attacker_sq: attacker_symbol,
            target_sq: target_symbol,
            blocker_end: blocker_symbol
        }

        # State 3: Capture completed
        state3 = {
            target_sq: attacker_symbol,  # Attacker now at target position
            blocker_end: blocker_symbol
            # Target pawn removed
        }

        return {
            "case_id": f"L3_{piece_type}_cleared_{case_num}",
            "type": "path_capture_temporal_explicit",
            "subtype": "path_cleared",
            "piece_type": piece_type,
            "attacker_color": attacker_color,
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []}
            ],
            "question": f"Is this capture by the {piece_name} legal?",
            "expected": "yes",
            "reasoning": f"Knight moved from {blocker_start} to {blocker_end}, path is now clear for capture"
        }

    # ==================== INVALID: STILL BLOCKED ====================

    def _generate_still_blocked_case(self, piece_type: str, case_num: int) -> Optional[Dict]:
        """
        Invalid: Blocking piece moves but still on path
        State 1: Blocking piece at path position A
        State 2: Blocking piece moves to path position B (still blocks)
        State 3: Attempted capture (illegal)
        Answer: No
        """
        setup = self._generate_attack_setup(piece_type)
        if not setup:
            return None

        attacker_sq = setup['attacker_sq']
        target_sq = setup['target_sq']
        path = setup['path']

        if len(path) < 2:
            return None

        attacker_color = random.choice(['white', 'black'])
        target_color = self._get_opposite_color(attacker_color)
        blocker_color = random.choice(['white', 'black'])

        blocker_positions = random.sample(path, 2)
        blocker_start = blocker_positions[0]
        blocker_end = blocker_positions[1]

        # Use Queen as blocker (can move along straight and diagonal lines)
        forbidden = {attacker_sq, target_sq}
        occupied = {attacker_sq, target_sq}

        if not self._is_valid_move_for_piece(blocker_start, blocker_end, 'queen'):
            return None

        move_path = self._get_path_squares(blocker_start, blocker_end)
        for sq in move_path:
            if sq in occupied:
                return None

        attacker_symbol = self._piece_symbol(piece_type, attacker_color)
        target_symbol = self._piece_symbol('pawn', target_color)
        blocker_symbol = self._piece_symbol('queen', blocker_color)

        piece_name = piece_type.capitalize()

        state1 = {
            attacker_sq: attacker_symbol,
            target_sq: target_symbol,
            blocker_start: blocker_symbol
        }

        state2 = {
            attacker_sq: attacker_symbol,
            target_sq: target_symbol,
            blocker_end: blocker_symbol
        }

        # State 3: Attempted capture (blocker still there but we show capture anyway)
        state3 = {
            target_sq: attacker_symbol,
            blocker_end: blocker_symbol
        }

        return {
            "case_id": f"L3_{piece_type}_still_blocked_{case_num}",
            "type": "path_capture_temporal_explicit",
            "subtype": "still_blocked",
            "piece_type": piece_type,
            "attacker_color": attacker_color,
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []}
            ],
            "question": f"Is this capture by the {piece_name} legal?",
            "expected": "no",
            "reasoning": f"Queen moved from {blocker_start} to {blocker_end}, but still blocks the path"
        }

    # ==================== INVALID: PATH BLOCKED ====================

    def _generate_path_blocked_case(self, piece_type: str, case_num: int) -> Optional[Dict]:
        """
        Invalid: Piece moves into path, blocking originally clear path
        State 1: Path clear, piece outside path
        State 2: Piece moves into path
        State 3: Attempted capture (illegal)
        Answer: No
        """
        setup = self._generate_attack_setup(piece_type)
        if not setup:
            return None

        attacker_sq = setup['attacker_sq']
        target_sq = setup['target_sq']
        path = setup['path']

        attacker_color = random.choice(['white', 'black'])
        target_color = self._get_opposite_color(attacker_color)
        blocker_color = random.choice(['white', 'black'])

        blocker_end = random.choice(path)
        forbidden = {attacker_sq, target_sq, blocker_end} | set(path)

        # Find knight position that can jump into path
        end_f, end_r = self._square_to_coords(blocker_end)
        possible_starts = []

        for df, dr in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
            sq = self._coords_to_square(end_f + df, end_r + dr)
            if sq and sq not in forbidden:
                possible_starts.append(sq)

        if not possible_starts:
            return None

        blocker_start = random.choice(possible_starts)

        attacker_symbol = self._piece_symbol(piece_type, attacker_color)
        target_symbol = self._piece_symbol('pawn', target_color)
        blocker_symbol = self._piece_symbol('knight', blocker_color)

        piece_name = piece_type.capitalize()

        state1 = {
            attacker_sq: attacker_symbol,
            target_sq: target_symbol,
            blocker_start: blocker_symbol
        }

        state2 = {
            attacker_sq: attacker_symbol,
            target_sq: target_symbol,
            blocker_end: blocker_symbol
        }

        state3 = {
            target_sq: attacker_symbol,
            blocker_end: blocker_symbol
        }

        return {
            "case_id": f"L3_{piece_type}_blocked_{case_num}",
            "type": "path_capture_temporal_explicit",
            "subtype": "path_blocked",
            "piece_type": piece_type,
            "attacker_color": attacker_color,
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []}
            ],
            "question": f"Is this capture by the {piece_name} legal?",
            "expected": "no",
            "reasoning": f"Knight moved from {blocker_start} to {blocker_end}, now blocks the path"
        }

    # ==================== INVALID: WRONG PATTERN ====================

    def _generate_invalid_pattern_case(self, piece_type: str, case_num: int) -> Optional[Dict]:
        """
        Invalid: Attacker movement pattern is wrong
        Example: Rook moves diagonally, Bishop moves straight
        """
        for _ in range(100):
            attacker_sq = self._random_square()
            attacker_f, attacker_r = self._square_to_coords(attacker_sq)

            if piece_type == 'rook':
                # Rook moves diagonally (wrong)
                distance = random.randint(2, 4)
                dir_f = random.choice([-1, 1])
                dir_r = random.choice([-1, 1])
                target_f = attacker_f + dir_f * distance
                target_r = attacker_r + dir_r * distance
                error_desc = "Rook cannot move diagonally"

            elif piece_type == 'bishop':
                # Bishop moves straight (wrong)
                move_type = random.choice(['horizontal', 'vertical'])
                distance = random.randint(2, 4)
                direction = random.choice([-1, 1])
                if move_type == 'horizontal':
                    target_f = attacker_f + direction * distance
                    target_r = attacker_r
                else:
                    target_f = attacker_f
                    target_r = attacker_r + direction * distance
                error_desc = "Bishop cannot move in straight line"

            else:  # queen
                # Queen moves in L-shape (wrong)
                l_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                           (1, 2), (1, -2), (-1, 2), (-1, -2)]
                df, dr = random.choice(l_moves)
                target_f = attacker_f + df
                target_r = attacker_r + dr
                error_desc = "Queen cannot move in L-shape"

            if 0 <= target_f < 8 and 0 <= target_r < 8:
                target_sq = self._coords_to_square(target_f, target_r)

                attacker_color = random.choice(['white', 'black'])
                target_color = self._get_opposite_color(attacker_color)

                forbidden = {attacker_sq, target_sq}
                extra_sq = None
                for _ in range(50):
                    sq = self._random_square()
                    if sq not in forbidden:
                        extra_sq = sq
                        break

                attacker_symbol = self._piece_symbol(
                    piece_type, attacker_color)
                target_symbol = self._piece_symbol('pawn', target_color)

                state1_pieces = {
                    attacker_sq: attacker_symbol,
                    target_sq: target_symbol,
                }

                state2_pieces = {
                    attacker_sq: attacker_symbol,
                    target_sq: target_symbol,
                }

                if extra_sq:
                    extra_color = random.choice(['white', 'black'])
                    extra_symbol = self._piece_symbol('knight', extra_color)

                    extra_moves = self._get_knight_moves(extra_sq, forbidden)
                    if extra_moves:
                        extra_end = random.choice(extra_moves)
                        state1_pieces[extra_sq] = extra_symbol
                        state2_pieces[extra_end] = extra_symbol

                        # State 3 with extra piece
                        state3_pieces = {
                            target_sq: attacker_symbol,
                            extra_end: extra_symbol
                        }
                    else:
                        state3_pieces = {
                            target_sq: attacker_symbol,
                        }
                else:
                    state3_pieces = {
                        target_sq: attacker_symbol,
                    }

                piece_name = piece_type.capitalize()

                return {
                    "case_id": f"L3_{piece_type}_invalid_{case_num}",
                    "type": "path_capture_temporal_explicit",
                    "subtype": "invalid_pattern",
                    "piece_type": piece_type,
                    "attacker_color": attacker_color,
                    "states": [
                        {"pieces": state1_pieces, "squares": []},
                        {"pieces": state2_pieces, "squares": []},
                        {"pieces": state3_pieces, "squares": []}
                    ],
                    "question": f"Is this capture by the {piece_name} legal?",
                    "expected": "no",
                    "reasoning": error_desc
                }

        return None

    # ==================== GENERATE ALL ====================

    def generate_all(self, n_cases: int = 90) -> List[Dict]:
        """Generate all Level 3 test cases"""
        all_cases = []

        cases_per_piece = n_cases // 3
        remainder = n_cases % 3

        for idx, piece_type in enumerate(self.piece_types):
            n_piece_cases = cases_per_piece + (1 if idx < remainder else 0)

            # Distribution: 25% valid, 75% invalid
            n_valid = n_piece_cases // 4
            n_still_blocked = n_piece_cases // 4
            n_path_blocked = n_piece_cases // 4
            n_invalid = n_piece_cases - n_valid - n_still_blocked - n_path_blocked

            print(f"Generating {piece_type} tests...")

            # Valid: path cleared
            cleared_count = 0
            for _ in range(n_valid * 10):
                if cleared_count >= n_valid:
                    break
                case = self._generate_path_cleared_case(
                    piece_type, cleared_count + 1)
                if case:
                    all_cases.append(case)
                    cleared_count += 1
            print(f"  ✓ Generated {cleared_count} path_cleared cases")

            # Invalid: still blocked
            still_count = 0
            for _ in range(n_still_blocked * 10):
                if still_count >= n_still_blocked:
                    break
                case = self._generate_still_blocked_case(
                    piece_type, still_count + 1)
                if case:
                    all_cases.append(case)
                    still_count += 1
            print(f"  ✓ Generated {still_count} still_blocked cases")

            # Invalid: path blocked
            blocked_count = 0
            for _ in range(n_path_blocked * 10):
                if blocked_count >= n_path_blocked:
                    break
                case = self._generate_path_blocked_case(
                    piece_type, blocked_count + 1)
                if case:
                    all_cases.append(case)
                    blocked_count += 1
            print(f"  ✓ Generated {blocked_count} path_blocked cases")

            # Invalid: wrong pattern
            invalid_count = 0
            for _ in range(n_invalid * 10):
                if invalid_count >= n_invalid:
                    break
                case = self._generate_invalid_pattern_case(
                    piece_type, invalid_count + 1)
                if case:
                    all_cases.append(case)
                    invalid_count += 1
            print(f"  ✓ Generated {invalid_count} invalid_pattern cases")

        random.shuffle(all_cases)

        # Statistics
        stats = defaultdict(int)
        for case in all_cases:
            stats[case['subtype']] += 1

        print(f"\n✓ Total generated: {len(all_cases)} Level 3 test cases")
        print(f"  Breakdown:")
        for subtype, count in sorted(stats.items()):
            print(f"    {subtype}: {count} ({count/len(all_cases)*100:.1f}%)")

        return all_cases
