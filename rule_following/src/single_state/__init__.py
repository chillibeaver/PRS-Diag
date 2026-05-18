"""
Single State Tests Module
Contains base classes and game-specific implementations for static board reasoning.
"""

from .single_state_test_base import SingleStateTestBase

# Chess
from .chess import ChessNoRuleTest, ChessWithRuleTest

# Xiangqi
from .xiangqi import XiangqiNoRuleTest, XiangqiWithRuleTest

__all__ = [
    'SingleStateTestBase',
    # Chess
    'ChessNoRuleTest',
    'ChessWithRuleTest',
    # Xiangqi
    'XiangqiNoRuleTest',
    'XiangqiWithRuleTest',
]
