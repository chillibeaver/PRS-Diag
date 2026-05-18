"""
Spatial Test 1: Rule Following Baseline
Tests chess rule application ability (all 6 piece types + castling)
With per-case board recognition verification
"""

from typing import List, Dict
from ..single_state_test_base import SingleStateTestBase
from .with_rule_generator import ChessWithRuleGenerator
from .verification_generator import ChessSingleStateVerificationGenerator
from src.board_generator import ChessBoardGenerator


class ChessWithRuleTest(SingleStateTestBase):
    """Test 1: Chess rule following (all piece types + castling)"""

    N_TYPES = 8

    def __init__(self,
                 base_output_dir: str = "./output/single_state/chess_with_rule",
                 n_cases_per_type: int = None,
                 n_cases: int = 100,
                 seed: int = 42,
                 auto_timestamp: bool = True,
                 rate_limit_requests: int = 0,
                 rate_limit_pause: int = 0):
        """
        Initialize Chess With Rule Test
        """

        if n_cases_per_type is not None:
            n_cases = n_cases_per_type * self.N_TYPES

        super().__init__(
            test_name="Chess With Rule (Legal Moves)",
            test_layer=1,
            base_output_dir=base_output_dir,
            n_cases=n_cases,
            seed=seed,
            auto_timestamp=auto_timestamp,
            rate_limit_requests=rate_limit_requests,
            rate_limit_pause=rate_limit_pause
        )

        self.board_gen = ChessBoardGenerator()
        self.verification_gen = ChessSingleStateVerificationGenerator()

    def generate_test_cases(self) -> List[Dict]:
        """Generate test cases automatically"""
        print(
            f"\nGenerating test cases (n_cases={self.n_cases}, seed={self.seed})")
        print("=" * 60)

        generator = ChessWithRuleGenerator(seed=self.seed)
        cases = generator.generate_all(n_cases=self.n_cases)

        for case in cases:
            verification_info = self.verification_gen.generate_verification(
                case)
            case.update(verification_info)

        self.test_cases = cases
        return cases
