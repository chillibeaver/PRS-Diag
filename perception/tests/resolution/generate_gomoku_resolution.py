"""
Gomoku Resolution Test Generator.
Generates images at varying resolutions to test VLM preprocessing artifacts.

Tests divisible vs non-divisible resolutions relative to model's patch_size.
Supports different patch configurations for different model families.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
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

# Model key → Patch config mapping
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


class GomokuResolutionDiagnosticTest:
    """
    Gomoku board resolution diagnostic test generator.

    Design:
    - Tests how VLM perception varies with image resolution
    - Compares divisible vs non-divisible resolutions (relative to model's patch_size)
    - Uses medium density boards to isolate resolution effects
    - Board size: 15×15 intersections
    """

    def __init__(self, output_dir: Path, board_size: int = 15, patch_size: int = 16):
        self.output_dir = Path(output_dir)
        self.board_size = board_size
        self.patch_size = patch_size
        self.board_to_image_ratio = 1

        # Get resolution configs for this patch size
        self.resolution_configs = get_resolution_configs(patch_size)

        # Asset paths
        script_dir = Path(__file__).parent
        assets_dir = script_dir.parent.parent / "assets"
        self.assets = {
            "black_piece": assets_dir / "black_stone.png",
            "white_piece": assets_dir / "white_stone.png",
        }

        # Star points for traditional layout
        self.star_points = [
            (3, 3), (3, 7), (3, 11),
            (7, 3), (7, 7), (7, 11),
            (11, 3), (11, 7), (11, 11),
        ]

        self._load_assets()

        # Create output directories
        for group_name, group_info in self.resolution_configs.items():
            for resolution in group_info["resolutions"]:
                (self.output_dir / "images" / group_name / str(resolution)).mkdir(
                    parents=True, exist_ok=True)

    def _load_assets(self):
        """Load PNG assets."""
        print("Loading PNG assets...")

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
        grid_margin = int(board_size_px * 0.08)
        grid_size_px = board_size_px - 2 * grid_margin
        cell_size = grid_size_px / (self.board_size - 1)
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
            "cell_size": cell_size,
            "is_divisible": is_divisible,
            "padded_to": padded_to,
            "token_grid": f"{token_grid}x{token_grid}",
        }

    def generate_board_state(self) -> np.ndarray:
        """Generate random board state with medium density."""
        board = np.zeros((self.board_size, self.board_size), dtype=int)

        # Medium density: 40-50% occupancy
        min_pieces = int(self.board_size * self.board_size * 0.40)
        max_pieces = int(self.board_size * self.board_size * 0.50)
        num_pieces = random.randint(min_pieces, max_pieces)

        all_positions = [(i, j) for i in range(self.board_size)
                         for j in range(self.board_size)]
        selected = random.sample(all_positions, num_pieces)

        for idx, (row, col) in enumerate(selected):
            board[row, col] = 1 if idx % 2 == 0 else 2

        return board

    def render_board(self, board: np.ndarray, dimensions: Dict) -> Image.Image:
        """Render Gomoku board at specified resolution."""
        img_size = dimensions["image_size"]
        board_size_px = dimensions["board_size_px"]
        board_border = dimensions["board_border"]
        grid_border = dimensions["grid_border"]
        cell_size = dimensions["cell_size"]

        # Create canvas
        img = Image.new("RGB", (img_size, img_size), (245, 242, 238))
        draw = ImageDraw.Draw(img)

        # Board background
        board_color = (220, 179, 92)
        draw.rectangle(
            [(board_border, board_border),
             (board_border + board_size_px, board_border + board_size_px)],
            fill=board_color
        )

        img = img.convert("RGBA")
        draw = ImageDraw.Draw(img)

        # Grid lines
        line_width = max(1, int(cell_size * 0.035))
        line_color = (70, 45, 25, 255)

        for i in range(self.board_size):
            pos = grid_border + i * cell_size
            draw.line([(grid_border, pos), (grid_border + (self.board_size - 1) * cell_size, pos)],
                      fill=line_color, width=line_width)
            draw.line([(pos, grid_border), (pos, grid_border + (self.board_size - 1) * cell_size)],
                      fill=line_color, width=line_width)

        # Star points
        star_radius = max(2, int(cell_size * 0.15))
        for row, col in self.star_points:
            x = grid_border + col * cell_size
            y = grid_border + row * cell_size
            draw.ellipse([x - star_radius, y - star_radius, x + star_radius, y + star_radius],
                         fill=(70, 45, 25, 255))

        # Coordinate labels
        font_size = max(10, int(cell_size * 0.5))
        font = self._load_font(font_size)
        label_offset = max(10, int(cell_size * 0.6))
        edge = grid_border + (self.board_size - 1) * cell_size

        for i in range(self.board_size):
            col_label = chr(ord("A") + i) if i < 8 else chr(ord("A") + i + 1)
            row_label = str(self.board_size - i)

            y = grid_border + i * cell_size
            x = grid_border + i * cell_size

            draw.text((grid_border - label_offset, y), row_label,
                      fill=(80, 50, 30, 255), font=font, anchor="rm")
            draw.text((edge + label_offset, y), row_label,
                      fill=(80, 50, 30, 255), font=font, anchor="lm")
            draw.text((x, grid_border - label_offset), col_label,
                      fill=(80, 50, 30, 255), font=font, anchor="mb")
            draw.text((x, edge + label_offset), col_label,
                      fill=(80, 50, 30, 255), font=font, anchor="mt")

        # Draw pieces
        piece_radius = cell_size * 0.42

        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i, j] != 0:
                    cx = grid_border + j * cell_size
                    cy = grid_border + i * cell_size

                    piece_asset = self.black_piece if board[i,
                                                            j] == 1 else self.white_piece

                    if piece_asset is not None:
                        piece_size = int(piece_radius * 2)
                        piece_resized = piece_asset.resize(
                            (piece_size, piece_size), Image.Resampling.LANCZOS)
                        paste_x = int(cx - piece_radius)
                        paste_y = int(cy - piece_radius)
                        img.paste(piece_resized,
                                  (paste_x, paste_y), piece_resized)

        return img.convert("RGB")

    def generate_resolution_test_suite(self, n_samples_per_resolution: int = 30):
        """Generate complete resolution diagnostic test suite."""
        print("=" * 70)
        print("GOMOKU RESOLUTION DIAGNOSTIC TEST GENERATOR")
        print("=" * 70)
        print(f"Board size: {self.board_size}x{self.board_size}")
        print(f"Patch size: {self.patch_size}x{self.patch_size}")
        print(f"Samples per resolution: {n_samples_per_resolution}")
        print()

        test_data = {
            "metadata": {
                "game": "gomoku",
                "board_size": self.board_size,
                "patch_size": self.patch_size,
                "board_to_image_ratio": self.board_to_image_ratio,
                "density": "medium (40-50%)",
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

        piece_counts = [np.sum(b > 0) for b in board_states]
        avg_pieces = np.mean(piece_counts)
        avg_density = avg_pieces / (self.board_size ** 2)
        print(
            f"  Average pieces: {avg_pieces:.1f} ({avg_density:.1%} density)")
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

                    filename = f"gomoku_{group_name}_{resolution}_{idx:03d}.png"
                    filepath = self.output_dir / "images" / \
                        group_name / str(resolution) / filename
                    img.save(filepath)

                    total_pieces = int(np.sum(board > 0))
                    resolution_piece_counts.append(total_pieces)

                    test_case = {
                        "test_id": f"{group_name}_{resolution}_{idx:03d}",
                        "resolution_group": group_name,
                        "resolution": resolution,
                        "sample_index": idx,
                        "image_file": str(filepath),
                        "ground_truth": board.tolist(),
                        "statistics": {
                            "total_pieces": total_pieces,
                            "black_count": int(np.sum(board == 1)),
                            "white_count": int(np.sum(board == 2)),
                            "density": float(total_pieces / (self.board_size ** 2)),
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
        f"standalone-gomoku-resolution-{timestamp}"

    generator = GomokuResolutionDiagnosticTest(output_dir=output_dir)
    test_data = generator.generate_resolution_test_suite(
        n_samples_per_resolution=10)

    print("\n[DONE]")
