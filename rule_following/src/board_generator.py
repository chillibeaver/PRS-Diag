"""
Chess board image generation utilities - Using custom piece images
"""

from PIL import Image, ImageDraw, ImageFont
import chess
from typing import List, Dict, Optional
import os


class ChessBoardGenerator:
    """Generate chess board images using custom piece PNG files"""

    def __init__(self, square_size: int = 80, pieces_dir: str = "assets/pieces"):
        """
        Initialize board generator

        Args:
            square_size: Size of each square in pixels
            pieces_dir: Directory containing piece PNG files
        """
        self.square_size = square_size
        self.board_size = square_size * 8
        self.pieces_dir = pieces_dir

        # Mapping from piece symbols to image filenames
        self.piece_files = {
            'K': 'wk.png',  # White King
            'Q': 'wq.png',  # White Queen
            'R': 'wr.png',  # White Rook
            'B': 'wb.png',  # White Bishop
            'N': 'wn.png',  # White Knight
            'P': 'wp.png',  # White Pawn
            'k': 'bk.png',  # Black King
            'q': 'bq.png',  # Black Queen
            'r': 'br.png',  # Black Rook
            'b': 'bb.png',  # Black Bishop
            'n': 'bn.png',  # Black Knight
            'p': 'bp.png',  # Black Pawn
        }

        # Colors
        self.light_square = '#F0D9B5'
        self.dark_square = '#B58863'
        self.highlight_light = '#FFFF99'
        self.highlight_dark = '#FFCC66'

        # Preload and resize piece images
        self._load_piece_images()

    def _load_piece_images(self):
        """Load and resize all piece images"""
        self.piece_images = {}

        # Calculate piece size (slightly smaller than square for padding)
        piece_size = int(self.square_size * 0.85)

        for symbol, filename in self.piece_files.items():
            filepath = os.path.join(self.pieces_dir, filename)

            if os.path.exists(filepath):
                try:
                    # Load image
                    img = Image.open(filepath)

                    # Resize to fit square (maintaining aspect ratio)
                    img = img.resize((piece_size, piece_size),
                                     Image.Resampling.LANCZOS)

                    # Convert to RGBA if not already
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
                "WARNING: No piece images loaded! Check if assets/pieces directory exists.")

    def create_empty_board(self, highlighted_squares: Optional[List[str]] = None) -> Image.Image:
        """
        Create an empty chess board

        Args:
            highlighted_squares: Squares to highlight, e.g., ["a1", "a8"]

        Returns:
            PIL Image of the chess board
        """
        return self._draw_board(pieces={}, highlighted_squares=highlighted_squares or [])

    def create_board_with_pieces(
        self,
        pieces: Dict[str, str],
        highlighted_squares: Optional[List[str]] = None
    ) -> Image.Image:
        """
        Create a chess board with pieces

        Args:
            pieces: Piece positions, e.g., {"e4": "N", "f6": "n"} 
                   (uppercase=white, lowercase=black)
            highlighted_squares: Squares to highlight

        Returns:
            PIL Image of the chess board
        """
        return self._draw_board(pieces=pieces, highlighted_squares=highlighted_squares or [])

    def _draw_board(self, pieces: Dict[str, str], highlighted_squares: List[str]) -> Image.Image:
        """Draw the complete chess board with pieces"""

        # Create image with border
        border = 30
        total_size = self.board_size + 2 * border
        img = Image.new('RGB', (total_size, total_size), 'white')
        draw = ImageDraw.Draw(img)

        # Try to load font for coordinates
        try:
            coord_font = ImageFont.truetype("arial.ttf", 18)
        except:
            try:
                coord_font = ImageFont.truetype("Arial.ttf", 18)
            except:
                coord_font = ImageFont.load_default()

        # Draw checkerboard
        for row in range(8):
            for col in range(8):
                x1 = border + col * self.square_size
                y1 = border + row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                # Calculate square name (a1 is bottom-left)
                file = chr(ord('a') + col)
                rank = str(8 - row)
                square_name = file + rank

                # Determine square color
                is_light = (row + col) % 2 == 0

                if square_name in highlighted_squares:
                    color = self.highlight_light if is_light else self.highlight_dark
                else:
                    color = self.light_square if is_light else self.dark_square

                # Draw square
                draw.rectangle([x1, y1, x2, y2], fill=color, outline=None)

        # Draw border
        draw.rectangle([border-1, border-1, border + self.board_size, border + self.board_size],
                       outline='black', width=2)

        # Draw coordinates
        for i in range(8):
            # Files (a-h) at bottom
            file_char = chr(ord('a') + i)
            x = border + i * self.square_size + self.square_size // 2
            y = border + self.board_size + 10
            draw.text((x, y), file_char, fill='black',
                      font=coord_font, anchor='mm')

            # Ranks (1-8) at left
            rank_char = str(8 - i)
            x = border - 15
            y = border + i * self.square_size + self.square_size // 2
            draw.text((x, y), rank_char, fill='black',
                      font=coord_font, anchor='mm')

        # Draw pieces using loaded images
        for square_name, piece_symbol in pieces.items():
            try:
                # Check if we have the piece image
                if piece_symbol not in self.piece_images:
                    print(f"Warning: No image for piece '{piece_symbol}'")
                    continue

                piece_img = self.piece_images[piece_symbol]

                # Parse square
                file = ord(square_name[0]) - ord('a')
                rank = int(square_name[1]) - 1

                # Calculate position (rank 1 is at bottom)
                col = file
                row = 7 - rank

                # Calculate top-left corner for piece (centered in square)
                piece_width, piece_height = piece_img.size
                x = border + col * self.square_size + \
                    (self.square_size - piece_width) // 2
                y = border + row * self.square_size + \
                    (self.square_size - piece_height) // 2

                # Paste piece image with transparency
                img.paste(piece_img, (x, y), piece_img)

            except Exception as e:
                print(
                    f"Warning: Could not draw piece {piece_symbol} at {square_name}: {e}")

        return img
