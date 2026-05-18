"""
Run Temporal Levels Tests
Unified script to run any combination of Level 1-6 tests
Supports multiple games: chess, xiangqi
"""

from src.model_client import (
    DummyModelClient, NovitaModelClient, DashScopeModelClient,
    XAIModelClient, GoogleModelClient, AnthropicModelClient, OpenAIModelClient, SiliconFlowModelClient,
    OpenRouterModelClient
)
from src.temporal_levels.xiangqi import (
    XiangqiTemporalLevel1, XiangqiTemporalLevel2, XiangqiTemporalLevel3,
    XiangqiTemporalLevel4, XiangqiTemporalLevel5, XiangqiTemporalLevel6
)
from src.temporal_levels import (
    ChessTemporalLevel1, ChessTemporalLevel2, ChessTemporalLevel3,
    ChessTemporalLevel4, ChessTemporalLevel5, ChessTemporalLevel6
)
import sys
import argparse
import os
import json
from datetime import datetime
from typing import List, Dict, Any

sys.path.append('.')


# ===== Game Configurations =====

GAME_CONFIGS = {
    "chess": {
        "name": "Chess",
        "levels": {
            1: {
                "name": "Basic Movement Rules",
                "class": ChessTemporalLevel1,
                "default_cases": 100,
                "description": "Tests basic movement patterns for all 6 piece types"
            },
            2: {
                "name": "En Passant Basic",
                "class": ChessTemporalLevel2,
                "default_cases": 100,
                "description": "Tests 3 basic conditions for en passant"
            },
            3: {
                "name": "Path Blocked Capture",
                "class": ChessTemporalLevel3,
                "default_cases": 100,
                "description": "Tests capture with path blocking (Rook/Bishop/Queen)"
            },
            4: {
                "name": "En Passant Constraints",
                "class": ChessTemporalLevel4,
                "default_cases": 100,
                "description": "Tests en passant timing and check constraints"
            },
            5: {
                "name": "Castling with 2 Check Rules",
                "class": ChessTemporalLevel5,
                "default_cases": 100,
                "description": "Tests castling legality regarding 2 check constraints"
            },
            6: {
                "name": "Castling with 3 Check Rules",
                "class": ChessTemporalLevel6,
                "default_cases": 100,
                "description": "Tests castling with all 3 check rules"
            },
        }
    },
    "xiangqi": {
        "name": "Chinese Chess (Xiangqi)",
        "levels": {
            1: {
                "name": "Basic Movement",
                "class": XiangqiTemporalLevel1,
                "default_cases": 100,
                "description": "Basic movement validation for Rook and Cannon."
            },
            2: {
                "name": "Move Constraints",
                "class": XiangqiTemporalLevel2,
                "default_cases": 100,
                "description": "Horse legs, Elephant eyes, Palace confinement, and River crossing."
            },
            3: {
                "name": "Capture Rules",
                "class": XiangqiTemporalLevel3,
                "default_cases": 100,
                "description": "Capture logic: Cannon screens, blocking during capture, and Pawn direction."
            },
            4: {
                "name": "Flying General",
                "class": XiangqiTemporalLevel4,
                "default_cases": 100,
                "description": "Tests if a piece blocking two Kings can legally move away."
            },
            5: {
                "name": "Pinned Captures",
                "class": XiangqiTemporalLevel5,
                "default_cases": 100,
                "description": "Capture constraints involving Absolute Pins and Flying General blocks."
            },
            6: {
                "name": "Perpetual Check/Chase",
                "class": XiangqiTemporalLevel6,
                "default_cases": 100,
                "description": "Testing Perpetual Check (长将) and Perpetual Chase (长捉)."
            }
        },
    }
}

# Legacy alias for backward compatibility
LEVEL_CONFIG = GAME_CONFIGS["chess"]["levels"]


def get_model_client(model_type: str, use_dummy: bool = False, dummy_pass_rate: float = 0.8):
    """Get model client based on type"""
    if use_dummy or model_type == 'dummy':
        print(f"\n🤖 Using Dummy Model Client (pass_rate={dummy_pass_rate})")
        return DummyModelClient(verification_pass_rate=dummy_pass_rate)

    if model_type == 'novita':
        print("\n🤖 Using Novita Model Client")
        return NovitaModelClient()
    elif model_type == 'dashscope':
        print("\n🤖 Using DashScope Model Client")
        return DashScopeModelClient()
    elif model_type == 'xai':
        print("\n🤖 Using XAI Model Client")
        return XAIModelClient()
    elif model_type == 'google':
        print("\n🤖 Using Google Model Client")
        return GoogleModelClient()
    elif model_type == 'anth':
        print("\n🤖 Using Anthropic Model Client")
        return AnthropicModelClient()
    elif model_type == 'openai':
        print("\n🤖 Using OpenAI Model Client")
        return OpenAIModelClient()
    elif model_type == 'sf':
        print("\n🤖 Using SiliconFlow Model Client")
        return SiliconFlowModelClient()
    elif model_type == 'openrouter':
        print("\n🤖 Using OpenRouter Model Client")
        return OpenRouterModelClient()
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def get_available_levels(game: str) -> List[int]:
    """Get list of available levels for a game"""
    if game not in GAME_CONFIGS:
        raise ValueError(
            f"Unknown game: {game}. Available: {list(GAME_CONFIGS.keys())}")
    return sorted(GAME_CONFIGS[game]["levels"].keys())


def run_single_level(game: str,
                     level: int,
                     n_cases: int = None,
                     seed: int = 42,
                     model_client=None,
                     output_base: str = "./output",
                     rate_limit_requests: int = 0,
                     rate_limit_pause: int = 0,
                     mode: str = "predictive") -> Dict[str, Any]:
    """Run a single level test"""

    if game not in GAME_CONFIGS:
        raise ValueError(f"Unknown game: {game}")

    game_config = GAME_CONFIGS[game]
    level_configs = game_config["levels"]

    if level not in level_configs:
        raise ValueError(f"Level {level} not implemented for {game}")

    config = level_configs[level]
    n_cases = n_cases or config["default_cases"]

    print("\n" + "=" * 70)
    print(f"GAME: {game_config['name']}")
    print(f"LEVEL {level}: {config['name']}")
    print(f"Description: {config['description']}")
    print(f"Mode: {mode}")
    print(f"Test cases: {n_cases}")
    print("=" * 70)

    # Initialize test
    test_class = config["class"]
    test = test_class(
        base_output_dir=f"{output_base}/{game}_temporal_level_{level}",
        n_cases=n_cases,
        seed=seed,
        auto_timestamp=True,
        rate_limit_requests=rate_limit_requests,
        rate_limit_pause=rate_limit_pause,
        mode=mode
    )

    # Generate test cases
    test.generate_test_cases()

    # Create images
    test.create_test_images()

    # Set test cases for dummy model
    if isinstance(model_client, DummyModelClient):
        model_client.set_test_cases(test.test_cases)

    # Run test
    results, stats = test.run_test(model_client, save_results_flag=True)

    return {
        "game": game,
        "level": level,
        "name": config["name"],
        "stats": stats,
        "output_dir": test.output_dir,
        "model_name": model_client.model_name
    }


def save_suite_summary(all_results: List[Dict[str, Any]], output_base: str, game: str, mode: str):
    """Save a summary of all levels to a JSON file"""
    os.makedirs(output_base, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "game": game,
        "game_name": GAME_CONFIGS[game]["name"],
        "model_name": all_results[0]["model_name"] if all_results else "unknown",
        "mode": mode,
        "levels_run": len(all_results),
        "results": []
    }

    print("\n" + "=" * 70)
    print(f"SUMMARY - {GAME_CONFIGS[game]['name']}")
    print("=" * 70)

    for res in all_results:
        level = res["level"]
        name = res["name"]
        stats = res["stats"]

        verification_rate = stats['verification_passed'] / \
            stats['total'] if stats['total'] > 0 else 0
        accuracy_verified = stats['test_correct_given_verified'] / \
            stats['verification_passed'] if stats['verification_passed'] > 0 else 0
        overall_accuracy = stats['test_correct'] / \
            stats['total'] if stats['total'] > 0 else 0

        level_summary = {
            "level": level,
            "name": name,
            "total_cases": stats['total'],
            "verification_rate": round(verification_rate, 3),
            "accuracy_given_verified": round(accuracy_verified, 3),
            "overall_accuracy": round(overall_accuracy, 3),
            "output_dir": res["output_dir"],
            "details": stats
        }
        summary_data["results"].append(level_summary)

        print(f"\nLevel {level}: {name}")
        print(f"  Total cases: {stats['total']}")
        print(f"  Verification rate: {verification_rate:.1%}")
        print(f"  Accuracy (verified cases): {accuracy_verified:.1%}")
        print(f"  Overall accuracy: {overall_accuracy:.1%}")
        print(f"  Output: {res['output_dir']}")

    filename = f"{game}_temporal_levels_summary_{mode}_{timestamp}.json"
    filepath = os.path.join(output_base, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        print("\n" + "=" * 70)
        print(f"✅ All tests completed!")
        print(f"📄 Suite summary saved to: {filepath}")
        print("=" * 70)
    except Exception as e:
        print(f"\n⚠️ Failed to save summary file: {e}")


def run_multiple_levels(game: str,
                        levels: List[int],
                        n_cases: int = None,
                        seed: int = 42,
                        model_type: str = "dummy",
                        use_dummy: bool = False,
                        dummy_pass_rate: float = 0.8,
                        output_base: str = "./output",
                        rate_limit_requests: int = 0,
                        rate_limit_pause: int = 0,
                        mode: str = "predictive") -> List[Dict[str, Any]]:
    """Run multiple level tests for a specific game"""

    if game not in GAME_CONFIGS:
        raise ValueError(
            f"Unknown game: {game}. Available: {list(GAME_CONFIGS.keys())}")

    game_config = GAME_CONFIGS[game]
    available_levels = get_available_levels(game)

    # Validate levels
    levels_to_run = []
    for level in levels:
        if level in available_levels:
            levels_to_run.append(level)
        else:
            print(
                f"⚠️  Warning: Level {level} not implemented for {game}, skipping...")

    if not levels_to_run:
        print("❌ No valid levels to run!")
        return []

    print("\n" + "=" * 70)
    print(f"TEMPORAL LEVELS TEST SUITE - {game_config['name']}")
    print("=" * 70)
    print(f"Game: {game}")
    print(f"Levels to run: {levels_to_run}")
    print(f"Available levels: {available_levels}")
    print(f"Mode: {mode}")
    print(f"Random seed: {seed}")
    print(f"Output directory: {output_base}")
    if rate_limit_requests > 0:
        print(
            f"Rate limiting: {rate_limit_requests} requests, {rate_limit_pause}s pause")
    print("=" * 70)

    # Initialize model client
    model_client = get_model_client(model_type, use_dummy, dummy_pass_rate)

    # Run each level
    all_results = []
    for level in levels_to_run:
        try:
            result = run_single_level(
                game=game,
                level=level,
                n_cases=n_cases,
                seed=seed,
                model_client=model_client,
                output_base=output_base,
                rate_limit_requests=rate_limit_requests,
                rate_limit_pause=rate_limit_pause,
                mode=mode
            )
            all_results.append(result)
        except Exception as e:
            print(f"\n❌ Error running Level {level}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Save summary
    save_suite_summary(all_results, output_base, game, mode)

    return all_results


def main():
    parser = argparse.ArgumentParser(
        description="Run Temporal Levels Tests for Chess or Xiangqi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Game selection
    parser.add_argument(
        "-g", "--game",
        type=str,
        choices=list(GAME_CONFIGS.keys()),
        default="chess",
        help="Game to test: chess or xiangqi (default: chess)"
    )

    # Level selection
    level_group = parser.add_mutually_exclusive_group()
    level_group.add_argument(
        "-l", "--levels",
        type=int,
        nargs="+",
        help="Levels to run (e.g., -l 1 2 3)"
    )
    level_group.add_argument(
        "--all",
        action="store_true",
        help="Run all available levels for the selected game"
    )
    level_group.add_argument(
        "--list",
        action="store_true",
        help="List available levels for the selected game and exit"
    )

    # Test configuration
    parser.add_argument(
        "-n", "--n-cases",
        type=int,
        default=None,
        help="Number of test cases per level (default: use level defaults)"
    )
    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="./output",
        help="Output directory (default: ./output)"
    )

    # Mode selection
    parser.add_argument(
        "--mode",
        type=str,
        choices=["predictive", "explicit"],
        default="predictive",
        help="Test mode: predictive (default) or explicit"
    )

    # Model selection
    parser.add_argument(
        "-m", "--model",
        type=str,
        choices=["dummy", "novita", "dashscope",
                 "xai", "google", "anth", "openai", "sf"],
        default="dummy",
        help="Model type to use (default: dummy)"
    )
    parser.add_argument(
        "--dummy-pass-rate",
        type=float,
        default=0.8,
        help="Pass rate for dummy model (default: 0.8)"
    )

    # Rate limiting
    parser.add_argument(
        "--rate-limit",
        type=int,
        default=0,
        help="Number of requests before pausing (0 = no limit)"
    )
    parser.add_argument(
        "--rate-pause",
        type=int,
        default=0,
        help="Seconds to pause when rate limit reached"
    )

    args = parser.parse_args()

    # Handle --list option
    if args.list:
        game = args.game
        game_config = GAME_CONFIGS[game]
        print(f"\n{game_config['name']} - Available Levels:")
        print("=" * 70)
        for level, config in sorted(game_config["levels"].items()):
            print(f"  Level {level}: {config['name']}")
            print(f"           {config['description']}")
        print("=" * 70)
        return

    # Require level selection if not --list
    if not args.levels and not args.all:
        parser.error("Please specify levels with -l/--levels or use --all")

    # Determine which levels to run
    if args.all:
        levels = get_available_levels(args.game)
    else:
        levels = sorted(args.levels)

    # Run tests
    run_multiple_levels(
        game=args.game,
        levels=levels,
        n_cases=args.n_cases,
        seed=args.seed,
        model_type=args.model,
        use_dummy=(args.model == "dummy"),
        dummy_pass_rate=args.dummy_pass_rate,
        output_base=args.output,
        rate_limit_requests=args.rate_limit,
        rate_limit_pause=args.rate_pause,
        mode=args.mode
    )


if __name__ == "__main__":
    main()
