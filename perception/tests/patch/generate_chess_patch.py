"""
Chess Patch Alignment Test Generator.
Generates images and test data for VLM patch alignment perception testing.

Supports multiple patch configurations for different model families:
- patch16: Qwen3-VL (qwen8b/30b/235b), GPT (gpt)  → 1024×1024
- patch14_1008: GLM-4.1V (glm)                    → 1008×1008  
- patch14_896: Gemma 3 (gemma)                    → 896×896
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
import chess
from pathlib import Path
from typing import Dict, List, Tuple


# ============================================================================
# Patch Configurations for Different Model Families
# ============================================================================

PATCH_CONFIGS = {
    "patch16": {
        "patch_size": 16,
        "image_size": 1024,  # 1024 = 64 × 16
        "description": "For Qwen3-VL and GPT-5.2 (patch_size=16, native resolution)",
    },
    "patch14_1008": {
        "patch_size": 14,
        "image_size": 1008,  # 1008 = 72 × 14
        "description": "For GLM-4.1V (patch_size=14, native resolution)",
    },
    "patch14_896": {
        "patch_size": 14,
        "image_size": 896,   # 896 = 64 × 14
        "description": "For Gemma 3 (patch_size=14, fixed resize to 896×896)",
    },
}

# Model key → Patch config mapping (based on model_configs.py)
MODEL_TO_PATCH_CONFIG = {
    # Qwen3-VL family (patch_size=16)
    "qwen8b": "patch16",
    "qwen30b": "patch16",
    "qwen235b": "patch16",
    # GPT (assumed patch_size=16)
    "gpt": "patch16",
    # GLM-4.1V (patch_size=14, native resolution)
    "glm": "patch14_1008",
    # Gemma 3 (patch_size=14, fixed 896×896)
    "gemma": "patch14_896",
    # Dummy for testing
    "dummy": "patch16",
}


def get_patch_config_for_model(model_key: str) -> str:
    """Get the appropriate patch config for a given model key."""
    if model_key in MODEL_TO_PATCH_CONFIG:
        return MODEL_TO_PATCH_CONFIG[model_key]
    else:
        print(f"[WARN] Unknown model '{model_key}', defaulting to patch16")
        return "patch16"


def get_alignment_conditions(patch_size: int) -> Dict:
    """Generate alignment conditions based on patch size."""
    half = patch_size // 2
    quarter = patch_size // 4
    three_quarter = patch_size * 3 // 4

    return {
        "boundary": {
            "offset": 0,
            "description": f"Piece center at patch boundary (offset=0)",
        },
        "quarter": {
            "offset": quarter,
            "description": f"Piece center at 1/4 patch (offset={quarter}px)",
        },
        "center": {
            "offset": half,
            "description": f"Piece center at patch center (offset={half}px)",
        },
        "three_quarter": {
            "offset": three_quarter,
            "description": f"Piece center at 3/4 patch (offset={three_quarter}px)",
        },
    }


class ChessPatchDiagnosticTest:
    """
    Chess board patch alignment diagnostic test generator.

    Design:
    - Tests how VLM perception varies with patch alignment offsets
    - Four alignment conditions: boundary, quarter, center, three_quarter
    - Configurable for different patch sizes (14 or 16) and image sizes
    - Board size: 8×8 squares

    IMPORTANT: For chess, we align PIECE CENTERS (not square corners) to patch offsets,
    since VLM perceives piece positions, not grid corners.
    """

    PIECE_ENCODING = {
        "P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6,
        "p": -1, "n": -2, "b": -3, "r": -4, "q": -5, "k": -6,
        ".": 0,
    }

    def __init__(self, output_dir: Path, patch_config: str = "patch16", board_size: int = 8):
        """
        Initialize the generator.

        Args:
            output_dir: Output directory for generated test data
            patch_config: One of "patch16", "patch14_1008", "patch14_896"
            board_size: Board size (default: 8 for standard chess)
        """
        if patch_config not in PATCH_CONFIGS:
            raise ValueError(
                f"Unknown patch_config: {patch_config}. Available: {list(PATCH_CONFIGS.keys())}")

        self.output_dir = Path(output_dir)
        self.board_size = board_size

        # Load patch configuration
        config = PATCH_CONFIGS[patch_config]
        self.patch_config_name = patch_config
        self.patch_size = config["patch_size"]
        self.image_size = config["image_size"]

        # Generate alignment conditions for this patch size
        self.alignment_conditions = get_alignment_conditions(self.patch_size)

        # Calculate board layout parameters
        self._calculate_board_params()

        # Asset paths
        script_dir = Path(__file__).parent
        assets_dir = script_dir.parent.parent / "assets"
        self.assets_dir = assets_dir

        # Colors
        self.colors = {
            "background": (245, 242, 238),
            "light_square": (240, 217, 181),
            "dark_square": (181, 136, 99),
            "coordinate": (60, 40, 20),
        }

        # Density configurations for varied board states
        self.density_levels = {
            "low": {"range": (8, 12), "description": "8-12 pieces (endgame)"},
            "medium": {"range": (16, 20), "description": "16-20 pieces (midgame)"},
            "high": {"range": (28, 32), "description": "28-32 pieces (opening)"},
        }

        self._load_assets()

        # Create output directories
        for condition in self.alignment_conditions.keys():
            (self.output_dir / "images" / condition).mkdir(parents=True, exist_ok=True)

    def _calculate_board_params(self):
        """
        Calculate board layout parameters to ensure proper patch alignment.

        Key insight: To ensure ALL square centers have the same patch-relative offset,
        square_size must be a multiple of patch_size.

        square_size = k × patch_size, where k is an integer
        """
        target_board_ratio = 0.85
        target_span = self.image_size * target_board_ratio

        target_square = target_span / self.board_size

        k = round(target_square / self.patch_size)
        k = max(k, 1)

        self.square_size = k * self.patch_size
        self.k = k  # Store k for reference

        # Board spans board_size squares = 8 squares for chess
        self.board_pixel_span = self.board_size * self.square_size

        # Calculate available margin
        total_margin = self.image_size - self.board_pixel_span

        # Base position (will be adjusted by offset for each condition)
        self.base_position = total_margin // 2

        # Calculate half_square offset (important for alignment)
        self.half_square = self.square_size // 2
        self.half_square_offset = self.half_square % self.patch_size

        # Verify the math
        print(f"\n[Board Layout Parameters]")
        print(f"  Patch config: {self.patch_config_name}")
        print(f"  Patch size: {self.patch_size}×{self.patch_size}")
        print(f"  Image size: {self.image_size}×{self.image_size}")
        print(f"  Square size: {self.square_size}px (= {k} patches)")
        print(f"  Board span: {self.board_pixel_span}px")
        print(f"  Total margin: {total_margin}px")
        print(f"  Base position: {self.base_position}px")
        print(f"  Half square: {self.half_square}px")
        print(f"  Half square offset: {self.half_square_offset}px")
        if k % 2 != 0:
            print(
                f"  [NOTE] k={k} is odd, piece center alignment adjustment active")

    def _load_assets(self):
        """Load chess piece PNG assets."""
        print("\nLoading chess piece assets...")

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

    def _count_pieces(self, board: chess.Board) -> int:
        """Count total pieces on board."""
        return len(board.piece_map())

    def generate_board_state(self, density: str = "medium", max_attempts: int = 200) -> chess.Board:
        """Generate chess position with target density using simulated gameplay."""
        min_p, max_p = self.density_levels[density]["range"]
        target_piece_count = random.randint(min_p, max_p)

        for attempt in range(max_attempts):
            board = chess.Board()

            if density == "high":
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

        raise RuntimeError(
            f"Failed to generate board with {min_p}-{max_p} pieces after {max_attempts} attempts")

    def get_board_start_position(self, condition: str) -> int:
        """
        Calculate board start position so that PIECE CENTERS align to desired patch offset.

        For chess, pieces are placed at square centers, not corners.

        piece_center = board_start + col * square_size + square_size/2

        We want: piece_center % patch_size = desired_offset

        Since square_size = k * patch_size:
            piece_center % patch_size = (board_start + square_size/2) % patch_size

        So we need: (board_start + half_square) % patch_size = desired_offset
        Therefore:  board_start % patch_size = (desired_offset - half_square) % patch_size
        """
        desired_offset = self.alignment_conditions[condition]["offset"]

        # Calculate what board_start offset we need for piece centers to align
        target_board_start_offset = (
            desired_offset - self.half_square) % self.patch_size

        # Find board_start near base_position that gives target offset
        current_offset = self.base_position % self.patch_size
        adjustment = (target_board_start_offset -
                      current_offset) % self.patch_size

        board_start = self.base_position + adjustment

        return board_start

    def render_board(self, board: chess.Board, condition: str) -> Image.Image:
        """Render chess board with controlled offset for patch alignment testing."""
        board_start = self.get_board_start_position(condition)

        # Create canvas
        img = Image.new("RGB", (self.image_size, self.image_size),
                        self.colors["background"])
        draw = ImageDraw.Draw(img)

        # Draw chess board squares
        for row in range(self.board_size):
            for col in range(self.board_size):
                x = board_start + col * self.square_size
                y = board_start + row * self.square_size
                color = self.colors["light_square"] if (
                    row + col) % 2 == 0 else self.colors["dark_square"]
                draw.rectangle([x, y, x + self.square_size,
                               y + self.square_size], fill=color)

        # Draw coordinates
        available_margin = board_start
        font_size = max(14, min(24, int(available_margin * 0.4)))
        font = self._load_font(font_size)
        label_padding = max(10, int(available_margin * 0.3))

        for i in range(self.board_size):
            # File labels (a-h) at bottom
            file_label = chr(ord("a") + i)
            x_center = board_start + i * self.square_size + self.square_size / 2
            draw.text((x_center, board_start + self.board_pixel_span + label_padding),
                      file_label, fill=self.colors["coordinate"], font=font, anchor="mt")

            # Rank labels (8-1) on left
            rank_label = str(self.board_size - i)
            y_center = board_start + i * self.square_size + self.square_size / 2
            draw.text((board_start - label_padding, y_center),
                      rank_label, fill=self.colors["coordinate"], font=font, anchor="rm")

        # Convert to RGBA for piece compositing
        img = img.convert("RGBA")

        # Draw pieces
        piece_size = int(self.square_size * 0.85)
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
                x = board_start + col * self.square_size + \
                    (self.square_size - piece_size) // 2
                y = board_start + row * self.square_size + \
                    (self.square_size - piece_size) // 2
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

    def verify_alignment(self, condition: str):
        """Verify that PIECE CENTERS have correct patch alignment."""
        board_start = self.get_board_start_position(condition)
        expected_offset = self.alignment_conditions[condition]["offset"]

        print(f"\n[Alignment Verification: {condition}]")
        print(f"  Board start: {board_start}px")
        print(f"  Expected piece center offset: {expected_offset}px")

        test_points = [(0, 0, "a8"), (3, 3, "d5"), (7, 7, "h1")]
        all_correct = True

        for row, col, label in test_points:
            # PIECE CENTER position (not square corner!)
            x = board_start + col * self.square_size + self.half_square
            y = board_start + row * self.square_size + self.half_square
            actual_offset_x = x % self.patch_size
            actual_offset_y = y % self.patch_size

            status = "✓" if actual_offset_x == expected_offset else "✗"
            if actual_offset_x != expected_offset:
                all_correct = False

            print(f"  {status} {label} ({row},{col}): piece_center=({x},{y}), "
                  f"offset=({actual_offset_x},{actual_offset_y})")

        return all_correct

    def generate_patch_test_suite(self, n_samples_per_condition: int = 10):
        """Generate complete patch alignment diagnostic test suite."""
        print("=" * 70)
        print("CHESS PATCH ALIGNMENT DIAGNOSTIC TEST GENERATOR")
        print("=" * 70)
        print(f"Patch config: {self.patch_config_name}")
        print(f"Patch size: {self.patch_size}×{self.patch_size}")
        print(f"Image size: {self.image_size}×{self.image_size}")
        print(f"Board size: {self.board_size}×{self.board_size}")
        print(f"Square size: {self.square_size}px (k={self.k})")
        print(f"Samples per condition: {n_samples_per_condition}")

        # Verify alignment for all conditions
        print("\n" + "=" * 70)
        print("ALIGNMENT VERIFICATION (PIECE CENTERS)")
        print("=" * 70)
        for condition in self.alignment_conditions.keys():
            self.verify_alignment(condition)

        test_data = {
            "metadata": {
                "game": "chess",
                "patch_config": self.patch_config_name,
                "patch_size": self.patch_size,
                "image_size": self.image_size,
                "board_size": self.board_size,
                "square_size": self.square_size,
                "k": self.k,
                "alignment_target": "piece_center",  # Document what we're aligning
                "samples_per_condition": n_samples_per_condition,
                "total_samples": n_samples_per_condition * len(self.alignment_conditions),
            },
            "condition_stats": {},
            "test_cases": [],
        }

        # Generate board states (same for all conditions)
        print("\n" + "=" * 70)
        print("GENERATING BOARD STATES")
        print("=" * 70)
        board_states = []
        for i in range(n_samples_per_condition):
            if i < n_samples_per_condition // 3:
                board = self.generate_board_state("low")
            elif i < 2 * n_samples_per_condition // 3:
                board = self.generate_board_state("medium")
            else:
                board = self.generate_board_state("high")
            board_states.append(board)
        print(f"Generated {len(board_states)} board states")

        # Generate images for each condition
        for condition, config in self.alignment_conditions.items():
            print(f"\n{'='*70}")
            print(f"Generating {condition.upper()} condition")
            print(f"  Offset: {config['offset']}px (piece center)")
            print(f"  {config['description']}")
            print(f"{'='*70}")

            piece_counts = []
            board_start = self.get_board_start_position(condition)

            for idx, board in enumerate(board_states):
                img = self.render_board(board, condition)

                filename = f"chess_{condition}_{idx:03d}.png"
                filepath = self.output_dir / "images" / condition / filename
                img.save(filepath)

                piece_map = board.piece_map()
                total_pieces = len(piece_map)
                piece_counts.append(total_pieces)

                white_pieces = sum(1 for p in piece_map.values()
                                   if p.color == chess.WHITE)
                black_pieces = sum(1 for p in piece_map.values()
                                   if p.color == chess.BLACK)

                test_case = {
                    "test_id": f"{condition}_{idx:03d}",
                    "alignment_condition": condition,
                    "offset_px": config["offset"],
                    "board_start_px": board_start,
                    "sample_index": idx,
                    "image_file": str(filepath),
                    "ground_truth": self.board_to_matrix(board),
                    "statistics": {
                        "total_pieces": total_pieces,
                        "white_pieces": white_pieces,
                        "black_pieces": black_pieces,
                        "density": float(total_pieces / 32),
                    },
                }
                test_data["test_cases"].append(test_case)

                if (idx + 1) % 10 == 0:
                    print(f"  Generated {idx+1}/{n_samples_per_condition}...")

            test_data["condition_stats"][condition] = {
                "offset_px": config["offset"],
                "board_start_px": board_start,
                "description": config["description"],
                "n_samples": len(board_states),
                "avg_pieces": float(np.mean(piece_counts)),
                "piece_range": [int(min(piece_counts)), int(max(piece_counts))],
            }

            print(f"  [OK] Completed {condition}")

        print(f"\n{'='*70}")
        print(f"[SUCCESS] Generated {len(test_data['test_cases'])} test cases")
        print(f"{'='*70}")

        return test_data


if __name__ == "__main__":
    from datetime import datetime

    print("\n" + "=" * 70)
    print("CHESS PATCH ALIGNMENT DIAGNOSTIC TEST GENERATOR")
    print("=" * 70)

    # Test all configurations
    for patch_config in PATCH_CONFIGS.keys():
        print(f"\n\n{'#'*70}")
        print(f"# Testing: {patch_config}")
        print(f"{'#'*70}")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(__file__).parent.parent.parent / \
            f"standalone-chess-{patch_config}-{timestamp}"

        generator = ChessPatchDiagnosticTest(
            output_dir=output_dir, patch_config=patch_config)
        test_data = generator.generate_patch_test_suite(
            n_samples_per_condition=3)

    print("\n" + "=" * 70)
    print("SUCCESS")
    print("=" * 70)
