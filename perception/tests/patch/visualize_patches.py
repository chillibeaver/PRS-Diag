"""
Patch Alignment Visualization Tool.

Visualizes how VLM patches overlay on Chess and Gomoku boards,
helping to understand the patch alignment concept.

This tool reuses the rendering logic from generate_chess_patch.py and
generate_gomoku_patch.py to ensure consistency with actual test images.

Usage:
    python visualize_patches.py --game gomoku
    python visualize_patches.py --game chess
    python visualize_patches.py --game all
    python visualize_patches.py --game gomoku --patch-config patch14_896
"""
from generate_chess_patch import ChessPatchDiagnosticTest
from generate_gomoku_patch import (
    GomokuPatchDiagnosticTest,
    PATCH_CONFIGS,
    get_alignment_conditions,
)
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import sys

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # perception/

# Add project root to path for imports
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import from same directory (tests/patch/)


class PatchVisualizer:
    """
    Visualize patch grid overlay on Chess/Gomoku boards.

    Reuses the actual board generators to ensure visualization
    matches what VLMs see during testing.
    """

    def __init__(self, game: str = "gomoku", patch_config: str = "patch16"):
        """
        Initialize visualizer.

        Args:
            game: "chess" or "gomoku"
            patch_config: One of "patch16", "patch14_1008", "patch14_896"
        """
        if game not in ["chess", "gomoku"]:
            raise ValueError(f"Unknown game: {game}. Use 'chess' or 'gomoku'")
        if patch_config not in PATCH_CONFIGS:
            raise ValueError(f"Unknown patch_config: {patch_config}")

        self.game = game
        self.patch_config = patch_config
        self.patch_size = PATCH_CONFIGS[patch_config]["patch_size"]
        self.image_size = PATCH_CONFIGS[patch_config]["image_size"]

        # Create temporary output dir for the generator
        self.temp_dir = Path(__file__).parent / ".temp_viz"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Initialize the appropriate generator
        if game == "gomoku":
            self.generator = GomokuPatchDiagnosticTest(
                output_dir=self.temp_dir,
                patch_config=patch_config
            )
            self.board_size = self.generator.board_size  # 15
            self.cell_size = self.generator.cell_size
            self.alignment_target = "intersection"
        else:  # chess
            self.generator = ChessPatchDiagnosticTest(
                output_dir=self.temp_dir,
                patch_config=patch_config
            )
            self.board_size = self.generator.board_size  # 8
            self.cell_size = self.generator.square_size
            self.alignment_target = "piece_center"

        # Alignment conditions
        self.alignment_conditions = get_alignment_conditions(self.patch_size)

        # Visualization colors
        self.viz_colors = {
            "patch_grid": (255, 0, 0, 100),       # Red, semi-transparent
            "patch_border": (255, 0, 0, 200),     # Red, more opaque
            "target_aligned": (0, 255, 0),        # Green - aligned
            "target_misaligned": (255, 0, 0),     # Red - misaligned
            "zoom_bg": (255, 255, 255),
            "zoom_grid": (200, 200, 200),
            "zoom_marker": (0, 200, 0),
        }

        # Output directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_dir = Path(__file__).parent.parent.parent / \
            f"visualize-{game}-{patch_config}-{timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"PATCH VISUALIZER: {game.upper()}")
        print(f"{'='*60}")
        print(f"  Patch config: {patch_config}")
        print(f"  Patch size: {self.patch_size}×{self.patch_size}")
        print(f"  Image size: {self.image_size}×{self.image_size}")
        print(f"  Board size: {self.board_size}×{self.board_size}")
        print(f"  Cell/Square size: {self.cell_size}px")
        print(f"  Alignment target: {self.alignment_target}")
        print(f"  Output: {self.output_dir}")

    def _load_font(self, size: int):
        """Load font with fallback."""
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

    def generate_board_state(self):
        """Generate a sample board state using the generator."""
        if self.game == "gomoku":
            return self.generator.generate_board_state("medium")
        else:  # chess
            return self.generator.generate_board_state("medium")

    def render_base_board(self, board_state, condition: str) -> Image.Image:
        """Render board using the actual generator (ensures consistency)."""
        return self.generator.render_board(board_state, condition)

    def get_target_positions(self, board_start: int):
        """
        Get all target positions (intersections for Gomoku, piece centers for Chess).

        Returns list of (x, y, row, col) tuples.
        """
        positions = []

        if self.game == "gomoku":
            # Gomoku: intersections are at grid points
            for row in range(self.board_size):
                for col in range(self.board_size):
                    x = board_start + col * self.cell_size
                    y = board_start + row * self.cell_size
                    positions.append((x, y, row, col))
        else:  # chess
            # Chess: piece centers are at square centers
            half = self.generator.half_square
            for row in range(self.board_size):
                for col in range(self.board_size):
                    x = board_start + col * self.cell_size + half
                    y = board_start + row * self.cell_size + half
                    positions.append((x, y, row, col))

        return positions

    def draw_patch_grid(self, img: Image.Image):
        """Draw patch grid overlay on image."""
        draw = ImageDraw.Draw(img, 'RGBA')

        # Draw all patch boundaries
        for i in range(self.image_size // self.patch_size + 1):
            pos = i * self.patch_size
            # Vertical lines
            draw.line([(pos, 0), (pos, self.image_size)],
                      fill=self.viz_colors["patch_grid"], width=1)
            # Horizontal lines
            draw.line([(0, pos), (self.image_size, pos)],
                      fill=self.viz_colors["patch_grid"], width=1)

    def draw_alignment_markers(self, img: Image.Image, board_start: int, expected_offset: int):
        """Draw markers on target positions showing alignment status."""
        draw = ImageDraw.Draw(img, 'RGBA')
        marker_radius = 4

        positions = self.get_target_positions(board_start)

        for x, y, row, col in positions:
            actual_offset_x = x % self.patch_size
            actual_offset_y = y % self.patch_size

            # Check if aligned
            is_aligned = (actual_offset_x == expected_offset and
                          actual_offset_y == expected_offset)

            color = (self.viz_colors["target_aligned"] if is_aligned
                     else self.viz_colors["target_misaligned"])

            draw.ellipse([x - marker_radius, y - marker_radius,
                         x + marker_radius, y + marker_radius],
                         fill=color)

    def draw_zoomed_patch(self, img: Image.Image, board_start: int, offset: int,
                          board_state=None):
        """Draw a zoomed view of a single patch showing the target position."""
        draw = ImageDraw.Draw(img, 'RGBA')

        # Find center position
        if self.game == "gomoku":
            center_row, center_col = 7, 7
            target_x = board_start + center_col * self.cell_size
            target_y = board_start + center_row * self.cell_size
        else:  # chess
            center_row, center_col = 3, 3  # d5 square
            half = self.generator.half_square
            target_x = board_start + center_col * self.cell_size + half
            target_y = board_start + center_row * self.cell_size + half

        # Find the patch containing this target
        patch_x = (target_x // self.patch_size) * self.patch_size
        patch_y = (target_y // self.patch_size) * self.patch_size

        # Zoom parameters
        zoom = 10
        zoom_size = self.patch_size * zoom
        zoom_x, zoom_y = 20, 20

        # Background
        draw.rectangle([zoom_x, zoom_y, zoom_x + zoom_size, zoom_y + zoom_size],
                       fill=self.viz_colors["zoom_bg"], outline=(0, 0, 0), width=2)

        # Grid inside zoomed patch
        for i in range(self.patch_size + 1):
            pos_h = zoom_y + i * zoom
            draw.line([(zoom_x, pos_h), (zoom_x + zoom_size, pos_h)],
                      fill=self.viz_colors["zoom_grid"], width=1)
            pos_v = zoom_x + i * zoom
            draw.line([(pos_v, zoom_y), (pos_v, zoom_y + zoom_size)],
                      fill=self.viz_colors["zoom_grid"], width=1)

        # Target position in zoomed view
        rel_x = target_x - patch_x
        rel_y = target_y - patch_y
        zoomed_x = zoom_x + rel_x * zoom + zoom // 2
        zoomed_y = zoom_y + rel_y * zoom + zoom // 2

        # Draw target marker
        r = zoom // 2
        draw.ellipse([zoomed_x - r, zoomed_y - r, zoomed_x + r, zoomed_y + r],
                     fill=self.viz_colors["zoom_marker"])

        # Labels
        font = self._load_font(14)
        label_y = zoom_y + zoom_size + 5

        draw.text((zoom_x, label_y),
                  f"Zoomed patch (10×)", fill=(0, 0, 0), font=font)
        draw.text((zoom_x, label_y + 17),
                  f"{self.alignment_target.replace('_', ' ').title()} at ({rel_x}, {rel_y})",
                  fill=(0, 0, 0), font=font)
        draw.text((zoom_x, label_y + 34),
                  f"Expected offset = {offset}px", fill=(0, 0, 0), font=font)

        # Show actual offset for verification
        actual_offset = target_x % self.patch_size
        status = "✓ Aligned" if actual_offset == offset else f"✗ Actual: {actual_offset}px"
        color = (0, 128, 0) if actual_offset == offset else (200, 0, 0)
        draw.text((zoom_x, label_y + 51), status, fill=color, font=font)

    def draw_info_panel(self, img: Image.Image, condition: str, offset: int, board_start: int):
        """Draw information panel."""
        draw = ImageDraw.Draw(img, 'RGBA')
        font_large = self._load_font(20)
        font_small = self._load_font(14)

        # Panel position (bottom-left)
        panel_x, panel_y = 20, self.image_size - 140

        # Background
        draw.rectangle([panel_x - 5, panel_y - 5, panel_x + 320, panel_y + 130],
                       fill=(255, 255, 255, 220), outline=(0, 0, 0))

        # Text
        game_name = "Chess" if self.game == "chess" else "Gomoku"
        draw.text((panel_x, panel_y), f"{game_name} - {condition}",
                  fill=(0, 0, 0), font=font_large)
        draw.text((panel_x, panel_y + 28), f"Patch config: {self.patch_config}",
                  fill=(0, 0, 0), font=font_small)
        draw.text((panel_x, panel_y + 48), f"Target offset: {offset}px",
                  fill=(0, 0, 0), font=font_small)
        draw.text((panel_x, panel_y + 68), f"Board start: {board_start}px",
                  fill=(0, 0, 0), font=font_small)
        draw.text((panel_x, panel_y + 88), f"Patch size: {self.patch_size}×{self.patch_size}",
                  fill=(0, 0, 0), font=font_small)
        draw.text((panel_x, panel_y + 108), f"Alignment: {self.alignment_target}",
                  fill=(0, 0, 0), font=font_small)

    def draw_legend(self, img: Image.Image):
        """Draw legend."""
        draw = ImageDraw.Draw(img, 'RGBA')
        font = self._load_font(12)

        # Panel position (bottom-right)
        panel_x = self.image_size - 200
        panel_y = self.image_size - 100

        draw.rectangle([panel_x - 5, panel_y - 5, panel_x + 195, panel_y + 95],
                       fill=(255, 255, 255, 220), outline=(0, 0, 0))

        # Legend items
        y_offset = 0

        # Red grid line
        draw.line([(panel_x, panel_y + 8 + y_offset), (panel_x + 30, panel_y + 8 + y_offset)],
                  fill=(255, 0, 0, 150), width=2)
        draw.text((panel_x + 35, panel_y + y_offset), "Patch boundary",
                  fill=(0, 0, 0), font=font)
        y_offset += 20

        # Green dot
        draw.ellipse([panel_x + 10, panel_y + 2 + y_offset, panel_x + 20, panel_y + 12 + y_offset],
                     fill=(0, 255, 0))
        target_name = "Aligned " + self.alignment_target.replace("_", " ")
        draw.text((panel_x + 35, panel_y + y_offset), target_name,
                  fill=(0, 0, 0), font=font)
        y_offset += 20

        # Red dot
        draw.ellipse([panel_x + 10, panel_y + 2 + y_offset, panel_x + 20, panel_y + 12 + y_offset],
                     fill=(255, 0, 0))
        draw.text((panel_x + 35, panel_y + y_offset), "Misaligned",
                  fill=(0, 0, 0), font=font)
        y_offset += 20

        # Game-specific info
        if self.game == "chess":
            draw.text((panel_x, panel_y + y_offset + 5),
                      f"k={self.generator.k} (half_sq={self.generator.half_square}px)",
                      fill=(100, 100, 100), font=font)

    def visualize_condition(self, condition: str, board_state=None,
                            with_pieces: bool = True) -> Image.Image:
        """Generate visualization for one alignment condition."""
        offset = self.alignment_conditions[condition]["offset"]
        board_start = self.generator.get_board_start_position(condition)

        # Generate board state if not provided
        if board_state is None and with_pieces:
            board_state = self.generate_board_state()

        # Render base board using the actual generator
        if with_pieces and board_state is not None:
            img = self.render_base_board(board_state, condition)
        else:
            # Render empty board - create minimal board state
            if self.game == "gomoku":
                empty_board = np.zeros(
                    (self.board_size, self.board_size), dtype=int)
                img = self.generator.render_board(empty_board, condition)
            else:  # chess
                import chess
                empty_board = chess.Board(fen=None)  # Empty board
                empty_board.clear()
                img = self.generator.render_board(empty_board, condition)

        # Convert to RGBA for overlay
        img = img.convert("RGBA")

        # Add visualization overlays
        self.draw_patch_grid(img)
        self.draw_alignment_markers(img, board_start, offset)
        self.draw_zoomed_patch(img, board_start, offset, board_state)
        self.draw_info_panel(img, condition, offset, board_start)
        self.draw_legend(img)

        return img.convert("RGB")

    def generate_all_visualizations(self):
        """Generate visualizations for all alignment conditions."""
        print(f"\n{'='*60}")
        print(f"GENERATING VISUALIZATIONS")
        print(f"{'='*60}")

        # Generate one board state to use across conditions (for consistency)
        board_state = self.generate_board_state()

        if self.game == "gomoku":
            piece_count = int(np.sum(board_state > 0))
        else:
            piece_count = len(board_state.piece_map())
        print(f"\nSample board: {piece_count} pieces")

        for condition, config in self.alignment_conditions.items():
            print(f"\nGenerating: {condition} (offset={config['offset']}px)")

            # Version 1: Empty board
            img_empty = self.visualize_condition(condition, with_pieces=False)
            filename_empty = f"{self.game}_{condition}_empty.png"
            filepath_empty = self.output_dir / filename_empty
            img_empty.save(filepath_empty)
            print(f"  Saved: {filename_empty}")

            # Version 2: With pieces
            img_pieces = self.visualize_condition(
                condition, board_state=board_state, with_pieces=True)
            filename_pieces = f"{self.game}_{condition}_pieces.png"
            filepath_pieces = self.output_dir / filename_pieces
            img_pieces.save(filepath_pieces)
            print(f"  Saved: {filename_pieces}")

        # Generate comparison images
        self.generate_comparison_image(with_pieces=False)
        self.generate_comparison_image(
            with_pieces=True, board_state=board_state)

        print(f"\n{'='*60}")
        print(f"Output directory: {self.output_dir}")
        print(f"{'='*60}")

    def generate_comparison_image(self, with_pieces: bool = False, board_state=None):
        """Generate a side-by-side comparison of all conditions."""
        n_conditions = len(self.alignment_conditions)
        cols = 2
        rows = (n_conditions + 1) // 2

        thumb_size = 512
        margin = 10
        total_width = cols * thumb_size + (cols + 1) * margin
        total_height = rows * thumb_size + (rows + 1) * margin

        comparison = Image.new(
            "RGB", (total_width, total_height), (255, 255, 255))

        # Add each condition
        for idx, condition in enumerate(self.alignment_conditions.keys()):
            row = idx // cols
            col = idx % cols

            x = margin + col * (thumb_size + margin)
            y = margin + row * (thumb_size + margin)

            img = self.visualize_condition(
                condition, board_state=board_state, with_pieces=with_pieces)
            thumb = img.resize((thumb_size, thumb_size),
                               Image.Resampling.LANCZOS)
            comparison.paste(thumb, (x, y))

        suffix_filename = "_pieces" if with_pieces else "_empty"
        filepath = self.output_dir / f"comparison_all{suffix_filename}.png"
        comparison.save(filepath)
        print(f"\nSaved comparison: {filepath.name}")

    def cleanup(self):
        """Clean up temporary directory."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


def combine_comparison_images(output_dirs: Dict[str, Path], suffix: str = "_pieces"):
    """Combine chess and gomoku comparison images side by side."""
    if "chess" not in output_dirs or "gomoku" not in output_dirs:
        return None

    chess_path = output_dirs["chess"] / f"comparison_all{suffix}.png"
    gomoku_path = output_dirs["gomoku"] / f"comparison_all{suffix}.png"

    if not chess_path.exists() or not gomoku_path.exists():
        print(f"Warning: Could not find comparison images for combining")
        return None

    chess_img = Image.open(chess_path)
    gomoku_img = Image.open(gomoku_path)

    # Calculate combined dimensions
    total_width = chess_img.width + gomoku_img.width
    max_height = max(chess_img.height, gomoku_img.height)

    # Create combined image
    combined = Image.new("RGB", (total_width, max_height), (255, 255, 255))
    combined.paste(chess_img, (0, 0))
    combined.paste(gomoku_img, (chess_img.width, 0))

    # Save to parent directory
    output_path = output_dirs["chess"].parent / \
        f"comparison_chess_gomoku{suffix}.png"
    combined.save(output_path)
    print(f"\nSaved combined comparison: {output_path}")

    return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Patch Alignment Visualization")
    parser.add_argument("--game", "-g", choices=["chess", "gomoku", "all"],
                        default="all", help="Game to visualize (default: all)")
    parser.add_argument("--patch-config", "-p", choices=list(PATCH_CONFIGS.keys()),
                        default="patch16", help="Patch configuration (default: patch16)")
    args = parser.parse_args()

    games = ["chess", "gomoku"] if args.game == "all" else [args.game]
    output_dirs: Dict[str, Path] = {}

    for game in games:
        print(f"\n{'#'*70}")
        print(f"# {game.upper()}")
        print(f"{'#'*70}")

        visualizer = PatchVisualizer(game=game, patch_config=args.patch_config)
        visualizer.generate_all_visualizations()
        output_dirs[game] = visualizer.output_dir
        visualizer.cleanup()

    # Combine comparison images if both games were generated
    if args.game == "all":
        print(f"\n{'#'*70}")
        print(f"# COMBINING COMPARISON IMAGES")
        print(f"{'#'*70}")
        combine_comparison_images(output_dirs, "_pieces")
        combine_comparison_images(output_dirs, "_empty")

    print("\n[DONE] All visualizations complete!")


if __name__ == "__main__":
    main()
