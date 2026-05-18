"""
Chess Standard Temporal Level
A generic class to handle any chess temporal level by injecting the specific generator.
Supports two modes: 'predictive' (default) and 'explicit'
"""

from typing import List, Dict, Type, Literal, Optional
from ..temporal_level_base import TemporalLevelBase
from .verification_generator import ChessVerificationGenerator
from .board_generator import ChessBoardGenerator

# Predictive generators
from .generators import (
    Level1Generator,
    Level2Generator,
    Level3Generator,
    Level4Generator,
    Level5Generator,
    Level6Generator,
    Level1GeneratorExplicit,
    Level2GeneratorExplicit,
    Level3GeneratorExplicit,
    Level4GeneratorExplicit,
    Level5GeneratorExplicit,
    Level6GeneratorExplicit,
)

# Generator mapping
_GENERATORS = {
    'predictive': {
        1: Level1Generator,
        2: Level2Generator,
        3: Level3Generator,
        4: Level4Generator,
        5: Level5Generator,
        6: Level6Generator,
    },
    'explicit': {
        1: Level1GeneratorExplicit,
        2: Level2GeneratorExplicit,
        3: Level3GeneratorExplicit,
        4: Level4GeneratorExplicit,
        5: Level5GeneratorExplicit,
        6: Level6GeneratorExplicit,
    }
}

Mode = Literal['predictive', 'explicit']

# ============ Rule Clarifications ============
RULE_CLARIFICATIONS = {
    'en_passant': """Note: En passant capture is legal only when: 
(1) the opponent's pawn has just advanced two squares from its starting position, and 
(2) your pawn is on an adjacent file on the 5th rank (for White) or 4th rank (for Black). 
The capture must be made immediately on the next move, or the right is forfeited.""",

    'castling': """Note: Castling is legal only when all of the following conditions are met: 
(1) the King has never moved, 
(2) the Rook involved has never moved, 
(3) there are no pieces between the King and the Rook, 
(4) the King is not currently in check, 
(5) the King does not pass through a square attacked by an enemy piece, and 
(6) the King does not end up in check.""",
}

# Mapping levels to their rule types
LEVEL_RULE_MAPPING = {
    1: None,           # Basic movement - no special rules
    2: 'en_passant',   # En Passant Basic
    3: None,           # Path Blocked Capture - no special rules needed
    4: 'en_passant',   # En Passant + Constraints
    5: 'castling',     # Castling + 2 Check Rules
    6: 'castling',     # Castling + 3 Check Rules
}


CASE_TYPE_RULE_MAPPING = {
    # Level 1: Basic movement
    'basic_movement': None,
    'basic_movement_predictive': None,

    # Level 2 & 4: En Passant
    'en_passant_temporal': 'en_passant',
    'en_passant_temporal_explicit': 'en_passant',
    'en_passant_constraint': 'en_passant',
    'en_passant_constraint_explicit': 'en_passant',

    # Level 3: Path blocking
    'path_capture_temporal': None,
    'path_capture_temporal_explicit': None,

    # Level 5 & 6: Castling
    'castling_temporal': 'castling',
    'castling_temporal_explicit': 'castling',
}


class StandardTemporalLevel(TemporalLevelBase):
    """
    A generic implementation for Chess Temporal Levels.
    Supports two modes: 'predictive' (default) and 'explicit'
    """

    def __init__(self,
                 level: int,
                 generator_class: Type = None,
                 mode: Mode = 'predictive',
                 base_output_dir: str = None,
                 n_cases: int = 100,
                 seed: int = 42,
                 auto_timestamp: bool = True,
                 rate_limit_requests: int = 0,
                 rate_limit_pause: int = 0,
                 include_rule_clarification: bool = True,
                 **generator_kwargs):
        """
        Initialize Standard Temporal Level for Chess

        Args:
            level: Level number (1-6)
            generator_class: Custom generator class (overrides mode if provided)
            mode: 'predictive' (default) or 'explicit'
            base_output_dir: Output directory
            n_cases: Number of test cases
            seed: Random seed
            auto_timestamp: Append timestamp to output dir
            rate_limit_requests: Rate limiting config
            rate_limit_pause: Rate limiting pause seconds
            include_rule_clarification: Whether to include rule clarifications in prompts
            **generator_kwargs: Extra arguments for generator
        """
        if base_output_dir is None:
            base_output_dir = f"./output/chess_temporal_level_{level}"

        super().__init__(
            level=level,
            base_output_dir=base_output_dir,
            n_cases=n_cases,
            seed=seed,
            auto_timestamp=auto_timestamp,
            rate_limit_requests=rate_limit_requests,
            rate_limit_pause=rate_limit_pause
        )

        # Use provided generator_class, otherwise select based on mode
        if generator_class is not None:
            self.generator_class = generator_class
        else:
            if mode not in _GENERATORS:
                raise ValueError(
                    f"Unknown mode: {mode}. Use 'predictive' or 'explicit'")
            if level not in _GENERATORS[mode]:
                raise ValueError(f"Level {level} not supported")
            self.generator_class = _GENERATORS[mode][level]

        self.mode = mode
        self.generator_kwargs = generator_kwargs
        self.include_rule_clarification = include_rule_clarification

        # Set Chess-specific board generator (required by base class)
        self.board_gen = ChessBoardGenerator()

        # Set Chess-specific verification generator (required by base class)
        self.verification_gen = ChessVerificationGenerator()

    def get_rule_clarification_for_level(self) -> Optional[str]:
        """Get rule clarification based on level number"""
        rule_type = LEVEL_RULE_MAPPING.get(self.level)
        if rule_type:
            return RULE_CLARIFICATIONS.get(rule_type)
        return None

    def get_rule_clarification_for_case(self, case: Dict) -> Optional[str]:
        """Get rule clarification based on case type"""
        case_type = case.get('type', '')
        rule_type = CASE_TYPE_RULE_MAPPING.get(case_type)
        if rule_type:
            return RULE_CLARIFICATIONS.get(rule_type)
        # Fall back to level-based rule
        return self.get_rule_clarification_for_level()

    def get_question_with_rules(self, case: Dict) -> str:
        """
        Get question with rule clarification appended (if enabled).
        Does NOT modify the case dict.

        Args:
            case: Test case dictionary

        Returns:
            Question string, with rules appended if include_rule_clarification is True
        """
        original_question = case.get('question', '')

        if not self.include_rule_clarification:
            return original_question

        clarification = self.get_rule_clarification_for_case(case)
        if clarification:
            return f"{clarification}\n{original_question}"

        return original_question

    def get_full_prompt(self, case: Dict, include_verification: bool = False) -> str:
        """
        Build complete prompt for a test case.

        Args:
            case: Test case dictionary
            include_verification: Whether to include verification question first

        Returns:
            Complete prompt string
        """
        parts = []

        if include_verification:
            verification_q = case.get('verification_question', '')
            if verification_q:
                parts.append(f"First, {verification_q}")
                parts.append("")

        # Main question with rules
        parts.append(self.get_question_with_rules(case))

        return "\n".join(parts)

    def generate_combined_prompt(self, case: Dict) -> str:
        """
        Override base class method to include rule clarifications.
        Generate combined prompt with verification question first, then test question.
        """
        verification_q = case.get('verification_question', '')
        # Use get_question_with_rules instead of case['question'] directly
        test_q = self.get_question_with_rules(case)

        # Count the number of states
        num_states = len(case.get('states', []))

        # Create explicit image-to-state mapping
        if num_states == 1:
            image_ref = "Image 1 shows State 1."
        elif num_states == 2:
            image_ref = "Image 1 shows State 1. Image 2 shows State 2."
        elif num_states == 3:
            image_ref = "Image 1 shows State 1. Image 2 shows State 2. Image 3 shows State 3."
        elif num_states == 4:
            image_ref = "Image 1 shows State 1. Image 2 shows State 2. Image 3 shows State 3. Image 4 shows State 4."
        else:
            image_refs = [
                f"Image {i+1} shows State {i+1}" for i in range(num_states)]
            image_ref = ". ".join(image_refs) + "."

        prompt = f"""Look at these board states carefully.

{image_ref}

The images are shown in chronological order and represent consecutive states.

First, a verification question to ensure you see the states correctly:
{verification_q}

For verification, use this format:
- List pieces as: [Color] [Piece Type] at [square]
- Separate states with semicolons

Now, the main question:
{test_q}

Please answer both questions. Format your response exactly as:
Verification: [your answer]
Main answer: [yes/no/unknown]"""

        return prompt

    def generate_test_cases(self) -> List[Dict]:
        """Generate test cases using the selected generator class"""
        print(
            f"\nGenerating Chess Level {self.level} test cases (mode={self.mode}, n_cases={self.n_cases}, seed={self.seed})")
        print(f"Include rule clarification: {self.include_rule_clarification}")
        print("=" * 60)

        generator = self.generator_class(
            seed=self.seed, **self.generator_kwargs)
        cases = generator.generate_all(n_cases=self.n_cases)

        for case in cases:
            # Add verification info
            case.update(self.verification_gen.generate_verification(case))

        self.test_cases = cases
        return cases


# ============ Helper functions for external use ============

def get_rule_clarification(level: int = None, case_type: str = None) -> Optional[str]:
    """
    Get rule clarification by level or case type.
    Utility function for external use.

    Args:
        level: Level number (1-6)
        case_type: Case type string

    Returns:
        Rule clarification string or None
    """
    rule_type = None

    if case_type:
        rule_type = CASE_TYPE_RULE_MAPPING.get(case_type)

    if rule_type is None and level:
        rule_type = LEVEL_RULE_MAPPING.get(level)

    if rule_type:
        return RULE_CLARIFICATIONS.get(rule_type)

    return None


def build_question_with_rules(case: Dict, level: int = None) -> str:
    """
    Build question with rules for a case.
    Utility function for external use.

    Args:
        case: Test case dictionary
        level: Level number (optional, will infer from case type if not provided)

    Returns:
        Question with rules appended
    """
    original_question = case.get('question', '')
    clarification = get_rule_clarification(
        level=level, case_type=case.get('type'))

    if clarification:
        return f"{original_question}\n\n{clarification}"

    return original_question


# ============ Backward-compatible aliases ============

def _create_level_class(level: int):
    """Create backward-compatible level class with mode support"""

    class _ChessTemporalLevelN(StandardTemporalLevel):
        def __init__(self,
                     base_output_dir: str = None,
                     n_cases: int = 100,
                     seed: int = 42,
                     auto_timestamp: bool = True,
                     rate_limit_requests: int = 0,
                     rate_limit_pause: int = 0,
                     mode: Mode = 'predictive',
                     include_rule_clarification: bool = True):
            super().__init__(
                level=level,
                mode=mode,
                base_output_dir=base_output_dir,
                n_cases=n_cases,
                seed=seed,
                auto_timestamp=auto_timestamp,
                rate_limit_requests=rate_limit_requests,
                rate_limit_pause=rate_limit_pause,
                include_rule_clarification=include_rule_clarification
            )

    _ChessTemporalLevelN.__name__ = f"ChessTemporalLevel{level}"
    _ChessTemporalLevelN.__qualname__ = f"ChessTemporalLevel{level}"
    return _ChessTemporalLevelN


ChessTemporalLevel1 = _create_level_class(1)
ChessTemporalLevel2 = _create_level_class(2)
ChessTemporalLevel3 = _create_level_class(3)
ChessTemporalLevel4 = _create_level_class(4)
ChessTemporalLevel5 = _create_level_class(5)
ChessTemporalLevel6 = _create_level_class(6)

# Legacy aliases for backward compatibility
TemporalLevel1 = ChessTemporalLevel1
TemporalLevel2 = ChessTemporalLevel2
TemporalLevel3 = ChessTemporalLevel3
TemporalLevel4 = ChessTemporalLevel4
TemporalLevel5 = ChessTemporalLevel5
TemporalLevel6 = ChessTemporalLevel6
