"""Chess Level Generators"""

from .level_1_generator import Level1Generator
from .level_2_generator import Level2Generator
from .level_3_generator import Level3Generator
from .level_4_generator import Level4Generator
from .level_5_generator import Level5Generator
from .level_6_generator import Level6Generator

from .level_1_generator_explicit import Level1Generator as Level1GeneratorExplicit
from .level_2_generator_explicit import Level2Generator as Level2GeneratorExplicit
from .level_3_generator_explicit import Level3Generator as Level3GeneratorExplicit
from .level_4_generator_explicit import Level4Generator as Level4GeneratorExplicit
from .level_5_generator_explicit import Level5Generator as Level5GeneratorExplicit
from .level_6_generator_explicit import Level6Generator as Level6GeneratorExplicit

__all__ = [
    # Predictive generators
    "Level1Generator",
    "Level2Generator",
    "Level3Generator",
    "Level4Generator",
    "Level5Generator",
    "Level6Generator",
    # Explicit generators
    "Level1GeneratorExplicit",
    "Level2GeneratorExplicit",
    "Level3GeneratorExplicit",
    "Level4GeneratorExplicit",
    "Level5GeneratorExplicit",
    "Level6GeneratorExplicit",
]
