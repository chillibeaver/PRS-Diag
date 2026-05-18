"""
Chess Random Density Test Generator.
Generates chess boards with randomly placed pieces (not simulated gameplay).
Piece counts respect standard chess rules (e.g., max 1 king per side).
"""
import random
from pathlib import Path

import chess

from tests.density.generate_chess_density import ChessDensityDiagnosticTest


class ChessRandomDensityDiagnosticTest(ChessDensityDiagnosticTest):
    """
    Random-placement chess density test generator.

    Inherits rendering and test suite logic from ChessDensityDiagnosticTest.
    Only overrides board generation to use random placement instead of
    simulated gameplay, while keeping piece counts legal:
    - Exactly 1 King per side
    - Max 1 Queen, 2 Rooks, 2 Bishops, 2 Knights per side
    - Max 8 Pawns per side, not on rank 1 or 8
    """

    # Non-king pieces available per side (max legal counts)
    _SIDE_POOL = (
        [chess.QUEEN] * 1 +
        [chess.ROOK] * 2 +
        [chess.BISHOP] * 2 +
        [chess.KNIGHT] * 2 +
        [chess.PAWN] * 8
    )  # 15 pieces per side

    def generate_board_state(self, density_level: str, max_attempts: int = 200) -> chess.Board:
        """Generate a random chess position with legal piece counts."""
        min_p, max_p = self.density_levels[density_level]["range"]
        target = random.randint(min_p, max_p)

        # Build piece pool: both kings + random selection from combined pool
        combined_pool = (
            [(pt, chess.WHITE) for pt in self._SIDE_POOL] +
            [(pt, chess.BLACK) for pt in self._SIDE_POOL]
        )  # 30 pieces total
        random.shuffle(combined_pool)
        extra_pieces = combined_pool[:target - 2]

        # All pieces to place
        pieces_to_place = [
            (chess.KING, chess.WHITE),
            (chess.KING, chess.BLACK),
        ] + extra_pieces

        # Separate squares: pawns can only go on ranks 2-7 (indices 8-55)
        all_squares = list(range(64))
        pawn_squares = [s for s in all_squares if 8 <= s <= 55]

        random.shuffle(all_squares)
        random.shuffle(pawn_squares)

        board = chess.Board(fen=None)  # empty board

        used = set()
        all_iter = iter(all_squares)
        pawn_iter = iter(pawn_squares)

        for piece_type, color in pieces_to_place:
            if piece_type == chess.PAWN:
                sq = next(s for s in pawn_iter if s not in used)
            else:
                sq = next(s for s in all_iter if s not in used)
            used.add(sq)
            board.set_piece_at(sq, chess.Piece(piece_type, color))

        return board

    def generate_density_test_suite(self, n_samples_per_density=30):
        """Generate test suite with random placement metadata."""
        test_data = super().generate_density_test_suite(n_samples_per_density)
        test_data["metadata"]["generation_method"] = "random_placement"
        return test_data


if __name__ == "__main__":
    from datetime import datetime

    print("\n" + "=" * 70)
    print("CHESS RANDOM DENSITY DIAGNOSTIC TEST GENERATOR")
    print("=" * 70)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(__file__).parent.parent.parent / \
        f"standalone-chess-random-density-{timestamp}"

    generator = ChessRandomDensityDiagnosticTest(output_dir=output_dir)
    metadata = generator.generate_density_test_suite(n_samples_per_density=30)

    print("\n" + "=" * 70)
    print("SUCCESS")
    print("=" * 70)
