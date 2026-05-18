"""VLM Rule Following Test Framework"""

__version__ = "0.1.0"

from .data_structures import TestResult, TestType, PieceType
from .board_generator import ChessBoardGenerator
from .model_client import (
    ModelClient,
    DummyModelClient,
    NovitaModelClient,
    DashScopeModelClient,
    XAIModelClient,
    SiliconFlowModelClient,
    GoogleModelClient,
    AnthropicModelClient,
    OpenAIModelClient,
    OpenRouterModelClient
)

__all__ = [
    "TestResult",
    "TestType",
    "PieceType",
    "ChessBoardGenerator",
    "ModelClient",
    "DummyModelClient",
    "NovitaModelClient",
    "DashScopeModelClient",
    "XAIModelClient",
    "SiliconFlowModelClient",
    "GoogleModelClient",
    "AnthropicModelClient",
    "OpenAIModelClient",
    "OpenRouterModelClient"
]
