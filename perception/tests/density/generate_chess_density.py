"""
Chess Density Test Generator.
Generates images and test data for VLM board perception testing.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
import json
from pathlib import Path
import chess


class ChessDensityDiagnosticTest:
    """
    Chess board density diagnostic test generator.

    Design:
    - Uses python-chess to generate legal board states via simulated gameplay
    - Three density levels: Low (8-12 pieces), Medium (16-20), High (28-32)
    - Board size: 8x8, Resolution: 1024x1024
    """

    PIECE_ENCODING = {
        "P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6,
        "p": -1, "n": -2, "b": -3, "r": -4, "q": -5, "k": -6,
        ".": 0,
    }

    def __init__(self, output_dir: Path, assets_dir: str = "assets"):
        """
        Initialize the generator.

        Args:
            output_dir: Output directory for generated test data
            assets_dir: Directory containing chess piece PNG assets
        """
        self.output_dir = Path(output_dir)

        # Set up assets directory
        script_dir = Path(__file__).parent
        if assets_dir == "assets":
            self.assets_dir = script_dir.parent.parent / "assets"
        else:
            self.assets_dir = Path(assets_dir)

        # Fixed parameters
        self.resolution = 1024
        self.board_size = 8
        self.board_to_image_ratio = 0.92

        # Density configurations
        self.density_levels = {
            "low": {"range": (8, 12), "description": "8-12 pieces (endgame)"},
            "medium": {"range": (16, 20), "description": "16-20 pieces (midgame)"},
            "high": {"range": (28, 32), "description": "28-32 pieces (opening)"},
        }

        self._load_assets()

        # Create output directory and subdirectories for images
        for density_name in self.density_levels.keys():
            (self.output_dir / "images" /
             density_name).mkdir(parents=True, exist_ok=True)

    def _load_assets(self):
        """Load chess piece PNG assets."""
        print("Loading chess piece assets...")

        self.pieces = {}
        piece_files = {
            "bb": "black bishop", "bk": "black king", "bn": "black knight",
            "bp": "black pawn", "bq": "black queen", "br": "black rook",
            "wb": "white bishop", "wk": "white king", "wn": "white knight",
            "wp": "white pawn", "wq": "white queen", "wr": "white rook",
        }

        for code, name in piece_files.items():
            filepath = self.assets_dir / f"{code}.png"
            try:
                self.pieces[code] = Image.open(filepath).convert("RGBA")
                print(f"  [OK] Loaded {name}: {self.pieces[code].size}")
            except FileNotFoundError:
                print(f"  [MISSING] {name} at {filepath}")
                self.pieces[code] = None

        # if any assets are missing, raise error
        missing = [name for code, name in piece_files.items()
                   if self.pieces[code] is None]
        if missing:
            raise FileNotFoundError(
                f"Missing required assets: {missing}. Check: {self.assets_dir}")
        print()

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load font with cross-platform fallback."""
        font_paths = [
            "arial.ttf",
            "Arial.ttf",
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf",
        ]
        for path in font_paths:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def _calculate_dimensions(self):
        """Calculate board dimensions."""
        image_size = self.resolution
        board_size_px = int(image_size * self.board_to_image_ratio)
        board_border = (image_size - board_size_px) // 2
        grid_margin = int(board_size_px * 0.02)
        grid_size_px = board_size_px - 2 * grid_margin
        square_size = grid_size_px / self.board_size
        grid_border = board_border + grid_margin

        return {
            "image_size": image_size,
            "board_size_px": board_size_px,
            "board_border": board_border,
            "grid_border": grid_border,
            "square_size": square_size,
        }

    def _count_pieces(self, board: chess.Board) -> int:
        """Count total pieces on board."""
        return len(board.piece_map())

    def generate_board_state(self, density_level: str, max_attempts: int = 200) -> chess.Board:
        """Generate chess position with target density using simulated gameplay."""
        min_p, max_p = self.density_levels[density_level]["range"]
        target_piece_count = random.randint(min_p, max_p)

        for attempt in range(max_attempts):
            board = chess.Board()

            if density_level == "high":
                moves_to_play = random.randint(3, 8)
                for _ in range(moves_to_play):
                    if board.legal_moves:
                        board.push(random.choice(list(board.legal_moves)))
                if self._count_pieces(board) < min_p:
                    continue
                return board
            else:
                while self._count_pieces(board) > target_piece_count:
                    if not board.legal_moves:
                        break

                    legal_moves = list(board.legal_moves)
                    capturing_moves = [
                        m for m in legal_moves if board.is_capture(m)]
                    current_count = self._count_pieces(board)

                    capture_prob = 0.8 if current_count > target_piece_count + 5 else 0.5

                    if capturing_moves and random.random() < capture_prob:
                        board.push(random.choice(capturing_moves))
                    else:
                        board.push(random.choice(legal_moves))

                    if board.fullmove_number > 250:
                        break

                final_count = self._count_pieces(board)
                if min_p <= final_count <= max_p:
                    return board

        # failed to generate valid board within max_attempts
        raise RuntimeError(
            f"Failed to generate board with {min_p}-{max_p} pieces after {max_attempts} attempts")

    def _draw_chessboard(self, dimensions: dict) -> Image.Image:
        """Draw chessboard background and labels."""
        img_size = dimensions["image_size"]
        grid_border = dimensions["grid_border"]
        square_size = dimensions["square_size"]

        img = Image.new("RGB", (img_size, img_size), (245, 242, 238))
        draw = ImageDraw.Draw(img)

        light_square = (240, 217, 181)
        dark_square = (181, 136, 99)

        for row in range(8):
            for col in range(8):
                x = grid_border + col * square_size
                y = grid_border + row * square_size
                color = light_square if (row + col) % 2 == 0 else dark_square
                draw.rectangle(
                    [x, y, x + square_size, y + square_size], fill=color)

        font_size = int(square_size * 0.35)
        font = self._load_font(font_size)

        text_color = (60, 40, 20)
        label_padding = square_size * 0.2

        for i in range(8):
            file_label = chr(ord("a") + i)
            rank_label = str(8 - i)
            file_x_center = grid_border + i * square_size + square_size / 2
            rank_y_center = grid_border + i * square_size + square_size / 2

            draw.text((file_x_center, grid_border + 8 * square_size + label_padding), file_label,
                      fill=text_color, font=font, anchor="mm")  # bottom
            draw.text((grid_border - label_padding, rank_y_center), rank_label,
                      fill=text_color, font=font, anchor="mm")  # left

        return img

    def render_board(self, board: chess.Board, dimensions: dict) -> Image.Image:
        """Render chess board with pieces."""
        img = self._draw_chessboard(dimensions)
        grid_border = dimensions["grid_border"]
        square_size = dimensions["square_size"]
        piece_size = int(square_size * 0.90)

        piece_to_asset = {
            "P": "wp", "N": "wn", "B": "wb", "R": "wr", "Q": "wq", "K": "wk",
            "p": "bp", "n": "bn", "b": "bb", "r": "br", "q": "bq", "k": "bk",
        }

        img = img.convert("RGBA")

        for square, piece in board.piece_map().items():
            row = 7 - (square // 8)
            col = square % 8
            piece_symbol = piece.symbol()
            asset_code = piece_to_asset.get(piece_symbol)

            if asset_code and self.pieces.get(asset_code):
                piece_img = self.pieces[asset_code].resize(
                    (piece_size, piece_size), Image.Resampling.LANCZOS
                )
                x = grid_border + col * square_size + \
                    (square_size - piece_size) // 2
                y = grid_border + row * square_size + \
                    (square_size - piece_size) // 2
                img.paste(piece_img, (int(x), int(y)), piece_img)

        return img.convert("RGB")

    def board_to_matrix(self, board: chess.Board) -> list:
        """Convert python-chess Board to matrix format."""
        matrix = []
        for rank in range(7, -1, -1):
            row = []
            for file in range(8):
                square = chess.square(file, rank)
                piece = board.piece_at(square)
                row.append(
                    0 if piece is None else self.PIECE_ENCODING[piece.symbol()])
            matrix.append(row)
        return matrix

    def generate_density_test_suite(self, n_samples_per_density: int = 30):
        """
        Generate complete density diagnostic test suite.

        All test cases are saved in a single unified JSON file.
        """
        print("=" * 70)
        print("CHESS DENSITY DIAGNOSTIC TEST GENERATOR")
        print("=" * 70)
        print(f"Board size: {self.board_size}x{self.board_size}")
        print(f"Resolution: {self.resolution}x{self.resolution}px")
        print(f"Samples per density: {n_samples_per_density}")
        print()

        test_data = {
            "metadata": {
                "game": "chess",
                "board_size": self.board_size,
                "resolution": self.resolution,
                "board_to_image_ratio": self.board_to_image_ratio,
                "generation_method": "simulated_gameplay",
                "samples_per_density": n_samples_per_density,
                "total_samples": n_samples_per_density * len(self.density_levels),
            },
            "density_stats": {},
            "test_cases": [],
        }

        dimensions = self._calculate_dimensions()

        for density_name, density_config in self.density_levels.items():
            print(f"\n{'='*70}")
            print(f"Generating {density_name.upper()} density boards")
            print(f"  Target: {density_config['description']}")
            print(f"{'='*70}")

            boards = []
            piece_counts = []

            for i in range(n_samples_per_density):
                board = self.generate_board_state(density_name)
                boards.append(board)
                piece_counts.append(self._count_pieces(board))

                if (i + 1) % 10 == 0:
                    print(f"  Generated {i+1}/{n_samples_per_density}...")

            avg_pieces = np.mean(piece_counts)
            avg_density = avg_pieces / 32

            print(f"  Generated {len(boards)} boards")
            print(
                f"  Actual average: {avg_pieces:.1f} pieces ({avg_density:.1%})")
            print(f"  Range: {min(piece_counts)}-{max(piece_counts)} pieces")

            test_data["density_stats"][density_name] = {
                "target_description": density_config["description"],
                "actual_mean_pieces": float(avg_pieces),
                "actual_mean_density": float(avg_density),
                "piece_count_range": [int(min(piece_counts)), int(max(piece_counts))],
                "n_samples": len(boards),
            }

            print(f"  Rendering images...")
            for idx, board in enumerate(boards):
                img = self.render_board(board, dimensions)
                matrix = self.board_to_matrix(board)

                filename = f"chess_{density_name}_{idx:03d}.png"
                filepath = self.output_dir / "images" / density_name / filename
                img.save(filepath)

                piece_map = board.piece_map()
                white_pieces = sum(1 for p in piece_map.values()
                                   if p.color == chess.WHITE)
                black_pieces = sum(1 for p in piece_map.values()
                                   if p.color == chess.BLACK)

                test_case = {
                    "test_id": f"{density_name}_{idx:03d}",
                    "density_level": density_name,
                    "sample_index": idx,
                    "image_file": str(filepath),
                    "ground_truth": matrix,
                    "statistics": {
                        "total_pieces": len(piece_map),
                        "white_pieces": white_pieces,
                        "black_pieces": black_pieces,
                        "density": len(piece_map) / 32,
                    },
                }
                test_data["test_cases"].append(test_case)

            print(f"  [OK] Completed {density_name}")

        print(f"\n{'='*70}")
        print(f"[SUCCESS] Generated {len(test_data['test_cases'])} test cases")
        print(f"{'='*70}")

        return test_data


if __name__ == "__main__":
    from datetime import datetime

    print("\n" + "=" * 70)
    print("CHESS DENSITY DIAGNOSTIC TEST GENERATOR")
    print("=" * 70)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(__file__).parent.parent.parent / \
        f"standalone-chess-density-{timestamp}"

    generator = ChessDensityDiagnosticTest(output_dir=output_dir)
    metadata = generator.generate_density_test_suite(n_samples_per_density=30)

    print("\n" + "=" * 70)
    print("SUCCESS")
    print("=" * 70)
