"""
Patch Alignment Test Runner for Board Game VLM Perception Tests.
Tests how VLM perception accuracy varies with patch alignment offsets.
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


PATCH_CONFIGS = {
    "patch16": {
        "patch_size": 16,
        "image_size": 1024,
        "description": "For Qwen3-VL and GPT (patch_size=16)",
    },
    "patch14_1008": {
        "patch_size": 14,
        "image_size": 1008,
        "description": "For GLM-4.1V (patch_size=14)",
    },
    "patch14_896": {
        "patch_size": 14,
        "image_size": 896,
        "description": "For Gemma 3 (patch_size=14, 896x896)",
    },
}

MODEL_TO_PATCH_CONFIG = {
    "qwen8b": "patch16",
    "qwen30b": "patch16",
    "qwen235b": "patch16",
    "gpt": "patch16",
    "glm": "patch14_1008",
    "gemma": "patch14_896",
    "dummy": "patch16",
}


def get_patch_config_for_model(model_key: str) -> str:
    if model_key in MODEL_TO_PATCH_CONFIG:
        return MODEL_TO_PATCH_CONFIG[model_key]
    print(f"[WARN] Unknown model '{model_key}', defaulting to patch16")
    return "patch16"


def get_alignment_conditions(patch_size: int) -> Dict:
    half = patch_size // 2
    quarter = patch_size // 4
    three_quarter = patch_size * 3 // 4
    return {
        "boundary": {"offset": 0, "description": f"At patch boundary (offset=0)"},
        "quarter": {"offset": quarter, "description": f"At 1/4 patch (offset={quarter}px)"},
        "center": {"offset": half, "description": f"At patch center (offset={half}px)"},
        "three_quarter": {"offset": three_quarter, "description": f"At 3/4 patch (offset={three_quarter}px)"},
    }


class PatchTestRunner(BaseTestRunner):
    """Test runner for patch alignment tests."""

    def __init__(self, game: str, model_key: str, output_dir: Path, patch_config: str,
                 rate_limit: int = 0, rate_pause: float = 0,
                 dummy_parse_fail_rate: float = 0.0, dummy_api_error_rate: float = 0.0):
        super().__init__(game, model_key, output_dir, rate_limit, rate_pause,
                         dummy_parse_fail_rate, dummy_api_error_rate)

        if patch_config not in PATCH_CONFIGS:
            raise ValueError(f"Unknown patch_config: {patch_config}")

        self.patch_config = patch_config
        self.patch_size = PATCH_CONFIGS[patch_config]["patch_size"]
        self.image_size = PATCH_CONFIGS[patch_config]["image_size"]
        self.alignment_conditions = get_alignment_conditions(self.patch_size)

    def get_group_key(self) -> str:
        return "alignment_condition"

    def get_group_values(self) -> List[str]:
        return list(self.alignment_conditions.keys())

    def compute_summary(self, results: List[Dict]) -> Dict:
        summary = {}
        group_key = self.get_group_key()

        by_condition = {cond: [] for cond in self.alignment_conditions.keys()}
        for r in results:
            if r.get(group_key) in by_condition:
                by_condition[r[group_key]].append(r)

        for condition, condition_results in by_condition.items():
            extra_fields = {
                "offset_px": self.alignment_conditions[condition]["offset"],
                "description": self.alignment_conditions[condition]["description"],
            }
            group_summary = self.compute_summary_for_group(
                condition_results, condition, extra_fields=extra_fields
            )
            if group_summary:
                summary[condition] = group_summary

        return summary

    def print_summary(self, summary: Dict):
        print(f"\n{'='*85}")
        print(f"SUMMARY")
        print(
            f"  Patch Config: {self.patch_config} ({self.patch_size}x{self.patch_size}, {self.image_size}x{self.image_size})")
        print(f"{'='*85}\n")

        print("FAILURE STATISTICS:")
        print(
            f"{'Condition':<18} {'Total':<10} {'Success':<10} {'API Err':<10} {'Parse Fail':<12}")
        print(f"{'-'*65}")

        for condition in self.alignment_conditions.keys():
            if condition not in summary:
                continue
            data = summary[condition]
            print(f"{condition:<18} "
                  f"{data.get('n_total', data['n_tests']):<10} "
                  f"{data['n_tests']:<10} "
                  f"{data.get('n_api_errors', 0):<10} "
                  f"{data.get('n_parse_failures', 0):<12}")

        print(f"\nMETRICS (successful tests only):")
        print(f"{'Condition':<18} {'Offset':<8} {'Samples':<10} {'Overall':<12} {'Piece':<14} {'Balanced':<12}")
        print(f"{'-'*85}")

        for condition in self.alignment_conditions.keys():
            if condition not in summary:
                continue
            data = summary[condition]
            if data.get("all_failed"):
                print(f"{condition:<18} {'ALL FAILED':<67}")
                continue
            m = data["metrics"]
            print(f"{condition:<18} "
                  f"{data['offset_px']}px{'':<4} "
                  f"{data['n_tests']:<10} "
                  f"{m['overall_accuracy']['mean']:<12.1%} "
                  f"{m['piece_accuracy']['mean']:<14.1%} "
                  f"{m['balanced_accuracy']['mean']:<12.1%}")

        print(f"{'='*85}\n")


def get_test_specific_args() -> list:
    return [
        {"name": ["--condition", "-c"], "kwargs": {
            "choices": ["boundary", "quarter", "center", "three_quarter", "all"],
            "default": "all",
            "help": "Alignment condition(s) to test"
        }},
        {"name": ["--samples", "-n"], "kwargs": {
            "type": int,
            "default": 100,
            "help": "Number of samples per alignment condition"
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


def run(game: str = "gomoku", model: str = "dummy", condition: str = "all",
        samples: int = 100, output_dir: Path = None, rate_limit: int = 0,
        rate_pause: float = 0, dummy_parse_fail_rate: float = 0.0,
        dummy_api_error_rate: float = 0.0, **kwargs):
    """Main entry point."""
    patch_config = get_patch_config_for_model(model)
    patch_size = PATCH_CONFIGS[patch_config]["patch_size"]
    image_size = PATCH_CONFIGS[patch_config]["image_size"]

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    project_root = Path(__file__).parent.parent.parent

    if output_dir:
        output_dir = Path(output_dir) / f"{model}-{game}-patch-{timestamp}"
    else:
        output_dir = project_root / f"{model}-{game}-patch-{timestamp}"

    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "results.json"

    print(f"\n{'#'*70}")
    print(f"# PATCH ALIGNMENT TEST: {game.upper()}")
    print(f"# Model: {model}")
    print(
        f"# Patch Config: {patch_config} ({patch_size}x{patch_size}, {image_size}x{image_size})")
    print(f"# Output: {output_dir.name}")
    print(f"{'#'*70}")

    print(f"\n[1/2] Generating test images...")

    if game == "gomoku":
        from tests.patch.generate_gomoku_patch import GomokuPatchDiagnosticTest
        generator = GomokuPatchDiagnosticTest(
            output_dir=output_dir, patch_config=patch_config)
        test_data = generator.generate_patch_test_suite(
            n_samples_per_condition=samples)
    elif game == "chess":
        from tests.patch.generate_chess_patch import ChessPatchDiagnosticTest
        generator = ChessPatchDiagnosticTest(
            output_dir=output_dir, patch_config=patch_config)
        test_data = generator.generate_patch_test_suite(
            n_samples_per_condition=samples)
    else:
        raise ValueError(f"Unknown game: {game}")

    print(f"\n[2/2] Running tests...")

    runner = PatchTestRunner(
        game=game, model_key=model, output_dir=output_dir, patch_config=patch_config,
        rate_limit=rate_limit, rate_pause=rate_pause,
        dummy_parse_fail_rate=dummy_parse_fail_rate,
        dummy_api_error_rate=dummy_api_error_rate,
    )

    test_cases = test_data["test_cases"]
    if condition != "all":
        test_cases = [
            tc for tc in test_cases if tc["alignment_condition"] == condition]

    metadata = {
        "game": game,
        "model_key": model,
        "model_name": runner.model_name,
        "timestamp": timestamp,
        "samples_per_condition": samples,
        "condition_filter": condition,
        "patch_config": patch_config,
        "patch_size": patch_size,
        "image_size": image_size,
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
    parser = argparse.ArgumentParser(description="Patch Alignment Test Runner")
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
        condition=args.condition,
        samples=args.samples,
        dummy_parse_fail_rate=args.dummy_parse_fail_rate,
        dummy_api_error_rate=args.dummy_api_error_rate,
    )
    print("\n[DONE]")
