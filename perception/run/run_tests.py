"""
Unified Test Entry Point for VLM Perception Tests.

Routes to appropriate test runners based on --test argument.

"""

import argparse
import sys
from pathlib import Path
from importlib import import_module
import time

# Add project root to path BEFORE any local imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Lazy Loading
# ============================================================================

_MODEL_CONFIGS = None


def get_model_configs():
    """Lazy load MODEL_CONFIGS to avoid import order issues."""
    global _MODEL_CONFIGS
    if _MODEL_CONFIGS is None:
        from shared.model_configs import MODEL_CONFIGS
        _MODEL_CONFIGS = MODEL_CONFIGS
    return _MODEL_CONFIGS


# ============================================================================
# Test Registry
# ============================================================================

TEST_REGISTRY = {
    "density": {
        "module": "tests.density.density_runner",
        "description": "Board density effect on VLM perception (low/medium/high piece count)",
    },
    "patch": {
        "module": "tests.patch.patch_runner",
        "description": "Patch alignment effect on VLM perception (boundary/center offset testing)",
    },
    "resolution": {
        "module": "tests.resolution.resolution_runner",
        "description": "Image resolution effect on VLM perception",
    },
    "richness": {
        "module": "tests.richness.richness_runner",
        "description": "Visual richness effect on VLM perception",
    },
}


# ============================================================================
# Helper Functions
# ============================================================================

def load_test_module(test_name: str):
    """Dynamically import a test runner module."""
    if test_name not in TEST_REGISTRY:
        raise ValueError(f"Unknown test: {test_name}")

    module_path = TEST_REGISTRY[test_name]["module"]
    try:
        return import_module(module_path)
    except ImportError as e:
        raise ImportError(f"Failed to import {module_path}: {e}")


def list_tests():
    """Print available test types."""
    print("\n📋 Available test types:")
    print("-" * 60)
    for name, info in TEST_REGISTRY.items():
        print(f"  {name:<15} {info['description']}")
    print(f"  {'all':<15} Run all tests above")
    print()


def list_models():
    """Print available models."""
    configs = get_model_configs()
    print("\n🤖 Available models:")
    print("-" * 60)
    print(f"  {'dummy':<30}")
    for key, config in configs.items():
        print(f"  {key:<30} {config['model_name']}")
    print()


def list_games_for_test(test_name: str):
    """Print available games for a specific test type."""
    if test_name == "all":
        print("\n🎮 Available games (common across all tests):")
        print("-" * 40)
        print("  chess")
        print("  gomoku")
        print()
        return

    module = load_test_module(test_name)
    games = module.get_available_games()
    print(f"\n🎮 Available games for '{test_name}' test:")
    print("-" * 40)
    for game in games:
        print(f"  {game}")
    print()


def get_common_games() -> list:
    """Get games that are available across all tests."""
    common_games = None
    for test_name in TEST_REGISTRY.keys():
        module = load_test_module(test_name)
        games = set(module.get_available_games())
        if common_games is None:
            common_games = games
        else:
            common_games = common_games & games
    return sorted(list(common_games)) if common_games else []


def run_all_tests(game: str, model: str, samples: int, output_dir: Path = None,
                  rate_limit: int = 0, rate_pause: float = 0):
    """Run all tests with common parameters."""
    results = {}
    test_names = list(TEST_REGISTRY.keys())

    for i, test_name in enumerate(test_names):
        # pause betwen tests if rate_pause is set
        if i > 0 and rate_pause > 0:
            print(
                f"\n[BETWEEN TESTS] Pausing for {rate_pause}s before '{test_name}' test...")
            time.sleep(rate_pause)

        print(f"\n{'#'*70}")
        print(f"# TEST: {test_name.upper()}")
        print(f"{'#'*70}")

        try:
            module = load_test_module(test_name)

            # Build test-specific kwargs
            kwargs = {"game": game, "model": model}

            # Map common 'samples' to test-specific parameter
            if test_name == "density":
                kwargs["samples"] = samples
            elif test_name == "patch":
                kwargs["samples"] = samples
            elif test_name == "resolution":
                kwargs["samples"] = samples
            elif test_name == "richness":
                kwargs["samples"] = samples

            # Add output_dir if specified
            if output_dir:
                kwargs["output_dir"] = output_dir

            # Add rate limiting parameters
            kwargs["rate_limit"] = rate_limit
            kwargs["rate_pause"] = rate_pause

            result = module.run(**kwargs)
            results[test_name] = {"status": "success", "result": result}

        except Exception as e:
            print(f"\n[ERROR] {test_name} test failed: {e}")
            results[test_name] = {"status": "failed", "error": str(e)}

    # Print summary
    print(f"\n{'='*70}")
    print("ALL TESTS SUMMARY")
    print(f"{'='*70}")
    for test_name, result in results.items():
        status = "✓" if result["status"] == "success" else "✗"
        print(f"  {status} {test_name:<15} {result['status']}")
    print(f"{'='*70}\n")

    return results


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    # First pass: parse just the test type and info flags
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--test", "-t", type=str)
    pre_parser.add_argument("--list-tests", action="store_true")
    pre_parser.add_argument("--list-models", action="store_true")
    pre_parser.add_argument("--list-games", action="store_true")

    pre_args, remaining = pre_parser.parse_known_args()

    # Handle info flags
    if pre_args.list_tests:
        list_tests()
        return

    if pre_args.list_models:
        list_models()
        return

    if pre_args.list_games:
        if not pre_args.test:
            print("Error: --list-games requires --test <test_type>")
            print("Example: python run_tests.py --test density --list-games")
            sys.exit(1)
        list_games_for_test(pre_args.test)
        return

    # Validate test type is provided
    if not pre_args.test:
        print("Error: --test is required")
        print("\nUsage: python run_tests.py --test <test_type>")
        print("\nUse --list-tests to see available test types")
        sys.exit(1)

    all_test_choices = list(TEST_REGISTRY.keys()) + ["all"]
    if pre_args.test not in all_test_choices:
        print(f"Error: Unknown test type '{pre_args.test}'")
        list_tests()
        sys.exit(1)

    # Handle --test all
    if pre_args.test == "all":
        configs = get_model_configs()
        common_games = get_common_games()

        parser = argparse.ArgumentParser(
            description="VLM Perception Test Runner - ALL TESTS",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python run/run_tests.py --test all --game chess --model dummy
  python run/run_tests.py --test all --game all --model qwen30b --samples 50
  python run/run_tests.py --test all --game chess -o ./my_results/
  python run/run_tests.py --test all --game chess --rate-limit 10 --rate-pause 60
            """
        )

        parser.add_argument("--test", "-t", required=True)
        parser.add_argument(
            "--game", "-g",
            choices=common_games + ["all"],
            default=common_games[0] if common_games else "chess",
            help=f"Game type to test (default: {common_games[0] if common_games else 'chess'})"
        )
        parser.add_argument(
            "--model", "-m",
            choices=list(configs.keys()) + ["dummy"],
            default="dummy",
            help="Model to use for testing (default: dummy)"
        )
        parser.add_argument(
            "--samples", "-n",
            type=int,
            default=100,
            help="Number of samples per test condition (default: 100)"
        )
        parser.add_argument(
            "--output", "-o",
            type=str,
            default=None,
            help="Output directory for all results (default: auto-generated in project root)"
        )
        parser.add_argument(
            "--rate-limit",
            type=int,
            default=0,
            help="Number of requests to process before pausing. 0 means no limit (default: 0)"
        )
        parser.add_argument(
            "--rate-pause",
            type=float,
            default=0,
            help="Duration in seconds to pause when the rate limit is reached (default: 0)"
        )
        parser.add_argument("--list-tests", action="store_true")
        parser.add_argument("--list-models", action="store_true")
        parser.add_argument("--list-games", action="store_true")

        args = parser.parse_args()

        # Process output directory
        output_dir = None
        if args.output:
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)

        # Print header
        print("\n" + "=" * 70)
        print("VLM PERCEPTION TEST - ALL TESTS")
        print("=" * 70)
        if args.game == "all":
            print(f"  Game:      all ({', '.join(common_games)})")
        else:
            print(f"  Game:      {args.game}")
        if args.model == "dummy":
            print(f"  Model:     dummy")
        else:
            print(
                f"  Model:     {args.model} ({configs[args.model]['model_name']})")
        print(f"  Samples:   {args.samples} per condition")
        print(f"  Tests:     {', '.join(TEST_REGISTRY.keys())}")
        if args.rate_limit > 0:
            print(
                f"  Rate Limit: {args.rate_limit} requests, then pause {args.rate_pause}s")
        if output_dir:
            print(f"  Output:    {output_dir.absolute()}")
        else:
            print(f"  Output:    (auto-generated)")
        print("=" * 70)

        # Run all tests
        if args.game == "all":
            for game in common_games:
                print(f"\n{'#'*70}")
                print(f"# GAME: {game.upper()}")
                print(f"{'#'*70}")

                # Create game-specific output dir if output_dir specified
                game_output_dir = output_dir / game if output_dir else None
                if game_output_dir:
                    game_output_dir.mkdir(parents=True, exist_ok=True)

                run_all_tests(
                    game=game, model=args.model, samples=args.samples,
                    output_dir=game_output_dir,
                    rate_limit=args.rate_limit, rate_pause=args.rate_pause
                )
        else:
            run_all_tests(
                game=args.game, model=args.model, samples=args.samples,
                output_dir=output_dir,
                rate_limit=args.rate_limit, rate_pause=args.rate_pause
            )

        print("\n[OK] All tests complete!")
        if output_dir:
            print(f"[OK] Results saved to: {output_dir.absolute()}")
        return

    # Load the test module and model configs (for single test)
    test_module = load_test_module(pre_args.test)
    available_games = test_module.get_available_games()
    test_specific_args = test_module.get_test_specific_args()
    configs = get_model_configs()

    # Build full parser with test-specific arguments
    parser = argparse.ArgumentParser(
        description=f"VLM Perception Test Runner - {pre_args.test.upper()}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python run/run_tests.py --test {pre_args.test}
  python run/run_tests.py --test {pre_args.test} --game {available_games[0]} --model qwen30b
  python run/run_tests.py --test {pre_args.test} -o ./my_output/
  python run/run_tests.py --test {pre_args.test} --rate-limit 10 --rate-pause 60
  python run/run_tests.py --test all --game chess --samples 50
  python run/run_tests.py --list-models
        """
    )

    # Common arguments
    parser.add_argument(
        "--test", "-t",
        choices=all_test_choices,
        required=True,
        help="Test type to run (use 'all' for all tests)"
    )

    parser.add_argument(
        "--game", "-g",
        choices=available_games + ["all"],
        default=available_games[0],
        help=f"Game type to test, or 'all' for all games (default: {available_games[0]})"
    )

    parser.add_argument(
        "--model", "-m",
        choices=list(configs.keys()) + ["dummy"],
        default="dummy",
        help="Model to use for testing (default: dummy)"
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory for results (default: auto-generated in project root)"
    )

    # Rate limiting arguments
    parser.add_argument(
        "--rate-limit",
        type=int,
        default=0,
        help="Number of requests to process before pausing. 0 means no limit (default: 0)"
    )

    parser.add_argument(
        "--rate-pause",
        type=float,
        default=0,
        help="Duration in seconds to pause when the rate limit is reached (default: 0)"
    )

    # Info flags (already handled, but needed for help)
    parser.add_argument("--list-tests", action="store_true",
                        help="List available test types")
    parser.add_argument("--list-models", action="store_true",
                        help="List available models")
    parser.add_argument("--list-games", action="store_true",
                        help="List available games for this test")

    # Add test-specific arguments
    for arg_def in test_specific_args:
        parser.add_argument(*arg_def["name"], **arg_def["kwargs"])

    # Parse all arguments
    args = parser.parse_args()

    # Convert to dict and remove common args
    args_dict = vars(args)
    test_name = args_dict.pop("test")
    game = args_dict.pop("game")
    model = args_dict.pop("model")
    output = args_dict.pop("output")
    rate_limit = args_dict.pop("rate_limit")
    rate_pause = args_dict.pop("rate_pause")

    # Remove info flags
    args_dict.pop("list_tests", None)
    args_dict.pop("list_models", None)
    args_dict.pop("list_games", None)

    # Process output directory
    output_dir = None
    if output:
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
        args_dict["output_dir"] = output_dir

    # Add rate limiting to args_dict
    args_dict["rate_limit"] = rate_limit
    args_dict["rate_pause"] = rate_pause

    # Print header
    print("\n" + "=" * 70)
    print("VLM PERCEPTION TEST")
    print("=" * 70)
    print(f"  Test Type: {test_name}")
    if game == "all":
        print(f"  Game:      all ({', '.join(available_games)})")
    else:
        print(f"  Game:      {game}")
    if model == "dummy":
        print(f"  Model:     dummy")
    else:
        print(f"  Model:     {model} ({configs[model]['model_name']})")
    if rate_limit > 0:
        print(f"  Rate Limit: {rate_limit} requests, then pause {rate_pause}s")
    if output_dir:
        print(f"  Output:    {output_dir.absolute()}")
    else:
        print(f"  Output:    (auto-generated)")
    if args_dict:
        # Filter out output_dir and rate params from display since we showed them above
        display_dict = {k: v for k, v in args_dict.items()
                        if k not in ["output_dir", "rate_limit", "rate_pause"]}
        if display_dict:
            print(f"  Options:   {display_dict}")
    print("=" * 70)

    # Run the test
    if game == "all":
        for g in available_games:
            print(f"\n{'#'*70}")
            print(f"# Running: {g.upper()}")
            print(f"{'#'*70}")

            # Create game-specific output dir if output_dir specified
            if output_dir:
                game_output_dir = output_dir / g
                game_output_dir.mkdir(parents=True, exist_ok=True)
                args_dict["output_dir"] = game_output_dir

            test_module.run(game=g, model=model, **args_dict)
    else:
        test_module.run(game=game, model=model, **args_dict)

    print("\n[OK] Test complete!")
    if output_dir:
        print(f"[OK] Results saved to: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
