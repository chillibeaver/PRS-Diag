"""
Xiangqi Standard Temporal Level
A generic class to handle any Xiangqi temporal level by injecting the specific generator.
Supports two modes: 'predictive' (default) and 'explicit'
"""

from typing import List, Dict, Type, Literal, Optional
from ..temporal_level_base import TemporalLevelBase
from .verification_generator import XiangqiVerificationGenerator
from .board_generator import XiangqiBoardGenerator

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
    'flying_general': """Note: In Xiangqi, the Flying General rule states that: 
(1) the two Kings cannot face each other directly on the same file (column) with no pieces between them, 
(2) if a piece is the only blocker between the two Kings, it cannot move to a position that would expose the Kings to face each other, and 
(3) this rule applies even if the move is otherwise legal.""",
}

# Mapping levels to their rule types
LEVEL_RULE_MAPPING = {
    1: None,              # Basic movement - no special rules
    2: None,              # Complex movement - no special rules
    3: None,              # Capture rules - no special rules
    4: 'flying_general',  # Flying General constraint
    5: 'flying_general',  # Capture constraints (includes Flying General)
    6: None,              # Perpetual check/chase (rules already in generator)
}

# Mapping case types to their rule types
CASE_TYPE_RULE_MAPPING = {
    # Level 1: Basic movement
    'basic_movement': None,

    # Level 2: Complex movement
    'movement_rule': None,

    # Level 3: Capture rules
    'capture_rule': None,

    # Level 4: Flying General
    'flying_general': 'flying_general',
    'pawn_river_crossing': None,

    # Level 5: Capture constraints
    'capture_constraint': 'flying_general',

    # Level 6: Perpetual check/chase (rules already embedded in questions)
    'perpetual_check': None,
    'perpetual_chase': None,
}


class StandardTemporalLevel(TemporalLevelBase):
    """
    A generic implementation for Xiangqi Temporal Levels.
    Supports two modes: 'predictive' (default) and 'explicit'
    """

    def __init__(
        self,
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
        **generator_kwargs
    ):
        """
        Initialize Standard Temporal Level for Xiangqi

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
            base_output_dir = f"./output/xiangqi_temporal_level_{level}"

        super().__init__(
            level=level,
            base_output_dir=base_output_dir,
            n_cases=n_cases,
            seed=seed,
            auto_timestamp=auto_timestamp,
            rate_limit_requests=rate_limit_requests,
            rate_limit_pause=rate_limit_pause
        )

        if generator_class is not None:
            self.generator_class = generator_class
        else:
            if mode not in _GENERATORS:
                raise ValueError(
                    f"Unknown mode: {mode}. Use 'predictive' or 'explicit'")
            if level not in _GENERATORS[mode]:
                raise ValueError(
                    f"Level {level} not yet implemented for Xiangqi")
            self.generator_class = _GENERATORS[mode][level]

        self.mode = mode
        self.generator_kwargs = generator_kwargs
        self.include_rule_clarification = include_rule_clarification
        self.board_gen = XiangqiBoardGenerator()
        self.verification_gen = XiangqiVerificationGenerator()

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
        Get question with rule clarification prepended (if enabled).
        Does NOT modify the case dict.

        Args:
            case: Test case dictionary

        Returns:
            Question string, with rules prepended if include_rule_clarification is True
        """
        original_question = case.get('question', '')

        if not self.include_rule_clarification:
            return original_question

        # Skip if rules already in question (some generators embed rules)
        if 'Flying General' in original_question:
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

First, a simple verification question to make sure you see the states correctly:
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
            f"\nGenerating Xiangqi Level {self.level} test cases (mode={self.mode}, n_cases={self.n_cases}, seed={self.seed})")
        print(f"Include rule clarification: {self.include_rule_clarification}")
        print("=" * 60)

        generator = self.generator_class(
            seed=self.seed, **self.generator_kwargs)
        cases = generator.generate_all(n_cases=self.n_cases)

        for case in cases:
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
        Question with rules prepended
    """
    original_question = case.get('question', '')

    # Skip if rules already in question
    if 'Flying General' in original_question:
        return original_question

    clarification = get_rule_clarification(
        level=level, case_type=case.get('type'))

    if clarification:
        return f"{clarification}\n{original_question}"

    return original_question


# ============ Convenience aliases ============

def _create_level_class(level: int):
    class _XiangqiTemporalLevelN(StandardTemporalLevel):
        def __init__(
            self,
            base_output_dir: str = None,
            n_cases: int = 100,
            seed: int = 42,
            auto_timestamp: bool = True,
            rate_limit_requests: int = 0,
            rate_limit_pause: int = 0,
            mode: Mode = 'predictive',
            include_rule_clarification: bool = True
        ):
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

    _XiangqiTemporalLevelN.__name__ = f"XiangqiTemporalLevel{level}"
    _XiangqiTemporalLevelN.__qualname__ = f"XiangqiTemporalLevel{level}"
    return _XiangqiTemporalLevelN


XiangqiTemporalLevel1 = _create_level_class(1)
XiangqiTemporalLevel2 = _create_level_class(2)
XiangqiTemporalLevel3 = _create_level_class(3)
XiangqiTemporalLevel4 = _create_level_class(4)
XiangqiTemporalLevel5 = _create_level_class(5)
XiangqiTemporalLevel6 = _create_level_class(6)
