"""
Xiangqi Level 5 Generator: Capture Constraints (Explicit Mode)
Explicit version: Shows both before and after states, asks if the capture is legal

Tests whether a piece can capture another piece considering:
1. Capture causes check (Absolute Pin): Piece blocks enemy Rook/Cannon attacking own King.
2. Capture causes Flying General: Piece is the only blocker between two Kings.

Test cases:
1. Invalid: Capture would expose King to Rook/Cannon check (pinned piece)
2. Invalid: Capture would cause Flying General
3. Valid: Capture is legal (not pinned, or another piece still blocks)

Note: Cannon requires a screen piece to capture. This is handled in all scenarios.
"""

import random
from typing import List, Dict, Tuple, Optional, Set


class Level5Generator:
    """Generate Level 5 test cases - capture constraints (explicit mode)"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.cols = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']
        self.rows = list(range(10))
        self.palace_cols = ['d', 'e', 'f']
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

    def _get_squares_between_vertical(self, col: int, row1: int, row2: int) -> List[str]:
        min_row, max_row = min(row1, row2), max(row1, row2)
        squares = []
        for r in range(min_row + 1, max_row):
            sq = self._coords_to_square(col, r)
            if sq:
                squares.append(sq)
        return squares

    def _place_cannon_capture_setup(self, cannon_col: int, cannon_row: int,
                                    direction: int, forbidden: Set[str]) -> Optional[Tuple[str, str]]:
        """Place screen and target for cannon capture (horizontal)."""
        for screen_dist in range(1, 6):
            screen_col = cannon_col + direction * screen_dist
            if not (0 <= screen_col < 9):
                continue
            screen_sq = self._coords_to_square(screen_col, cannon_row)
            if screen_sq in forbidden:
                continue

            for target_dist in range(screen_dist + 1, screen_dist + 4):
                target_col = cannon_col + direction * target_dist
                if not (0 <= target_col < 9):
                    continue
                target_sq = self._coords_to_square(target_col, cannon_row)
                if target_sq in forbidden and target_sq != screen_sq:
                    continue
                if target_sq == screen_sq:
                    continue
                return (screen_sq, target_sq)
        return None

    # ==================== SCENARIO 1: CAPTURE CAUSES CHECK (ABSOLUTE PIN) ====================

    def _generate_pin_by_rook_invalid(self, case_num: int) -> Optional[Dict]:
        """Invalid: Piece is pinned by enemy Rook."""
        pinned_color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(pinned_color)

        for _ in range(50):
            king_col = random.choice(self.palace_col_indices)
            if pinned_color == 'red':
                king_row = random.randint(0, 2)
            else:
                king_row = random.randint(7, 9)

            king_sq = self._coords_to_square(king_col, king_row)

            if pinned_color == 'red':
                rook_row = random.randint(6, 9)
            else:
                rook_row = random.randint(0, 3)

            rook_sq = self._coords_to_square(king_col, rook_row)

            between = self._get_squares_between_vertical(
                king_col, king_row, rook_row)
            if len(between) < 1:
                continue

            pinned_sq = random.choice(between)
            pinned_col, pinned_row = self._square_to_coords(pinned_sq)
            pinned_type = random.choice(['rook', 'cannon'])

            forbidden = {king_sq, rook_sq, pinned_sq}
            target_direction = random.choice([-1, 1])

            if pinned_type == 'rook':
                target_col = pinned_col + target_direction
                if target_col < 0 or target_col > 8:
                    target_col = pinned_col - target_direction
                target_sq = self._coords_to_square(target_col, pinned_row)
                if not target_sq or target_sq in forbidden:
                    continue
                screen_sq = None
            else:
                result = self._place_cannon_capture_setup(
                    pinned_col, pinned_row, target_direction, forbidden)
                if not result:
                    result = self._place_cannon_capture_setup(
                        pinned_col, pinned_row, -target_direction, forbidden)
                if not result:
                    continue
                screen_sq, target_sq = result

            king_symbol = self._piece_symbol('king', pinned_color)
            rook_symbol = self._piece_symbol('rook', enemy_color)
            pinned_symbol = self._piece_symbol(pinned_type, pinned_color)
            target_symbol = self._piece_symbol('pawn', enemy_color)

            pieces_before = {
                king_sq: king_symbol,
                rook_sq: rook_symbol,
                pinned_sq: pinned_symbol,
                target_sq: target_symbol,
            }
            if screen_sq:
                screen_color = random.choice([pinned_color, enemy_color])
                pieces_before[screen_sq] = self._piece_symbol(
                    'pawn', screen_color)

            # After capture: pinned piece moves to target, target removed
            pieces_after = {
                king_sq: king_symbol,
                rook_sq: rook_symbol,
                target_sq: pinned_symbol,
            }
            if screen_sq:
                pieces_after[screen_sq] = pieces_before[screen_sq]

            pinned_name = pinned_type.capitalize()

            return {
                "case_id": f"L5_pin_rook_invalid_{case_num}",
                "type": "capture_constraint",
                "subtype": "pinned_by_rook",
                "piece_type": pinned_type,
                "color": pinned_color,
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []}
                ],
                "question": "Is this a legal capture according to Xiangqi rules?",
                "expected": "no",
                "reasoning": f"The {pinned_name} is pinned by the enemy Rook at {rook_sq}. "
                f"If it captures at {target_sq}, the King at {king_sq} would be exposed to check. Illegal capture."
            }
        return None

    def _generate_pin_by_cannon_invalid(self, case_num: int) -> Optional[Dict]:
        """Invalid: Piece is pinned by enemy Cannon."""
        pinned_color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(pinned_color)

        for _ in range(50):
            king_col = random.choice(self.palace_col_indices)
            if pinned_color == 'red':
                king_row = random.randint(0, 2)
            else:
                king_row = random.randint(7, 9)

            king_sq = self._coords_to_square(king_col, king_row)

            if pinned_color == 'red':
                cannon_row = random.randint(7, 9)
            else:
                cannon_row = random.randint(0, 2)

            enemy_cannon_sq = self._coords_to_square(king_col, cannon_row)

            between = self._get_squares_between_vertical(
                king_col, king_row, cannon_row)
            if len(between) < 2:
                continue

            if pinned_color == 'red':
                between_sorted = sorted(
                    between, key=lambda sq: self._square_to_coords(sq)[1])
            else:
                between_sorted = sorted(
                    between, key=lambda sq: -self._square_to_coords(sq)[1])

            pinned_sq = between_sorted[0]
            cannon_screen_sq = between_sorted[-1]

            if pinned_sq == cannon_screen_sq:
                if len(between_sorted) >= 2:
                    cannon_screen_sq = between_sorted[1]
                else:
                    continue

            pinned_col, pinned_row = self._square_to_coords(pinned_sq)
            pinned_type = random.choice(['rook', 'cannon'])

            forbidden = {king_sq, enemy_cannon_sq, pinned_sq, cannon_screen_sq}
            target_direction = random.choice([-1, 1])

            if pinned_type == 'rook':
                target_col = pinned_col + target_direction
                if target_col < 0 or target_col > 8:
                    target_col = pinned_col - target_direction
                target_sq = self._coords_to_square(target_col, pinned_row)
                if not target_sq or target_sq in forbidden:
                    continue
                capture_screen_sq = None
            else:
                result = self._place_cannon_capture_setup(
                    pinned_col, pinned_row, target_direction, forbidden)
                if not result:
                    result = self._place_cannon_capture_setup(
                        pinned_col, pinned_row, -target_direction, forbidden)
                if not result:
                    continue
                capture_screen_sq, target_sq = result

            cannon_screen_color = random.choice([pinned_color, enemy_color])

            king_symbol = self._piece_symbol('king', pinned_color)
            cannon_symbol = self._piece_symbol('cannon', enemy_color)
            pinned_symbol = self._piece_symbol(pinned_type, pinned_color)
            target_symbol = self._piece_symbol('pawn', enemy_color)
            cannon_screen_symbol = self._piece_symbol(
                'pawn', cannon_screen_color)

            pieces_before = {
                king_sq: king_symbol,
                enemy_cannon_sq: cannon_symbol,
                pinned_sq: pinned_symbol,
                cannon_screen_sq: cannon_screen_symbol,
                target_sq: target_symbol,
            }
            if capture_screen_sq and capture_screen_sq not in pieces_before:
                capture_screen_color = random.choice(
                    [pinned_color, enemy_color])
                pieces_before[capture_screen_sq] = self._piece_symbol(
                    'pawn', capture_screen_color)

            pieces_after = {
                king_sq: king_symbol,
                enemy_cannon_sq: cannon_symbol,
                target_sq: pinned_symbol,
                cannon_screen_sq: cannon_screen_symbol,
            }
            if capture_screen_sq and capture_screen_sq in pieces_before:
                pieces_after[capture_screen_sq] = pieces_before[capture_screen_sq]

            pinned_name = pinned_type.capitalize()

            return {
                "case_id": f"L5_pin_cannon_invalid_{case_num}",
                "type": "capture_constraint",
                "subtype": "pinned_by_cannon",
                "piece_type": pinned_type,
                "color": pinned_color,
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []}
                ],
                "question": "Is this a legal capture according to Xiangqi rules?",
                "expected": "no",
                "reasoning": f"The {pinned_name} is pinned by the enemy Cannon at {enemy_cannon_sq}. "
                f"If the {pinned_name} moves to capture at {target_sq}, the King at {king_sq} would be in check. Illegal capture."
            }
        return None

    # ==================== SCENARIO 2: CAPTURE CAUSES FLYING GENERAL ====================

    def _generate_flying_general_capture_invalid(self, case_num: int) -> Optional[Dict]:
        """Invalid: Piece is the only blocker between two Kings."""
        blocker_color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(blocker_color)

        for _ in range(50):
            king_col = random.choice(self.palace_col_indices)

            red_king_row = random.randint(0, 2)
            black_king_row = random.randint(7, 9)

            red_king_sq = self._coords_to_square(king_col, red_king_row)
            black_king_sq = self._coords_to_square(king_col, black_king_row)

            between = self._get_squares_between_vertical(
                king_col, red_king_row, black_king_row)
            if len(between) < 1:
                continue

            blocker_sq = random.choice(between)
            blocker_col, blocker_row = self._square_to_coords(blocker_sq)
            blocker_type = random.choice(['rook', 'cannon'])

            forbidden = {red_king_sq, black_king_sq, blocker_sq} | set(between)
            target_direction = random.choice([-1, 1])

            if blocker_type == 'rook':
                target_col = blocker_col + target_direction
                if target_col < 0 or target_col > 8:
                    target_col = blocker_col - target_direction
                target_sq = self._coords_to_square(target_col, blocker_row)
                if not target_sq or target_sq in forbidden:
                    continue
                screen_sq = None
            else:
                result = self._place_cannon_capture_setup(
                    blocker_col, blocker_row, target_direction, forbidden)
                if not result:
                    result = self._place_cannon_capture_setup(
                        blocker_col, blocker_row, -target_direction, forbidden)
                if not result:
                    continue
                screen_sq, target_sq = result

            if target_sq in between:
                continue

            blocker_symbol = self._piece_symbol(blocker_type, blocker_color)
            target_symbol = self._piece_symbol('pawn', enemy_color)

            pieces_before = {
                red_king_sq: 'K',
                black_king_sq: 'k',
                blocker_sq: blocker_symbol,
                target_sq: target_symbol,
            }
            if screen_sq and screen_sq not in between:
                screen_color = random.choice([blocker_color, enemy_color])
                pieces_before[screen_sq] = self._piece_symbol(
                    'pawn', screen_color)
            elif screen_sq and screen_sq in between:
                continue

            pieces_after = {
                red_king_sq: 'K',
                black_king_sq: 'k',
                target_sq: blocker_symbol,
            }
            if screen_sq and screen_sq in pieces_before:
                pieces_after[screen_sq] = pieces_before[screen_sq]

            blocker_name = blocker_type.capitalize()

            return {
                "case_id": f"L5_flying_general_capture_invalid_{case_num}",
                "type": "capture_constraint",
                "subtype": "flying_general_capture",
                "piece_type": blocker_type,
                "color": blocker_color,
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []}
                ],
                "question": "Is this a legal capture according to Xiangqi rules?",
                "expected": "no",
                "reasoning": f"The {blocker_name} is the only piece between the two Kings. "
                f"Capturing at {target_sq} would cause Flying General, which is illegal."
            }
        return None

    # ==================== VALID CASES ====================

    def _generate_not_pinned_valid(self, case_num: int) -> Optional[Dict]:
        """Valid: Piece is NOT on the line between King and attacker."""
        capturer_color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(capturer_color)

        for _ in range(50):
            king_col = random.choice(self.palace_col_indices)
            if capturer_color == 'red':
                king_row = random.randint(0, 2)
            else:
                king_row = random.randint(7, 9)

            king_sq = self._coords_to_square(king_col, king_row)

            capturer_col = random.choice(
                [c for c in range(9) if c != king_col])
            capturer_row = random.randint(3, 6)
            capturer_sq = self._coords_to_square(capturer_col, capturer_row)

            capturer_type = random.choice(['rook', 'cannon'])

            forbidden = {king_sq, capturer_sq}
            target_direction = random.choice([-1, 1])

            if capturer_type == 'rook':
                target_col = capturer_col + target_direction
                if target_col < 0 or target_col > 8:
                    target_col = capturer_col - target_direction
                target_sq = self._coords_to_square(target_col, capturer_row)
                if not target_sq or target_sq in forbidden:
                    continue
                screen_sq = None
            else:
                result = self._place_cannon_capture_setup(
                    capturer_col, capturer_row, target_direction, forbidden)
                if not result:
                    result = self._place_cannon_capture_setup(
                        capturer_col, capturer_row, -target_direction, forbidden)
                if not result:
                    continue
                screen_sq, target_sq = result

            king_symbol = self._piece_symbol('king', capturer_color)
            capturer_symbol = self._piece_symbol(capturer_type, capturer_color)
            target_symbol = self._piece_symbol('pawn', enemy_color)

            pieces_before = {
                king_sq: king_symbol,
                capturer_sq: capturer_symbol,
                target_sq: target_symbol,
            }
            if screen_sq:
                screen_color = random.choice([capturer_color, enemy_color])
                pieces_before[screen_sq] = self._piece_symbol(
                    'pawn', screen_color)

            pieces_after = {
                king_sq: king_symbol,
                target_sq: capturer_symbol,
            }
            if screen_sq:
                pieces_after[screen_sq] = pieces_before[screen_sq]

            capturer_name = capturer_type.capitalize()

            return {
                "case_id": f"L5_not_pinned_valid_{case_num}",
                "type": "capture_constraint",
                "subtype": "not_pinned",
                "piece_type": capturer_type,
                "color": capturer_color,
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []}
                ],
                "question": "Is this a legal capture according to Xiangqi rules?",
                "expected": "yes",
                "reasoning": f"The {capturer_name} is not pinned and not blocking Flying General. It can freely capture at {target_sq}."
            }
        return None

    def _generate_multiple_blockers_valid(self, case_num: int) -> Optional[Dict]:
        """Valid: There are multiple blockers between Kings."""
        blocker_color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(blocker_color)

        for _ in range(50):
            king_col = random.choice(self.palace_col_indices)

            red_king_row = random.randint(0, 2)
            black_king_row = random.randint(7, 9)

            red_king_sq = self._coords_to_square(king_col, red_king_row)
            black_king_sq = self._coords_to_square(king_col, black_king_row)

            between = self._get_squares_between_vertical(
                king_col, red_king_row, black_king_row)
            if len(between) < 2:
                continue

            blocker_positions = random.sample(between, 2)
            moving_blocker_sq = blocker_positions[0]
            staying_blocker_sq = blocker_positions[1]

            moving_col, moving_row = self._square_to_coords(moving_blocker_sq)

            moving_type = random.choice(['rook', 'cannon'])
            staying_type = random.choice(['rook', 'cannon', 'pawn'])
            staying_color = random.choice([blocker_color, enemy_color])

            forbidden = {red_king_sq, black_king_sq,
                         moving_blocker_sq, staying_blocker_sq}
            target_direction = random.choice([-1, 1])

            if moving_type == 'rook':
                target_col = moving_col + target_direction
                if target_col < 0 or target_col > 8:
                    target_col = moving_col - target_direction
                target_sq = self._coords_to_square(target_col, moving_row)
                if not target_sq or target_sq in forbidden:
                    continue
                screen_sq = None
            else:
                result = self._place_cannon_capture_setup(
                    moving_col, moving_row, target_direction, forbidden)
                if not result:
                    result = self._place_cannon_capture_setup(
                        moving_col, moving_row, -target_direction, forbidden)
                if not result:
                    continue
                screen_sq, target_sq = result

            all_squares = {red_king_sq, black_king_sq,
                           moving_blocker_sq, staying_blocker_sq, target_sq}
            if screen_sq:
                all_squares.add(screen_sq)
            if len(all_squares) != (5 if not screen_sq else 6):
                continue

            moving_symbol = self._piece_symbol(moving_type, blocker_color)
            staying_symbol = self._piece_symbol(staying_type, staying_color)
            target_symbol = self._piece_symbol('pawn', enemy_color)

            pieces_before = {
                red_king_sq: 'K',
                black_king_sq: 'k',
                moving_blocker_sq: moving_symbol,
                staying_blocker_sq: staying_symbol,
                target_sq: target_symbol,
            }
            if screen_sq:
                screen_color = random.choice([blocker_color, enemy_color])
                pieces_before[screen_sq] = self._piece_symbol(
                    'pawn', screen_color)

            pieces_after = {
                red_king_sq: 'K',
                black_king_sq: 'k',
                target_sq: moving_symbol,
                staying_blocker_sq: staying_symbol,
            }
            if screen_sq:
                pieces_after[screen_sq] = pieces_before[screen_sq]

            moving_name = moving_type.capitalize()

            return {
                "case_id": f"L5_multiple_blockers_valid_{case_num}",
                "type": "capture_constraint",
                "subtype": "multiple_blockers",
                "piece_type": moving_type,
                "color": blocker_color,
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []}
                ],
                "question": "Is this a legal capture according to Xiangqi rules?",
                "expected": "yes",
                "reasoning": f"Although the {moving_name} is between the two Kings, there is another piece at {staying_blocker_sq} that will still block. "
                f"No Flying General occurs. Legal capture."
            }
        return None

    def _generate_pin_along_capture_line_valid(self, case_num: int) -> Optional[Dict]:
        """Valid: Piece captures along the pin line."""
        pinned_color = random.choice(['red', 'black'])
        enemy_color = self._opposite_color(pinned_color)

        for _ in range(50):
            king_col = random.choice(self.palace_col_indices)
            if pinned_color == 'red':
                king_row = random.randint(0, 2)
            else:
                king_row = random.randint(7, 9)

            king_sq = self._coords_to_square(king_col, king_row)

            if pinned_color == 'red':
                rook_row = random.randint(6, 9)
            else:
                rook_row = random.randint(0, 3)

            enemy_rook_sq = self._coords_to_square(king_col, rook_row)

            between = self._get_squares_between_vertical(
                king_col, king_row, rook_row)
            if len(between) < 1:
                continue

            pinned_sq = random.choice(between)
            pinned_type = 'rook'

            all_squares = {king_sq, enemy_rook_sq, pinned_sq}
            if len(all_squares) != 3:
                continue

            king_symbol = self._piece_symbol('king', pinned_color)
            enemy_rook_symbol = self._piece_symbol('rook', enemy_color)
            pinned_symbol = self._piece_symbol(pinned_type, pinned_color)

            pieces_before = {
                king_sq: king_symbol,
                enemy_rook_sq: enemy_rook_symbol,
                pinned_sq: pinned_symbol,
            }

            # After: pinned rook captures enemy rook
            pieces_after = {
                king_sq: king_symbol,
                enemy_rook_sq: pinned_symbol,
            }

            return {
                "case_id": f"L5_capture_along_pin_valid_{case_num}",
                "type": "capture_constraint",
                "subtype": "capture_along_pin",
                "piece_type": pinned_type,
                "color": pinned_color,
                "states": [
                    {"pieces": pieces_before, "squares": []},
                    {"pieces": pieces_after, "squares": []}
                ],
                "question": "Is this a legal capture according to Xiangqi rules?",
                "expected": "yes",
                "reasoning": f"The Rook at {pinned_sq} is pinned by the enemy Rook at {enemy_rook_sq}, but it can capture along the pin line. "
                f"Capturing the attacker removes the threat. Legal capture."
            }
        return None

    # ==================== GENERATE ALL ====================

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        """Generate all Level 5 test cases (explicit mode)"""
        all_cases = []

        n_pin_rook = int(n_cases * 0.20)
        n_pin_cannon = int(n_cases * 0.10)
        n_flying_general = int(n_cases * 0.30)
        n_not_pinned = int(n_cases * 0.15)
        n_multi_blockers = int(n_cases * 0.15)
        n_along_pin = n_cases - n_pin_rook - n_pin_cannon - \
            n_flying_general - n_not_pinned - n_multi_blockers

        print(f"Generating pin by Rook (invalid) cases...")
        count = 0
        for _ in range(n_pin_rook * 10):
            if count >= n_pin_rook:
                break
            case = self._generate_pin_by_rook_invalid(count + 1)
            if case:
                all_cases.append(case)
                count += 1
        print(f"  ✓ Generated {count} pin by Rook cases")

        print(f"Generating pin by Cannon (invalid) cases...")
        count = 0
        for _ in range(n_pin_cannon * 10):
            if count >= n_pin_cannon:
                break
            case = self._generate_pin_by_cannon_invalid(count + 1)
            if case:
                all_cases.append(case)
                count += 1
        print(f"  ✓ Generated {count} pin by Cannon cases")

        print(f"Generating Flying General capture (invalid) cases...")
        count = 0
        for _ in range(n_flying_general * 10):
            if count >= n_flying_general:
                break
            case = self._generate_flying_general_capture_invalid(count + 1)
            if case:
                all_cases.append(case)
                count += 1
        print(f"  ✓ Generated {count} Flying General capture cases")

        print(f"Generating not pinned (valid) cases...")
        count = 0
        for _ in range(n_not_pinned * 10):
            if count >= n_not_pinned:
                break
            case = self._generate_not_pinned_valid(count + 1)
            if case:
                all_cases.append(case)
                count += 1
        print(f"  ✓ Generated {count} not pinned cases")

        print(f"Generating multiple blockers (valid) cases...")
        count = 0
        for _ in range(n_multi_blockers * 10):
            if count >= n_multi_blockers:
                break
            case = self._generate_multiple_blockers_valid(count + 1)
            if case:
                all_cases.append(case)
                count += 1
        print(f"  ✓ Generated {count} multiple blockers cases")

        print(f"Generating capture along pin (valid) cases...")
        count = 0
        for _ in range(n_along_pin * 10):
            if count >= n_along_pin:
                break
            case = self._generate_pin_along_capture_line_valid(count + 1)
            if case:
                all_cases.append(case)
                count += 1
        print(f"  ✓ Generated {count} capture along pin cases")

        random.shuffle(all_cases)

        valid_count = sum(1 for c in all_cases if c['expected'] == 'yes')
        invalid_count = sum(1 for c in all_cases if c['expected'] == 'no')

        print(
            f"\n✓ Total generated: {len(all_cases)} Level 5 explicit test cases")
        print(
            f"  Valid (yes): {valid_count} ({valid_count/len(all_cases)*100:.1f}%)")
        print(
            f"  Invalid (no): {invalid_count} ({invalid_count/len(all_cases)*100:.1f}%)")

        return all_cases
