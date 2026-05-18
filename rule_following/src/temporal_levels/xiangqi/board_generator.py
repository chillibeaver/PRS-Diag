"""
Chinese Chess (Xiangqi) board image generation utilities
9x10 board with river and palace markings
Uses external piece image files from assets/xiangqi_pieces
"""

from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Optional
import os


class XiangqiBoardGenerator:
    """Generate Xiangqi board images using custom piece PNG files"""

    # Piece symbol to filename mapping
    PIECE_FILES = {
        # Red pieces (uppercase) - 紅方
        'K': 'rk.png',  # Red King (帥)
        'A': 'ra.png',  # Red Advisor (仕)
        'B': 'rb.png',  # Red Bishop (相)
        'N': 'rn.png',  # Red Knight (馬)
        'R': 'rr.png',  # Red Rook (車)
        'C': 'rc.png',  # Red Cannon (炮)
        'P': 'rp.png',  # Red Pawn (兵)
        # Black pieces (lowercase) - 黑方
        'k': 'bk.png',  # Black King (將)
        'a': 'ba.png',  # Black Advisor (士)
        'b': 'bb.png',  # Black Bishop (象)
        'n': 'bn.png',  # Black Knight (馬)
        'r': 'br.png',  # Black Rook (車)
        'c': 'bc.png',  # Black Cannon (砲)
        'p': 'bp.png',  # Black Pawn (卒)
    }

    def __init__(self, square_size: int = 60, pieces_dir: str = None):
        """
        Initialize board generator

        Args:
            square_size: Size of each square in pixels
            pieces_dir: Directory containing piece PNG files
                       If None, defaults to assets/xiangqi_pieces
        """
        self.square_size = square_size
        self.board_width = square_size * 8   # 9 columns = 8 intervals
        self.board_height = square_size * 9  # 10 rows = 9 intervals

        # Find pieces directory
        if pieces_dir is None:
            possible_paths = [
                "assets/xiangqi_pieces",
                "../assets/xiangqi_pieces",
                "../../assets/xiangqi_pieces",
                "../../../assets/xiangqi_pieces",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    pieces_dir = path
                    break
            if pieces_dir is None:
                pieces_dir = "assets/xiangqi_pieces"

        self.pieces_dir = pieces_dir

        # Colors
        self.board_color = '#F5DEB3'       # Wheat color for board
        self.line_color = '#8B4513'        # Brown for lines
        self.highlight_color = '#90EE90'   # Light green for highlights
        self.river_color = '#E6D5AC'       # Slightly different for river

        # Load piece images
        self._load_piece_images()

    def _load_piece_images(self):
        """Load and resize all piece images"""
        self.piece_images = {}
        piece_size = int(self.square_size * 0.9)

        for symbol, filename in self.PIECE_FILES.items():
            filepath = os.path.join(self.pieces_dir, filename)

            if os.path.exists(filepath):
                try:
                    img = Image.open(filepath)
                    img = img.resize((piece_size, piece_size),
                                     Image.Resampling.LANCZOS)
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    self.piece_images[symbol] = img
                except Exception as e:
                    print(
                        f"Warning: Could not load piece image {filename}: {e}")
            else:
                print(f"Warning: Piece image not found: {filepath}")

        if not self.piece_images:
            print(
                "WARNING: No piece images loaded! Check if assets/xiangqi_pieces directory exists.")

    def _get_chinese_font(self, size: int):
        """Try to load a Chinese-capable font"""
        font_paths = [
            # Windows
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/msyh.ttc",
            # macOS
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            # Linux
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]

        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except:
                    continue

        return ImageFont.load_default()

    def _square_to_pixel(self, square: str) -> tuple:
        """Convert board coordinate to pixel position"""
        col = ord(square[0]) - ord('a')  # 0-8
        row = int(square[1])              # 0-9
        return col, row

    def create_board_with_pieces(
        self,
        pieces: Dict[str, str],
        highlighted_squares: Optional[List[str]] = None
    ) -> Image.Image:
        """
        Create a Xiangqi board with pieces

        Args:
            pieces: Piece positions, e.g., {"e0": "K", "e9": "k"}
            highlighted_squares: Squares to highlight

        Returns:
            PIL Image of the board
        """
        highlighted_squares = highlighted_squares or []

        # Asymmetric borders: more space on left/bottom for labels
        border_left = 50
        border_right = 30
        border_top = 30
        border_bottom = 50

        total_width = self.board_width + border_left + border_right
        total_height = self.board_height + border_top + border_bottom

        img = Image.new('RGB', (total_width, total_height), self.board_color)
        draw = ImageDraw.Draw(img)

        # Load fonts
        try:
            coord_font = ImageFont.truetype("arial.ttf", 16)
        except:
            coord_font = ImageFont.load_default()

        # Draw river area (between row 4 and 5)
        river_top = border_top + 4 * self.square_size
        river_bottom = border_top + 5 * self.square_size
        draw.rectangle(
            [border_left, river_top, border_left + self.board_width, river_bottom],
            fill=self.river_color
        )

        # Draw highlighted squares (circles at intersections)
        for sq in highlighted_squares:
            col, row = self._square_to_pixel(sq)
            x = border_left + col * self.square_size
            y = border_top + (9 - row) * self.square_size
            radius = self.square_size // 3
            draw.ellipse(
                [x - radius, y - radius, x + radius, y + radius],
                fill=self.highlight_color,
                outline='#228B22',
                width=2
            )

        # Draw grid lines
        line_width = 2

        # Vertical lines
        for col in range(9):
            x = border_left + col * self.square_size
            # Top half (black side)
            draw.line(
                [(x, border_top), (x, border_top + 4 * self.square_size)],
                fill=self.line_color, width=line_width
            )
            # Bottom half (red side)
            draw.line(
                [(x, border_top + 5 * self.square_size),
                 (x, border_top + 9 * self.square_size)],
                fill=self.line_color, width=line_width
            )

        # Only edge vertical lines cross the river
        for col in [0, 8]:
            x = border_left + col * self.square_size
            draw.line(
                [(x, border_top + 4 * self.square_size),
                 (x, border_top + 5 * self.square_size)],
                fill=self.line_color, width=line_width
            )

        # Horizontal lines
        for row in range(10):
            y = border_top + row * self.square_size
            draw.line(
                [(border_left, y), (border_left + self.board_width, y)],
                fill=self.line_color, width=line_width
            )

        # Draw palace diagonal lines
        # Red palace (bottom, d0-f2)
        palace_red_left = border_left + 3 * self.square_size
        palace_red_right = border_left + 5 * self.square_size
        palace_red_top = border_top + 7 * self.square_size
        palace_red_bottom = border_top + 9 * self.square_size
        draw.line(
            [(palace_red_left, palace_red_bottom),
             (palace_red_right, palace_red_top)],
            fill=self.line_color, width=line_width
        )
        draw.line(
            [(palace_red_left, palace_red_top),
             (palace_red_right, palace_red_bottom)],
            fill=self.line_color, width=line_width
        )

        # Black palace (top, d7-f9)
        palace_black_left = border_left + 3 * self.square_size
        palace_black_right = border_left + 5 * self.square_size
        palace_black_top = border_top
        palace_black_bottom = border_top + 2 * self.square_size
        draw.line(
            [(palace_black_left, palace_black_bottom),
             (palace_black_right, palace_black_top)],
            fill=self.line_color, width=line_width
        )
        draw.line(
            [(palace_black_left, palace_black_top),
             (palace_black_right, palace_black_bottom)],
            fill=self.line_color, width=line_width
        )

        # Draw cannon and pawn position markers
        self._draw_position_markers(draw, border_left, border_top)

        # Draw coordinates - positioned further from board edge
        label_offset = 35  # Distance from board edge to labels

        # Column labels (a-i) at bottom
        for col in range(9):
            x = border_left + col * self.square_size
            draw.text(
                (x, border_top + self.board_height + label_offset),
                chr(ord('a') + col),
                fill='black', font=coord_font, anchor='mm'
            )

        # Row labels (0-9) at left
        for row in range(10):
            y = border_top + (9 - row) * self.square_size
            draw.text(
                (border_left - label_offset, y),
                str(row),
                fill='black', font=coord_font, anchor='mm'
            )

        # Draw border
        draw.rectangle(
            [border_left - 2, border_top - 2, border_left + self.board_width + 2,
             border_top + self.board_height + 2],
            outline=self.line_color, width=3
        )

        # Draw pieces using loaded images
        for square, piece_symbol in pieces.items():
            if piece_symbol not in self.piece_images:
                print(f"Warning: No image for piece '{piece_symbol}'")
                continue

            piece_img = self.piece_images[piece_symbol]
            col, row = self._square_to_pixel(square)

            piece_w, piece_h = piece_img.size
            x = border_left + col * self.square_size - piece_w // 2
            y = border_top + (9 - row) * self.square_size - piece_h // 2

            img.paste(piece_img, (x, y), piece_img)

        return img

    def _draw_position_markers(self, draw: ImageDraw, border_left: int, border_top: int):
        """Draw the small markers at cannon and pawn positions"""
        marker_len = 6
        marker_offset = 4

        marker_positions = [
            # Cannons
            (1, 2, 'all'), (7, 2, 'all'),  # Red cannons
            (1, 7, 'all'), (7, 7, 'all'),  # Black cannons
            # Red pawns
            (0, 3, 'right'), (2, 3, 'all'), (4, 3, 'all'),
            (6, 3, 'all'), (8, 3, 'left'),
            # Black pawns
            (0, 6, 'right'), (2, 6, 'all'), (4, 6, 'all'),
            (6, 6, 'all'), (8, 6, 'left'),
        ]

        for col, row, sides in marker_positions:
            x = border_left + col * self.square_size
            y = border_top + (9 - row) * self.square_size

            if sides in ('all', 'left'):
                # Top-left
                draw.line([(x - marker_offset, y - marker_offset - marker_len),
                          (x - marker_offset, y - marker_offset)],
                          fill=self.line_color, width=1)
                draw.line([(x - marker_offset - marker_len, y - marker_offset),
                          (x - marker_offset, y - marker_offset)],
                          fill=self.line_color, width=1)
                # Bottom-left
                draw.line([(x - marker_offset, y + marker_offset),
                          (x - marker_offset, y + marker_offset + marker_len)],
                          fill=self.line_color, width=1)
                draw.line([(x - marker_offset - marker_len, y + marker_offset),
                          (x - marker_offset, y + marker_offset)],
                          fill=self.line_color, width=1)

            if sides in ('all', 'right'):
                # Top-right
                draw.line([(x + marker_offset, y - marker_offset - marker_len),
                          (x + marker_offset, y - marker_offset)],
                          fill=self.line_color, width=1)
                draw.line([(x + marker_offset, y - marker_offset),
                          (x + marker_offset + marker_len, y - marker_offset)],
                          fill=self.line_color, width=1)
                # Bottom-right
                draw.line([(x + marker_offset, y + marker_offset),
                          (x + marker_offset, y + marker_offset + marker_len)],
                          fill=self.line_color, width=1)
                draw.line([(x + marker_offset, y + marker_offset),
                          (x + marker_offset + marker_len, y + marker_offset)],
                          fill=self.line_color, width=1)

    def create_empty_board(self, highlighted_squares: Optional[List[str]] = None) -> Image.Image:
        """Create an empty Xiangqi board"""
        return self.create_board_with_pieces({}, highlighted_squares)
