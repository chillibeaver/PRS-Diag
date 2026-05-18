"""
Generate verification questions for single state chess test cases
"""
import re
from typing import Dict, List


class ChessSingleStateVerificationGenerator:
    """Generate verification questions for single state chess tests"""

    @staticmethod
    def generate_verification(case: Dict) -> Dict:
        """
        Generate a verification question based on pieces or highlighted squares
        """
        pieces = case.get('pieces', {})
        squares = case.get('squares', [])

        all_keywords = []
        all_pieces = []  # For color-piece association check
        pieces_desc = []

        # 1. Verification based on pieces present
        if pieces:
            for sq, piece in pieces.items():
                p_name = ChessSingleStateVerificationGenerator._piece_name(
                    piece)
                pieces_desc.append(f"{p_name} at {sq}")
                all_keywords.append(sq)
                piece_type = ChessSingleStateVerificationGenerator._get_piece_type(
                    piece)
                all_keywords.append(piece_type)

                # Add color keywords
                color = 'white' if piece.isupper() else 'black'
                all_keywords.append(color)

                # Store piece info for color association check
                all_pieces.append({
                    'color': color,
                    'type': piece_type,
                    'position': sq,
                    'symbol': piece
                })

            question = "What pieces are on the board and where are they located?"
            expected = ", ".join(pieces_desc)

        # 2. Verification based on highlighted squares (if no pieces, e.g. Test 0 empty board)
        elif squares:
            question = "Which squares are highlighted on the empty board?"
            expected = f"Squares {', '.join(squares)} are highlighted"
            all_keywords.extend(squares)

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
    def _piece_name(symbol: str) -> str:
        return {'K': 'White King', 'Q': 'White Queen', 'R': 'White Rook', 'B': 'White Bishop',
                'N': 'White Knight', 'P': 'White Pawn', 'k': 'Black King', 'q': 'Black Queen',
                'r': 'Black Rook', 'b': 'Black Bishop', 'n': 'Black Knight', 'p': 'Black Pawn'}.get(symbol, 'Unknown')

    @staticmethod
    def _get_piece_type(symbol: str) -> str:
        return {'K': 'king', 'Q': 'queen', 'R': 'rook', 'B': 'bishop', 'N': 'knight', 'P': 'pawn',
                'k': 'king', 'q': 'queen', 'r': 'rook', 'b': 'bishop', 'n': 'knight', 'p': 'pawn'}.get(symbol, 'unknown')

    @staticmethod
    def check_verification_answer(response: str, case: Dict) -> bool:
        """Check if all key elements (squares/pieces) are mentioned with correct colors"""
        response_lower = response.lower().strip()
        # Clean punctuation to avoid matching issues (e.g. "e4." vs "e4")
        for char in ".,!?'":
            response_lower = response_lower.replace(char, "")

        keywords = case.get('verification_keywords', [])

        # Simple keyword matching: all keywords must be present
        for kw in keywords:
            if str(kw).lower() not in response_lower:
                return False

        # Enhanced: Check color-piece-position associations
        verification_pieces = case.get('verification_pieces', [])
        for piece_info in verification_pieces:
            expected_color = piece_info.get('color', '').lower()
            expected_type = piece_info.get('type', '').lower()
            expected_position = piece_info.get('position', '').lower()

            if not ChessSingleStateVerificationGenerator._check_color_piece_association(
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
            color: Expected color ('white' or 'black')
            piece_type: Expected piece type (e.g., 'rook', 'king')
            position: Expected position (e.g., 'e4')

        Returns:
            True if association is correct, False otherwise
        """
        # Define the opposite color
        opposite_color = 'black' if color == 'white' else 'white'

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
