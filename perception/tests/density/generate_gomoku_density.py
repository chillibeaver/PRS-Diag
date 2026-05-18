"""
Gomoku Density Test Generator.
Generates images and test data for VLM board perception testing.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
import json
from pathlib import Path


class GomokuDensityDiagnosticTest:
    """
    Gomoku board density diagnostic test generator.

    Design:
    - 3D rendered style with PNG assets
    - Three density levels: Low (20-30%), Medium (40-50%), High (60-70%)
    - Board size: 15x15, Resolution: 1024x1024
    """

    def __init__(self, output_dir: Path, board_size: int = 15):
        """
        Initialize the generator.

        Args:
            output_dir: Output directory for generated test data
            board_size: Board size, default 15
        """
        self.board_size = board_size
        self.output_dir = Path(output_dir)

        # Fixed parameters
        self.resolution = 1024
        self.board_to_image_ratio = 1

        # Asset paths
        script_dir = Path(__file__).parent
        assets_dir = script_dir.parent.parent / "assets"
        self.assets = {
            "black_piece": str(assets_dir / "black_stone.png"),
            "white_piece": str(assets_dir / "white_stone.png"),
        }

        # Density configurations
        self.density_levels = {
            "low": {
                "range": (int(board_size * board_size * 0.20), int(board_size * board_size * 0.30)),
                "description": "20-30% occupancy",
            },
            "medium": {
                "range": (int(board_size * board_size * 0.40), int(board_size * board_size * 0.50)),
                "description": "40-50% occupancy",
            },
            "high": {
                "range": (int(board_size * board_size * 0.60), int(board_size * board_size * 0.70)),
                "description": "60-70% occupancy",
            },
        }

        # Star points for traditional layout
        self.star_points = [
            (3, 3), (3, 7), (3, 11),
            (7, 3), (7, 7), (7, 11),
            (11, 3), (11, 7), (11, 11),
        ]

        self._load_assets()

        # Create output directory and subdirectories for images
        for density_name in self.density_levels.keys():
            (self.output_dir / "images" /
             density_name).mkdir(parents=True, exist_ok=True)

    def _load_assets(self):
        """Load PNG assets."""
        print("Loading PNG assets...")

        try:
            self.black_piece = Image.open(
                self.assets["black_piece"]).convert("RGBA")
            print(f"  [OK] Black piece: {self.black_piece.size}")
        except FileNotFoundError:
            print(f"  [MISSING] Black piece")
            self.black_piece = None

        try:
            self.white_piece = Image.open(
                self.assets["white_piece"]).convert("RGBA")
            print(f"  [OK] White piece: {self.white_piece.size}")
        except FileNotFoundError:
            print(f"  [MISSING] White piece")
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
        grid_margin = int(board_size_px * 0.08)
        grid_size_px = board_size_px - 2 * grid_margin
        cell_size = grid_size_px / (self.board_size - 1)
        grid_border = board_border + grid_margin

        return {
            "image_size": image_size,
            "board_size_px": board_size_px,
            "board_border": board_border,
            "grid_border": grid_border,
            "cell_size": cell_size,
        }

    def generate_board_state(self, density_level: str) -> np.ndarray:
        """Generate random board state for given density."""
        board = np.zeros((self.board_size, self.board_size), dtype=int)

        min_pieces, max_pieces = self.density_levels[density_level]["range"]
        num_pieces = random.randint(min_pieces, max_pieces)

        all_positions = [(i, j) for i in range(self.board_size)
                         for j in range(self.board_size)]
        selected = random.sample(all_positions, num_pieces)

        for idx, (row, col) in enumerate(selected):
            board[row, col] = 1 if idx % 2 == 0 else 2

        return board

    def render_board(self, board: np.ndarray, dimensions: dict) -> Image.Image:
        """Render 3D-style board with PNG assets."""
        img_size = dimensions["image_size"]
        board_size_px = dimensions["board_size_px"]
        board_border = dimensions["board_border"]
        grid_border = dimensions["grid_border"]
        cell_size = dimensions["cell_size"]

        img = Image.new("RGB", (img_size, img_size), (245, 242, 238))

        draw = ImageDraw.Draw(img)
        board_color = (220, 179, 92)
        draw.rectangle(
            [(board_border, board_border),
             (board_border + board_size_px, board_border + board_size_px)],
            fill=board_color
        )

        img = img.convert("RGBA")
        draw = ImageDraw.Draw(img)

        # Grid lines
        line_width = max(2, int(cell_size * 0.035))
        line_color = (70, 45, 25, 255)

        for i in range(self.board_size):
            pos = grid_border + i * cell_size
            draw.line([(grid_border, pos), (grid_border + (self.board_size - 1) * cell_size, pos)],
                      fill=line_color, width=line_width)
            draw.line([(pos, grid_border), (pos, grid_border + (self.board_size - 1) * cell_size)],
                      fill=line_color, width=line_width)

        # Star points
        star_radius = int(cell_size * 0.20)
        for row, col in self.star_points:
            x = grid_border + col * cell_size
            y = grid_border + row * cell_size
            draw.ellipse([x - star_radius, y - star_radius, x + star_radius, y + star_radius],
                         fill=(70, 45, 25, 255))

        # Coordinate labels
        font_size = max(24, int(cell_size * 0.6))
        font = self._load_font(font_size)

        label_offset = int(cell_size * 0.7)
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
        piece_radius = cell_size * 0.48

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

    def generate_density_test_suite(self, n_samples_per_density: int = 30):
        """
        Generate complete density diagnostic test suite.

        All test cases are saved in a single unified JSON file.
        """
        print("=" * 70)
        print("GOMOKU DENSITY DIAGNOSTIC TEST GENERATOR")
        print("=" * 70)
        print(f"Board size: {self.board_size}x{self.board_size}")
        print(f"Resolution: {self.resolution}x{self.resolution}px")
        print(f"Samples per density: {n_samples_per_density}")
        print()

        test_data = {
            "metadata": {
                "game": "gomoku",
                "board_size": self.board_size,
                "resolution": self.resolution,
                "board_to_image_ratio": self.board_to_image_ratio,
                "visual_style": "3D rendered with PNG assets",
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
            for i in range(n_samples_per_density):
                board = self.generate_board_state(density_name)
                boards.append(board)
                if (i + 1) % 10 == 0:
                    print(f"  Generated {i+1}/{n_samples_per_density}...")

            piece_counts = [np.sum(b > 0) for b in boards]
            avg_pieces = np.mean(piece_counts)
            avg_density = avg_pieces / (self.board_size * self.board_size)

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

                filename = f"gomoku_{density_name}_{idx:03d}.png"
                filepath = self.output_dir / "images" / density_name / filename
                img.save(filepath)

                test_case = {
                    "test_id": f"{density_name}_{idx:03d}",
                    "density_level": density_name,
                    "sample_index": idx,
                    "image_file": str(filepath),
                    "ground_truth": board.tolist(),
                    "statistics": {
                        "total_pieces": int(np.sum(board > 0)),
                        "black_count": int(np.sum(board == 1)),
                        "white_count": int(np.sum(board == 2)),
                        "density": float(np.sum(board > 0) / (self.board_size ** 2)),
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

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(__file__).parent.parent.parent / \
        f"standalone-gomoku-density-{timestamp}"

    generator = GomokuDensityDiagnosticTest(output_dir=output_dir)
    metadata = generator.generate_density_test_suite(n_samples_per_density=30)
