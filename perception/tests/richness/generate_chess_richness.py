"""
Chess Visual Richness Test Generator.
Generates images with varying visual styles to test VLM perception.

Tests 2D flat vs 3D rendered styles to determine if visual richness
helps or hinders VLM board perception.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
import chess
from pathlib import Path
from typing import Dict, List


class ChessRichnessDiagnosticTest:
    """
    Chess board visual richness diagnostic test generator.

    Design:
    - Compares 2D flat vs 3D rendered visual styles
    - Uses medium density boards to isolate visual richness effects
    - Board size: 8×8 squares
    - Fixed resolution: 1024×1024
    - Same layout as density test (no white border)
    """

    PIECE_ENCODING = {
        "P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6,
        "p": -1, "n": -2, "b": -3, "r": -4, "q": -5, "k": -6,
        ".": 0,
    }

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.board_size = 8
        self.resolution = 1024
        self.board_to_image_ratio = 0.92  # Same as density test

        # Asset paths
        script_dir = Path(__file__).parent
        self.assets_dir = script_dir.parent.parent / "assets"

        # Style configurations
        self.style_configs = {
            "2d_flat": {
                "description": "Minimalist 2D flat chess pieces",
            },
            "3d_rendered": {
                "description": "Realistic 3D chess pieces with wood texture",
            },
        }

        # Colors for 2D style (same as density test)
        self.colors_2d = {
            "light_square": (240, 217, 181),
            "dark_square": (181, 136, 99),
            "background": (245, 242, 238),
            "coordinate": (60, 40, 20),
        }

        # Density configuration (medium)
        self.density_levels = {
            "low": {"range": (8, 12), "description": "8-12 pieces (endgame)"},
            "medium": {"range": (16, 20), "description": "16-20 pieces (midgame)"},
            "high": {"range": (28, 32), "description": "28-32 pieces (opening)"},
        }

        self._load_assets()

        # Create output directories
        for style in self.style_configs.keys():
            (self.output_dir / "images" / style).mkdir(parents=True, exist_ok=True)

    def _load_assets(self):
        """Load PNG assets for both 2D and 3D styles."""
        print("Loading chess piece assets...")

        # 2D pieces (existing assets: wp.png, wb.png, etc.)
        self.pieces_2d = {}
        piece_codes_2d = ["wb", "wk", "wn", "wp", "wq", "wr",
                          "bb", "bk", "bn", "bp", "bq", "br"]

        for code in piece_codes_2d:
            filepath = self.assets_dir / f"{code}.png"
            try:
                self.pieces_2d[code] = Image.open(filepath).convert("RGBA")
                print(f"  [OK] 2D {code}: {self.pieces_2d[code].size}")
            except FileNotFoundError:
                print(f"  [WARN] 2D {code} not found at {filepath}")
                self.pieces_2d[code] = None

        # 3D pieces
        self.pieces_3d = {}
        piece_codes_3d = ["wb_3d", "wk_3d", "wn_3d", "wp_3d", "wq_3d", "wr_3d",
                          "bb_3d", "bk_3d", "bn_3d", "bp_3d", "bq_3d", "br_3d"]

        for code in piece_codes_3d:
            filepath = self.assets_dir / f"{code}.png"
            try:
                self.pieces_3d[code] = Image.open(filepath).convert("RGBA")
                print(f"  [OK] 3D {code}: {self.pieces_3d[code].size}")
            except FileNotFoundError:
                print(f"  [WARN] 3D {code} not found at {filepath}")
                self.pieces_3d[code] = None

        # Wood textures for 3D style (light and dark for alternating squares)
        self.light_wood_texture = None
        self.dark_wood_texture = None

        light_wood_path = self.assets_dir / "chess_light_texture.png"
        try:
            self.light_wood_texture = Image.open(
                light_wood_path).convert("RGB")
            print(f"  [OK] Light wood texture: {self.light_wood_texture.size}")
        except FileNotFoundError:
            print(
                f"  [WARN] Light wood texture not found at {light_wood_path}")

        dark_wood_path = self.assets_dir / "chess_dark_texture.png"
        try:
            self.dark_wood_texture = Image.open(dark_wood_path).convert("RGB")
            print(f"  [OK] Dark wood texture: {self.dark_wood_texture.size}")
        except FileNotFoundError:
            print(f"  [WARN] Dark wood texture not found at {dark_wood_path}")

        missing_2d = [
            c for c in piece_codes_2d if self.pieces_2d.get(c) is None]
        missing_3d = [
            c for c in piece_codes_3d if self.pieces_3d.get(c) is None]
        missing_textures = []
        if self.light_wood_texture is None:
            missing_textures.append("chess_light_texture.png")
        if self.dark_wood_texture is None:
            missing_textures.append("chess_dark_texture.png")

        if missing_2d or missing_3d or missing_textures:
            raise FileNotFoundError(
                f"Missing required assets - 2D: {missing_2d}, 3D: {missing_3d}, Textures: {missing_textures}")

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

    def generate_board_state(self, density: str = "medium",
                             max_attempts: int = 200) -> chess.Board:
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

    def _get_texture_tile(self, texture: Image.Image, size: int) -> Image.Image:
        """Get a tiled texture of specified size."""
        if texture is None:
            return None

        # Tile if necessary
        if texture.width < size or texture.height < size:
            tiles_x = (size // texture.width) + 2
            tiles_y = (size // texture.height) + 2
            tiled = Image.new(
                "RGB", (texture.width * tiles_x, texture.height * tiles_y))
            for i in range(tiles_x):
                for j in range(tiles_y):
                    tiled.paste(
                        texture, (i * texture.width, j * texture.height))
            return tiled.crop((0, 0, size, size))
        else:
            return texture.crop((0, 0, size, size))

    def _render_2d_flat(self, board: chess.Board, dimensions: Dict) -> Image.Image:
        """Render 2D flat style board (same layout as density test)."""
        image_size = dimensions["image_size"]
        grid_border = dimensions["grid_border"]
        square_size = dimensions["square_size"]

        # Create canvas
        img = Image.new("RGB", (image_size, image_size),
                        self.colors_2d["background"])
        draw = ImageDraw.Draw(img)

        # Draw squares
        for row in range(8):
            for col in range(8):
                x = grid_border + col * square_size
                y = grid_border + row * square_size
                color = (self.colors_2d["light_square"] if (row + col) % 2 == 0
                         else self.colors_2d["dark_square"])
                draw.rectangle(
                    [x, y, x + square_size, y + square_size], fill=color)

        # Coordinate labels (same as density test)
        font_size = int(square_size * 0.35)
        font = self._load_font(font_size)
        text_color = self.colors_2d["coordinate"]
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

        # Draw pieces using 2D assets
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

            if asset_code and self.pieces_2d.get(asset_code):
                piece_img = self.pieces_2d[asset_code].resize(
                    (piece_size, piece_size), Image.Resampling.LANCZOS)
                x = grid_border + col * square_size + \
                    (square_size - piece_size) // 2
                y = grid_border + row * square_size + \
                    (square_size - piece_size) // 2
                img.paste(piece_img, (int(x), int(y)), piece_img)

        return img.convert("RGB")

    def _render_3d_rendered(self, board: chess.Board, dimensions: Dict) -> Image.Image:
        """Render 3D style board with alternating wood textures and 3D pieces."""
        image_size = dimensions["image_size"]
        board_size_px = dimensions["board_size_px"]
        board_border = dimensions["board_border"]
        grid_border = dimensions["grid_border"]
        square_size = dimensions["square_size"]

        # Create canvas with background
        img = Image.new("RGB", (image_size, image_size), (245, 242, 238))

        # Prepare texture tiles for squares
        square_size_int = int(square_size) + 1
        light_tile = self._get_texture_tile(
            self.light_wood_texture, square_size_int)
        dark_tile = self._get_texture_tile(
            self.dark_wood_texture, square_size_int)

        # Fallback colors if textures not available
        light_fallback = (240, 217, 181)
        dark_fallback = (181, 136, 99)

        # Draw squares with wood textures
        for row in range(8):
            for col in range(8):
                x = int(grid_border + col * square_size)
                y = int(grid_border + row * square_size)
                is_light = (row + col) % 2 == 0

                if is_light and light_tile is not None:
                    # Crop tile to exact square size
                    tile = light_tile.crop(
                        (0, 0, int(square_size), int(square_size)))
                    img.paste(tile, (x, y))
                elif not is_light and dark_tile is not None:
                    tile = dark_tile.crop(
                        (0, 0, int(square_size), int(square_size)))
                    img.paste(tile, (x, y))
                else:
                    # Fallback to solid color
                    draw = ImageDraw.Draw(img)
                    color = light_fallback if is_light else dark_fallback
                    draw.rectangle(
                        [x, y, x + square_size, y + square_size], fill=color)

        img = img.convert("RGBA")
        draw = ImageDraw.Draw(img)

        # Coordinate labels
        font_size = int(square_size * 0.35)
        font = self._load_font(font_size)
        text_color = (60, 40, 20, 255)
        label_padding = square_size * 0.2

        for i in range(8):
            file_label = chr(ord("a") + i)
            rank_label = str(8 - i)
            file_x_center = grid_border + i * square_size + square_size / 2
            rank_y_center = grid_border + i * square_size + square_size / 2

            draw.text((file_x_center, grid_border + 8 * square_size + label_padding),
                      file_label, fill=text_color, font=font, anchor="mm")
            draw.text((grid_border - label_padding, rank_y_center),
                      rank_label, fill=text_color, font=font, anchor="mm")

        # Draw pieces using 3D assets
        piece_size = int(square_size * 0.90)
        piece_to_asset = {
            "P": "wp_3d", "N": "wn_3d", "B": "wb_3d", "R": "wr_3d", "Q": "wq_3d", "K": "wk_3d",
            "p": "bp_3d", "n": "bn_3d", "b": "bb_3d", "r": "br_3d", "q": "bq_3d", "k": "bk_3d",
        }

        for square, piece in board.piece_map().items():
            row = 7 - (square // 8)
            col = square % 8
            piece_symbol = piece.symbol()
            asset_code = piece_to_asset.get(piece_symbol)

            if asset_code and self.pieces_3d.get(asset_code):
                piece_img = self.pieces_3d[asset_code].resize(
                    (piece_size, piece_size), Image.Resampling.LANCZOS)
                x = grid_border + col * square_size + \
                    (square_size - piece_size) // 2
                y = grid_border + row * square_size + \
                    (square_size - piece_size) // 2
                img.paste(piece_img, (int(x), int(y)), piece_img)

        return img.convert("RGB")

    def render_board(self, board: chess.Board, style: str,
                     dimensions: Dict) -> Image.Image:
        """Render board with specified style."""
        if style == "2d_flat":
            return self._render_2d_flat(board, dimensions)
        elif style == "3d_rendered":
            return self._render_3d_rendered(board, dimensions)
        else:
            raise ValueError(f"Unknown style: {style}")

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

    def generate_richness_test_suite(self, n_samples_per_style: int = 30):
        """Generate complete visual richness test suite."""
        print("=" * 70)
        print("CHESS VISUAL RICHNESS DIAGNOSTIC TEST GENERATOR")
        print("=" * 70)
        print(f"Board size: {self.board_size}×{self.board_size}")
        print(f"Resolution: {self.resolution}×{self.resolution}px")
        print(f"Samples per style: {n_samples_per_style}")
        print()

        test_data = {
            "metadata": {
                "game": "chess",
                "board_size": self.board_size,
                "resolution": self.resolution,
                "board_to_image_ratio": self.board_to_image_ratio,
                "density": "medium (16-20 pieces)",
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

        piece_counts = [self._count_pieces(b) for b in board_states]
        avg_pieces = np.mean(piece_counts)
        avg_density = avg_pieces / 32
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
                matrix = self.board_to_matrix(board)

                filename = f"chess_{style_name}_{idx:03d}.png"
                filepath = self.output_dir / "images" / style_name / filename
                img.save(filepath)

                piece_map = board.piece_map()
                total_pieces = len(piece_map)
                style_piece_counts.append(total_pieces)

                white_pieces = sum(1 for p in piece_map.values()
                                   if p.color == chess.WHITE)
                black_pieces = sum(1 for p in piece_map.values()
                                   if p.color == chess.BLACK)

                test_case = {
                    "test_id": f"{style_name}_{idx:03d}",
                    "visual_style": style_name,
                    "sample_index": idx,
                    "image_file": str(filepath),
                    "ground_truth": matrix,
                    "statistics": {
                        "total_pieces": total_pieces,
                        "white_pieces": white_pieces,
                        "black_pieces": black_pieces,
                        "density": float(total_pieces / 32),
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
        f"standalone-chess-richness-{timestamp}"

    generator = ChessRichnessDiagnosticTest(output_dir=output_dir)
    test_data = generator.generate_richness_test_suite(n_samples_per_style=10)

    print("\n[DONE]")
