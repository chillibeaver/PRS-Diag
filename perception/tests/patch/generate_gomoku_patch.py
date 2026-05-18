"""
Gomoku Patch Alignment Test Generator.
Generates images and test data for VLM patch alignment perception testing.

Supports multiple patch configurations for different model families:
- patch16: Qwen3-VL (qwen8b/30b/235b), GPT (gpt)  → 1024×1024
- patch14_1008: GLM-4.1V (glm)                    → 1008×1008  
- patch14_896: Gemma 3 (gemma)                    → 896×896
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
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
        # Default to patch16 for unknown models
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
            "description": f"Intersection at patch boundary (offset=0)",
        },
        "quarter": {
            "offset": quarter,
            "description": f"Intersection at 1/4 patch (offset={quarter}px)",
        },
        "center": {
            "offset": half,
            "description": f"Intersection at patch center (offset={half}px)",
        },
        "three_quarter": {
            "offset": three_quarter,
            "description": f"Intersection at 3/4 patch (offset={three_quarter}px)",
        },
    }


class GomokuPatchDiagnosticTest:
    """
    Gomoku board patch alignment diagnostic test generator.

    Design:
    - Tests how VLM perception varies with patch alignment offsets
    - Four alignment conditions: boundary, quarter, center, three_quarter
    - Configurable for different patch sizes (14 or 16) and image sizes
    - Board size: 15×15 intersections
    """

    def __init__(self, output_dir: Path, patch_config: str = "patch16", board_size: int = 15):
        """
        Initialize the generator.

        Args:
            output_dir: Output directory for generated test data
            patch_config: One of "patch16", "patch14_1008", "patch14_896"
            board_size: Board size (default: 15 for standard Gomoku)
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
        self.assets = {
            "black_piece": assets_dir / "black_stone.png",
            "white_piece": assets_dir / "white_stone.png",
        }

        # Colors
        self.colors = {
            "background": (245, 245, 240),
            "board": (220, 179, 92),
            "line": (0, 0, 0),
            "coordinate": (50, 50, 50),
        }

        # Star points for traditional layout
        self.star_points = [
            (3, 3), (3, 7), (3, 11),
            (7, 3), (7, 7), (7, 11),
            (11, 3), (11, 7), (11, 11),
        ]

        self._load_assets()

        # Create output directories
        for condition in self.alignment_conditions.keys():
            (self.output_dir / "images" / condition).mkdir(parents=True, exist_ok=True)

    def _calculate_board_params(self):
        """
        Calculate board layout parameters to ensure proper patch alignment.

        Key insight: To ensure ALL intersections have the same patch-relative offset,
        cell_size must be a multiple of patch_size.

        cell_size = k × patch_size, where k is an integer
        """
        target_board_ratio = 0.85
        target_span = self.image_size * target_board_ratio

        num_cells = self.board_size - 1  # 14 cells
        target_cell = target_span / num_cells

        k = round(target_cell / self.patch_size)
        k = max(k, 1)

        self.cell_size = k * self.patch_size

        # Board spans (board_size - 1) cells = 14 cells for 15×15 board
        self.board_pixel_span = (self.board_size - 1) * self.cell_size

        # Calculate available margin
        total_margin = self.image_size - self.board_pixel_span

        # Base position (will be adjusted by offset for each condition)
        self.base_position = total_margin // 2

        # Verify the math
        print(f"\n[Board Layout Parameters]")
        print(f"  Patch config: {self.patch_config_name}")
        print(f"  Patch size: {self.patch_size}×{self.patch_size}")
        print(f"  Image size: {self.image_size}×{self.image_size}")
        print(
            f"  Cell size: {self.cell_size}px (= {self.cell_size // self.patch_size} patches)")
        print(f"  Board span: {self.board_pixel_span}px")
        print(f"  Total margin: {total_margin}px")
        print(f"  Base position: {self.base_position}px")

    def _load_assets(self):
        """Load PNG assets."""
        print("\nLoading PNG assets...")

        try:
            self.black_piece = Image.open(
                self.assets["black_piece"]).convert("RGBA")
            print(f"  [OK] Black piece: {self.black_piece.size}")
        except FileNotFoundError:
            print(f"  [MISSING] Black piece at {self.assets['black_piece']}")
            self.black_piece = None

        try:
            self.white_piece = Image.open(
                self.assets["white_piece"]).convert("RGBA")
            print(f"  [OK] White piece: {self.white_piece.size}")
        except FileNotFoundError:
            print(f"  [MISSING] White piece at {self.assets['white_piece']}")
            self.white_piece = None

        missing = []
        if self.black_piece is None:
            missing.append("black_piece")
        if self.white_piece is None:
            missing.append("white_piece")
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

    def generate_board_state(self, density: str = "medium") -> np.ndarray:
        """Generate random board state with controlled density."""
        board = np.zeros((self.board_size, self.board_size), dtype=int)

        density_ranges = {
            "low": (10, 20),
            "medium": (25, 40),
            "high": (45, 60),
        }
        min_pieces, max_pieces = density_ranges.get(density, (25, 40))
        num_pieces = random.randint(min_pieces, max_pieces)

        all_positions = [(i, j) for i in range(self.board_size)
                         for j in range(self.board_size)]
        selected = random.sample(all_positions, num_pieces)

        for idx, (row, col) in enumerate(selected):
            board[row, col] = 1 if idx % 2 == 0 else 2

        return board

    def get_board_start_position(self, condition: str) -> int:
        """
        Calculate board start position for given alignment condition.

        The key formula:
            intersection_position = board_start + i * cell_size
            offset_in_patch = intersection_position % patch_size

        To achieve desired offset:
            board_start % patch_size = desired_offset
        """
        desired_offset = self.alignment_conditions[condition]["offset"]

        # Find board_start near base_position that gives desired offset
        current_offset = self.base_position % self.patch_size
        adjustment = (desired_offset - current_offset) % self.patch_size

        board_start = self.base_position + adjustment

        return board_start

    def render_board(self, board: np.ndarray, condition: str) -> Image.Image:
        """Render Gomoku board with controlled offset for patch alignment testing."""
        board_start = self.get_board_start_position(condition)

        # Create canvas
        img = Image.new("RGB", (self.image_size, self.image_size),
                        self.colors["background"])
        draw = ImageDraw.Draw(img)

        # Draw board background with margin
        board_margin = 15
        draw.rectangle(
            [board_start - board_margin, board_start - board_margin,
             board_start + self.board_pixel_span + board_margin,
             board_start + self.board_pixel_span + board_margin],
            fill=self.colors["board"],
        )

        # Draw grid lines
        for i in range(self.board_size):
            x = board_start + i * self.cell_size
            y = board_start + i * self.cell_size

            draw.line([(board_start, y), (board_start + self.board_pixel_span, y)],
                      fill=self.colors["line"], width=1)
            draw.line([(x, board_start), (x, board_start + self.board_pixel_span)],
                      fill=self.colors["line"], width=1)

        # Draw star points
        star_radius = max(3, self.cell_size // 10)
        for row, col in self.star_points:
            x = board_start + col * self.cell_size
            y = board_start + row * self.cell_size
            draw.ellipse([x - star_radius, y - star_radius, x + star_radius, y + star_radius],
                         fill=self.colors["line"])

        # Draw coordinates
        available_margin = board_start - board_margin
        font_size = max(14, min(24, int(available_margin * 0.5)))
        font = self._load_font(font_size)
        label_offset = max(20, int(available_margin * 0.6))

        for i in range(self.board_size):
            # Row labels (left side)
            row_label = str(self.board_size - i)
            y_pos = board_start + i * self.cell_size
            draw.text((board_start - label_offset, y_pos), row_label,
                      fill=(80, 50, 30), font=font, anchor="rm")

            # Column labels (top side)
            col_label = chr(ord("A") + i) if i < 8 else chr(ord("A") + i + 1)
            x_pos = board_start + i * self.cell_size
            draw.text((x_pos, board_start - label_offset), col_label,
                      fill=(80, 50, 30), font=font, anchor="mb")

        # Convert to RGBA for piece compositing
        img = img.convert("RGBA")

        # Draw pieces
        piece_radius = int(self.cell_size * 0.4)
        piece_size = piece_radius * 2

        for row in range(self.board_size):
            for col in range(self.board_size):
                if board[row, col] != 0:
                    cx = board_start + col * self.cell_size
                    cy = board_start + row * self.cell_size

                    piece_asset = self.black_piece if board[row,
                                                            col] == 1 else self.white_piece

                    if piece_asset is not None:
                        piece_resized = piece_asset.resize(
                            (piece_size, piece_size), Image.Resampling.LANCZOS)
                        paste_x = cx - piece_radius
                        paste_y = cy - piece_radius
                        img.paste(piece_resized,
                                  (paste_x, paste_y), piece_resized)

        return img.convert("RGB")

    def verify_alignment(self, condition: str):
        """Verify that intersections have correct patch alignment."""
        board_start = self.get_board_start_position(condition)
        expected_offset = self.alignment_conditions[condition]["offset"]

        print(f"\n[Alignment Verification: {condition}]")
        print(f"  Board start: {board_start}px")
        print(f"  Expected offset: {expected_offset}px")

        test_points = [(0, 0, "Top-left"), (7, 7, "Center"),
                       (14, 14, "Bottom-right")]
        all_correct = True

        for row, col, label in test_points:
            x = board_start + col * self.cell_size
            y = board_start + row * self.cell_size
            actual_offset_x = x % self.patch_size
            actual_offset_y = y % self.patch_size

            status = "✓" if actual_offset_x == expected_offset else "✗"
            if actual_offset_x != expected_offset:
                all_correct = False

            print(f"  {status} {label} ({row},{col}): pixel=({x},{y}), "
                  f"offset=({actual_offset_x},{actual_offset_y})")

        return all_correct

    def generate_patch_test_suite(self, n_samples_per_condition: int = 10):
        """Generate complete patch alignment diagnostic test suite."""
        print("=" * 70)
        print("GOMOKU PATCH ALIGNMENT DIAGNOSTIC TEST GENERATOR")
        print("=" * 70)
        print(f"Patch config: {self.patch_config_name}")
        print(f"Patch size: {self.patch_size}×{self.patch_size}")
        print(f"Image size: {self.image_size}×{self.image_size}")
        print(f"Board size: {self.board_size}×{self.board_size}")
        print(f"Cell size: {self.cell_size}px")
        print(f"Samples per condition: {n_samples_per_condition}")

        # Verify alignment for all conditions
        print("\n" + "=" * 70)
        print("ALIGNMENT VERIFICATION")
        print("=" * 70)
        for condition in self.alignment_conditions.keys():
            self.verify_alignment(condition)

        test_data = {
            "metadata": {
                "game": "gomoku",
                "patch_config": self.patch_config_name,
                "patch_size": self.patch_size,
                "image_size": self.image_size,
                "board_size": self.board_size,
                "cell_size": self.cell_size,
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
            print(f"  Offset: {config['offset']}px")
            print(f"  {config['description']}")
            print(f"{'='*70}")

            piece_counts = []
            board_start = self.get_board_start_position(condition)

            for idx, board in enumerate(board_states):
                img = self.render_board(board, condition)

                filename = f"gomoku_{condition}_{idx:03d}.png"
                filepath = self.output_dir / "images" / condition / filename
                img.save(filepath)

                total_pieces = int(np.sum(board > 0))
                piece_counts.append(total_pieces)

                test_case = {
                    "test_id": f"{condition}_{idx:03d}",
                    "alignment_condition": condition,
                    "offset_px": config["offset"],
                    "board_start_px": board_start,
                    "sample_index": idx,
                    "image_file": str(filepath),
                    "ground_truth": board.tolist(),
                    "statistics": {
                        "total_pieces": total_pieces,
                        "black_count": int(np.sum(board == 1)),
                        "white_count": int(np.sum(board == 2)),
                        "density": float(total_pieces / (self.board_size ** 2)),
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
    print("GOMOKU PATCH ALIGNMENT DIAGNOSTIC TEST GENERATOR")
    print("=" * 70)

    # Test all configurations
    for patch_config in PATCH_CONFIGS.keys():
        print(f"\n\n{'#'*70}")
        print(f"# Testing: {patch_config}")
        print(f"{'#'*70}")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(__file__).parent.parent.parent / \
            f"standalone-gomoku-{patch_config}-{timestamp}"

        generator = GomokuPatchDiagnosticTest(
            output_dir=output_dir, patch_config=patch_config)
        test_data = generator.generate_patch_test_suite(
            n_samples_per_condition=3)

    print("\n" + "=" * 70)
    print("SUCCESS")
    print("=" * 70)
