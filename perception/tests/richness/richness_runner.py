"""
Visual Richness Test Runner for Board Game VLM Perception Tests.
Tests how VLM perception varies with visual style (2D flat vs 3D rendered).
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


STYLE_CONFIGS = {
    "2d_flat": {"description": "Minimalist 2D geometric shapes"},
    "3d_rendered": {"description": "Realistic 3D using PNG assets"},
}


class RichnessTestRunner(BaseTestRunner):
    """Test runner for visual richness tests."""

    def get_group_key(self) -> str:
        return "visual_style"

    def get_group_values(self) -> List[str]:
        return list(STYLE_CONFIGS.keys())

    def compute_summary(self, results: List[Dict]) -> Dict:
        summary = {}
        group_key = self.get_group_key()

        by_style = {style: [] for style in STYLE_CONFIGS.keys()}
        for r in results:
            if r.get(group_key) in by_style:
                by_style[r[group_key]].append(r)

        for style, style_results in by_style.items():
            group_summary = self.compute_summary_for_group(
                style_results, style,
                extra_fields={
                    "description": STYLE_CONFIGS[style]["description"]}
            )
            if group_summary:
                summary[style] = group_summary

        # Style comparison
        if ("2d_flat" in summary and "3d_rendered" in summary and
            not summary["2d_flat"].get("all_failed") and
                not summary["3d_rendered"].get("all_failed")):
            acc_2d = summary["2d_flat"]["metrics"]["overall_accuracy"]["mean"]
            acc_3d = summary["3d_rendered"]["metrics"]["overall_accuracy"]["mean"]
            diff = acc_3d - acc_2d

            summary["comparison"] = {
                "accuracy_difference": diff,
                "winner": ("3D rendered" if diff > 0.02 else
                           "2D flat" if diff < -0.02 else
                           "No significant difference"),
                "interpretation": (
                    "Visual richness helps perception" if diff > 0.02 else
                    "Visual complexity hinders perception" if diff < -0.02 else
                    "Visual style has minimal impact"
                ),
            }

        return summary

    def print_summary(self, summary: Dict):
        print(f"\n{'='*85}")
        print(f"SUMMARY")
        print(f"{'='*85}\n")

        print("FAILURE STATISTICS:")
        print(
            f"{'Style':<18} {'Total':<10} {'Success':<10} {'API Err':<10} {'Parse Fail':<12}")
        print(f"{'-'*65}")

        for style in STYLE_CONFIGS.keys():
            if style not in summary:
                continue
            data = summary[style]
            print(f"{style:<18} "
                  f"{data.get('n_total', data['n_tests']):<10} "
                  f"{data['n_tests']:<10} "
                  f"{data.get('n_api_errors', 0):<10} "
                  f"{data.get('n_parse_failures', 0):<12}")

        print(f"\nMETRICS (successful tests only):")
        print(
            f"{'Style':<18} {'Samples':<10} {'Overall':<12} {'Piece':<14} {'Balanced':<12}")
        print(f"{'-'*70}")

        for style in STYLE_CONFIGS.keys():
            if style not in summary:
                continue
            data = summary[style]
            if data.get("all_failed"):
                print(f"{style:<18} {'ALL FAILED':<52}")
                continue
            m = data["metrics"]
            print(f"{style:<18} "
                  f"{data['n_tests']:<10} "
                  f"{m['overall_accuracy']['mean']:<12.1%} "
                  f"{m['piece_accuracy']['mean']:<14.1%} "
                  f"{m['balanced_accuracy']['mean']:<12.1%}")

        if "comparison" in summary:
            comp = summary["comparison"]
            print(f"\n{'-'*70}")
            print("STYLE COMPARISON (2D vs 3D):")
            print(
                f"  Accuracy Difference: {comp['accuracy_difference']:+.1%} (3D - 2D)")
            print(f"  Winner: {comp['winner']}")
            print(f"  Interpretation: {comp['interpretation']}")

        print(f"{'='*85}\n")


def get_test_specific_args() -> list:
    return [
        {"name": ["--style", "-s"], "kwargs": {
            "choices": ["2d_flat", "3d_rendered", "all"],
            "default": "all",
            "help": "Visual style(s) to test"
        }},
        {"name": ["--samples", "-n"], "kwargs": {
            "type": int,
            "default": 100,
            "help": "Number of samples per visual style"
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


def run(game: str = "gomoku", model: str = "dummy", style: str = "all",
        samples: int = 100, output_dir: Path = None, rate_limit: int = 0,
        rate_pause: float = 0, dummy_parse_fail_rate: float = 0.0,
        dummy_api_error_rate: float = 0.0, **kwargs):
    """Main entry point."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    project_root = Path(__file__).parent.parent.parent

    if output_dir:
        output_dir = Path(output_dir) / f"{model}-{game}-richness-{timestamp}"
    else:
        output_dir = project_root / f"{model}-{game}-richness-{timestamp}"

    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "results.json"

    print(f"\n{'#'*70}")
    print(f"# VISUAL RICHNESS TEST: {game.upper()}")
    print(f"# Model: {model}")
    print(f"# Output: {output_dir.name}")
    print(f"{'#'*70}")

    print(f"\n[1/2] Generating test images...")

    if game == "gomoku":
        from tests.richness.generate_gomoku_richness import GomokuRichnessDiagnosticTest
        generator = GomokuRichnessDiagnosticTest(output_dir=output_dir)
        test_data = generator.generate_richness_test_suite(
            n_samples_per_style=samples)
    elif game == "chess":
        from tests.richness.generate_chess_richness import ChessRichnessDiagnosticTest
        generator = ChessRichnessDiagnosticTest(output_dir=output_dir)
        test_data = generator.generate_richness_test_suite(
            n_samples_per_style=samples)
    else:
        raise ValueError(f"Unknown game: {game}")

    print(f"\n[2/2] Running tests...")

    runner = RichnessTestRunner(
        game=game, model_key=model, output_dir=output_dir,
        rate_limit=rate_limit, rate_pause=rate_pause,
        dummy_parse_fail_rate=dummy_parse_fail_rate,
        dummy_api_error_rate=dummy_api_error_rate,
    )

    test_cases = test_data["test_cases"]
    if style != "all":
        test_cases = [tc for tc in test_cases if tc["visual_style"] == style]

    metadata = {
        "game": game,
        "model_key": model,
        "model_name": runner.model_name,
        "timestamp": timestamp,
        "samples_per_style": samples,
        "style_filter": style,
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
    parser = argparse.ArgumentParser(description="Visual Richness Test Runner")
    parser.add_argument(
        "--game", "-g", choices=get_available_games(), default="gomoku")
    parser.add_argument("--model", "-m", default="dummy",
                        help="Model key or 'dummy'")
    for arg_def in get_test_specific_args():
        parser.add_argument(*arg_def["name"], **arg_def["kwargs"])
    args = parser.parse_args()

    run(
        game=args.game,
        model=args.model,
        style=args.style,
        samples=args.samples,
        dummy_parse_fail_rate=args.dummy_parse_fail_rate,
        dummy_api_error_rate=args.dummy_api_error_rate,
    )
    print("\n[DONE]")
