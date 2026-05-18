"""
Automated test case generator for Chess With-Rule Multi-State Test
Temporal rule following - En Passant, Castling, etc.
"""

import random
from typing import List, Dict, Tuple, Optional


class ChessWithRuleGenerator:
    """Generate chess rule following multi-state test cases"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.ranks = ['1', '2', '3', '4', '5', '6', '7', '8']

    def _random_file(self) -> str:
        return random.choice(self.files)

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

    def _square_to_coords(self, square: str) -> Tuple[int, int]:
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        return (file, rank)

    def _coords_to_square(self, file: int, rank: int) -> Optional[str]:
        if 0 <= file < 8 and 0 <= rank < 8:
            return chr(ord('a') + file) + str(rank + 1)
        return None

    def _distribute_counts(self, total: int, n_slots: int) -> List[int]:
        base = total // n_slots
        remainder = total % n_slots
        return [base + (1 if i < remainder else 0) for i in range(n_slots)]

    def _get_safe_squares_for_castling(self, color: str, side: str) -> List[str]:
        if color == 'white':
            if side == 'kingside':
                blocked = ['e1', 'f1', 'g1', 'h1']
            else:
                blocked = ['a1', 'b1', 'c1', 'd1', 'e1']
        else:
            if side == 'kingside':
                blocked = ['e8', 'f8', 'g8', 'h8']
            else:
                blocked = ['a8', 'b8', 'c8', 'd8', 'e8']
        all_squares = [f + r for f in self.files for r in self.ranks]
        return [sq for sq in all_squares if sq not in blocked]

    # ============= Type 1: En Passant Rule Judgment =============

    def generate_en_passant_rule_tests(self, n_cases: int = 10) -> List[Dict]:
        cases = []
        # Distribute: 50% positive, 50% negative (split into 2 subtypes)
        subtypes = ['valid', 'moved_one_square', 'not_adjacent']
        counts = self._distribute_counts(n_cases, len(subtypes))

        # Positive cases
        for i in range(counts[0]):
            white_file = random.choice(['a', 'b', 'c', 'd', 'e', 'f', 'g'])
            white_sq = white_file + '5'
            adjacent = self._adjacent_files(white_file)
            black_file = random.choice(adjacent) if adjacent else (
                'b' if white_file == 'a' else 'g')
            black_start = black_file + '7'
            black_end = black_file + '5'

            cases.append({
                "case_id": f"en_passant_rule_pos_{i+1}",
                "type": "en_passant_rule",
                "subtype": "valid",
                "states": [
                    {"pieces": {white_sq: 'P', black_start: 'p'}, "squares": []},
                    {"pieces": {white_sq: 'P', black_end: 'p'}, "squares": []}
                ],
                "label": "These are consecutive board states (State 2 immediately follows State 1)",
                "question": "Can white capture the black pawn en passant?",
                "expected": "yes",
                "reasoning": f"Black pawn moved 2 squares from {black_start} to {black_end}"
            })

        # Negative Type 1: Only moved 1 square
        for i in range(counts[1]):
            white_file = random.choice(['a', 'b', 'c', 'd', 'e', 'f', 'g'])
            white_sq = white_file + '5'
            adjacent = self._adjacent_files(white_file)
            black_file = random.choice(adjacent) if adjacent else (
                'b' if white_file == 'a' else 'g')
            black_start = black_file + '6'
            black_end = black_file + '5'

            cases.append({
                "case_id": f"en_passant_rule_neg_{i+1}",
                "type": "en_passant_rule",
                "subtype": "moved_one_square",
                "states": [
                    {"pieces": {white_sq: 'P', black_start: 'p'}, "squares": []},
                    {"pieces": {white_sq: 'P', black_end: 'p'}, "squares": []}
                ],
                "label": "These are consecutive states",
                "question": "Can white capture the black pawn en passant?",
                "expected": "no",
                "reasoning": f"Black pawn only moved 1 square from {black_start} to {black_end}"
            })

        # Negative Type 2: Not adjacent
        for i in range(counts[2]):
            white_file = random.choice(['a', 'b', 'c', 'd'])
            white_sq = white_file + '5'
            black_file_idx = self.files.index(
                white_file) + random.choice([2, 3, 4])
            if black_file_idx >= 8:
                black_file_idx = self.files.index(
                    white_file) - random.choice([2, 3])
            black_file = self.files[black_file_idx]
            black_start = black_file + '7'
            black_end = black_file + '5'

            cases.append({
                "case_id": f"en_passant_rule_neg_{counts[1] + i + 1}",
                "type": "en_passant_rule",
                "subtype": "not_adjacent",
                "states": [
                    {"pieces": {white_sq: 'P', black_start: 'p'}, "squares": []},
                    {"pieces": {white_sq: 'P', black_end: 'p'}, "squares": []}
                ],
                "label": "These are consecutive states",
                "question": "Can white capture the black pawn en passant?",
                "expected": "no",
                "reasoning": f"White pawn at {white_sq} is not adjacent to black pawn at {black_end}"
            })

        return cases

    # ============= Type 2: Castling Rule Judgment =============

    def generate_castling_rule_tests(self, n_cases: int = 10) -> List[Dict]:
        cases = []

        positive_templates = [
            {"color": "white", "side": "kingside", "king_sq": "e1", "rook_sq": "h1",
             "states": [
                 {"pieces": {'e1': 'K', 'h1': 'R', 'e2': 'P'}, "squares": []},
                 {"pieces": {'e1': 'K', 'h1': 'R', 'e4': 'P'}, "squares": []},
                 {"pieces": {'e1': 'K', 'h1': 'R', 'e4': 'P', 'd2': 'P'}, "squares": []},
             ],
             "reasoning": "King and Rook never moved (only pawns moved)"},
            {"color": "white", "side": "queenside", "king_sq": "e1", "rook_sq": "a1",
             "states": [
                 {"pieces": {'e1': 'K', 'a1': 'R', 'd2': 'P'}, "squares": []},
                 {"pieces": {'e1': 'K', 'a1': 'R', 'd4': 'P'}, "squares": []},
                 {"pieces": {'e1': 'K', 'a1': 'R', 'd4': 'P', 'c3': 'N'}, "squares": []},
             ],
             "reasoning": "King and Rook never moved (pawn and knight moved)"},
            {"color": "black", "side": "kingside", "king_sq": "e8", "rook_sq": "h8",
             "states": [
                 {"pieces": {'e8': 'k', 'h8': 'r', 'e7': 'p'}, "squares": []},
                 {"pieces": {'e8': 'k', 'h8': 'r', 'e5': 'p'}, "squares": []},
                 {"pieces": {'e8': 'k', 'h8': 'r', 'e5': 'p', 'd7': 'p'}, "squares": []},
             ],
             "reasoning": "King and Rook never moved (only pawns moved)"},
            {"color": "black", "side": "queenside", "king_sq": "e8", "rook_sq": "a8",
             "states": [
                 {"pieces": {'e8': 'k', 'a8': 'r', 'd7': 'p'}, "squares": []},
                 {"pieces": {'e8': 'k', 'a8': 'r', 'd5': 'p'}, "squares": []},
                 {"pieces": {'e8': 'k', 'a8': 'r', 'd5': 'p', 'c6': 'n'}, "squares": []},
             ],
             "reasoning": "King and Rook never moved (pawn and knight moved)"},
        ]

        # Subtypes: valid (use templates), king_moved, rook_moved, path_blocked, in_check
        subtypes = ['valid', 'king_moved',
                    'rook_moved', 'path_blocked', 'in_check']
        counts = self._distribute_counts(n_cases, len(subtypes))

        # Positive cases - cycle through templates
        for i in range(counts[0]):
            template = positive_templates[i % len(positive_templates)]
            cases.append({
                "case_id": f"castling_rule_pos_{i+1}",
                "type": "castling_rule",
                "subtype": f"valid_{template['color']}_{template['side']}",
                "states": template["states"],
                "label": "States shown in chronological order. Other pieces moved, but King and Rook never moved.",
                "question": f"Can {template['color']} castle {template['side']}?",
                "expected": "yes",
                "reasoning": template["reasoning"]
            })

        neg_idx = 0

        # Type: King moved
        for i in range(counts[1]):
            color = random.choice(['white', 'black'])
            side = random.choice(['kingside', 'queenside'])
            if color == 'white':
                king_sq, rook_sq = 'e1', ('h1' if side == 'kingside' else 'a1')
                king_temp, king_symbol, rook_symbol = 'e2', 'K', 'R'
            else:
                king_sq, rook_sq = 'e8', ('h8' if side == 'kingside' else 'a8')
                king_temp, king_symbol, rook_symbol = 'e7', 'k', 'r'

            cases.append({
                "case_id": f"castling_rule_neg_{neg_idx + 1}",
                "type": "castling_rule",
                "subtype": "king_moved",
                "states": [
                    {"pieces": {king_sq: king_symbol,
                                rook_sq: rook_symbol}, "squares": []},
                    {"pieces": {king_temp: king_symbol,
                                rook_sq: rook_symbol}, "squares": []},
                    {"pieces": {king_sq: king_symbol,
                                rook_sq: rook_symbol}, "squares": []}
                ],
                "label": "States shown in chronological order",
                "question": f"Can {color} castle {side}?",
                "expected": "no",
                "reasoning": "King has moved (even though it returned to original position)"
            })
            neg_idx += 1

        # Type: Rook moved
        for i in range(counts[2]):
            color = random.choice(['white', 'black'])
            side = random.choice(['kingside', 'queenside'])
            if color == 'white':
                king_sq, rook_sq = 'e1', ('h1' if side == 'kingside' else 'a1')
                rook_temp = ('h2' if side == 'kingside' else 'a2')
                king_symbol, rook_symbol = 'K', 'R'
            else:
                king_sq, rook_sq = 'e8', ('h8' if side == 'kingside' else 'a8')
                rook_temp = ('h7' if side == 'kingside' else 'a7')
                king_symbol, rook_symbol = 'k', 'r'

            cases.append({
                "case_id": f"castling_rule_neg_{neg_idx + 1}",
                "type": "castling_rule",
                "subtype": "rook_moved",
                "states": [
                    {"pieces": {king_sq: king_symbol,
                                rook_sq: rook_symbol}, "squares": []},
                    {"pieces": {king_sq: king_symbol,
                                rook_temp: rook_symbol}, "squares": []},
                    {"pieces": {king_sq: king_symbol,
                                rook_sq: rook_symbol}, "squares": []}
                ],
                "label": "States shown in chronological order",
                "question": f"Can {color} castle {side}?",
                "expected": "no",
                "reasoning": "Rook has moved"
            })
            neg_idx += 1

        # Type: Path blocked
        for i in range(counts[3]):
            color = random.choice(['white', 'black'])
            side = random.choice(['kingside', 'queenside'])
            if color == 'white':
                king_sq = 'e1'
                if side == 'kingside':
                    rook_sq = 'h1'
                    blocking_sq = random.choice(['f1', 'g1'])
                    blocker_piece = random.choice(['N', 'B'])
                else:
                    rook_sq = 'a1'
                    blocking_sq = random.choice(['b1', 'c1', 'd1'])
                    blocker_piece = random.choice(['N', 'B', 'Q'])
                king_symbol, rook_symbol = 'K', 'R'
            else:
                king_sq = 'e8'
                if side == 'kingside':
                    rook_sq = 'h8'
                    blocking_sq = random.choice(['f8', 'g8'])
                    blocker_piece = random.choice(['n', 'b'])
                else:
                    rook_sq = 'a8'
                    blocking_sq = random.choice(['b8', 'c8', 'd8'])
                    blocker_piece = random.choice(['n', 'b', 'q'])
                king_symbol, rook_symbol = 'k', 'r'

            pieces = {king_sq: king_symbol,
                      rook_sq: rook_symbol, blocking_sq: blocker_piece}
            cases.append({
                "case_id": f"castling_rule_neg_{neg_idx + 1}",
                "type": "castling_rule",
                "subtype": "path_blocked",
                "states": [
                    {"pieces": pieces, "squares": []},
                    {"pieces": pieces, "squares": []},
                    {"pieces": pieces, "squares": []}
                ],
                "label": "King and Rook have never moved",
                "question": f"Can {color} castle {side}?",
                "expected": "no",
                "reasoning": f"Path is blocked by piece at {blocking_sq}"
            })
            neg_idx += 1

        # Type: In check
        for i in range(counts[4]):
            color = random.choice(['white', 'black'])
            side = random.choice(['kingside', 'queenside'])
            if color == 'white':
                king_sq, rook_sq = 'e1', ('h1' if side == 'kingside' else 'a1')
                attacker_sq, attacker_symbol = 'e8', 'r'
                king_symbol, rook_symbol = 'K', 'R'
            else:
                king_sq, rook_sq = 'e8', ('h8' if side == 'kingside' else 'a8')
                attacker_sq, attacker_symbol = 'e1', 'R'
                king_symbol, rook_symbol = 'k', 'r'

            cases.append({
                "case_id": f"castling_rule_neg_{neg_idx + 1}",
                "type": "castling_rule",
                "subtype": "in_check",
                "states": [
                    {"pieces": {king_sq: king_symbol, rook_sq: rook_symbol,
                                attacker_sq: attacker_symbol}, "squares": []},
                    {"pieces": {king_sq: king_symbol, rook_sq: rook_symbol,
                                attacker_sq: attacker_symbol}, "squares": []},
                    {"pieces": {king_sq: king_symbol, rook_sq: rook_symbol,
                                attacker_sq: attacker_symbol}, "squares": []}
                ],
                "label": "King and Rook have never moved",
                "question": f"Can {color} castle {side}?",
                "expected": "no",
                "reasoning": "King is currently in check (cannot castle out of check)"
            })
            neg_idx += 1

        return cases

    # ============= Type 3: En Passant Event Recognition =============

    def generate_en_passant_event_tests(self, n_cases: int = 10) -> List[Dict]:
        cases = []
        subtypes = ['en_passant', 'regular_capture', 'no_capture']
        counts = self._distribute_counts(n_cases, len(subtypes))

        # En passant cases
        for i in range(counts[0]):
            white_file = random.choice(['a', 'b', 'c', 'd', 'e', 'f', 'g'])
            white_sq = white_file + '5'
            adjacent = self._adjacent_files(white_file)
            black_file = random.choice(adjacent) if adjacent else 'b'
            black_start = black_file + '7'
            black_mid = black_file + '5'
            capture_sq = black_file + '6'

            cases.append({
                "case_id": f"en_passant_event_pos_{i+1}",
                "type": "en_passant_event",
                "subtype": "en_passant",
                "states": [
                    {"pieces": {white_sq: 'P', black_start: 'p'}, "squares": []},
                    {"pieces": {white_sq: 'P', black_mid: 'p'}, "squares": []},
                    {"pieces": {capture_sq: 'P'}, "squares": []}
                ],
                "label": "States shown in chronological order",
                "question": "What happened in this sequence?",
                "options": {"A": "Castling", "B": "En passant capture", "C": "Regular capture (not en passant)", "D": "None of the above"},
                "expected": "B",
                "reasoning": "White pawn performed en passant capture"
            })

        # Regular capture confuser
        for i in range(counts[1]):
            white_file = random.choice(['a', 'b', 'c', 'd', 'e', 'f', 'g'])
            white_sq = white_file + '5'
            adjacent = self._adjacent_files(white_file)
            black_file = random.choice(adjacent) if adjacent else 'b'
            black_start = black_file + '6'
            black_mid = black_file + '5'
            capture_sq = black_file + '5'

            cases.append({
                "case_id": f"en_passant_event_confuser_{i+1}",
                "type": "en_passant_event",
                "subtype": "regular_capture",
                "states": [
                    {"pieces": {white_sq: 'P', black_start: 'p'}, "squares": []},
                    {"pieces": {white_sq: 'P', black_mid: 'p'}, "squares": []},
                    {"pieces": {capture_sq: 'P'}, "squares": []}
                ],
                "label": "States shown in chronological order",
                "question": "What happened in this sequence?",
                "options": {"A": "Castling", "B": "En passant capture", "C": "Regular capture (not en passant)", "D": "None of the above"},
                "expected": "C",
                "reasoning": "Regular diagonal capture, pawn only moved 1 square"
            })

        # No capture confuser
        for i in range(counts[2]):
            white_file = random.choice(['a', 'b', 'c', 'd', 'e', 'f', 'g'])
            white_sq = white_file + '5'
            white_advanced = white_file + '6'
            adjacent = self._adjacent_files(white_file)
            black_file = random.choice(adjacent) if adjacent else 'b'
            black_start = black_file + '7'
            black_mid = black_file + '5'

            cases.append({
                "case_id": f"en_passant_event_confuser_{counts[1] + i + 1}",
                "type": "en_passant_event",
                "subtype": "no_capture",
                "states": [
                    {"pieces": {white_sq: 'P', black_start: 'p'}, "squares": []},
                    {"pieces": {white_sq: 'P', black_mid: 'p'}, "squares": []},
                    {"pieces": {white_advanced: 'P', black_mid: 'p'}, "squares": []}
                ],
                "label": "States shown in chronological order",
                "question": "What happened in this sequence?",
                "options": {"A": "En passant capture", "B": "Regular capture", "C": "White pawn advanced, no capture", "D": "Castling"},
                "expected": "C",
                "reasoning": "White pawn just advanced, no capture occurred"
            })

        return cases

    # ============= Type 4: Castling Event Recognition =============

    def generate_castling_event_tests(self, n_cases: int = 10) -> List[Dict]:
        cases = []

        positive_templates = [
            {"color": "white", "side": "kingside",
             "state_before": {"pieces": {'e1': 'K', 'h1': 'R'}, "squares": []},
             "state_after": {"pieces": {'g1': 'K', 'f1': 'R'}, "squares": []},
             "expected": "A", "reasoning": "White castled kingside"},
            {"color": "white", "side": "queenside",
             "state_before": {"pieces": {'e1': 'K', 'a1': 'R'}, "squares": []},
             "state_after": {"pieces": {'c1': 'K', 'd1': 'R'}, "squares": []},
             "expected": "B", "reasoning": "White castled queenside"},
            {"color": "black", "side": "kingside",
             "state_before": {"pieces": {'e8': 'k', 'h8': 'r'}, "squares": []},
             "state_after": {"pieces": {'g8': 'k', 'f8': 'r'}, "squares": []},
             "expected": "A", "reasoning": "Black castled kingside"},
            {"color": "black", "side": "queenside",
             "state_before": {"pieces": {'e8': 'k', 'a8': 'r'}, "squares": []},
             "state_after": {"pieces": {'c8': 'k', 'd8': 'r'}, "squares": []},
             "expected": "B", "reasoning": "Black castled queenside"},
        ]

        subtypes = ['castling', 'separate_moves', 'pawn_advance']
        counts = self._distribute_counts(n_cases, len(subtypes))

        # Positive cases - cycle through templates
        for i in range(counts[0]):
            template = positive_templates[i % len(positive_templates)]
            add_other_pieces = random.choice([True, False])
            state_before_pieces = dict(template["state_before"]["pieces"])
            state_after_pieces = dict(template["state_after"]["pieces"])

            if add_other_pieces:
                safe_squares = self._get_safe_squares_for_castling(
                    template["color"], template["side"])
                n_extra = random.randint(1, 3)
                for _ in range(min(n_extra, len(safe_squares))):
                    extra_sq = random.choice(safe_squares)
                    safe_squares.remove(extra_sq)
                    extra_piece = random.choice(
                        ['P', 'N', 'B'] if template["color"] == 'white' else ['p', 'n', 'b'])
                    state_before_pieces[extra_sq] = extra_piece
                    state_after_pieces[extra_sq] = extra_piece

            cases.append({
                "case_id": f"castling_event_pos_{i+1}",
                "type": "castling_event",
                "subtype": f"{template['color']}_{template['side']}",
                "states": [
                    {"pieces": state_before_pieces, "squares": []},
                    {"pieces": state_after_pieces, "squares": []}
                ],
                "label": f"{template['color'].capitalize()} just moved",
                "question": "What happened?",
                "options": {"A": "Castling kingside", "B": "Castling queenside", "C": "King and Rook moved separately", "D": "None of the above"},
                "expected": template["expected"],
                "reasoning": template["reasoning"]
            })

        # Confuser: Separate moves
        for i in range(counts[1]):
            color = random.choice(['white', 'black'])
            side = random.choice(['kingside', 'queenside'])
            if color == 'white':
                if side == 'kingside':
                    states_sequence = [
                        {"pieces": {'e1': 'K', 'h1': 'R'}, "squares": []},
                        {"pieces": {'f1': 'K', 'h1': 'R'}, "squares": []},
                        {"pieces": {'g1': 'K', 'h1': 'R'}, "squares": []},
                        {"pieces": {'g1': 'K', 'f1': 'R'}, "squares": []}
                    ]
                else:
                    states_sequence = [
                        {"pieces": {'e1': 'K', 'a1': 'R'}, "squares": []},
                        {"pieces": {'d1': 'K', 'a1': 'R'}, "squares": []},
                        {"pieces": {'c1': 'K', 'a1': 'R'}, "squares": []},
                        {"pieces": {'c1': 'K', 'd1': 'R'}, "squares": []}
                    ]
                player = "White"
            else:
                if side == 'kingside':
                    states_sequence = [
                        {"pieces": {'e8': 'k', 'h8': 'r'}, "squares": []},
                        {"pieces": {'f8': 'k', 'h8': 'r'}, "squares": []},
                        {"pieces": {'g8': 'k', 'h8': 'r'}, "squares": []},
                        {"pieces": {'g8': 'k', 'f8': 'r'}, "squares": []}
                    ]
                else:
                    states_sequence = [
                        {"pieces": {'e8': 'k', 'a8': 'r'}, "squares": []},
                        {"pieces": {'d8': 'k', 'a8': 'r'}, "squares": []},
                        {"pieces": {'c8': 'k', 'a8': 'r'}, "squares": []},
                        {"pieces": {'c8': 'k', 'd8': 'r'}, "squares": []}
                    ]
                player = "Black"

            cases.append({
                "case_id": f"castling_event_confuser_{i+1}",
                "type": "castling_event",
                "subtype": f"{color}_separate_moves",
                "states": states_sequence,
                "label": "Four states shown in chronological order",
                "question": "Was this castling?",
                "options": {"A": "Yes, castling occurred", "B": "No, King and Rook moved separately", "C": "No, only King moved", "D": "Cannot determine"},
                "expected": "B",
                "reasoning": f"{player} King and Rook moved in separate turns, not castling"
            })

        # Confuser: Pawn advance
        for i in range(counts[2]):
            white_file = random.choice(['a', 'b', 'c', 'd', 'e', 'f', 'g'])
            white_sq = white_file + '5'
            white_advanced = white_file + '6'
            adjacent = self._adjacent_files(white_file)
            black_file = random.choice(adjacent) if adjacent else 'b'
            black_start = black_file + '7'
            black_mid = black_file + '5'

            cases.append({
                "case_id": f"castling_event_confuser_{counts[1] + i + 1}",
                "type": "castling_event",
                "subtype": "no_capture",
                "states": [
                    {"pieces": {white_sq: 'P', black_start: 'p'}, "squares": []},
                    {"pieces": {white_sq: 'P', black_mid: 'p'}, "squares": []},
                    {"pieces": {white_advanced: 'P', black_mid: 'p'}, "squares": []}
                ],
                "label": "States shown in chronological order",
                "question": "What happened in this sequence?",
                "options": {"A": "En passant capture", "B": "Regular capture", "C": "White pawn advanced, no capture", "D": "Castling"},
                "expected": "C",
                "reasoning": "White pawn just advanced, no capture occurred"
            })

        return cases

    # ============= Type 5: Direct Movement Validation =============

    def generate_direct_movement_tests(self, n_cases: int = 10) -> List[Dict]:
        cases = []
        piece_types = ['knight', 'bishop', 'rook']
        cases_per_piece = self._distribute_counts(n_cases, len(piece_types))

        for idx, piece_type in enumerate(piece_types):
            n_piece_cases = cases_per_piece[idx]
            # valid_direct, valid_not_direct, invalid
            subtypes_counts = self._distribute_counts(n_piece_cases, 3)

            if piece_type == 'knight':
                cases.extend(self._generate_knight_direct_tests(
                    subtypes_counts[0], subtypes_counts[1], subtypes_counts[2]))
            elif piece_type == 'bishop':
                cases.extend(self._generate_bishop_direct_tests(
                    subtypes_counts[0], subtypes_counts[1], subtypes_counts[2]))
            else:
                cases.extend(self._generate_rook_direct_tests(
                    subtypes_counts[0], subtypes_counts[1], subtypes_counts[2]))

        return cases

    def _generate_knight_direct_tests(self, n_valid_direct: int, n_valid_not_direct: int, n_invalid: int) -> List[Dict]:
        cases = []
        question = """Can this piece move directly from its State 1 position to its State 2 position according to its chess movement rules?
- Answer 'yes' if this is a valid single move for this piece
- Answer 'no' if this requires multiple moves or violates the piece's rules
- Answer 'unknown' if you cannot determine"""

        # Valid direct moves - with retry
        generated = 0
        for attempt in range(n_valid_direct * 10):
            if generated >= n_valid_direct:
                break
            start_sq = self._random_square()
            end_sq = self._get_knight_move(start_sq)
            if end_sq:
                generated += 1
                cases.append({
                    "case_id": f"knight_direct_valid_{generated}",
                    "type": "direct_movement", "subtype": "valid_direct", "piece": "knight",
                    "states": [{"pieces": {start_sq: 'N'}, "squares": []}, {"pieces": {end_sq: 'N'}, "squares": []}],
                    "label": "These are consecutive states",
                    "question": question, "expected": "yes",
                    "reasoning": f"Valid L-shape move from {start_sq} to {end_sq}"
                })

        # Valid but not direct - with retry
        generated = 0
        for attempt in range(n_valid_not_direct * 20):
            if generated >= n_valid_not_direct:
                break
            start_sq = self._random_square()
            intermediate_sq = self._get_knight_move(start_sq)
            if intermediate_sq:
                end_sq = self._get_knight_move(intermediate_sq)
                if end_sq and end_sq != start_sq:
                    generated += 1
                    cases.append({
                        "case_id": f"knight_direct_indirect_{generated}",
                        "type": "direct_movement", "subtype": "valid_not_direct", "piece": "knight",
                        "states": [{"pieces": {start_sq: 'N'}, "squares": []}, {"pieces": {end_sq: 'N'}, "squares": []}],
                        "label": "There were intermediate moves between these states",
                        "question": question, "expected": "no",
                        "reasoning": f"Knight moved via intermediate square {intermediate_sq}"
                    })

        # Invalid pattern - with retry
        generated = 0
        for attempt in range(n_invalid * 10):
            if generated >= n_invalid:
                break
            start_sq = self._random_square()
            f, r = self._square_to_coords(start_sq)
            direction = random.choice(['vertical', 'horizontal'])
            if direction == 'vertical':
                end_sq = self._coords_to_square(f, min(7, r + 2))
            else:
                end_sq = self._coords_to_square(min(7, f + 2), r)
            if end_sq and end_sq != start_sq:
                generated += 1
                cases.append({
                    "case_id": f"knight_direct_invalid_{generated}",
                    "type": "direct_movement", "subtype": "invalid_pattern", "piece": "knight",
                    "states": [{"pieces": {start_sq: 'N'}, "squares": []}, {"pieces": {end_sq: 'N'}, "squares": []}],
                    "label": "These are consecutive states",
                    "question": question, "expected": "no",
                    "reasoning": "Knight cannot move in straight line"
                })

        return cases

    def _generate_bishop_direct_tests(self, n_valid_direct: int, n_valid_not_direct: int, n_invalid: int) -> List[Dict]:
        cases = []
        question = """Can this piece move directly from its State 1 position to its State 2 position according to its chess movement rules?
    - Answer 'yes' if this is a valid single move for this piece
    - Answer 'no' if this requires multiple moves or violates the piece's rules
    - Answer 'unknown' if you cannot determine"""

        # Valid direct moves - with retry
        generated = 0
        for attempt in range(n_valid_direct * 10):
            if generated >= n_valid_direct:
                break
            start_sq = self._random_square()
            f, r = self._square_to_coords(start_sq)
            distance = random.randint(2, 4)
            direction = random.choice([(1, 1), (1, -1), (-1, 1), (-1, -1)])
            end_f = f + direction[0] * distance
            end_r = r + direction[1] * distance
            if 0 <= end_f < 8 and 0 <= end_r < 8:
                end_sq = self._coords_to_square(end_f, end_r)
                generated += 1
                cases.append({
                    "case_id": f"bishop_direct_valid_{generated}",
                    "type": "direct_movement", "subtype": "valid_direct", "piece": "bishop",
                    "states": [{"pieces": {start_sq: 'B'}, "squares": []}, {"pieces": {end_sq: 'B'}, "squares": []}],
                    "label": "These are consecutive states",
                    "question": question, "expected": "yes",
                    "reasoning": f"Valid diagonal move from {start_sq} to {end_sq}"
                })

        # Valid but not direct - same color square but NOT on diagonal (requires 2+ moves)
        generated = 0
        for attempt in range(n_valid_not_direct * 30):
            if generated >= n_valid_not_direct:
                break
            start_sq = self._random_square()
            f, r = self._square_to_coords(start_sq)

            # Find a same-color square (reachable eventually) but not on any diagonal
            end_f = random.randint(0, 7)
            end_r = random.randint(0, 7)

            # Same color check: (f + r) and (end_f + end_r) must have same parity
            same_color = (f + r) % 2 == (end_f + end_r) % 2
            # Not on diagonal: |delta_f| != |delta_r|
            not_on_diagonal = abs(end_f - f) != abs(end_r - r)
            # Not same square
            not_same = (end_f != f or end_r != r)

            if same_color and not_on_diagonal and not_same:
                end_sq = self._coords_to_square(end_f, end_r)
                generated += 1
                cases.append({
                    "case_id": f"bishop_direct_indirect_{generated}",
                    "type": "direct_movement", "subtype": "valid_not_direct", "piece": "bishop",
                    "states": [{"pieces": {start_sq: 'B'}, "squares": []}, {"pieces": {end_sq: 'B'}, "squares": []}],
                    "label": "These are consecutive states",
                    "question": question, "expected": "no",
                    "reasoning": f"Bishop at {start_sq} cannot reach {end_sq} in one move (not on same diagonal, requires multiple moves)"
                })

        # Invalid pattern - with retry (straight line move)
        generated = 0
        for attempt in range(n_invalid * 10):
            if generated >= n_invalid:
                break
            start_sq = self._random_square()
            f, r = self._square_to_coords(start_sq)
            direction = random.choice(['vertical', 'horizontal'])
            if direction == 'vertical':
                end_sq = self._coords_to_square(f, min(7, r + 3))
            else:
                end_sq = self._coords_to_square(min(7, f + 3), r)
            if end_sq and end_sq != start_sq:
                generated += 1
                cases.append({
                    "case_id": f"bishop_direct_invalid_{generated}",
                    "type": "direct_movement", "subtype": "invalid_pattern", "piece": "bishop",
                    "states": [{"pieces": {start_sq: 'B'}, "squares": []}, {"pieces": {end_sq: 'B'}, "squares": []}],
                    "label": "These are consecutive states",
                    "question": question, "expected": "no",
                    "reasoning": "Bishop cannot move in straight line"
                })

        return cases

    def _generate_rook_direct_tests(self, n_valid_direct: int, n_valid_not_direct: int, n_invalid: int) -> List[Dict]:
        cases = []
        question = """Can this piece move directly from its State 1 position to its State 2 position according to its chess movement rules?
    - Answer 'yes' if this is a valid single move for this piece
    - Answer 'no' if this requires multiple moves or violates the piece's rules
    - Answer 'unknown' if you cannot determine"""

        # Valid direct moves - with retry
        generated = 0
        for attempt in range(n_valid_direct * 10):
            if generated >= n_valid_direct:
                break
            start_sq = self._random_square()
            f, r = self._square_to_coords(start_sq)
            if random.choice([True, False]):  # Vertical
                distance = random.randint(2, 5)
                direction = random.choice([1, -1])
                end_r = r + direction * distance
                end_f = f
            else:  # Horizontal
                distance = random.randint(2, 5)
                direction = random.choice([1, -1])
                end_f = f + direction * distance
                end_r = r
            if 0 <= end_f < 8 and 0 <= end_r < 8:
                end_sq = self._coords_to_square(end_f, end_r)
                generated += 1
                cases.append({
                    "case_id": f"rook_direct_valid_{generated}",
                    "type": "direct_movement", "subtype": "valid_direct", "piece": "rook",
                    "states": [{"pieces": {start_sq: 'R'}, "squares": []}, {"pieces": {end_sq: 'R'}, "squares": []}],
                    "label": "These are consecutive states",
                    "question": question, "expected": "yes",
                    "reasoning": f"Valid straight move from {start_sq} to {end_sq}"
                })

        # Valid but not direct - different file AND different rank (requires 2 moves)
        generated = 0
        for attempt in range(n_valid_not_direct * 20):
            if generated >= n_valid_not_direct:
                break
            start_sq = self._random_square()
            f, r = self._square_to_coords(start_sq)

            # Find a square not on same file AND not on same rank
            end_f = random.randint(0, 7)
            end_r = random.randint(0, 7)

            # Must be on different file AND different rank
            if end_f != f and end_r != r:
                end_sq = self._coords_to_square(end_f, end_r)
                generated += 1
                cases.append({
                    "case_id": f"rook_direct_indirect_{generated}",
                    "type": "direct_movement", "subtype": "valid_not_direct", "piece": "rook",
                    "states": [{"pieces": {start_sq: 'R'}, "squares": []}, {"pieces": {end_sq: 'R'}, "squares": []}],
                    "label": "These are consecutive states",
                    "question": question, "expected": "no",
                    "reasoning": f"Rook at {start_sq} cannot reach {end_sq} in one move (requires both horizontal and vertical movement)"
                })

        # Invalid pattern - diagonal move
        generated = 0
        for attempt in range(n_invalid * 10):
            if generated >= n_invalid:
                break
            start_sq = self._random_square()
            f, r = self._square_to_coords(start_sq)
            end_f = min(7, f + 2)
            end_r = min(7, r + 2)
            end_sq = self._coords_to_square(end_f, end_r)
            if end_sq and end_sq != start_sq and end_f != f and end_r != r:  # Ensure diagonal
                generated += 1
                cases.append({
                    "case_id": f"rook_direct_invalid_{generated}",
                    "type": "direct_movement", "subtype": "invalid_pattern", "piece": "rook",
                    "states": [{"pieces": {start_sq: 'R'}, "squares": []}, {"pieces": {end_sq: 'R'}, "squares": []}],
                    "label": "These are consecutive states",
                    "question": question, "expected": "no",
                    "reasoning": "Rook cannot move diagonally"
                })

        return cases

    def _get_knight_move(self, square: str) -> Optional[str]:
        f, r = self._square_to_coords(square)
        l_moves = [(f+2, r+1), (f+2, r-1), (f-2, r+1), (f-2, r-1),
                   (f+1, r+2), (f+1, r-2), (f-1, r+2), (f-1, r-2)]
        valid_moves = [(nf, nr)
                       for nf, nr in l_moves if 0 <= nf < 8 and 0 <= nr < 8]
        if valid_moves:
            end_f, end_r = random.choice(valid_moves)
            return self._coords_to_square(end_f, end_r)
        return None

    # ============= Main Generation =============

    def generate_all(self, n_cases: int = 100) -> List[Dict]:
        all_cases = []
        types_counts = self._distribute_counts(n_cases, 5)

        print(f"Generating En Passant rule tests ({types_counts[0]} cases)...")
        all_cases.extend(self.generate_en_passant_rule_tests(types_counts[0]))

        print(f"Generating Castling rule tests ({types_counts[1]} cases)...")
        all_cases.extend(self.generate_castling_rule_tests(types_counts[1]))

        print(
            f"Generating En Passant event tests ({types_counts[2]} cases)...")
        all_cases.extend(self.generate_en_passant_event_tests(types_counts[2]))

        print(f"Generating Castling event tests ({types_counts[3]} cases)...")
        all_cases.extend(self.generate_castling_event_tests(types_counts[3]))

        print(f"Generating Direct Movement tests ({types_counts[4]} cases)...")
        all_cases.extend(self.generate_direct_movement_tests(types_counts[4]))

        print(f"\n✓ Total generated: {len(all_cases)} test cases")
        return all_cases
