"""
Xiangqi With Rule Multi-State Test
Tests temporal Xiangqi rule application (Flying General, Perpetual Check, etc.)
"""

from typing import List, Dict
from ..multi_state_test_base import MultiStateTestBase
from .with_rule_generator import XiangqiWithRuleGenerator
from .verification_generator import XiangqiMultiStateVerificationGenerator

# Import board generator from temporal_levels
from src.temporal_levels.xiangqi import XiangqiBoardGenerator


class XiangqiWithRuleTest(MultiStateTestBase):
    """Test 1: Temporal rule following"""

    def __init__(self,
                 base_output_dir: str = "./output/multi_state/xiangqi_with_rule",
                 n_cases: int = 100,
                 n_cases_per_type: int = None,
                 seed: int = 42,
                 auto_timestamp: bool = True,
                 rate_limit_requests: int = 0,
                 rate_limit_pause: int = 0):

        super().__init__(
            test_name="Xiangqi With Rule (Temporal)",
            test_layer=1,
            base_output_dir=base_output_dir,
            n_cases=n_cases,
            n_cases_per_type=n_cases_per_type,
            seed=seed,
            auto_timestamp=auto_timestamp,
            rate_limit_requests=rate_limit_requests,
            rate_limit_pause=rate_limit_pause
        )

        self.board_gen = XiangqiBoardGenerator()
        self.verification_gen = XiangqiMultiStateVerificationGenerator()

    def generate_test_cases(self) -> List[Dict]:
        print(
            f"\nGenerating test cases (n_cases={self.n_cases}, seed={self.seed})")
        print("=" * 60)

        generator = XiangqiWithRuleGenerator(seed=self.seed)
        cases = generator.generate_all(n_cases=self.n_cases)

        for case in cases:
            verification_info = self.verification_gen.generate_verification(
                case)
            case.update(verification_info)

        self.test_cases = cases
        return cases
