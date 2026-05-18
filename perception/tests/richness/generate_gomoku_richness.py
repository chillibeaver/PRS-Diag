"""
Gomoku Visual Richness Test Generator.
Generates images with varying visual styles to test VLM perception.

Tests 2D flat vs 3D rendered styles to determine if visual richness
helps or hinders VLM board perception.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
from pathlib import Path
from typing import Dict, List


class GomokuRichnessDiagnosticTest:
    """
    Gomoku board visual richness diagnostic test generator.

    Design:
    - Compares 2D flat vs 3D rendered visual styles
    - Uses medium density boards to isolate visual richness effects
    - Board size: 15×15 intersections
    - Fixed resolution: 1024×1024
    - Same layout as density test (no white border)
    """

    def __init__(self, output_dir: Path, board_size: int = 15):
        self.output_dir = Path(output_dir)
        self.board_size = board_size
        self.resolution = 1024
        self.board_to_image_ratio = 1  # No white border, same as density test

        # Asset paths
        script_dir = Path(__file__).parent
        assets_dir = script_dir.parent.parent / "assets"
        self.assets = {
            "wood_texture": assets_dir / "wood_texture.jpg",
            "black_stone": assets_dir / "black_stone.png",
            "white_stone": assets_dir / "white_stone.png",
        }

        # Style configurations
        self.style_configs = {
            "2d_flat": {
                "description": "Minimalist 2D geometric shapes",
            },
            "3d_rendered": {
                "description": "Realistic 3D using PNG assets",
            },
        }

        # Colors for 2D style
        self.colors_2d = {
            "board": (220, 179, 92),  # Same as density test
            "line": (70, 45, 25),
            "black_stone": (30, 30, 30),
            "white_stone": (240, 240, 240),
            "coordinate": (80, 50, 30),
            "star_point": (70, 45, 25),
        }

        # Star points for 15×15 board
        self.star_points = [
            (3, 3), (3, 7), (3, 11),
            (7, 3), (7, 7), (7, 11),
            (11, 3), (11, 7), (11, 11),
        ]

        self._load_assets()

        # Create output directories
        for style in self.style_configs.keys():
            (self.output_dir / "images" / style).mkdir(parents=True, exist_ok=True)

    def _load_assets(self):
        """Load PNG assets."""
        print("Loading PNG assets...")

        self.wood_texture = None
        self.black_stone = None
        self.white_stone = None

        try:
            self.wood_texture = Image.open(
                self.assets["wood_texture"]).convert("RGB")
            print(f"  [OK] Wood texture: {self.wood_texture.size}")
        except FileNotFoundError:
            print(f"  [WARN] Wood texture not found, using fallback color")

        try:
            self.black_stone = Image.open(
                self.assets["black_stone"]).convert("RGBA")
            print(f"  [OK] Black stone: {self.black_stone.size}")
        except FileNotFoundError:
            print(f"  [WARN] Black stone not found")

        try:
            self.white_stone = Image.open(
                self.assets["white_stone"]).convert("RGBA")
            print(f"  [OK] White stone: {self.white_stone.size}")
        except FileNotFoundError:
            print(f"  [WARN] White stone not found")

        missing = []
        if self.black_stone is None:
            missing.append("black_stone")
        if self.white_stone is None:
            missing.append("white_stone")
        if self.wood_texture is None:
            missing.append("wood_texture")
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

    def _calculate_dimensions(self) -> Dict:
        """Calculate board dimensions (same as density test)."""
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

    def generate_board_state(self, density: str = "medium") -> np.ndarray:
        """Generate random board state with specified density."""
        board = np.zeros((self.board_size, self.board_size), dtype=int)
        total = self.board_size * self.board_size

        density_ranges = {
            "low": (int(total * 0.20), int(total * 0.30)),
            "medium": (int(total * 0.40), int(total * 0.50)),
            "high": (int(total * 0.60), int(total * 0.70)),
        }
        min_pieces, max_pieces = density_ranges.get(
            density, density_ranges["medium"])
        num_pieces = random.randint(min_pieces, max_pieces)

        all_positions = [(i, j) for i in range(self.board_size)
                         for j in range(self.board_size)]
        selected = random.sample(all_positions, num_pieces)

        for idx, (row, col) in enumerate(selected):
            board[row, col] = 1 if idx % 2 == 0 else 2

        return board

    def _get_wood_background(self, size: int) -> Image.Image:
        """Get wood texture background."""
        if self.wood_texture is None:
            return Image.new("RGB", (size, size), (220, 179, 92))

        texture = self.wood_texture
        tiles_x = (size // texture.width) + 2
        tiles_y = (size // texture.height) + 2

        tiled = Image.new(
            "RGB", (texture.width * tiles_x, texture.height * tiles_y))
        for i in range(tiles_x):
            for j in range(tiles_y):
                tiled.paste(texture, (i * texture.width, j * texture.height))

        return tiled.crop((0, 0, size, size))

    def _draw_star_points(self, draw, grid_border: float, cell_size: float,
                          radius: float, color):
        """Draw star points at key intersections."""
        for row, col in self.star_points:
            x = grid_border + col * cell_size
            y = grid_border + row * cell_size
            draw.ellipse([x - radius, y - radius, x +
                         radius, y + radius], fill=color)

    def _render_2d_flat(self, board: np.ndarray, dimensions: Dict) -> Image.Image:
        """Render 2D flat style board (same layout as density test)."""
        image_size = dimensions["image_size"]
        board_size_px = dimensions["board_size_px"]
        board_border = dimensions["board_border"]
        grid_border = dimensions["grid_border"]
        cell_size = dimensions["cell_size"]

        # Create canvas with board color directly (no background margin)
        img = Image.new("RGB", (image_size, image_size),
                        self.colors_2d["board"])
        draw = ImageDraw.Draw(img)

        # Grid lines
        line_width = max(2, int(cell_size * 0.035))
        for i in range(self.board_size):
            pos = grid_border + i * cell_size
            edge = grid_border + (self.board_size - 1) * cell_size
            draw.line([(grid_border, pos), (edge, pos)],
                      fill=self.colors_2d["line"], width=line_width)
            draw.line([(pos, grid_border), (pos, edge)],
                      fill=self.colors_2d["line"], width=line_width)

        # Star points
        star_radius = int(cell_size * 0.20)
        self._draw_star_points(draw, grid_border, cell_size,
                               star_radius, self.colors_2d["star_point"])

        # Coordinate labels (same style as density test)
        font_size = max(24, int(cell_size * 0.6))
        font = self._load_font(font_size)
        label_offset = int(cell_size * 0.7)
        edge = grid_border + (self.board_size - 1) * cell_size

        for i in range(self.board_size):
            col_label = chr(ord("A") + i) if i < 8 else chr(ord("A") + i + 1)
            row_label = str(self.board_size - i)

            y = grid_border + i * cell_size
            x = grid_border + i * cell_size

            # Left and right row labels
            draw.text((grid_border - label_offset, y), row_label,
                      fill=self.colors_2d["coordinate"], font=font, anchor="rm")
            draw.text((edge + label_offset, y), row_label,
                      fill=self.colors_2d["coordinate"], font=font, anchor="lm")
            # Top and bottom column labels
            draw.text((x, grid_border - label_offset), col_label,
                      fill=self.colors_2d["coordinate"], font=font, anchor="mb")
            draw.text((x, edge + label_offset), col_label,
                      fill=self.colors_2d["coordinate"], font=font, anchor="mt")

        # Draw stones (simple circles)
        stone_radius = cell_size * 0.48
        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i, j] != 0:
                    cx = grid_border + j * cell_size
                    cy = grid_border + i * cell_size
                    color = (self.colors_2d["black_stone"] if board[i, j] == 1
                             else self.colors_2d["white_stone"])
                    draw.ellipse([cx - stone_radius, cy - stone_radius,
                                  cx + stone_radius, cy + stone_radius], fill=color)

        return img

    def _render_3d_rendered(self, board: np.ndarray, dimensions: Dict) -> Image.Image:
        """Render 3D style board with PNG assets (same layout as density test)."""
        image_size = dimensions["image_size"]
        board_size_px = dimensions["board_size_px"]
        board_border = dimensions["board_border"]
        grid_border = dimensions["grid_border"]
        cell_size = dimensions["cell_size"]

        # Wood texture background (fills entire image)
        img = self._get_wood_background(image_size)
        img = img.convert("RGBA")
        draw = ImageDraw.Draw(img)

        # Grid lines
        line_width = max(2, int(cell_size * 0.035))
        line_color = (70, 45, 25, 255)

        for i in range(self.board_size):
            pos = grid_border + i * cell_size
            edge = grid_border + (self.board_size - 1) * cell_size
            draw.line([(grid_border, pos), (edge, pos)],
                      fill=line_color, width=line_width)
            draw.line([(pos, grid_border), (pos, edge)],
                      fill=line_color, width=line_width)

        # Star points
        star_radius = int(cell_size * 0.20)
        self._draw_star_points(draw, grid_border, cell_size,
                               star_radius, (70, 45, 25, 255))

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

        # Draw stones with PNG assets
        stone_radius = cell_size * 0.48

        for i in range(self.board_size):
            for j in range(self.board_size):
                if board[i, j] != 0:
                    cx = grid_border + j * cell_size
                    cy = grid_border + i * cell_size

                    stone_asset = (self.black_stone if board[i, j] == 1
                                   else self.white_stone)

                    if stone_asset is not None:
                        stone_size = int(stone_radius * 2)
                        stone_resized = stone_asset.resize(
                            (stone_size, stone_size), Image.Resampling.LANCZOS)
                        paste_x = int(cx - stone_radius)
                        paste_y = int(cy - stone_radius)
                        img.paste(stone_resized,
                                  (paste_x, paste_y), stone_resized)
                    else:
                        # Fallback to 2D circle
                        color = ((30, 30, 30, 255) if board[i, j] == 1
                                 else (240, 240, 240, 255))
                        draw.ellipse([cx - stone_radius, cy - stone_radius,
                                      cx + stone_radius, cy + stone_radius], fill=color)

        return img.convert("RGB")

    def render_board(self, board: np.ndarray, style: str,
                     dimensions: Dict) -> Image.Image:
        """Render board with specified style."""
        if style == "2d_flat":
            return self._render_2d_flat(board, dimensions)
        elif style == "3d_rendered":
            return self._render_3d_rendered(board, dimensions)
        else:
            raise ValueError(f"Unknown style: {style}")

    def generate_richness_test_suite(self, n_samples_per_style: int = 30):
        """Generate complete visual richness test suite."""
        print("=" * 70)
        print("GOMOKU VISUAL RICHNESS DIAGNOSTIC TEST GENERATOR")
        print("=" * 70)
        print(f"Board size: {self.board_size}×{self.board_size}")
        print(f"Resolution: {self.resolution}×{self.resolution}px")
        print(f"Samples per style: {n_samples_per_style}")
        print()

        test_data = {
            "metadata": {
                "game": "gomoku",
                "board_size": self.board_size,
                "resolution": self.resolution,
                "board_to_image_ratio": self.board_to_image_ratio,
                "density": "medium (40-50%)",
                "samples_per_style": n_samples_per_style,
                "total_samples": n_samples_per_style * len(self.style_configs),
            },
            "style_stats": {},
            "test_cases": [],
        }

        dimensions = self._calculate_dimensions()

        # Generate board states (same for all styles for fair comparison)
        print(f"Generating {n_samples_per_style} board states...")
        board_states = [self.generate_board_state("medium")
                        for _ in range(n_samples_per_style)]

        piece_counts = [np.sum(b > 0) for b in board_states]
        avg_pieces = np.mean(piece_counts)
        avg_density = avg_pieces / (self.board_size ** 2)
        print(
            f"  Average pieces: {avg_pieces:.1f} ({avg_density:.1%} density)")
        print()

        # Generate images for each style
        for style_name, style_config in self.style_configs.items():
            print(f"\n{'='*70}")
            print(f"Generating {style_name.upper()} style")
            print(f"  {style_config['description']}")
            print(f"{'='*70}")

            style_piece_counts = []

            for idx, board in enumerate(board_states):
                img = self.render_board(board, style_name, dimensions)

                filename = f"gomoku_{style_name}_{idx:03d}.png"
                filepath = self.output_dir / "images" / style_name / filename
                img.save(filepath)

                total_pieces = int(np.sum(board > 0))
                style_piece_counts.append(total_pieces)

                test_case = {
                    "test_id": f"{style_name}_{idx:03d}",
                    "visual_style": style_name,
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
                    print(f"  Generated {idx+1}/{n_samples_per_style}...")

            test_data["style_stats"][style_name] = {
                "description": style_config["description"],
                "n_samples": len(board_states),
                "avg_pieces": float(np.mean(style_piece_counts)),
                "piece_range": [int(min(style_piece_counts)),
                                int(max(style_piece_counts))],
            }

            print(f"  [OK] Completed {style_name}")

        print(f"\n{'='*70}")
        print(f"[SUCCESS] Generated {len(test_data['test_cases'])} test cases")
        print(f"{'='*70}")

        return test_data


if __name__ == "__main__":
    from datetime import datetime

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(__file__).parent.parent.parent / \
        f"standalone-gomoku-richness-{timestamp}"

    generator = GomokuRichnessDiagnosticTest(output_dir=output_dir)
    test_data = generator.generate_richness_test_suite(n_samples_per_style=10)

    print("\n[DONE]")
