"""
Unified Test Runner
Supports both Single-State and Multi-States tests for Chess and Xiangqi.
"""

from src.model_client import (
    DummyModelClient, NovitaModelClient, DashScopeModelClient,
    XAIModelClient, GoogleModelClient, AnthropicModelClient, OpenAIModelClient,
    OpenRouterModelClient
)
from src.multi_state.xiangqi import XiangqiNoRuleTest as XiangqiMultiNoRule, XiangqiWithRuleTest as XiangqiMultiWithRule
from src.multi_state.chess import ChessNoRuleTest as ChessMultiNoRule, ChessWithRuleTest as ChessMultiWithRule
from src.single_state.xiangqi import XiangqiNoRuleTest as XiangqiSingleNoRule, XiangqiWithRuleTest as XiangqiSingleWithRule
from src.single_state.chess import ChessNoRuleTest as ChessSingleNoRule, ChessWithRuleTest as ChessSingleWithRule
import sys
import argparse
from typing import Dict, Any

sys.path.append('.')


# ===== Configuration =====

GAME_CONFIGS = {
    "chess": {
        "name": "Chess",
        "single": {
            0: {"id": "no-rule", "name": "Single-State No Rule", "class": ChessSingleNoRule, "default_cases": 100},
            1: {"id": "with-rule", "name": "Single-State With Rule", "class": ChessSingleWithRule, "default_cases": 100},
        },
        "multi": {
            0: {"id": "no-rule", "name": "Multi-State No Rule", "class": ChessMultiNoRule, "default_cases": 100},
            1: {"id": "with-rule", "name": "Multi-State With Rule", "class": ChessMultiWithRule, "default_cases": 100},
        }
    },
    "xiangqi": {
        "name": "Xiangqi",
        "single": {
            0: {"id": "no-rule", "name": "Single-State No Rule", "class": XiangqiSingleNoRule, "default_cases": 100},
            1: {"id": "with-rule", "name": "Single-State With Rule", "class": XiangqiSingleWithRule, "default_cases": 100},
        },
        "multi": {
            0: {"id": "no-rule", "name": "Multi-State No Rule", "class": XiangqiMultiNoRule, "default_cases": 100},
            1: {"id": "with-rule", "name": "Multi-State With Rule", "class": XiangqiMultiWithRule, "default_cases": 100},
        }
    }
}

MODEL_CLIENTS = {
    "dummy": DummyModelClient,
    "novita": NovitaModelClient,
    "dashscope": DashScopeModelClient,
    "xai": XAIModelClient,
    "google": GoogleModelClient,
    "anth": AnthropicModelClient,
    "openai": OpenAIModelClient,
    "openrouter": OpenRouterModelClient
}


def get_model_client(model_type: str):
    if model_type not in MODEL_CLIENTS:
        raise ValueError(f"Unknown model type: {model_type}")
    return MODEL_CLIENTS[model_type]()


def run_test(game: str, mode: str, test_id: int, n_cases: int = None,
             seed: int = 42, model_client=None, output_base: str = "./output",
             rate_limit_requests: int = 0, rate_limit_pause: int = 0) -> Dict[str, Any]:

    if mode not in GAME_CONFIGS[game]:
        raise ValueError(f"Mode '{mode}' not available for {game}")

    config = GAME_CONFIGS[game][mode][test_id]
    n_cases = n_cases or config["default_cases"]

    clean_id = config['id'].replace('-', '')
    mode_label = "singlestate" if mode == "single" else "multistates"
    target_dir = f"{output_base}/{game}_{mode_label}_{clean_id}"

    test_instance = config["class"](
        base_output_dir=target_dir,
        n_cases=n_cases,
        seed=seed,
        auto_timestamp=True,
        rate_limit_requests=rate_limit_requests,
        rate_limit_pause=rate_limit_pause
    )

    test_instance.generate_test_cases()
    test_instance.create_test_images()

    if isinstance(model_client, DummyModelClient):
        model_client.set_test_cases(test_instance.test_cases)

    results, stats = test_instance.run_test(
        model_client, save_results_flag=True)

    return {
        "game": game, "mode": mode, "test_id": test_id,
        "test_name": config["name"], "stats": stats,
        "output_dir": test_instance.output_dir
    }


def main():
    parser = argparse.ArgumentParser(description="Unified Test Runner")

    parser.add_argument("--mode", "-M", type=str, required=True,
                        choices=["single", "multi", "all"],
                        help="Test mode: single, multi, or all")

    parser.add_argument("-g", "--game", type=str, default="chess",
                        choices=list(GAME_CONFIGS.keys()) + ["all"],
                        help="Game type: chess, xiangqi, or all")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true",
                       help="Run all tests in selected mode(s)")
    group.add_argument("-t", "--test", type=int, choices=[0, 1],
                       help="Test ID (0=No Rule, 1=With Rule)")

    parser.add_argument("-n", "--n-cases", type=int,
                        help="Total number of test cases (distributed across types)")
    parser.add_argument("-s", "--seed", type=int, default=42)
    parser.add_argument("-m", "--model", type=str, default="dummy",
                        choices=MODEL_CLIENTS.keys())
    parser.add_argument("-o", "--output", type=str, default="./output")
    parser.add_argument("--rate-limit", type=int, default=0)
    parser.add_argument("--rate-pause", type=int, default=0)

    args = parser.parse_args()

    # Determine games to run
    games = list(GAME_CONFIGS.keys()) if args.game == "all" else [args.game]

    # Determine tests to run
    tests = [0, 1] if args.all else [args.test]

    model_client = get_model_client(args.model)

    print(
        f"Starting Tests | Games: {games} | Mode: {args.mode} | Tests: {tests}")
    print("=" * 60)

    summaries = []
    for game in games:
        # Determine modes to run for this game
        if args.mode == "all":
            modes = [m for m in ["single", "multi"]
                     if m in GAME_CONFIGS[game]]
        else:
            if args.mode not in GAME_CONFIGS[game]:
                print(
                    f"Warning: Mode '{args.mode}' not available for {game}, skipping...")
                continue
            modes = [args.mode]

        for mode in modes:
            for t_id in tests:
                try:
                    s = run_test(game, mode, t_id, args.n_cases, args.seed,
                                 model_client, args.output, args.rate_limit, args.rate_pause)
                    summaries.append(s)
                except Exception as e:
                    print(f"ERROR [{game}][{mode}][{t_id}]: {e}")
                    import traceback
                    traceback.print_exc()

    print("\n" + "=" * 60)
    print("COMPLETION SUMMARY")
    print("=" * 60)
    for s in summaries:
        stats = s['stats']
        total = stats['total']
        acc = stats['test_correct'] / total if total > 0 else 0
        ver = stats['verification_passed'] / total if total > 0 else 0
        print(
            f"[{s['game'].upper()}] {s['test_name']:<30} | Recog: {ver:.1%} | Acc: {acc:.1%}")


if __name__ == "__main__":
    main()
