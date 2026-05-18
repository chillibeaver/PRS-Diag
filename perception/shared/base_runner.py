"""
Base Runner Module for Board Game VLM Perception Tests.

Features:
- Single-test exception isolation
- Safe dictionary access
- Localization computed in post-processing only
"""
import json
import re
import ast
import numpy as np
import base64
import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from shared.model_configs import MODEL_CONFIGS


# ============================================================================
# Game Configuration Classes
# ============================================================================

@dataclass
class GameConfig(ABC):
    """Base configuration for a board game."""
    name: str
    board_size: int
    system_prompt: str
    valid_values: set
    empty_value: int = 0

    def validate_matrix(self, matrix: List[List[int]]) -> bool:
        if not isinstance(matrix, list) or len(matrix) != self.board_size:
            return False
        for row in matrix:
            if not isinstance(row, list) or len(row) != self.board_size:
                return False
            for val in row:
                if not isinstance(val, int) or val not in self.valid_values:
                    return False
        return True

    def get_invalid_marker(self) -> List[List[int]]:
        marker = -99 if self.name == "chess" else -1
        return [[marker] * self.board_size for _ in range(self.board_size)]

    @abstractmethod
    def calculate_detection_breakdown(self, pred: np.ndarray, truth: np.ndarray) -> Dict:
        pass


class ChessConfig(GameConfig):
    def __init__(self):
        super().__init__(
            name="chess",
            board_size=8,
            system_prompt=self._get_prompt(),
            valid_values=set(range(-6, 7)),
        )

    @staticmethod
    def _get_prompt() -> str:
        return (
            "Analyze this chessboard image. Output the board state as an 8x8 JSON matrix.\n\n"
            "Encoding:\n"
            "- Empty: 0\n"
            "- White: Pawn=1, Knight=2, Bishop=3, Rook=4, Queen=5, King=6\n"
            "- Black: Pawn=-1, Knight=-2, Bishop=-3, Rook=-4, Queen=-5, King=-6\n\n"
            "Row 0 = top of image (rank 8), Row 7 = bottom of image (rank 1).\n\n"
            "Output ONLY the matrix, no explanation."
        )

    def calculate_detection_breakdown(self, pred: np.ndarray, truth: np.ndarray) -> Dict:
        breakdown = {
            "exact_detected": 0, "color_errors": 0,
            "type_errors": 0, "missed": 0, "false_positive": 0
        }
        for i in range(self.board_size):
            for j in range(self.board_size):
                if truth[i, j] != 0:
                    pred_val, truth_val = pred[i, j], truth[i, j]
                    if pred_val == truth_val:
                        breakdown["exact_detected"] += 1
                    elif pred_val != 0:
                        if (pred_val > 0) == (truth_val > 0):
                            breakdown["type_errors"] += 1
                        else:
                            breakdown["color_errors"] += 1
                    else:
                        breakdown["missed"] += 1
                else:
                    if pred[i, j] != 0:
                        breakdown["false_positive"] += 1
        return breakdown


class GomokuConfig(GameConfig):
    def __init__(self):
        super().__init__(
            name="gomoku",
            board_size=15,
            system_prompt=self._get_prompt(),
            valid_values={0, 1, 2},
        )

    @staticmethod
    def _get_prompt() -> str:
        return (
            "Analyze this Gomoku board image. Output the board state as a 15x15 JSON matrix.\n\n"
            "Encoding: Empty=0, Black=1, White=2\n\n"
            "Row 0 = top of image, Row 14 = bottom of image.\n\n"
            "Output ONLY the matrix, no explanation."
        )

    def calculate_detection_breakdown(self, pred: np.ndarray, truth: np.ndarray) -> Dict:
        breakdown = {
            "exact_detected": 0, "color_errors": 0,
            "missed": 0, "false_positive": 0
        }
        for i in range(self.board_size):
            for j in range(self.board_size):
                if truth[i, j] != 0:
                    pred_val, truth_val = pred[i, j], truth[i, j]
                    if pred_val == truth_val:
                        breakdown["exact_detected"] += 1
                    elif pred_val != 0:
                        breakdown["color_errors"] += 1
                    else:
                        breakdown["missed"] += 1
                else:
                    if pred[i, j] != 0:
                        breakdown["false_positive"] += 1
        return breakdown


GAME_CONFIGS = {
    "chess": ChessConfig,
    "gomoku": GomokuConfig,
}


def get_available_games() -> List[str]:
    return list(GAME_CONFIGS.keys())


# ============================================================================
# Default Values
# ============================================================================

def get_default_detection_breakdown(game: str = "gomoku") -> Dict:
    breakdown = {"exact_detected": 0, "color_errors": 0,
                 "missed": 0, "false_positive": 0}
    if game == "chess":
        breakdown["type_errors"] = 0
    return breakdown


# ============================================================================
# Dummy Client
# ============================================================================

class DummyClient:
    """Mock OpenAI client with configurable failure modes."""

    def __init__(self, board_size: int, valid_values: set,
                 parse_fail_rate: float = 0.0, api_error_rate: float = 0.0):
        self.board_size = board_size
        self.valid_values = list(valid_values)
        self.parse_fail_rate = parse_fail_rate
        self.api_error_rate = api_error_rate
        self.stats = {"total": 0, "success": 0,
                      "parse_fail": 0, "api_error": 0}

    @property
    def chat(self):
        return self

    @property
    def completions(self):
        return self

    def create(self, **kwargs):
        self.stats["total"] += 1

        if random.random() < self.api_error_rate:
            self.stats["api_error"] += 1
            raise Exception("Simulated API error")

        if random.random() < self.parse_fail_rate:
            self.stats["parse_fail"] += 1
            return self._make_response("I cannot analyze this image.")

        self.stats["success"] += 1
        matrix = [[random.choice(self.valid_values) for _ in range(self.board_size)]
                  for _ in range(self.board_size)]
        return self._make_response(str(matrix))

    def _make_response(self, content: str):
        return type('Response', (), {
            'choices': [type('Choice', (), {
                'message': type('Message', (), {'content': content})()
            })()]
        })()

    def print_stats(self):
        print(f"\n[DummyClient] {self.stats}")


# ============================================================================
# JSON Helpers
# ============================================================================

def convert_to_serializable(obj: Any) -> Any:
    """Convert numpy types to Python native types."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, Path):
        return str(obj)
    return obj


def json_dumps_compact_matrices(obj, indent=2):
    """JSON serialization with matrices on single lines."""
    obj = convert_to_serializable(obj)

    def format_value(v, level):
        ind = " " * (indent * level)
        ind_inner = " " * (indent * (level + 1))

        if isinstance(v, dict):
            if not v:
                return "{}"
            items = [
                f'{ind_inner}"{k}": {format_value(val, level + 1)}' for k, val in v.items()]
            return "{\n" + ",\n".join(items) + f"\n{ind}}}"
        elif isinstance(v, list):
            if not v:
                return "[]"
            if (isinstance(v[0], list) and
                all(isinstance(row, list) for row in v) and
                    all(isinstance(x, (int, float)) for row in v for x in row)):
                rows = [
                    f"{ind_inner}[" + ", ".join(str(x) for x in row) + "]" for row in v]
                return "[\n" + ",\n".join(rows) + f"\n{ind}]"
            elif all(isinstance(x, (int, float, str, bool, type(None))) for x in v):
                return "[" + ", ".join(json.dumps(x) for x in v) + "]"
            else:
                items = [f"{ind_inner}{format_value(x, level + 1)}" for x in v]
                return "[\n" + ",\n".join(items) + f"\n{ind}]"
        else:
            return json.dumps(v)

    return format_value(obj, 0)


def safe_get(d: Dict, *keys, default=0):
    """Safely get nested dictionary value."""
    try:
        result = d
        for key in keys:
            result = result[key]
        return result
    except (KeyError, TypeError, IndexError):
        return default


# ============================================================================
# Base Test Runner
# ============================================================================

class BaseTestRunner(ABC):
    """Base class for all test runners."""

    def __init__(self, game: str, model_key: str, output_dir: Path,
                 rate_limit: int = 0, rate_pause: float = 0,
                 dummy_parse_fail_rate: float = 0.0, dummy_api_error_rate: float = 0.0):
        if game not in GAME_CONFIGS:
            raise ValueError(f"Unknown game: {game}")

        self.config = GAME_CONFIGS[game]()
        self.model_key = model_key
        self.game = game
        self.output_dir = Path(output_dir)
        self.rate_limit = rate_limit
        self.rate_pause = rate_pause

        if model_key == "dummy":
            self.model_name = "dummy"
            self.client = DummyClient(
                self.config.board_size, self.config.valid_values,
                parse_fail_rate=dummy_parse_fail_rate, api_error_rate=dummy_api_error_rate)
        else:
            if model_key not in MODEL_CONFIGS:
                raise ValueError(f"Unknown model: {model_key}")
            cfg = MODEL_CONFIGS[model_key]
            self.model_name = cfg["model_name"]
            if OpenAI is None:
                raise ImportError("openai package not installed")
            self.client = OpenAI(
                api_key=cfg["api_key"], base_url=cfg["base_url"])

    def encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def parse_output(self, output: str) -> List[List[int]]:
        """Parse matrix from model output."""
        size = self.config.board_size

        # Strategy 1: Regex for full matrix
        pattern = r"\[\s*\[.*?\]\s*(?:,\s*\[.*?\]\s*){" + \
            str(size - 1) + r"}\]"
        for match_str in re.findall(pattern, output, re.DOTALL):
            try:
                matrix = ast.literal_eval(re.sub(r"\s+", " ", match_str))
                if self.config.validate_matrix(matrix):
                    return matrix
            except:
                continue

        # Strategy 2: Extract numbers
        try:
            bracket_content = re.findall(r'\[([^\[\]]+)\]', output)
            numbers = []
            for content in bracket_content:
                numbers.extend(re.findall(
                    r"(?<![a-zA-Z])-?\d+(?![a-zA-Z])", content))
            if len(numbers) == size * size:
                matrix = [[int(numbers[i * size + j])
                           for j in range(size)] for i in range(size)]
                if self.config.validate_matrix(matrix):
                    return matrix
        except:
            pass

        return self.config.get_invalid_marker()

    def calculate_metrics(self, predicted: List[List[int]], ground_truth: List[List[int]]) -> Dict:
        """Calculate basic metrics (no localization)."""
        pred = np.array(predicted)
        truth = np.array(ground_truth)
        invalid_marker = self.config.get_invalid_marker()[0][0]
        is_invalid = pred[0, 0] == invalid_marker

        metrics = {
            "parse_success": not is_invalid,
            "overall_accuracy": 0.0,
            "empty_accuracy": 0.0,
            "piece_accuracy": 0.0,
            "balanced_accuracy": 0.0,
            "piece_detection_precision": 0.0,
            "piece_detection_recall": 0.0,
        }

        if is_invalid:
            metrics["detection_breakdown"] = get_default_detection_breakdown(
                self.game)
            return metrics

        try:
            metrics["overall_accuracy"] = float(np.mean(pred == truth))

            empty_mask = truth == self.config.empty_value
            piece_mask = ~empty_mask

            if np.sum(empty_mask) > 0:
                metrics["empty_accuracy"] = float(
                    np.mean(pred[empty_mask] == self.config.empty_value))
            if np.sum(piece_mask) > 0:
                metrics["piece_accuracy"] = float(
                    np.mean(pred[piece_mask] == truth[piece_mask]))

            class_accs = []
            if np.sum(empty_mask) > 0:
                class_accs.append(
                    np.mean(pred[empty_mask] == self.config.empty_value))
            if np.sum(piece_mask) > 0:
                class_accs.append(
                    np.mean(pred[piece_mask] == truth[piece_mask]))
            if class_accs:
                metrics["balanced_accuracy"] = float(np.mean(class_accs))

            pred_piece = pred != self.config.empty_value
            truth_piece = piece_mask
            tp = np.sum(pred_piece & truth_piece)
            fp = np.sum(pred_piece & ~truth_piece)
            fn = np.sum(~pred_piece & truth_piece)
            if tp + fp > 0:
                metrics["piece_detection_precision"] = float(tp / (tp + fp))
            if tp + fn > 0:
                metrics["piece_detection_recall"] = float(tp / (tp + fn))

            metrics["detection_breakdown"] = self.config.calculate_detection_breakdown(
                pred, truth)
        except Exception as e:
            print(f" [WARN: {e}]", end="")
            metrics["detection_breakdown"] = get_default_detection_breakdown(
                self.game)

        return metrics

    def _create_error_result(self, test_case: Dict, error: Exception) -> Dict:
        """Create result dict for a failed test."""
        test_case["error"] = str(error)
        test_case["error_type"] = type(error).__name__
        test_case["parse_success"] = False
        test_case["overall_accuracy"] = 0.0
        test_case["empty_accuracy"] = 0.0
        test_case["piece_accuracy"] = 0.0
        test_case["balanced_accuracy"] = 0.0
        test_case["detection_breakdown"] = get_default_detection_breakdown(
            self.game)
        return test_case

    def run_single_test(self, test_case: Dict) -> Dict:
        """Run a single test case."""
        image_path = test_case["image_file"]
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": self.config.system_prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{self.encode_image(image_path)}"}},
            ],
        }]

        start_time = time.time()
        try:

            api_params = {
                "model": self.model_name,
                "messages": messages,
            }

            if self.model_key in MODEL_CONFIGS:
                cfg = MODEL_CONFIGS[self.model_key]
                if "reasoning_effort" in cfg:
                    api_params["reasoning_effort"] = cfg["reasoning_effort"]

            response = self.client.chat.completions.create(**api_params)
            model_output = response.choices[0].message.content
            api_time = time.time() - start_time
        except Exception as e:
            return self._create_error_result(test_case, e)

        predicted = self.parse_output(model_output)

        try:
            metrics = self.calculate_metrics(
                predicted, test_case["ground_truth"])
        except Exception as e:
            metrics = {
                "parse_success": False, "overall_accuracy": 0.0, "empty_accuracy": 0.0,
                "piece_accuracy": 0.0, "balanced_accuracy": 0.0,
                "detection_breakdown": get_default_detection_breakdown(self.game),
            }

        test_case["predicted"] = predicted
        test_case["raw_output"] = model_output
        test_case["api_time"] = api_time
        test_case.update(metrics)
        return test_case

    @abstractmethod
    def get_group_key(self) -> str:
        pass

    @abstractmethod
    def get_group_values(self) -> List[str]:
        pass

    def run_tests(self, test_cases: List[Dict], max_samples_per_group: Optional[int] = None) -> List[Dict]:
        """Run all tests with per-test exception isolation."""
        group_key = self.get_group_key()
        group_values = self.get_group_values()

        by_group = {g: [] for g in group_values}
        for tc in test_cases:
            if tc.get(group_key) in by_group:
                by_group[tc[group_key]].append(tc)

        if max_samples_per_group:
            for g in by_group:
                by_group[g] = by_group[g][:max_samples_per_group]

        print(f"\n{'#'*70}")
        print(f"# Model: {self.model_name}")
        print(f"# Output: {self.output_dir.name}")
        print(f"{'#'*70}")

        all_results = []
        request_count = 0

        for group in group_values:
            cases = by_group.get(group, [])
            if not cases:
                continue

            print(f"\n{'='*70}")
            print(f"Testing {group.upper()} ({len(cases)} samples)")
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
                        print(f"\n[RATE LIMIT] Pausing {self.rate_pause}s...")
                        time.sleep(self.rate_pause)
                    request_count = 0

                if "error" in result:
                    print(f"[ERROR] {result['error'][:50]}")
                else:
                    ok = "OK" if result["parse_success"] else "FAIL"
                    print(f"[{ok}] Overall: {result['overall_accuracy']:.1%} | "
                          f"Piece: {result['piece_accuracy']:.1%}")

        if self.model_key == "dummy" and hasattr(self.client, 'print_stats'):
            self.client.print_stats()

        return all_results

    def compute_summary_for_group(self, group_results: List[Dict], group_name: str,
                                  extra_fields: Optional[Dict] = None) -> Dict:
        """Compute summary for a single group."""
        valid = [r for r in group_results if "error" not in r and r.get(
            "parse_success", True)]
        n_api_errors = len([r for r in group_results if "error" in r])
        n_parse_failures = len(
            [r for r in group_results if "error" not in r and not r.get("parse_success", True)])

        def safe_mean(vals):
            vals = [v for v in vals if v is not None]
            return float(np.mean(vals)) if vals else 0.0

        def safe_std(vals):
            vals = [v for v in vals if v is not None]
            return float(np.std(vals)) if vals else 0.0

        if not valid:
            summary = {
                "n_tests": 0, "n_total": len(group_results),
                "n_api_errors": n_api_errors, "n_parse_failures": n_parse_failures,
                "all_failed": True,
                "metrics": {k: {"mean": 0.0, "std": 0.0} for k in
                            ["overall_accuracy", "empty_accuracy", "piece_accuracy", "balanced_accuracy"]},
            }
        else:
            summary = {
                "n_tests": len(valid), "n_total": len(group_results),
                "n_api_errors": n_api_errors, "n_parse_failures": n_parse_failures,
                "avg_pieces": safe_mean([safe_get(r, "statistics", "total_pieces", default=0) for r in valid]),
                "avg_density": safe_mean([safe_get(r, "statistics", "density", default=0) for r in valid]),
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

        if extra_fields:
            summary.update(extra_fields)
        return summary

    @abstractmethod
    def compute_summary(self, results: List[Dict]) -> Dict:
        pass

    @abstractmethod
    def print_summary(self, summary: Dict):
        pass


# ============================================================================
# Run Helper
# ============================================================================

def run_test_safely(runner: BaseTestRunner, test_cases: List[Dict],
                    max_samples: Optional[int], metadata: Dict, results_file: Path) -> Dict:
    """Run tests with error handling."""
    results = []
    test_error = None

    try:
        results = runner.run_tests(
            test_cases, max_samples_per_group=max_samples)
    except Exception as e:
        import traceback
        print(f"\n[ERROR] Test execution failed: {e}")
        test_error = {"stage": "test_execution", "message": str(e),
                      "type": type(e).__name__, "traceback": traceback.format_exc()}

    summary = {}
    summary_error = None
    if results:
        try:
            summary = runner.compute_summary(results)
        except Exception as e:
            import traceback
            print(f"\n[WARN] Summary failed: {e}")
            summary_error = {"stage": "compute_summary", "message": str(e),
                             "type": type(e).__name__, "traceback": traceback.format_exc()}
            summary = {"error": summary_error}

    status = "success"
    if test_error:
        status = "test_failed"
    elif summary_error:
        status = "summary_failed"

    final_output = {
        "metadata": {**metadata, "status": status, "total_tests": len(results)},
        "summary": summary,
        "test_cases": results,
    }
    if test_error:
        final_output["error"] = test_error
    elif summary_error:
        final_output["error"] = summary_error

    # Save
    with open(results_file, "w") as f:
        f.write(json_dumps_compact_matrices(final_output))
    print(f"\n[OK] Saved: {results_file}")

    # Print summary
    if not test_error and not summary_error and summary:
        try:
            runner.print_summary(summary)
        except Exception as e:
            print(f"\n[WARN] Failed to print summary: {e}")

    return final_output
