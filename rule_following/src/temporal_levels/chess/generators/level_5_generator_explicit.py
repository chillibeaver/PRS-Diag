"""
Level 5 Generator: Castling + Temporal History + 2 Check Rules (Explicit Version)
Aligned with Predictive version - tests temporal rules for castling

Shows N+1 states (predictive shows N):
- valid_other_moved: 4 states (was 3)
- invalid_king_moved: 4 states (was 3)
- invalid_rook_moved: 4 states (was 3)
- invalid_check_violation: 3 states (was 2)

Question: "Is this castling move legal?"
"""

import random
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict


class Level5Generator:
    """Generate Level 5 test cases - castling with temporal history + 2 check rules (Explicit version)"""

    PIECE_LIMITS = {
        'king': 1,
        'queen': 1,
        'rook': 2,
        'bishop': 2,
        'knight': 2
    }

    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        self.ranks = ['1', '2', '3', '4', '5', '6', '7', '8']

        self.castling_configs = {
            'white_kingside': {
                'king_start': 'e1', 'king_end': 'g1',
                'rook_start': 'h1', 'rook_end': 'f1',
                'in_sq': 'e1', 'through_sq': 'f1', 'into_sq': 'g1',
                'color': 'white',
                'king_symbol': 'K', 'rook_symbol': 'R',
                'path_squares': ['f1', 'g1'],
                'king_temp_moves': ['d1', 'f1'],
                'rook_temp_moves': ['g1', 'f1'],
                'question_text': 'white castle kingside'
            },
            'white_queenside': {
                'king_start': 'e1', 'king_end': 'c1',
                'rook_start': 'a1', 'rook_end': 'd1',
                'in_sq': 'e1', 'through_sq': 'd1', 'into_sq': 'c1',
                'color': 'white',
                'king_symbol': 'K', 'rook_symbol': 'R',
                'path_squares': ['b1', 'c1', 'd1'],
                'king_temp_moves': ['d1', 'f1'],
                'rook_temp_moves': ['b1', 'c1'],
                'question_text': 'white castle queenside'
            },
            'black_kingside': {
                'king_start': 'e8', 'king_end': 'g8',
                'rook_start': 'h8', 'rook_end': 'f8',
                'in_sq': 'e8', 'through_sq': 'f8', 'into_sq': 'g8',
                'color': 'black',
                'king_symbol': 'k', 'rook_symbol': 'r',
                'path_squares': ['f8', 'g8'],
                'king_temp_moves': ['d8', 'f8'],
                'rook_temp_moves': ['g8', 'f8'],
                'question_text': 'black castle kingside'
            },
            'black_queenside': {
                'king_start': 'e8', 'king_end': 'c8',
                'rook_start': 'a8', 'rook_end': 'd8',
                'in_sq': 'e8', 'through_sq': 'd8', 'into_sq': 'c8',
                'color': 'black',
                'king_symbol': 'k', 'rook_symbol': 'r',
                'path_squares': ['b8', 'c8', 'd8'],
                'king_temp_moves': ['d8', 'f8'],
                'rook_temp_moves': ['b8', 'c8'],
                'question_text': 'black castle queenside'
            }
        }

        # Level 5 tests 2 rules (choose 2 from 3)
        self.check_combinations = [
            ['in', 'through'],
            ['in', 'into'],
            ['through', 'into']
        ]

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

    def _can_add_piece(self, piece_type: str, color: str, piece_counts: Dict) -> bool:
        key = (piece_type, color)
        current = piece_counts.get(key, 0)
        limit = self.PIECE_LIMITS.get(piece_type, 2)
        return current < limit

    def _add_piece_to_counts(self, piece_type: str, color: str, piece_counts: Dict):
        key = (piece_type, color)
        piece_counts[key] = piece_counts.get(key, 0) + 1

    def _get_piece_symbol(self, piece_type: str, color: str) -> str:
        symbols = {
            ('rook', 'white'): 'R', ('rook', 'black'): 'r',
            ('bishop', 'white'): 'B', ('bishop', 'black'): 'b',
            ('knight', 'white'): 'N', ('knight', 'black'): 'n',
            ('queen', 'white'): 'Q', ('queen', 'black'): 'q',
            ('pawn', 'white'): 'P', ('pawn', 'black'): 'p'
        }
        return symbols.get((piece_type, color), 'p')

    def _get_path_squares(self, from_sq: str, to_sq: str) -> List[str]:
        from_f, from_r = self._square_to_coords(from_sq)
        to_f, to_r = self._square_to_coords(to_sq)
        df, dr = to_f - from_f, to_r - from_r
        step_f = 0 if df == 0 else (1 if df > 0 else -1)
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        if not ((df == 0 and dr != 0) or (dr == 0 and df != 0) or (abs(df) == abs(dr) and df != 0)):
            return []
        path = []
        curr_f, curr_r = from_f + step_f, from_r + step_r
        while (curr_f, curr_r) != (to_f, to_r):
            sq = self._coords_to_square(curr_f, curr_r)
            if sq:
                path.append(sq)
            curr_f += step_f
            curr_r += step_r
        return path

    def _is_path_clear(self, from_sq: str, to_sq: str, occupied: Set[str]) -> bool:
        for sq in self._get_path_squares(from_sq, to_sq):
            if sq in occupied:
                return False
        return True

    def _can_attack(self, from_sq: str, to_sq: str, piece_type: str) -> bool:
        from_f, from_r = self._square_to_coords(from_sq)
        to_f, to_r = self._square_to_coords(to_sq)
        df, dr = abs(to_f - from_f), abs(to_r - from_r)
        if piece_type == 'rook':
            return (df == 0 and dr > 0) or (dr == 0 and df > 0)
        elif piece_type == 'bishop':
            return df == dr and df > 0
        elif piece_type == 'queen':
            return (df == 0 and dr > 0) or (dr == 0 and df > 0) or (df == dr and df > 0)
        elif piece_type == 'knight':
            return (df == 2 and dr == 1) or (df == 1 and dr == 2)
        return False

    def _can_attack_with_clear_path(self, from_sq: str, to_sq: str,
                                    piece_type: str, occupied: Set[str]) -> bool:
        if not self._can_attack(from_sq, to_sq, piece_type):
            return False
        if piece_type == 'knight':
            return True
        return self._is_path_clear(from_sq, to_sq, occupied)

    def _get_attacker_positions(self, target_sq: str, attacker_type: str,
                                forbidden: Set[str], occupied: Set[str]) -> List[str]:
        target_f, target_r = self._square_to_coords(target_sq)
        positions = []
        if attacker_type in ['rook', 'queen']:
            for f in range(8):
                if f != target_f:
                    sq = self._coords_to_square(f, target_r)
                    if sq and sq not in forbidden and self._is_path_clear(sq, target_sq, occupied):
                        positions.append(sq)
            for r in range(8):
                if r != target_r:
                    sq = self._coords_to_square(target_f, r)
                    if sq and sq not in forbidden and self._is_path_clear(sq, target_sq, occupied):
                        positions.append(sq)
        if attacker_type in ['bishop', 'queen']:
            for d in range(1, 8):
                for df, dr in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                    sq = self._coords_to_square(
                        target_f + df * d, target_r + dr * d)
                    if sq and sq not in forbidden and self._is_path_clear(sq, target_sq, occupied):
                        positions.append(sq)
        if attacker_type == 'knight':
            for df, dr in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
                sq = self._coords_to_square(target_f + df, target_r + dr)
                if sq and sq not in forbidden:
                    positions.append(sq)
        return positions

    def _get_non_attacking_square(self, critical_squares: List[str],
                                  forbidden: Set[str], piece_type: str,
                                  occupied: Set[str]) -> Optional[str]:
        for _ in range(100):
            sq = self._random_square()
            if sq in forbidden:
                continue
            attacks = False
            for c_sq in critical_squares:
                if self._can_attack_with_clear_path(sq, c_sq, piece_type, occupied):
                    attacks = True
                    break
            if not attacks:
                return sq
        return None

    def _get_knight_moves(self, square: str, forbidden: Set[str]) -> List[str]:
        f, r = self._square_to_coords(square)
        moves = []
        for df, dr in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
            sq = self._coords_to_square(f + df, r + dr)
            if sq and sq not in forbidden:
                moves.append(sq)
        return moves

    def _get_legal_start_positions(self, end_sq: str, piece_type: str,
                                   forbidden: Set[str], occupied: Set[str],
                                   critical_squares: List[str]) -> List[str]:
        end_f, end_r = self._square_to_coords(end_sq)
        positions = []

        if piece_type == 'knight':
            for df, dr in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
                sq = self._coords_to_square(end_f + df, end_r + dr)
                if sq and sq not in forbidden:
                    attacks_critical = False
                    for c_sq in critical_squares:
                        if self._can_attack(sq, c_sq, 'knight'):
                            attacks_critical = True
                            break
                    if not attacks_critical:
                        positions.append(sq)

        elif piece_type in ['rook', 'bishop', 'queen']:
            directions = []
            if piece_type in ['rook', 'queen']:
                directions.extend([(1, 0), (-1, 0), (0, 1), (0, -1)])
            if piece_type in ['bishop', 'queen']:
                directions.extend([(1, 1), (1, -1), (-1, 1), (-1, -1)])

            for df, dr in directions:
                for dist in range(1, 8):
                    sq = self._coords_to_square(
                        end_f + df * dist, end_r + dr * dist)
                    if sq and sq not in forbidden:
                        if self._is_path_clear(sq, end_sq, occupied):
                            attacks_critical = False
                            for c_sq in critical_squares:
                                if self._can_attack_with_clear_path(sq, c_sq, piece_type, occupied):
                                    attacks_critical = True
                                    break
                            if not attacks_critical:
                                positions.append(sq)

        return positions

    # ==================== VALID CASES ====================

    def _generate_valid_case(self, case_num: int, check_combo: List[str]) -> Optional[Dict]:
        """
        Valid: Other pieces moved, king/rook haven't moved
        State 1: Initial (king/rook in place + other pieces)
        State 2: Other pieces move (king/rook don't move)
        State 3: Other pieces move again (king/rook still don't move)
        State 4: Castling completed
        Answer: Yes
        """
        castling_type = random.choice(list(self.castling_configs.keys()))
        config = self.castling_configs[castling_type]

        piece_counts = {}
        self._add_piece_to_counts('king', config['color'], piece_counts)
        self._add_piece_to_counts('rook', config['color'], piece_counts)

        target_map = {
            'in': config['in_sq'], 'through': config['through_sq'], 'into': config['into_sq']}
        critical_squares = [target_map[rule] for rule in check_combo]

        occupied = {config['king_start'], config['rook_start']}
        path_squares = set(config['path_squares'])
        forbidden = occupied | path_squares

        # Add a moving knight
        moving_piece_color = config['color']
        knight_sq = self._get_non_attacking_square(
            critical_squares, forbidden, 'knight', occupied)
        if not knight_sq:
            return None

        knight_symbol = 'N' if moving_piece_color == 'white' else 'n'
        self._add_piece_to_counts('knight', moving_piece_color, piece_counts)
        forbidden.add(knight_sq)
        occupied.add(knight_sq)

        knight_moves = self._get_knight_moves(knight_sq, forbidden)
        valid_knight_targets = []
        for target in knight_moves:
            test_occupied = (occupied - {knight_sq}) | {target}
            attacks = False
            for c_sq in critical_squares:
                if self._can_attack_with_clear_path(target, c_sq, 'knight', test_occupied):
                    attacks = True
                    break
            if not attacks:
                valid_knight_targets.append(target)

        if len(valid_knight_targets) < 2:
            return None

        knight_target_1 = valid_knight_targets[0]

        forbidden_2 = forbidden | {knight_target_1}
        knight_moves_2 = self._get_knight_moves(
            knight_target_1, forbidden_2 - {knight_sq})
        valid_knight_targets_2 = []
        for target in knight_moves_2:
            test_occupied = (occupied - {knight_sq}) | {target}
            attacks = False
            for c_sq in critical_squares:
                if self._can_attack_with_clear_path(target, c_sq, 'knight', test_occupied):
                    attacks = True
                    break
            if not attacks:
                valid_knight_targets_2.append(target)

        if not valid_knight_targets_2:
            return None

        knight_target_2 = random.choice(valid_knight_targets_2)

        # Add extra static pieces
        extra_pieces = {}
        for _ in range(random.randint(1, 2)):
            for _ in range(50):
                p_type = random.choice(['bishop', 'knight'])
                p_color = random.choice(['white', 'black'])
                if not self._can_add_piece(p_type, p_color, piece_counts):
                    continue
                sq = self._get_non_attacking_square(
                    critical_squares, forbidden, p_type, occupied)
                if sq:
                    extra_pieces[sq] = self._get_piece_symbol(p_type, p_color)
                    forbidden.add(sq)
                    occupied.add(sq)
                    self._add_piece_to_counts(p_type, p_color, piece_counts)
                    break

        base_pieces = {
            config['king_start']: config['king_symbol'],
            config['rook_start']: config['rook_symbol'],
            **extra_pieces
        }

        state1 = {**base_pieces, knight_sq: knight_symbol}
        state2 = {**base_pieces, knight_target_1: knight_symbol}
        state3 = {**base_pieces, knight_target_2: knight_symbol}

        # State 4: Castling completed
        state4 = {
            config['king_end']: config['king_symbol'],
            config['rook_end']: config['rook_symbol'],
            knight_target_2: knight_symbol,
            **extra_pieces
        }

        return {
            "case_id": f"L5_valid_{case_num}",
            "type": "castling_temporal_explicit",
            "subtype": "valid_other_moved",
            "castling_type": castling_type,
            "check_rules_tested": check_combo,
            "invalid_reason": None,
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []},
                {"pieces": state4, "squares": []}
            ],
            "question": f"Is this castling move legal?",
            "expected": "yes",
            "reasoning": f"King and rook have not moved; rules tested [{', '.join(check_combo)}] are satisfied"
        }

    # ==================== INVALID: KING MOVED ====================

    def _generate_king_moved_case(self, case_num: int, check_combo: List[str]) -> Optional[Dict]:
        """
        Invalid: King moved and moved back
        State 1: King at original position
        State 2: King moves to temporary position
        State 3: King moves back to original position
        State 4: Attempted castling (illegal)
        """
        castling_type = random.choice(list(self.castling_configs.keys()))
        config = self.castling_configs[castling_type]

        piece_counts = {}
        self._add_piece_to_counts('king', config['color'], piece_counts)
        self._add_piece_to_counts('rook', config['color'], piece_counts)

        king_temp = random.choice(config['king_temp_moves'])

        occupied = {config['king_start'], config['rook_start']}
        path_squares = set(config['path_squares'])
        forbidden = occupied | path_squares | {king_temp}

        extra_pieces = {}
        target_map = {
            'in': config['in_sq'], 'through': config['through_sq'], 'into': config['into_sq']}
        critical_squares = [target_map[rule] for rule in check_combo]

        for _ in range(random.randint(1, 2)):
            for _ in range(50):
                p_type = random.choice(['bishop', 'knight'])
                p_color = random.choice(['white', 'black'])
                if not self._can_add_piece(p_type, p_color, piece_counts):
                    continue
                sq = self._get_non_attacking_square(
                    critical_squares, forbidden, p_type, occupied)
                if sq:
                    extra_pieces[sq] = self._get_piece_symbol(p_type, p_color)
                    forbidden.add(sq)
                    occupied.add(sq)
                    self._add_piece_to_counts(p_type, p_color, piece_counts)
                    break

        base_pieces = {config['rook_start']
            : config['rook_symbol'], **extra_pieces}

        state1 = {config['king_start']: config['king_symbol'], **base_pieces}
        state2 = {king_temp: config['king_symbol'], **base_pieces}
        state3 = {config['king_start']: config['king_symbol'], **base_pieces}

        # State 4: Attempted castling (illegal)
        state4 = {
            config['king_end']: config['king_symbol'],
            config['rook_end']: config['rook_symbol'],
            **extra_pieces
        }

        return {
            "case_id": f"L5_king_moved_{case_num}",
            "type": "castling_temporal_explicit",
            "subtype": "invalid_king_moved",
            "castling_type": castling_type,
            "check_rules_tested": check_combo,
            "invalid_reason": "king_moved",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []},
                {"pieces": state4, "squares": []}
            ],
            "question": f"Is this castling move legal?",
            "expected": "no",
            "reasoning": f"King moved from {config['king_start']} to {king_temp} and back; castling rights lost"
        }

    # ==================== INVALID: ROOK MOVED ====================

    def _generate_rook_moved_case(self, case_num: int, check_combo: List[str]) -> Optional[Dict]:
        """
        Invalid: Rook moved and moved back
        State 1: Rook at original position
        State 2: Rook moves to temporary position
        State 3: Rook moves back to original position
        State 4: Attempted castling (illegal)
        """
        castling_type = random.choice(list(self.castling_configs.keys()))
        config = self.castling_configs[castling_type]

        piece_counts = {}
        self._add_piece_to_counts('king', config['color'], piece_counts)
        self._add_piece_to_counts('rook', config['color'], piece_counts)

        rook_temp = random.choice(config['rook_temp_moves'])

        occupied = {config['king_start'], config['rook_start']}
        path_squares = set(config['path_squares'])
        forbidden = occupied | path_squares | {rook_temp}

        extra_pieces = {}
        target_map = {
            'in': config['in_sq'], 'through': config['through_sq'], 'into': config['into_sq']}
        critical_squares = [target_map[rule] for rule in check_combo]

        for _ in range(random.randint(1, 2)):
            for _ in range(50):
                p_type = random.choice(['bishop', 'knight'])
                p_color = random.choice(['white', 'black'])
                if not self._can_add_piece(p_type, p_color, piece_counts):
                    continue
                sq = self._get_non_attacking_square(
                    critical_squares, forbidden, p_type, occupied)
                if sq:
                    extra_pieces[sq] = self._get_piece_symbol(p_type, p_color)
                    forbidden.add(sq)
                    occupied.add(sq)
                    self._add_piece_to_counts(p_type, p_color, piece_counts)
                    break

        base_pieces = {config['king_start']
            : config['king_symbol'], **extra_pieces}

        state1 = {config['rook_start']: config['rook_symbol'], **base_pieces}
        state2 = {rook_temp: config['rook_symbol'], **base_pieces}
        state3 = {config['rook_start']: config['rook_symbol'], **base_pieces}

        # State 4: Attempted castling (illegal)
        state4 = {
            config['king_end']: config['king_symbol'],
            config['rook_end']: config['rook_symbol'],
            **extra_pieces
        }

        return {
            "case_id": f"L5_rook_moved_{case_num}",
            "type": "castling_temporal_explicit",
            "subtype": "invalid_rook_moved",
            "castling_type": castling_type,
            "check_rules_tested": check_combo,
            "invalid_reason": "rook_moved",
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []},
                {"pieces": state4, "squares": []}
            ],
            "question": f"Is this castling move legal?",
            "expected": "no",
            "reasoning": f"Rook moved from {config['rook_start']} to {rook_temp} and back; castling rights lost"
        }

    # ==================== INVALID: CHECK VIOLATION ====================

    def _generate_check_violation_case(self, case_num: int, check_combo: List[str],
                                       violation_type: str) -> Optional[Dict]:
        """
        Invalid: Enemy piece attacks critical square
        State 1: Initial (no threat)
        State 2: Enemy piece moves to attacking position
        State 3: Attempted castling (illegal)
        """
        castling_type = random.choice(list(self.castling_configs.keys()))
        config = self.castling_configs[castling_type]

        piece_counts = {}
        self._add_piece_to_counts('king', config['color'], piece_counts)
        self._add_piece_to_counts('rook', config['color'], piece_counts)

        target_map = {
            'in': config['in_sq'], 'through': config['through_sq'], 'into': config['into_sq']}

        attack_targets = []
        violation_details = []

        if violation_type == 'first' or violation_type == 'both':
            rule = check_combo[0]
            attack_targets.append(target_map[rule])
            violation_details.append(f'{rule}_check')

        if violation_type == 'second' or violation_type == 'both':
            rule = check_combo[1]
            attack_targets.append(target_map[rule])
            violation_details.append(f'{rule}_check')

        attack_targets = list(set(attack_targets))
        violation_details = list(set(violation_details))

        occupied = {config['king_start'], config['rook_start']}
        path_squares = set(config['path_squares'])
        forbidden = occupied | path_squares

        attacker_color = 'black' if config['color'] == 'white' else 'white'
        critical_squares = [target_map[rule] for rule in check_combo]

        extra_pieces = {}
        attacker_info = []

        for target_sq in attack_targets:
            attacker_types = ['rook', 'bishop', 'knight', 'queen']
            random.shuffle(attacker_types)

            placed = False
            for a_type in attacker_types:
                if placed:
                    break
                if not self._can_add_piece(a_type, attacker_color, piece_counts):
                    continue

                final_positions = self._get_attacker_positions(
                    target_sq, a_type, forbidden, occupied)
                if not final_positions:
                    continue

                random.shuffle(final_positions)

                for final_pos in final_positions:
                    forbidden_for_start = forbidden | {final_pos}
                    start_positions = self._get_legal_start_positions(
                        final_pos, a_type, forbidden_for_start, occupied, critical_squares
                    )

                    if start_positions:
                        attacker_start = random.choice(start_positions)
                        attacker_final = final_pos

                        self._add_piece_to_counts(
                            a_type, attacker_color, piece_counts)
                        attacker_symbol = self._get_piece_symbol(
                            a_type, attacker_color)

                        attacker_info.append(
                            (attacker_start, attacker_final, a_type, target_sq, attacker_symbol))
                        forbidden.add(attacker_start)
                        forbidden.add(attacker_final)
                        occupied.add(attacker_start)
                        placed = True
                        break

            if not placed:
                return None

        # Add extra pieces
        protected_squares = set()
        for start, final, a_type, target, _ in attacker_info:
            protected_squares |= set(self._get_path_squares(start, final))
            if a_type != 'knight':
                protected_squares |= set(self._get_path_squares(final, target))

        non_targeted = [
            sq for sq in critical_squares if sq not in attack_targets]

        for _ in range(random.randint(1, 2)):
            for _ in range(50):
                p_type = random.choice(['bishop', 'knight'])
                p_color = random.choice(['white', 'black'])
                if not self._can_add_piece(p_type, p_color, piece_counts):
                    continue
                forbidden_extra = forbidden | protected_squares
                sq = self._get_non_attacking_square(
                    non_targeted, forbidden_extra, p_type, occupied)
                if sq:
                    extra_pieces[sq] = self._get_piece_symbol(p_type, p_color)
                    forbidden.add(sq)
                    occupied.add(sq)
                    self._add_piece_to_counts(p_type, p_color, piece_counts)
                    break

        base_pieces = {
            config['king_start']: config['king_symbol'],
            config['rook_start']: config['rook_symbol'],
            **extra_pieces
        }

        state1_attackers = {info[0]: info[4] for info in attacker_info}
        state2_attackers = {info[1]: info[4] for info in attacker_info}

        state1 = {**base_pieces, **state1_attackers}
        state2 = {**base_pieces, **state2_attackers}

        # State 3: Attempted castling (illegal)
        state3 = {
            config['king_end']: config['king_symbol'],
            config['rook_end']: config['rook_symbol'],
            **extra_pieces,
            **state2_attackers
        }

        return {
            "case_id": f"L5_check_{case_num}",
            "type": "castling_temporal_explicit",
            "subtype": "invalid_check_violation",
            "castling_type": castling_type,
            "check_rules_tested": check_combo,
            "invalid_reason": violation_details,
            "states": [
                {"pieces": state1, "squares": []},
                {"pieces": state2, "squares": []},
                {"pieces": state3, "squares": []}
            ],
            "question": f"Is this castling move legal?",
            "expected": "no",
            "reasoning": f"Violates: {', '.join(violation_details)}"
        }

    # ==================== GENERATE ALL ====================

    def generate_all(self, n_cases: int = 100, valid_ratio: float = 0.20) -> List[Dict]:
        """Generate all Level 5 test cases"""
        all_cases = []

        n_valid = int(n_cases * valid_ratio)
        n_invalid = n_cases - n_valid

        n_temporal = int(n_invalid * 0.4)
        n_check = n_invalid - n_temporal

        n_king_moved = n_temporal // 2
        n_rook_moved = n_temporal - n_king_moved

        n_check_per_combo = n_check // 3
        n_check_remainder = n_check % 3

        # Valid cases
        print(f"Generating {n_valid} VALID cases...")
        valid_gen = 0
        combo_idx = 0
        for _ in range(n_valid * 10):
            if valid_gen >= n_valid:
                break
            check_combo = self.check_combinations[combo_idx % 3]
            combo_idx += 1
            case = self._generate_valid_case(valid_gen + 1, check_combo)
            if case:
                all_cases.append(case)
                valid_gen += 1
        print(f"  ✓ Generated {valid_gen} valid cases")

        # Invalid: King moved
        print(f"Generating {n_king_moved} INVALID cases (king moved)...")
        king_gen = 0
        combo_idx = 0
        for _ in range(n_king_moved * 10):
            if king_gen >= n_king_moved:
                break
            check_combo = self.check_combinations[combo_idx % 3]
            combo_idx += 1
            case = self._generate_king_moved_case(king_gen + 1, check_combo)
            if case:
                all_cases.append(case)
                king_gen += 1
        print(f"  ✓ Generated {king_gen} king-moved cases")

        # Invalid: Rook moved
        print(f"Generating {n_rook_moved} INVALID cases (rook moved)...")
        rook_gen = 0
        combo_idx = 0
        for _ in range(n_rook_moved * 10):
            if rook_gen >= n_rook_moved:
                break
            check_combo = self.check_combinations[combo_idx % 3]
            combo_idx += 1
            case = self._generate_rook_moved_case(rook_gen + 1, check_combo)
            if case:
                all_cases.append(case)
                rook_gen += 1
        print(f"  ✓ Generated {rook_gen} rook-moved cases")

        # Invalid: Check violations
        print(f"Generating check violation cases...")
        check_gen = 0

        for combo_idx, check_combo in enumerate(self.check_combinations):
            n_combo = n_check_per_combo + \
                (1 if combo_idx < n_check_remainder else 0)
            n_first = n_combo // 3
            n_second = n_combo // 3
            n_both = n_combo - n_first - n_second

            combo_name = f"[{check_combo[0]}, {check_combo[1]}]"

            for _ in range(n_first * 10):
                if check_gen >= n_check:
                    break
                case = self._generate_check_violation_case(
                    check_gen + 1, check_combo, 'first')
                if case:
                    all_cases.append(case)
                    check_gen += 1
                    if len([c for c in all_cases if c.get('check_rules_tested') == check_combo and
                            c.get('invalid_reason') and 'first' in str(c.get('invalid_reason', []))]) >= n_first:
                        break

            for _ in range(n_second * 10):
                if check_gen >= n_check:
                    break
                case = self._generate_check_violation_case(
                    check_gen + 1, check_combo, 'second')
                if case:
                    all_cases.append(case)
                    check_gen += 1
                    if len([c for c in all_cases if c.get('check_rules_tested') == check_combo and
                            c.get('subtype') == 'invalid_check_violation']) >= n_first + n_second:
                        break

            for _ in range(n_both * 10):
                if check_gen >= n_check:
                    break
                case = self._generate_check_violation_case(
                    check_gen + 1, check_combo, 'both')
                if case:
                    all_cases.append(case)
                    check_gen += 1

            print(f"  ✓ Generated cases for combo {combo_name}")

        random.shuffle(all_cases)

        # Stats
        stats = defaultdict(int)
        for case in all_cases:
            stats[case['subtype']] += 1

        print(f"\n✓ Total generated: {len(all_cases)} Level 5 test cases")
        print(f"  Breakdown:")
        for subtype, count in sorted(stats.items()):
            print(f"    {subtype}: {count} ({count/len(all_cases)*100:.1f}%)")

        return all_cases
