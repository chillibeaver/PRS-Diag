"""Xiangqi Temporal Levels Test Framework"""

from .board_generator import XiangqiBoardGenerator
from .standard_temporal_level import (
    StandardTemporalLevel,
    XiangqiTemporalLevel1,
    XiangqiTemporalLevel2,
    XiangqiTemporalLevel3,
    XiangqiTemporalLevel4,
    XiangqiTemporalLevel5,
    XiangqiTemporalLevel6,
)
from .verification_generator import XiangqiVerificationGenerator

# Predictive generators
from .generators import (
    Level1Generator,
    Level2Generator,
    Level3Generator,
    Level4Generator,
    Level5Generator,
    Level6Generator,
)

# Explicit generators
from .generators import (
    Level1GeneratorExplicit,
    Level2GeneratorExplicit,
    Level3GeneratorExplicit,
    Level4GeneratorExplicit,
    Level5GeneratorExplicit,
    Level6GeneratorExplicit,
)

__all__ = [
    "XiangqiBoardGenerator",
    "StandardTemporalLevel",
    "XiangqiTemporalLevel1",
    "XiangqiTemporalLevel2",
    "XiangqiTemporalLevel3",
    "XiangqiTemporalLevel4",
    "XiangqiTemporalLevel5",
    "XiangqiTemporalLevel6",
    "XiangqiVerificationGenerator",
    # Predictive
    "Level1Generator",
    "Level2Generator",
    "Level3Generator",
    "Level4Generator",
    "Level5Generator",
    "Level6Generator",
    # Explicit
    "Level1GeneratorExplicit",
    "Level2GeneratorExplicit",
    "Level3GeneratorExplicit",
    "Level4GeneratorExplicit",
    "Level5GeneratorExplicit",
    "Level6GeneratorExplicit",
]
