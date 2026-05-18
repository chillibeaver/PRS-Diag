"""
Generate verification questions for single state xiangqi test cases
"""
import re
from typing import Dict, List


class XiangqiSingleStateVerificationGenerator:
    """Generate verification questions for single state xiangqi tests"""

    PIECE_NAMES = {
        'K': 'Red King', 'k': 'Black King',
        'A': 'Red Advisor', 'a': 'Black Advisor',
        'B': 'Red Bishop', 'b': 'Black Bishop',
        'N': 'Red Knight', 'n': 'Black Knight',
        'R': 'Red Rook', 'r': 'Black Rook',
        'C': 'Red Cannon', 'c': 'Black Cannon',
        'P': 'Red Pawn', 'p': 'Black Pawn',
    }

    PIECE_TYPES = {
        'K': 'king', 'k': 'king',
        'A': 'advisor', 'a': 'advisor',
        'B': 'bishop', 'b': 'bishop',
        'N': 'knight', 'n': 'knight',
        'R': 'rook', 'r': 'rook',
        'C': 'cannon', 'c': 'cannon',
        'P': 'pawn', 'p': 'pawn',
    }

    PIECE_MAPPING_INSTRUCTION = """
Note: Please use the following English names for the pieces:
- 帥/將 = King, 仕/士 = Advisor, 相/象 = Bishop
- 馬 = Knight, 車 = Rook, 炮/砲 = Cannon, 兵/卒 = Pawn
Red pieces have red borders, Black pieces have dark borders.
Answer format: "[Color] [PieceName] at [position]", e.g., "Red Rook at e4".
"""

    @staticmethod
    def generate_verification(case: Dict) -> Dict:
        """Generate a verification question based on pieces or highlighted squares"""
        pieces = case.get('pieces', {})
        squares = case.get('squares', [])
        all_keywords = []
        all_pieces = []  # For color-piece association check
        pieces_desc = []
        squares_desc = []

        if pieces:
            for sq, piece in pieces.items():
                p_name = XiangqiSingleStateVerificationGenerator.PIECE_NAMES.get(
                    piece, 'Unknown')
                pieces_desc.append(f"{p_name} at {sq}")
                all_keywords.append(sq)
                piece_type = XiangqiSingleStateVerificationGenerator.PIECE_TYPES.get(
                    piece, 'unknown')
                all_keywords.append(piece_type)

                # Add color keywords
                color = 'red' if piece.isupper() else 'black'
                all_keywords.append(color)

                # Store piece info for color association check
                all_pieces.append({
                    'color': color,
                    'type': piece_type,
                    'position': sq,
                    'symbol': piece
                })

        if squares:
            squares_desc = squares[:]
            all_keywords.extend(squares)

        if pieces and squares:
            question = f"What pieces are on the board and which squares are highlighted?\n{XiangqiSingleStateVerificationGenerator.PIECE_MAPPING_INSTRUCTION}"
            expected = f"Pieces: {', '.join(pieces_desc)}. Highlighted: {', '.join(squares_desc)}"
        elif pieces:
            question = f"What pieces are on the board and where are they located?\n{XiangqiSingleStateVerificationGenerator.PIECE_MAPPING_INSTRUCTION}"
            expected = ", ".join(pieces_desc)
        elif squares:
            question = "Which squares are highlighted on the board?"
            expected = f"Squares {', '.join(squares)} are highlighted"
        else:
            question = "Is the board empty?"
            expected = "Yes, the board is empty"
            all_keywords.append("empty")

        return {
            'verification_question': question,
            'verification_expected': expected,
            'verification_keywords': all_keywords,
            'verification_pieces': all_pieces
        }

    @staticmethod
    def check_verification_answer(response: str, case: Dict) -> bool:
        """Check if all key elements are mentioned with correct colors"""
        response_lower = response.lower().strip()
        for char in ".,!?'":
            response_lower = response_lower.replace(char, "")
        keywords = case.get('verification_keywords', [])
        for kw in keywords:
            if str(kw).lower() not in response_lower:
                return False

        # Enhanced: Check color-piece-position associations
        verification_pieces = case.get('verification_pieces', [])
        for piece_info in verification_pieces:
            expected_color = piece_info.get('color', '').lower()
            expected_type = piece_info.get('type', '').lower()
            expected_position = piece_info.get('position', '').lower()

            if not XiangqiSingleStateVerificationGenerator._check_color_piece_association(
                response_lower, expected_color, expected_type, expected_position
            ):
                return False

        return True

    @staticmethod
    def _check_color_piece_association(response: str, color: str, piece_type: str, position: str) -> bool:
        """
        Check if the color-piece-position association is correct in the response.

        Validates that:
        1. The correct color appears near the piece type
        2. The piece type appears near the position
        3. The wrong color does not appear associated with this piece at this position

        Args:
            response: Cleaned response string (lowercase)
            color: Expected color ('red' or 'black')
            piece_type: Expected piece type (e.g., 'rook', 'king')
            position: Expected position (e.g., 'e4')

        Returns:
            True if association is correct, False otherwise
        """
        # Define the opposite color
        opposite_color = 'black' if color == 'red' else 'red'

        # Pattern 1: "[color] [piece_type] at [position]" or similar
        # Allow some flexibility in format
        pattern1 = rf'{color}\s+{piece_type}.*?{position}'
        pattern2 = rf'{position}.*?{color}\s+{piece_type}'
        pattern3 = rf'{piece_type}.*?{position}.*?{color}'
        pattern4 = rf'{color}.*?{piece_type}.*?{position}'

        # Check if any valid pattern matches
        valid_patterns = [pattern1, pattern2, pattern3, pattern4]
        found_valid = any(re.search(p, response) for p in valid_patterns)

        # Check for wrong color association with same piece at same position
        wrong_pattern1 = rf'{opposite_color}\s+{piece_type}.*?{position}'
        wrong_pattern2 = rf'{position}.*?{opposite_color}\s+{piece_type}'

        # If wrong color is associated, fail
        found_wrong = re.search(wrong_pattern1, response) or re.search(
            wrong_pattern2, response)

        # Must find valid association and not find wrong association
        return found_valid and not found_wrong
