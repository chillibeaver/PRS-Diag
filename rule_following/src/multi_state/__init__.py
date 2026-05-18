"""
Multi-State Tests Module (Game-Agnostic)
"""

from .multi_state_test_base import MultiStateTestBase

# Import Chess multi-state tests
from .chess import (
    ChessNoRuleTest,
    ChessWithRuleTest,
    ChessNoRuleGenerator,
    ChessWithRuleGenerator,
    ChessMultiStateVerificationGenerator,
)

# Import Xiangqi multi-state tests
from .xiangqi import (
    XiangqiNoRuleTest,
    XiangqiWithRuleTest,
    XiangqiNoRuleGenerator,
    XiangqiWithRuleGenerator,
    XiangqiMultiStateVerificationGenerator,
)

__all__ = [
    # Base class
    'MultiStateTestBase',

    # Chess
    'ChessNoRuleTest',
    'ChessWithRuleTest',
    'ChessNoRuleGenerator',
    'ChessWithRuleGenerator',
    'ChessMultiStateVerificationGenerator',

    # Xiangqi
    'XiangqiNoRuleTest',
    'XiangqiWithRuleTest',
    'XiangqiNoRuleGenerator',
    'XiangqiWithRuleGenerator',
    'XiangqiMultiStateVerificationGenerator',
]
