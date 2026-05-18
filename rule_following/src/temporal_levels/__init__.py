"""
Temporal Levels Test Framework

Supports multiple games. Currently implemented:
- chess: Chess piece movement tests
"""

__version__ = "0.2.0"

from .temporal_level_base import TemporalLevelBase

# Import chess module
from .chess import (
    ChessBoardGenerator,
    StandardTemporalLevel,
    ChessTemporalLevel1,
    ChessTemporalLevel2,
    ChessTemporalLevel3,
    ChessTemporalLevel4,
    ChessTemporalLevel5,
    ChessTemporalLevel6,
    ChessVerificationGenerator,
    Level1Generator,
    Level2Generator,
    Level3Generator,
    Level4Generator,
    Level5Generator,
    Level6Generator,
)

# Legacy aliases for backward compatibility
TemporalLevel1 = ChessTemporalLevel1
TemporalLevel2 = ChessTemporalLevel2
TemporalLevel3 = ChessTemporalLevel3
TemporalLevel4 = ChessTemporalLevel4
TemporalLevel5 = ChessTemporalLevel5
TemporalLevel6 = ChessTemporalLevel6
TemporalLevelVerificationGenerator = ChessVerificationGenerator

__all__ = [
    # Base class
    "TemporalLevelBase",

    # Chess classes (new naming)
    "ChessBoardGenerator",
    "StandardTemporalLevel",
    "ChessTemporalLevel1",
    "ChessTemporalLevel2",
    "ChessTemporalLevel3",
    "ChessTemporalLevel4",
    "ChessTemporalLevel5",
    "ChessTemporalLevel6",
    "ChessVerificationGenerator",

    # Chess generators
    "Level1Generator",
    "Level2Generator",
    "Level3Generator",
    "Level4Generator",
    "Level5Generator",
    "Level6Generator",

    # Legacy aliases (backward compatibility)
    "TemporalLevel1",
    "TemporalLevel2",
    "TemporalLevel3",
    "TemporalLevel4",
    "TemporalLevel5",
    "TemporalLevel6",
    "TemporalLevelVerificationGenerator",
]
