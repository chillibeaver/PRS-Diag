"""
Resolution Test Runner for Board Game VLM Perception Tests.
Tests how VLM perception varies with image resolution (divisible vs non-divisible).
"""
from shared.base_runner import (
    BaseTestRunner,
    get_available_games,
    json_dumps_compact_matrices,
    run_test_safely,
    safe_get,
)
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


RESOLUTION_CONFIGS_BY_PATCH = {
    16: {
        "divisible": {
            "resolutions": [1024, 512, 384],
            "description": "Image sizes divisible by patch_size (16)",
        },
        "non_divisible": {
            "resolutions": [1010, 510, 370],
            "description": "Image sizes NOT divisible by 16",
        },
    },
    14: {
        "divisible": {
            "resolutions": [1008, 896, 392],
            "description": "Image sizes divisible by patch_size (14)",
        },
        "non_divisible": {
            "resolutions": [1010, 900, 400],
            "description": "Image sizes NOT divisible by 14",
        },
    },
}

MODEL_TO_PATCH_SIZE = {
    "qwen8b": 16, "qwen30b": 16, "qwen235b": 16, "gpt": 16,
    "glm": 14, "gemma": 14, "dummy": 16,
}


def get_patch_size_for_model(model_key: str) -> int:
    if model_key in MODEL_TO_PATCH_SIZE:
        return MODEL_TO_PATCH_SIZE[model_key]
    print(f"[WARN] Unknown model '{model_key}', defaulting to patch_size=16")
    return 16


def get_resolution_configs(patch_size: int) -> Dict:
    if patch_size not in RESOLUTION_CONFIGS_BY_PATCH:
        raise ValueError(f"Unsupported patch_size: {patch_size}")
    return RESOLUTION_CONFIGS_BY_PATCH[patch_size]


class ResolutionTestRunner(BaseTestRunner):
    """Test runner for resolution tests. Uses (group, resolution) composite key."""

    def __init__(self, game: str, model_key: str, output_dir: Path, patch_size: int,
                 rate_limit: int = 0, rate_pause: float = 0,
                 dummy_parse_fail_rate: float = 0.0, dummy_api_error_rate: float = 0.0):
        super().__init__(game, model_key, output_dir, rate_limit, rate_pause,
                         dummy_parse_fail_rate, dummy_api_error_rate)
        self.patch_size = patch_size
        self.resolution_configs = get_resolution_configs(patch_size)

    def get_group_key(self) -> str:
        return "resolution_group"

    def get_group_values(self) -> List[str]:
        return ["divisible", "non_divisible"]

    def run_tests(self, test_cases: List[Dict], max_samples_per_group: Optional[int] = None) -> List[Dict]:
        """Override to handle (group, resolution) composite key."""
        by_group_resolution = {}
        for tc in test_cases:
            key = (tc["resolution_group"], tc["resolution"])
            if key not in by_group_resolution:
                by_group_resolution[key] = []
            by_group_resolution[key].append(tc)

        if max_samples_per_group:
            for key in by_group_resolution:
                by_group_resolution[key] = by_group_resolution[key][:max_samples_per_group]

        print(f"\n{'#'*70}")
        print(f"# Model: {self.model_name}")
        print(f"# Patch Size: {self.patch_size}x{self.patch_size}")
        print(f"# Output: {self.output_dir.name}")
        print(f"{'#'*70}")

        all_results = []
        request_count = 0

        sorted_keys = sorted(by_group_resolution.keys(),
                             key=lambda x: (0 if x[0] == "divisible" else 1, -x[1]))

        for group, resolution in sorted_keys:
            cases = by_group_resolution[(group, resolution)]
            if not cases:
                continue

            is_divisible = cases[0]["statistics"]["is_divisible"]
            divisible_str = "Y" if is_divisible else "N"

            print(f"\n{'='*70}")
            print(
                f"Testing {group.upper()} - {resolution}x{resolution} [divisible={divisible_str}]")
            print(f"  Samples: {len(cases)}")
            print(f"{'='*70}\n")

            for i, test_case in enumerate(cases):
                print(f"[{i+1}/{len(cases)}] {test_case['test_id']}...",
                      end=" ", flush=True)

                try:
                    result = self.run_single_test(test_case)
                except Exception as e:
                    print(f"[EXCEPTION] {e}")
                    result = self._create_error_result(test_case, e)

                all_results.append(result)

                request_count += 1
                if self.rate_limit > 0 and request_count >= self.rate_limit:
                    if self.rate_pause > 0:
                        print(
                            f"\n[RATE LIMIT] Pausing for {self.rate_pause}s...")
                        time.sleep(self.rate_pause)
                    request_count = 0

                if "error" in result:
                    print(f"[ERROR] {result['error'][:50]}")
                else:
                    ok = "✓" if result["parse_success"] else "✗"
                    print(f"[{ok}] Overall: {result['overall_accuracy']:.1%} | "
                          f"Piece: {result['piece_accuracy']:.1%}")

        if self.model_key == "dummy" and hasattr(self.client, 'print_stats'):
            self.client.print_stats()

        return all_results

    def compute_summary(self, results: List[Dict]) -> Dict:
        """Compute summary with nested (group -> resolution) structure."""
        summary = {}

        by_group_resolution = {}
        for r in results:
            key = (r["resolution_group"], r["resolution"])
            if key not in by_group_resolution:
                by_group_resolution[key] = []
            by_group_resolution[key].append(r)

        def safe_mean(vals):
            vals = [v for v in vals if v is not None]
            return float(np.mean(vals)) if vals else 0.0

        def safe_std(vals):
            vals = [v for v in vals if v is not None]
            return float(np.std(vals)) if vals else 0.0

        for (group, resolution), group_results in by_group_resolution.items():
            valid = [r for r in group_results if "error" not in r and r.get(
                "parse_success", True)]
            n_api_errors = len([r for r in group_results if "error" in r])
            n_parse_failures = len(
                [r for r in group_results if "error" not in r and not r.get("parse_success", True)])

            if group not in summary:
                summary[group] = {}

            if not valid:
                summary[group][str(resolution)] = {
                    "resolution": resolution,
                    "n_tests": 0, "n_total": len(group_results),
                    "n_api_errors": n_api_errors, "n_parse_failures": n_parse_failures,
                    "all_failed": True,
                    "is_divisible": group_results[0]["statistics"]["is_divisible"] if group_results else False,
                    "metrics": {k: {"mean": 0.0, "std": 0.0} for k in
                                ["overall_accuracy", "empty_accuracy", "piece_accuracy", "balanced_accuracy"]},
                }
                continue

            summary[group][str(resolution)] = {
                "resolution": resolution,
                "n_tests": len(valid), "n_total": len(group_results),
                "n_api_errors": n_api_errors, "n_parse_failures": n_parse_failures,
                "is_divisible": valid[0]["statistics"]["is_divisible"],
                "padded_to": valid[0]["statistics"]["padded_to"],
                "token_grid": valid[0]["statistics"]["token_grid"],
                "avg_pieces": safe_mean([safe_get(r, "statistics", "total_pieces", default=0) for r in valid]),
                "metrics": {
                    "overall_accuracy": {"mean": safe_mean([r["overall_accuracy"] for r in valid]),
                                         "std": safe_std([r["overall_accuracy"] for r in valid])},
                    "empty_accuracy": {"mean": safe_mean([r["empty_accuracy"] for r in valid]),
                                       "std": safe_std([r["empty_accuracy"] for r in valid])},
                    "piece_accuracy": {"mean": safe_mean([r["piece_accuracy"] for r in valid]),
                                       "std": safe_std([r["piece_accuracy"] for r in valid])},
                    "balanced_accuracy": {"mean": safe_mean([r["balanced_accuracy"] for r in valid]),
                                          "std": safe_std([r["balanced_accuracy"] for r in valid])},
                },
            }

        return summary

    def print_summary(self, summary: Dict):
        print(f"\n{'='*90}")
        print(f"SUMMARY")
        print(f"  Patch Size: {self.patch_size}x{self.patch_size}")
        print(f"{'='*90}\n")

        print("FAILURE STATISTICS:")
        print(f"{'Group':<15} {'Resolution':<12} {'Total':<8} {'Success':<8} {'API Err':<10} {'Parse Fail':<12}")
        print(f"{'-'*70}")

        for group in ["divisible", "non_divisible"]:
            if group not in summary:
                continue
            for res_str in sorted(summary[group].keys(), key=lambda x: int(x) if x.isdigit() else 0, reverse=True):
                data = summary[group][res_str]
                print(f"{group:<15} "
                      f"{data['resolution']:<12} "
                      f"{data.get('n_total', data['n_tests']):<8} "
                      f"{data['n_tests']:<8} "
                      f"{data.get('n_api_errors', 0):<10} "
                      f"{data.get('n_parse_failures', 0):<12}")

        print(f"\nMETRICS (successful tests only):")
        print(f"{'Group':<15} {'Resolution':<12} {'Divisible':<10} {'Samples':<8} {'Overall':<12} {'Piece':<12} {'Balanced':<12}")
        print(f"{'-'*90}")

        for group in ["divisible", "non_divisible"]:
            if group not in summary:
                continue
            for res_str in sorted(summary[group].keys(), key=lambda x: int(x) if x.isdigit() else 0, reverse=True):
                data = summary[group][res_str]
                if data.get("all_failed"):
                    print(
                        f"{group:<15} {data['resolution']:<12} {'ALL FAILED':<66}")
                    continue
                m = data["metrics"]
                divisible_str = "Yes" if data["is_divisible"] else "No"
                print(f"{group:<15} "
                      f"{data['resolution']:<12} "
                      f"{divisible_str:<10} "
                      f"{data['n_tests']:<8} "
                      f"{m['overall_accuracy']['mean']:<12.1%} "
                      f"{m['piece_accuracy']['mean']:<12.1%} "
                      f"{m['balanced_accuracy']['mean']:<12.1%}")

        print(f"{'='*90}\n")


def get_test_specific_args() -> list:
    return [
        {"name": ["--resolution-group", "-r"], "kwargs": {
            "choices": ["divisible", "non_divisible", "all"],
            "default": "all",
            "help": "Resolution group(s) to test"
        }},
        {"name": ["--samples", "-n"], "kwargs": {
            "type": int,
            "default": 100,
            "help": "Number of samples per resolution"
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


def run(game: str = "gomoku", model: str = "dummy", resolution_group: str = "all",
        samples: int = 100, output_dir: Path = None, rate_limit: int = 0,
        rate_pause: float = 0, dummy_parse_fail_rate: float = 0.0,
        dummy_api_error_rate: float = 0.0, **kwargs):
    """Main entry point."""
    patch_size = get_patch_size_for_model(model)
    resolution_configs = get_resolution_configs(patch_size)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    project_root = Path(__file__).parent.parent.parent

    if output_dir:
        output_dir = Path(output_dir) / \
            f"{model}-{game}-resolution-{timestamp}"
    else:
        output_dir = project_root / f"{model}-{game}-resolution-{timestamp}"

    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "results.json"

    print(f"\n{'#'*70}")
    print(f"# RESOLUTION TEST: {game.upper()}")
    print(f"# Model: {model}")
    print(f"# Patch Size: {patch_size}x{patch_size}")
    print(f"# Output: {output_dir.name}")
    print(f"{'#'*70}")

    print(f"\n[1/2] Generating test images...")

    if game == "gomoku":
        from tests.resolution.generate_gomoku_resolution import GomokuResolutionDiagnosticTest
        generator = GomokuResolutionDiagnosticTest(
            output_dir=output_dir, patch_size=patch_size)
        test_data = generator.generate_resolution_test_suite(
            n_samples_per_resolution=samples)
    elif game == "chess":
        from tests.resolution.generate_chess_resolution import ChessResolutionDiagnosticTest
        generator = ChessResolutionDiagnosticTest(
            output_dir=output_dir, patch_size=patch_size)
        test_data = generator.generate_resolution_test_suite(
            n_samples_per_resolution=samples)
    else:
        raise ValueError(f"Unknown game: {game}")

    print(f"\n[2/2] Running tests...")

    runner = ResolutionTestRunner(
        game=game, model_key=model, output_dir=output_dir, patch_size=patch_size,
        rate_limit=rate_limit, rate_pause=rate_pause,
        dummy_parse_fail_rate=dummy_parse_fail_rate,
        dummy_api_error_rate=dummy_api_error_rate,
    )

    test_cases = test_data["test_cases"]
    if resolution_group != "all":
        test_cases = [
            tc for tc in test_cases if tc["resolution_group"] == resolution_group]

    metadata = {
        "game": game,
        "model_key": model,
        "model_name": runner.model_name,
        "timestamp": timestamp,
        "patch_size": patch_size,
        "samples_per_resolution": samples,
        "group_filter": resolution_group,
        "resolution_configs": resolution_configs,
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
    parser = argparse.ArgumentParser(description="Resolution Test Runner")
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
        resolution_group=args.resolution_group,
        samples=args.samples,
        dummy_parse_fail_rate=args.dummy_parse_fail_rate,
        dummy_api_error_rate=args.dummy_api_error_rate,
    )
    print("\n[DONE]")
