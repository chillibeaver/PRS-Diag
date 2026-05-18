"""
Generate verification questions for Xiangqi Multi-State test cases
To ensure the model can correctly recognize each board state before testing
"""

from typing import Dict, List


class XiangqiMultiStateVerificationGenerator:
    """Generate verification questions for Xiangqi multi-state test cases"""

    # Piece symbol to English name mapping
    PIECE_NAMES = {
        'K': 'Red King', 'k': 'Black King',
        'A': 'Red Advisor', 'a': 'Black Advisor',
        'B': 'Red Bishop', 'b': 'Black Bishop',
        'N': 'Red Knight', 'n': 'Black Knight',
        'R': 'Red Rook', 'r': 'Black Rook',
        'C': 'Red Cannon', 'c': 'Black Cannon',
        'P': 'Red Pawn', 'p': 'Black Pawn',
    }

    # Piece type keywords for verification matching
    PIECE_TYPES = {
        'K': 'king', 'k': 'king',
        'A': 'advisor', 'a': 'advisor',
        'B': 'bishop', 'b': 'bishop',
        'N': 'knight', 'n': 'knight',
        'R': 'rook', 'r': 'rook',
        'C': 'cannon', 'c': 'cannon',
        'P': 'pawn', 'p': 'pawn',
    }

    # Piece name mapping instruction for prompts
    PIECE_MAPPING_INSTRUCTION = """
Note: Please use the following English names for the pieces shown on the board:
- 帥/將 = King
- 仕/士 = Advisor
- 相/象 = Bishop
- 馬 = Knight
- 車 = Rook
- 炮/砲 = Cannon
- 兵/卒 = Pawn

Red pieces have red borders, Black pieces have dark borders.
Please answer using the format: "[Color] [PieceName] at [position]", e.g., "Red Rook at e4".
"""

    @staticmethod
    def generate_verification(case: Dict) -> Dict:
        """
        Generate a verification question for a multi-state test case

        Args:
            case: Test case dictionary with multiple states

        Returns:
            Dictionary with verification_question, verification_expected, verification_keywords
        """
        states = case.get('states', [])

        # For event recognition tests with multiple choice
        if 'options' in case:
            return XiangqiMultiStateVerificationGenerator._verify_with_options(case)

        # Default: verify all states
        return XiangqiMultiStateVerificationGenerator._verify_all_states(states)

    @staticmethod
    def _verify_with_options(case: Dict) -> Dict:
        """Verify for multiple choice cases - ask about ALL states"""
        states = case.get('states', [])
        return XiangqiMultiStateVerificationGenerator._verify_all_states(states)

    @staticmethod
    def _verify_all_states(states: List[Dict]) -> Dict:
        """
        Verify by asking about ALL states' content
        """
        if not states:
            return {
                'verification_question': "Can you see Xiangqi board states in these images?",
                'verification_expected': "yes",
                'verification_keywords': ['yes', 'board'],
                'verification_pieces': []
            }

        all_states_desc = []
        all_keywords = []
        all_pieces = []

        for i, state in enumerate(states):
            pieces = state.get('pieces', {})
            pieces_desc = []

            for sq, piece in pieces.items():
                piece_name = XiangqiMultiStateVerificationGenerator.PIECE_NAMES.get(
                    piece, 'Unknown')
                pieces_desc.append(f"{piece_name} at {sq}")

                # Add keywords
                all_keywords.append(sq)
                piece_type = XiangqiMultiStateVerificationGenerator.PIECE_TYPES.get(
                    piece, 'unknown')
                all_keywords.append(piece_type)

                # Add color keywords and piece info for association check
                if piece.isupper():
                    color = "red"
                else:
                    color = "black"
                all_keywords.append(color)

                # Store detailed piece info for color association verification
                all_pieces.append({
                    'color': color,
                    'type': piece_type,
                    'position': sq,
                    'state_index': i + 1,
                    'symbol': piece
                })

            state_text = ", ".join(
                pieces_desc) if pieces_desc else "Empty board"
            all_states_desc.append(f"State {i+1}: {state_text}")

        expected = "; ".join(all_states_desc)

        # Generate question based on number of states
        n = len(states)
        mapping = XiangqiMultiStateVerificationGenerator.PIECE_MAPPING_INSTRUCTION

        if n == 1:
            question = f"What are the pieces and their positions in State 1?\n{mapping}"
        elif n == 2:
            question = f"What are the pieces and their positions in State 1? What about State 2?\n{mapping}"
        elif n == 3:
            question = f"What are the pieces and their positions in State 1? State 2? State 3?\n{mapping}"
        elif n == 4:
            question = f"What are the pieces and their positions in State 1? State 2? State 3? State 4?\n{mapping}"
        elif n == 5:
            question = f"What are the pieces and their positions in States 1 through 5?\n{mapping}"
        elif n == 6:
            question = f"What are the pieces and their positions in States 1 through 6?\n{mapping}"
        else:
            question = f"What are the pieces and their positions in each of the {n} states?\n{mapping}"

        return {
            'verification_question': question,
            'verification_expected': expected,
            'verification_keywords': all_keywords,
            'verification_pieces': all_pieces
        }

    @staticmethod
    def check_verification_answer(response: str, case: Dict) -> bool:
        """
        Check if the model's verification response is correct

        Args:
            response: Model's response to verification question
            case: Test case dictionary with verification info

        Returns:
            True if verification passed, False otherwise
        """
        response_lower = response.lower().strip()
        response_clean = response_lower.replace(".", "").replace(
            ",", "").replace("!", "").replace("?", "").replace("'", "")

        keywords = case.get('verification_keywords', [])

        # All keywords must appear in response
        for keyword in keywords:
            keyword_lower = str(keyword).lower()
            if keyword_lower not in response_clean:
                return False

        # Enhanced: Check color-piece-position associations
        verification_pieces = case.get('verification_pieces', [])
        for piece_info in verification_pieces:
            expected_color = piece_info.get('color', '').lower()
            expected_type = piece_info.get('type', '').lower()
            expected_position = piece_info.get('position', '').lower()

            if not XiangqiMultiStateVerificationGenerator._check_color_piece_association(
                response_clean, expected_color, expected_type, expected_position
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
        import re

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
