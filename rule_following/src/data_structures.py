"""
Data structures for test results and configurations
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class TestType(Enum):
    SPATIAL = "spatial"
    TEMPORAL = "temporal"


class PieceType(Enum):
    KNIGHT = "knight"
    BISHOP = "bishop"
    ROOK = "rook"


@dataclass
class TestResult:
    """Test result data class"""
    # Basic information
    test_type: str  # "spatial" or "temporal"
    test_layer: int  # 0, 1, 2, 3
    case_id: str

    # Test specific
    piece_type: Optional[str] = None  # for spatial
    rule_type: Optional[str] = None  # for temporal

    # === Recognition verification (NEW) ===
    verification_question: Optional[str] = None
    verification_expected: Optional[str] = None
    verification_response: Optional[str] = None
    verification_passed: Optional[bool] = None

    # Question and answer
    question: str = ""
    expected_answer: str = ""  # "yes", "no", "unknown"
    model_response: str = ""
    correct: bool = False

    # Test 2 specific (Know-Do Gap)
    declarative_question: Optional[str] = None
    declarative_response: Optional[str] = None
    declarative_correct: Optional[bool] = None
    know_do_gap: Optional[bool] = None

    # Test 3 specific (Explicit Rule)
    condition: Optional[str] = None  # "without_rule", "with_rule"

    # Metadata
    image_paths: List[str] = None
    timestamp: str = ""
    model_name: str = ""

    def __post_init__(self):
        if self.image_paths is None:
            self.image_paths = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


def save_results(results: List[TestResult], output_path: str,
                 summary: Optional[Dict] = None):
    """
    Save test results to JSON file

    Args:
        results: List of TestResult objects
        output_path: Path to save the JSON file
        summary: Optional summary dictionary to include at the beginning of the file
                 If None, saves only the results list (backward compatible)
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(
        output_path) else '.', exist_ok=True)

    if summary is None:
        # Original behavior: save only results list
        results_dict = [r.to_dict() for r in results]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
    else:
        # New behavior: save with summary at the beginning
        output_data = {
            "summary": summary,
            "detailed_results": [r.to_dict() for r in results]
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Results saved to: {output_path}")


def create_summary(results: List[TestResult], stats: Dict,
                   test_cases: Optional[List[Dict]] = None) -> Dict:
    """
    Create a summary dictionary from test results

    Args:
        results: List of TestResult objects
        stats: Statistics dictionary with keys:
               - total
               - verification_passed
               - verification_failed
               - test_correct
               - test_incorrect
               - test_correct_given_verified
        test_cases: Optional list of test case dictionaries for type breakdown

    Returns:
        Summary dictionary
    """
    # Calculate rates
    verification_rate = stats['verification_passed'] / \
        stats['total'] if stats['total'] > 0 else 0
    accuracy_given_verified = stats['test_correct_given_verified'] / \
        stats['verification_passed'] if stats['verification_passed'] > 0 else 0
    overall_accuracy = stats['test_correct'] / \
        stats['total'] if stats['total'] > 0 else 0

    summary = {
        "model_name": results[0].model_name if results else "unknown",
        "total_cases": stats['total'],
        "timestamp": datetime.now().isoformat(),
        "board_recognition": {
            "verified_correctly": stats['verification_passed'],
            "failed_to_recognize": stats['verification_failed'],
            "verification_rate": round(verification_rate, 3)
        },
        "test_accuracy": {
            "correct_among_verified": stats['test_correct_given_verified'],
            "total_verified": stats['verification_passed'],
            "accuracy_given_verified": round(accuracy_given_verified, 3),
            "overall_correct": stats['test_correct'],
            "overall_accuracy": round(overall_accuracy, 3)
        }
    }

    # Add type breakdown if test_cases provided
    if test_cases:
        type_breakdown = {}
        for result in results:
            if not result.verification_passed:
                continue

            case = next((c for c in test_cases if c.get(
                'case_id') == result.case_id), None)
            if case:
                case_type = case.get('type', 'unknown')
                subtype = case.get('subtype', '')
                key = f"{case_type}" if not subtype else f"{case_type}_{subtype}"

                if key not in type_breakdown:
                    type_breakdown[key] = {'correct': 0, 'total': 0}
                type_breakdown[key]['total'] += 1
                if result.correct:
                    type_breakdown[key]['correct'] += 1

        # Add accuracy percentages
        for case_type in type_breakdown:
            stats_item = type_breakdown[case_type]
            stats_item['accuracy'] = round(
                stats_item['correct'] /
                stats_item['total'] if stats_item['total'] > 0 else 0,
                3
            )

        summary["accuracy_by_type_verified_only"] = dict(
            sorted(type_breakdown.items()))

    return summary


def load_results(input_path: str) -> List[TestResult]:
    """
    Load test results from JSON file

    Handles both formats:
    - Old format: direct list of results
    - New format: {"summary": {...}, "detailed_results": [...]}
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Check format
    if isinstance(data, list):
        # Old format: direct list
        results_dict = data
    elif isinstance(data, dict) and "detailed_results" in data:
        # New format: with summary
        results_dict = data["detailed_results"]
    else:
        raise ValueError(f"Unknown JSON format in {input_path}")

    return [TestResult.from_dict(r) for r in results_dict]
