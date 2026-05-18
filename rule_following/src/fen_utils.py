"""
Utilities for parsing verification_expected strings into piece dicts and converting to FEN.
"""

import re
from typing import List, Dict


# Piece name mappings
CHESS_PIECE_MAP = {
    'king': 'K',
    'queen': 'Q',
    'rook': 'R',
    'bishop': 'B',
    'knight': 'N',
    'pawn': 'P',
}

XIANGQI_PIECE_MAP = {
    'king': 'K',
    'general': 'K',
    'advisor': 'A',
    'guard': 'A',
    'bishop': 'E',
    'elephant': 'E',
    'knight': 'H',
    'horse': 'H',
    'rook': 'R',
    'chariot': 'R',
    'cannon': 'C',
    'pawn': 'P',
    'soldier': 'P',
}

# Colors that map to uppercase (White for chess, Red for xiangqi)
UPPERCASE_COLORS = {'white', 'red'}
LOWERCASE_COLORS = {'black'}


def parse_verification_expected(text: str, game: str = "chess") -> List[Dict[str, str]]:
    """
    Parse verification_expected string into a list of pieces dicts (one per state).

    Input format:
        "State 1: White Knight at a5; State 2: White Knight at c4"
        "State 1: Black Bishop at g6, White Pawn at g8; State 2: Black Bishop at g8"

    Returns:
        List of dicts mapping square -> FEN piece character.
        e.g. [{"a5": "N"}, {"c4": "N"}]
    """
    piece_map = CHESS_PIECE_MAP if game == "chess" else XIANGQI_PIECE_MAP

    # Split into per-state strings
    # States are separated by "; State " pattern
    states_raw = re.split(r';\s*State\s+', text)

    result = []
    for state_str in states_raw:
        # Strip "State N: " or "N: " prefix (latter when split already removed "State ")
        state_str = re.sub(r'^(State\s+)?\d+:\s*', '', state_str).strip()

        pieces = {}
        if not state_str:
            result.append(pieces)
            continue

        # Split by ", " to get individual piece entries
        entries = [e.strip() for e in state_str.split(',')]

        for entry in entries:
            # Parse "[Color] [PieceName] at [square]"
            match = re.match(
                r'(White|Black|Red)\s+(.+?)\s+at\s+([a-i]\d+)',
                entry.strip(),
                re.IGNORECASE
            )
            if not match:
                continue

            color_str = match.group(1).lower()
            piece_name = match.group(2).lower()
            square = match.group(3).lower()

            fen_char = piece_map.get(piece_name, '?')

            if color_str in LOWERCASE_COLORS:
                fen_char = fen_char.lower()
            # else uppercase (White/Red) stays uppercase

            pieces[square] = fen_char

        result.append(pieces)

    return result


def pieces_to_fen_chess(pieces: Dict[str, str]) -> str:
    """
    Convert a pieces dict to a chess FEN position string (board part only).

    Args:
        pieces: Dict mapping square (e.g. "e4") to FEN char (e.g. "N", "p")

    Returns:
        FEN string like "8/8/8/3p4/4N3/8/8/8"
    """
    board = [[None] * 8 for _ in range(8)]

    for square, piece in pieces.items():
        file_idx = ord(square[0]) - ord('a')  # a=0, h=7
        rank_idx = int(square[1]) - 1          # 1=0, 8=7

        if 0 <= file_idx < 8 and 0 <= rank_idx < 8:
            board[rank_idx][file_idx] = piece

    # Build FEN: ranks 8 down to 1
    fen_rows = []
    for rank_idx in range(7, -1, -1):
        row_str = ""
        empty = 0
        for file_idx in range(8):
            cell = board[rank_idx][file_idx]
            if cell is None:
                empty += 1
            else:
                if empty > 0:
                    row_str += str(empty)
                    empty = 0
                row_str += cell
        if empty > 0:
            row_str += str(empty)
        fen_rows.append(row_str)

    return "/".join(fen_rows)


def pieces_to_fen_xiangqi(pieces: Dict[str, str]) -> str:
    """
    Convert a pieces dict to a xiangqi FEN-like position string.

    Xiangqi board: 9 columns (a-i), 10 rows (0-9).
    FEN ranks go from row 9 (top, Black side) down to row 0 (bottom, Red side).

    Args:
        pieces: Dict mapping square (e.g. "e4") to FEN char (e.g. "H", "c")

    Returns:
        FEN-like string for xiangqi board
    """
    board = [[None] * 9 for _ in range(10)]

    for square, piece in pieces.items():
        file_idx = ord(square[0]) - ord('a')  # a=0, i=8
        rank_idx = int(square[1])              # 0-9

        if 0 <= file_idx < 9 and 0 <= rank_idx < 10:
            board[rank_idx][file_idx] = piece

    # Build FEN: rows 9 down to 0
    fen_rows = []
    for rank_idx in range(9, -1, -1):
        row_str = ""
        empty = 0
        for file_idx in range(9):
            cell = board[rank_idx][file_idx]
            if cell is None:
                empty += 1
            else:
                if empty > 0:
                    row_str += str(empty)
                    empty = 0
                row_str += cell
        if empty > 0:
            row_str += str(empty)
        fen_rows.append(row_str)

    return "/".join(fen_rows)
