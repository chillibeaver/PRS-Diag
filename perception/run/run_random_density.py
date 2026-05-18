"""
Random Density Test Runner.
Uses random piece placement instead of simulated gameplay for chess.
Reuses existing DensityTestRunner for evaluation.

Usage:
  python run/run_random_density.py -g chess -m dummy -n 30
  python run/run_random_density.py -g chess -m qwen30b -n 100 -d low
  python run/run_random_density.py -g chess -m dummy -o ./my_output/
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.base_runner import (
    get_available_games,
    run_test_safely,
)
from tests.density.density_runner import DensityTestRunner, get_test_specific_args


def run(game: str = "chess", model: str = "dummy", density: str = "all",
        samples: int = 100, output_dir: Path = None, rate_limit: int = 0,
        rate_pause: float = 0, dummy_parse_fail_rate: float = 0.0,
        dummy_api_error_rate: float = 0.0, **kwargs):
    """Main entry point for random density test."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    project_root = Path(__file__).parent.parent

    if output_dir:
        output_dir = Path(output_dir) / f"{model}-{game}-random-density-{timestamp}"
    else:
        output_dir = project_root / f"{model}-{game}-random-density-{timestamp}"

    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "results.json"

    print(f"\n{'#'*70}")
    print(f"# RANDOM DENSITY TEST: {game.upper()}")
    print(f"# Model: {model}")
    print(f"# Output: {output_dir.name}")
    print(f"{'#'*70}")

    print(f"\n[1/2] Generating test images (random placement)...")

    if game == "chess":
        from tests.density.generate_chess_random_density import ChessRandomDensityDiagnosticTest
        generator = ChessRandomDensityDiagnosticTest(output_dir=output_dir)
        test_data = generator.generate_density_test_suite(
            n_samples_per_density=samples)
    elif game == "gomoku":
        # Gomoku already uses random placement, reuse original generator
        from tests.density.generate_gomoku_density import GomokuDensityDiagnosticTest
        generator = GomokuDensityDiagnosticTest(output_dir=output_dir)
        test_data = generator.generate_density_test_suite(
            n_samples_per_density=samples)
    else:
        raise ValueError(f"Unknown game: {game}")

    print(f"\n[2/2] Running tests...")

    runner = DensityTestRunner(
        game=game, model_key=model, output_dir=output_dir,
        rate_limit=rate_limit, rate_pause=rate_pause,
        dummy_parse_fail_rate=dummy_parse_fail_rate,
        dummy_api_error_rate=dummy_api_error_rate,
    )

    test_cases = test_data["test_cases"]
    if density != "all":
        test_cases = [
            tc for tc in test_cases if tc["density_level"] == density]

    metadata = {
        "game": game,
        "model_key": model,
        "model_name": runner.model_name,
        "timestamp": timestamp,
        "samples_per_density": samples,
        "density_filter": density,
        "generation_method": "random_placement",
    }

    final_output = run_test_safely(
        runner=runner,
        test_cases=test_cases,
        max_samples=samples,
        metadata=metadata,
        results_file=results_file
    )

    print(f"\nOutput: {output_dir}")
    return final_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Random Density Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run/run_random_density.py -g chess -m dummy -n 30
  python run/run_random_density.py -g chess -m qwen30b -n 100
  python run/run_random_density.py -g chess -m dummy -d low -n 50
        """
    )
    parser.add_argument(
        "--game", "-g", choices=get_available_games(), required=True)
    parser.add_argument(
        "--model", "-m", default="dummy", help="Model key or 'dummy'")
    parser.add_argument(
        "--output", "-o", type=str, default=None, help="Output directory")
    for arg_def in get_test_specific_args():
        parser.add_argument(*arg_def["name"], **arg_def["kwargs"])

    args = parser.parse_args()

    run(
        game=args.game,
        model=args.model,
        density=args.density,
        samples=args.samples,
        output_dir=args.output,
        dummy_parse_fail_rate=args.dummy_parse_fail_rate,
        dummy_api_error_rate=args.dummy_api_error_rate,
    )
    print("\n[DONE]")
