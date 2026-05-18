"""
Chess Resolution Test Generator.
Generates images at varying resolutions to test VLM preprocessing artifacts.

Tests divisible vs non-divisible resolutions relative to model's patch_size.
Supports different patch configurations for different model families.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
import chess
from pathlib import Path
from typing import Dict, List


# ============================================================================
# Resolution Configurations by Patch Size
# ============================================================================

RESOLUTION_CONFIGS_BY_PATCH = {
    16: {
        "divisible": {
            # 1024=64×16, 512=32×16, 384=24×16
            "resolutions": [1024, 512, 384],
            "description": "Image sizes divisible by patch_size (16)",
        },
        "non_divisible": {
            "resolutions": [1010, 510, 370],
            "description": "Image sizes NOT divisible by 16 (require padding)",
        },
    },
    14: {
        "divisible": {
            # 1008=72×14, 896=64×14, 392=28×14
            "resolutions": [1008, 896, 392],
            "description": "Image sizes divisible by patch_size (14)",
        },
        "non_divisible": {
            "resolutions": [1010, 900, 400],
            "description": "Image sizes NOT divisible by 14 (require padding)",
        },
    },
}

# Model key → Patch size mapping
MODEL_TO_PATCH_SIZE = {
    "qwen8b": 16,
    "qwen30b": 16,
    "qwen235b": 16,
    "gpt": 16,
    "glm": 14,
    "gemma": 14,
    "dummy": 16,
}


def get_patch_size_for_model(model_key: str) -> int:
    """Get the patch size for a given model key."""
    if model_key in MODEL_TO_PATCH_SIZE:
        return MODEL_TO_PATCH_SIZE[model_key]
    else:
        print(
            f"[WARN] Unknown model '{model_key}', defaulting to patch_size=16")
        return 16


def get_resolution_configs(patch_size: int) -> Dict:
    """Get resolution configurations for a given patch size."""
    if patch_size not in RESOLUTION_CONFIGS_BY_PATCH:
        raise ValueError(
            f"Unsupported patch_size: {patch_size}. Available: {list(RESOLUTION_CONFIGS_BY_PATCH.keys())}")
    return RESOLUTION_CONFIGS_BY_PATCH[patch_size]


class ChessResolutionDiagnosticTest:
    """
    Chess board resolution diagnostic test generator.

    Design:
    - Tests how VLM perception varies with image resolution
    - Compares divisible vs non-divisible resolutions (relative to model's patch_size)
    - Uses medium density boards to isolate resolution effects
    - Board size: 8×8 squares
    """

    PIECE_ENCODING = {
        "P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6,
        "p": -1, "n": -2, "b": -3, "r": -4, "q": -5, "k": -6,
        ".": 0,
    }

    def __init__(self, output_dir: Path, patch_size: int = 16):
        self.output_dir = Path(output_dir)
        self.board_size = 8
        self.patch_size = patch_size
        self.board_to_image_ratio = 0.92  # Same as density test

        # Get resolution configs for this patch size
        self.resolution_configs = get_resolution_configs(patch_size)

        # Asset paths
        script_dir = Path(__file__).parent
        self.assets_dir = script_dir.parent.parent / "assets"

        # Density configuration (medium)
        self.density_range = (16, 20)  # 16-20 pieces (midgame)

        self._load_assets()

        # Create output directories
        for group_name, group_info in self.resolution_configs.items():
            for resolution in group_info["resolutions"]:
                (self.output_dir / "images" / group_name / str(resolution)).mkdir(
                    parents=True, exist_ok=True)

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

        missing = [name for code, name in piece_files.items()
                   if self.pieces[code] is None]
        if missing:
            raise FileNotFoundError(f"Missing required assets: {missing}")
        print()

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load font with cross-platform fallback."""
        font_paths = [
            "arial.ttf", "Arial.ttf", "DejaVuSans.ttf",
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

    def _calculate_dimensions(self, image_size: int) -> Dict:
        """Calculate board dimensions for a given image size."""
        board_size_px = int(image_size * self.board_to_image_ratio)
        board_border = (image_size - board_size_px) // 2
        grid_margin = int(board_size_px * 0.02)
        grid_size_px = board_size_px - 2 * grid_margin
        square_size = grid_size_px / self.board_size
        grid_border = board_border + grid_margin

        # Calculate token grid info
        is_divisible = (image_size % self.patch_size) == 0
        if is_divisible:
            padded_to = image_size
        else:
            padded_to = ((image_size + self.patch_size - 1) //
                         self.patch_size) * self.patch_size
        token_grid = padded_to // self.patch_size

        return {
            "image_size": image_size,
            "board_size_px": board_size_px,
            "board_border": board_border,
            "grid_border": grid_border,
            "square_size": square_size,
            "is_divisible": is_divisible,
            "padded_to": padded_to,
            "token_grid": f"{token_grid}x{token_grid}",
        }

    def _count_pieces(self, board: chess.Board) -> int:
        """Count total pieces on board."""
        return len(board.piece_map())

    def generate_board_state(self, max_attempts: int = 200) -> chess.Board:
        """Generate chess position with medium density using simulated gameplay."""
        min_p, max_p = self.density_range
        target_piece_count = random.randint(min_p, max_p)

        for attempt in range(max_attempts):
            board = chess.Board()

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

        raise RuntimeError(
            f"Failed to generate board with {min_p}-{max_p} pieces")

    def render_board(self, board: chess.Board, dimensions: Dict) -> Image.Image:
        """Render chess board at specified resolution with labels outside."""
        img_size = dimensions["image_size"]
        grid_border = dimensions["grid_border"]
        square_size = dimensions["square_size"]

        # Create canvas
        img = Image.new("RGB", (img_size, img_size), (245, 242, 238))
        draw = ImageDraw.Draw(img)

        # Draw squares
        light_square = (240, 217, 181)
        dark_square = (181, 136, 99)

        for row in range(8):
            for col in range(8):
                x = grid_border + col * square_size
                y = grid_border + row * square_size
                color = light_square if (row + col) % 2 == 0 else dark_square
                draw.rectangle(
                    [x, y, x + square_size, y + square_size], fill=color)

        # Coordinate labels (outside the board, same as density test)
        font_size = int(square_size * 0.35)
        font = self._load_font(font_size)
        text_color = (60, 40, 20)
        label_padding = square_size * 0.2

        for i in range(8):
            file_label = chr(ord("a") + i)
            rank_label = str(8 - i)
            file_x_center = grid_border + i * square_size + square_size / 2
            rank_y_center = grid_border + i * square_size + square_size / 2

            # File labels (a-h) at bottom
            draw.text((file_x_center, grid_border + 8 * square_size + label_padding),
                      file_label, fill=text_color, font=font, anchor="mm")
            # Rank labels (8-1) on left
            draw.text((grid_border - label_padding, rank_y_center),
                      rank_label, fill=text_color, font=font, anchor="mm")

        # Convert to RGBA for piece compositing
        img = img.convert("RGBA")

        # Draw pieces
        piece_size = int(square_size * 0.90)
        piece_to_asset = {
            "P": "wp", "N": "wn", "B": "wb", "R": "wr", "Q": "wq", "K": "wk",
            "p": "bp", "n": "bn", "b": "bb", "r": "br", "q": "bq", "k": "bk",
        }

        for square, piece in board.piece_map().items():
            row = 7 - (square // 8)
            col = square % 8
            piece_symbol = piece.symbol()
            asset_code = piece_to_asset.get(piece_symbol)

            if asset_code and self.pieces.get(asset_code):
                piece_img = self.pieces[asset_code].resize(
                    (piece_size, piece_size), Image.Resampling.LANCZOS)
                x = grid_border + col * square_size + \
                    (square_size - piece_size) // 2
                y = grid_border + row * square_size + \
                    (square_size - piece_size) // 2
                img.paste(piece_img, (int(x), int(y)), piece_img)

        return img.convert("RGB")

    def board_to_matrix(self, board: chess.Board) -> List[List[int]]:
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

    def generate_resolution_test_suite(self, n_samples_per_resolution: int = 30):
        """Generate complete resolution diagnostic test suite."""
        print("=" * 70)
        print("CHESS RESOLUTION DIAGNOSTIC TEST GENERATOR")
        print("=" * 70)
        print(f"Board size: {self.board_size}x{self.board_size}")
        print(f"Patch size: {self.patch_size}x{self.patch_size}")
        print(
            f"Density: {self.density_range[0]}-{self.density_range[1]} pieces (medium)")
        print(f"Samples per resolution: {n_samples_per_resolution}")
        print()

        test_data = {
            "metadata": {
                "game": "chess",
                "board_size": self.board_size,
                "patch_size": self.patch_size,
                "board_to_image_ratio": self.board_to_image_ratio,
                "density": f"medium ({self.density_range[0]}-{self.density_range[1]} pieces)",
                "samples_per_resolution": n_samples_per_resolution,
                "total_samples": n_samples_per_resolution * sum(
                    len(g["resolutions"]) for g in self.resolution_configs.values()),
            },
            "resolution_stats": {},
            "test_cases": [],
        }

        # Generate board states (same for all resolutions)
        print(f"Generating {n_samples_per_resolution} board states...")
        board_states = [self.generate_board_state()
                        for _ in range(n_samples_per_resolution)]

        piece_counts = [self._count_pieces(b) for b in board_states]
        avg_pieces = np.mean(piece_counts)
        print(f"  Average pieces: {avg_pieces:.1f}")
        print()

        # Generate images for each resolution
        for group_name, group_info in self.resolution_configs.items():
            print(f"\n{'='*70}")
            print(f"Generating {group_name.upper()} group")
            print(f"  {group_info['description']}")
            print(f"{'='*70}")

            for resolution in group_info["resolutions"]:
                print(f"\n  Resolution: {resolution}x{resolution}")
                dimensions = self._calculate_dimensions(resolution)
                print(
                    f"    Divisible by {self.patch_size}: {dimensions['is_divisible']}")
                print(
                    f"    Padded to: {dimensions['padded_to']}x{dimensions['padded_to']}")
                print(f"    Token grid: {dimensions['token_grid']}")

                resolution_piece_counts = []

                for idx, board in enumerate(board_states):
                    img = self.render_board(board, dimensions)
                    matrix = self.board_to_matrix(board)

                    filename = f"chess_{group_name}_{resolution}_{idx:03d}.png"
                    filepath = self.output_dir / "images" / \
                        group_name / str(resolution) / filename
                    img.save(filepath)

                    piece_map = board.piece_map()
                    total_pieces = len(piece_map)
                    resolution_piece_counts.append(total_pieces)

                    white_pieces = sum(
                        1 for p in piece_map.values() if p.color == chess.WHITE)
                    black_pieces = sum(
                        1 for p in piece_map.values() if p.color == chess.BLACK)

                    test_case = {
                        "test_id": f"{group_name}_{resolution}_{idx:03d}",
                        "resolution_group": group_name,
                        "resolution": resolution,
                        "sample_index": idx,
                        "image_file": str(filepath),
                        "ground_truth": matrix,
                        "statistics": {
                            "total_pieces": total_pieces,
                            "white_pieces": white_pieces,
                            "black_pieces": black_pieces,
                            "density": float(total_pieces / 32),
                            "is_divisible": dimensions["is_divisible"],
                            "padded_to": dimensions["padded_to"],
                            "token_grid": dimensions["token_grid"],
                        },
                    }
                    test_data["test_cases"].append(test_case)

                test_data["resolution_stats"][f"{group_name}_{resolution}"] = {
                    "group": group_name,
                    "resolution": resolution,
                    "is_divisible": dimensions["is_divisible"],
                    "padded_to": dimensions["padded_to"],
                    "token_grid": dimensions["token_grid"],
                    "n_samples": len(board_states),
                    "avg_pieces": float(np.mean(resolution_piece_counts)),
                }

                print(f"    [OK] Generated {len(board_states)} images")

        print(f"\n{'='*70}")
        print(f"[SUCCESS] Generated {len(test_data['test_cases'])} test cases")
        print(f"{'='*70}")

        return test_data


if __name__ == "__main__":
    from datetime import datetime

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(__file__).parent.parent.parent / \
        f"standalone-chess-resolution-{timestamp}"

    generator = ChessResolutionDiagnosticTest(output_dir=output_dir)
    test_data = generator.generate_resolution_test_suite(
        n_samples_per_resolution=10)

    print("\n[DONE]")
