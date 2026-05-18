"""
Unified model configurations for all perception tests.

Updated to use Environment Variables for security and specific user preferences.
"""

import os
from dotenv import load_dotenv
load_dotenv()


def get_env_variable(var_name, default=None):
    value = os.getenv(var_name, default)
    if value is None:
        # Warning: Using a placeholder if key is missing to prevent immediate crash on import,
        # but execution will fail if this specific model is used.
        return "YOUR_API_KEY_NOT_SET"
    return value

# --- API Keys & Base URLs (Loaded from Environment) ---


# Novita AI
NOVITA_API_KEY = get_env_variable("NOVITA_API_KEY")
NOVITA_BASE_URL = os.getenv("NOVITA_BASE_URL", "https://api.novita.ai/openai")

# DashScope
DASHSCOPE_API_KEY = get_env_variable("DASHSCOPE_API_KEY")
DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")

# OpenAI
OPENAI_API_KEY = get_env_variable("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# SiliconFlow
SILICONFLOW_API_KEY = get_env_variable("SILICONFLOW_API_KEY")
SILICONFLOW_BASE_URL = os.getenv(
    "SILICONFLOW_BASE_URL", "https://api.siliconflow.com/v1")


MODEL_CONFIGS = {

    # --- Novita AI Models ---
    "gemma": {
        "api_key": NOVITA_API_KEY,
        "base_url": NOVITA_BASE_URL,
        "model_name": "google/gemma-3-27b-it",
    },
    "glm46": {
        "api_key": NOVITA_API_KEY,
        "base_url": NOVITA_BASE_URL,
        "model_name": "zai-org/glm-4.6v",
    },
    "qwen235b": {
        "api_key": NOVITA_API_KEY,
        "base_url": NOVITA_BASE_URL,
        "model_name": "qwen/qwen3-vl-235b-a22b-thinking",
    },
    "qwen30b": {
        "api_key": NOVITA_API_KEY,
        "base_url": NOVITA_BASE_URL,
        "model_name": "qwen/qwen3-vl-30b-a3b-thinking",
    },

    # --- DashScope Models ---
    "qwen8b": {
        "api_key": DASHSCOPE_API_KEY,
        "base_url": DASHSCOPE_BASE_URL,
        "model_name": "qwen3-vl-8b-thinking",
    },

    # --- OpenAI Models ---
    "gpt": {
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
        "model_name": "gpt-5.2-2025-12-11",
        "reasoning_effort": "low",
    },
}
