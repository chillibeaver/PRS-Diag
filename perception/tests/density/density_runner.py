"""
Density Test Runner for Board Game VLM Perception Tests.
Tests how VLM perception accuracy varies with board piece density.
"""
from shared.base_runner import (
    BaseTestRunner,
    get_available_games,
    json_dumps_compact_matrices,
    run_test_safely,
)
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


DENSITY_LEVELS = ["low", "medium", "high"]


class DensityTestRunner(BaseTestRunner):
    """Test runner for density tests."""

    def get_group_key(self) -> str:
        return "density_level"

    def get_group_values(self) -> List[str]:
        return DENSITY_LEVELS

    def compute_summary(self, results: List[Dict]) -> Dict:
        summary = {}
        group_key = self.get_group_key()

        by_density = {d: [] for d in DENSITY_LEVELS}
        for r in results:
            if r.get(group_key) in by_density:
                by_density[r[group_key]].append(r)

        for density, density_results in by_density.items():
            group_summary = self.compute_summary_for_group(
                density_results, density)
            if group_summary:
                summary[density] = group_summary

        return summary

    def print_summary(self, summary: Dict):
        print(f"\n{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}\n")

        print("FAILURE STATISTICS:")
        print(
            f"{'Density':<10} {'Total':<10} {'Success':<10} {'API Err':<10} {'Parse Fail':<12}")
        print(f"{'-'*55}")

        for density in DENSITY_LEVELS:
            if density not in summary:
                continue
            data = summary[density]
            print(f"{density.capitalize():<10} "
                  f"{data.get('n_total', data['n_tests']):<10} "
                  f"{data['n_tests']:<10} "
                  f"{data.get('n_api_errors', 0):<10} "
                  f"{data.get('n_parse_failures', 0):<12}")

        print(f"\nMETRICS (successful tests only):")
        print(
            f"{'Density':<10} {'Samples':<10} {'Overall':<12} {'Piece':<14} {'Balanced':<12}")
        print(f"{'-'*60}")

        for density in DENSITY_LEVELS:
            if density not in summary:
                continue
            data = summary[density]
            if data.get("all_failed"):
                print(f"{density.capitalize():<10} {'ALL FAILED':<50}")
                continue
            m = data["metrics"]
            print(f"{density.capitalize():<10} "
                  f"{data['n_tests']:<10} "
                  f"{m['overall_accuracy']['mean']:<12.1%} "
                  f"{m['piece_accuracy']['mean']:<14.1%} "
                  f"{m['balanced_accuracy']['mean']:<12.1%}")

        print(f"{'='*80}\n")


def get_test_specific_args() -> list:
    return [
        {"name": ["--density", "-d"], "kwargs": {
            "choices": ["low", "medium", "high", "all"],
            "default": "all",
            "help": "Density level(s) to test"
        }},
        {"name": ["--samples", "-n"], "kwargs": {
            "type": int,
            "default": 100,
            "help": "Number of samples per density level"
        }},
        {"name": ["--dummy-parse-fail-rate"], "kwargs": {
            "type": float,
            "default": 0.0,
            "help": "For dummy model: probability of parse failure (0.0-1.0)"
        }},
        {"name": ["--dummy-api-error-rate"], "kwargs": {
            "type": float,
            "default": 0.0,
            "help": "For dummy model: probability of API error (0.0-1.0)"
        }},
    ]


def run(game: str = "chess", model: str = "dummy", density: str = "all",
        samples: int = 100, output_dir: Path = None, rate_limit: int = 0,
        rate_pause: float = 0, dummy_parse_fail_rate: float = 0.0,
        dummy_api_error_rate: float = 0.0, **kwargs):
    """Main entry point."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    project_root = Path(__file__).parent.parent.parent

    if output_dir:
        output_dir = Path(output_dir) / f"{model}-{game}-density-{timestamp}"
    else:
        output_dir = project_root / f"{model}-{game}-density-{timestamp}"

    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "results.json"

    print(f"\n{'#'*70}")
    print(f"# DENSITY TEST: {game.upper()}")
    print(f"# Model: {model}")
    print(f"# Output: {output_dir.name}")
    print(f"{'#'*70}")

    print(f"\n[1/2] Generating test images...")

    if game == "chess":
        from tests.density.generate_chess_density import ChessDensityDiagnosticTest
        generator = ChessDensityDiagnosticTest(output_dir=output_dir)
        test_data = generator.generate_density_test_suite(
            n_samples_per_density=samples)
    elif game == "gomoku":
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
    import argparse
    parser = argparse.ArgumentParser(description="Density Test Runner")
    parser.add_argument(
        "--game", "-g", choices=get_available_games(), required=True)
    parser.add_argument("--model", "-m", default="dummy",
                        help="Model key or 'dummy'")
    for arg_def in get_test_specific_args():
        parser.add_argument(*arg_def["name"], **arg_def["kwargs"])
    args = parser.parse_args()

    run(
        game=args.game,
        model=args.model,
        density=args.density,
        samples=args.samples,
        dummy_parse_fail_rate=args.dummy_parse_fail_rate,
        dummy_api_error_rate=args.dummy_api_error_rate,
    )
    print("\n[DONE]")
