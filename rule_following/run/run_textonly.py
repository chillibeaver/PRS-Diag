"""
Text-Only Mode Runner for Existing Test Results

Re-runs the exact same test samples in text-only mode (FEN strings instead of images,
no verification step) to isolate "rule reasoning" from "visual perception".
"""

import sys
import os
import argparse
import json
import glob
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))

from src.fen_utils import parse_verification_expected, pieces_to_fen_chess, pieces_to_fen_xiangqi
from src.data_structures import TestResult, save_results, create_summary
from src.temporal_levels.chess.standard_temporal_level import (
    get_rule_clarification as chess_get_rule_clarification
)
from src.temporal_levels.xiangqi.standard_temporal_level import (
    get_rule_clarification as xiangqi_get_rule_clarification
)
from run_comp_ladder import get_model_client


def get_rule_clarification_for_game(game: str, level: int) -> Optional[str]:
    """Get rule clarification for a given game and level."""
    if game == "chess":
        return chess_get_rule_clarification(level=level)
    elif game == "xiangqi":
        return xiangqi_get_rule_clarification(level=level)
    return None


def parse_main_answer(response: str) -> str:
    """
    Extract the 'Main answer: ...' portion from model response,
    then extract yes/no/unknown from it.

    Mirrors the original two-step process:
    1. _parse_combined_response() extracts text after 'Main answer:'
    2. _extract_answer() checks first 20 chars for yes/no
    """
    if not response:
        return "unknown"

    # Step 1: find "Main answer:" line
    answer_text = ""
    for line in response.split('\n'):
        line_lower = line.lower().strip()
        if line_lower.startswith('main answer:') or line_lower.startswith('main:'):
            answer_text = line.split(':', 1)[1].strip()
            break

    # Fallback: if no "Main answer:" found, use the full response
    if not answer_text:
        answer_text = response

    # Step 2: extract yes/no from first 20 chars
    answer_lower = answer_text.lower().strip()
    if "yes" in answer_lower[:20]:
        return "yes"
    elif "no" in answer_lower[:20]:
        return "no"
    else:
        return "unknown"


def build_textonly_prompt(fen_strings: List[str], question: str,
                          rule_clarification: Optional[str] = None) -> str:
    """Build the text-only prompt with FEN states, optional rule clarification, and question."""
    parts = ["Consider these board states carefully.", "",
             "The states are shown in chronological order and represent consecutive states.", ""]

    for i, fen in enumerate(fen_strings, 1):
        parts.append(f"State {i} FEN: {fen}")

    if rule_clarification:
        parts.append("")
        parts.append(rule_clarification)

    parts.append("")
    parts.append("Now, the main question:")
    parts.append(question)
    parts.append("")
    parts.append("Please answer. Format your response exactly as:")
    parts.append("Main answer: [yes/no/unknown]")

    return "\n".join(parts)


def load_reference_results(results_dir: str, game: str, mode: str,
                           source_model: str, level: int) -> Optional[List[Dict]]:
    """Load reference results for a given level from the source model's output."""
    # Build search path. `source_model` is the prefix (e.g. "qwen30b"); the
    # full directory is "{prefix}-{game}-{mode}" to match run_cot_ablation.py.
    source_dir = f"{source_model}-{game}-{mode}"
    base_path = os.path.join(results_dir, game, f"{mode} mode", source_dir)

    if not os.path.isdir(base_path):
        print(f"  Source directory not found: {base_path}")
        return None

    # Glob for level results file
    pattern = os.path.join(base_path, "**", f"level_{level}_results.json")
    matches = glob.glob(pattern, recursive=True)

    if not matches:
        # Also try alternate naming pattern
        pattern = os.path.join(base_path, "**", f"*level_{level}*results.json")
        matches = glob.glob(pattern, recursive=True)

    if not matches:
        print(f"  No results file found for level {level} in {base_path}")
        return None

    # Use the most recent file if multiple matches
    results_file = sorted(matches)[-1]
    print(f"  Loading: {results_file}")

    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "detailed_results" in data:
        return data["detailed_results"]
    else:
        print(f"  Unknown JSON format in {results_file}")
        return None


def run_textonly_level(game: str, mode: str, level: int, cases: List[Dict],
                       model_client, rate_limit_requests: int = 0,
                       rate_limit_pause: int = 0) -> tuple:
    """
    Run text-only testing for a single level.

    Returns:
        (results, stats) tuple
    """
    fen_func = pieces_to_fen_chess if game == "chess" else pieces_to_fen_xiangqi
    rule_clarification = get_rule_clarification_for_game(game, level)

    results = []
    stats = {
        'total': 0,
        'verification_passed': 0,
        'verification_failed': 0,
        'test_correct': 0,
        'test_incorrect': 0,
        'test_correct_given_verified': 0,
    }

    request_count = 0

    for i, case in enumerate(cases):
        case_id = case.get('case_id', f'case_{i}')
        question = case.get('question', '')
        expected_answer = case.get('expected_answer', '')
        verification_expected = case.get('verification_expected', '')

        if not verification_expected:
            print(f"  Skipping {case_id}: no verification_expected")
            continue

        stats['total'] += 1

        # Parse board states from verification_expected
        try:
            states_pieces = parse_verification_expected(verification_expected, game)
        except Exception as e:
            print(f"  Error parsing {case_id}: {e}")
            stats['verification_failed'] += 1
            continue

        # Convert to FEN
        fen_strings = [fen_func(pieces) for pieces in states_pieces]

        # Build prompt
        prompt = build_textonly_prompt(fen_strings, question, rule_clarification)

        # Query model
        try:
            response = model_client.query_text_only(prompt)
            if response is None:
                response = ""
        except Exception as e:
            print(f"  Error querying {case_id}: {e}")
            response = f"Error: {e}"

        # Parse answer
        answer = parse_main_answer(response)
        correct = (answer == expected_answer)

        # All text-only cases count as "verified" (no visual verification needed)
        stats['verification_passed'] += 1
        if correct:
            stats['test_correct'] += 1
            stats['test_correct_given_verified'] += 1
        else:
            stats['test_incorrect'] += 1

        result = TestResult(
            test_type="temporal_level",
            test_layer=level,
            case_id=case_id,
            verification_question="",
            verification_expected=verification_expected,
            verification_response="skipped_textonly",
            verification_passed=True,
            question=question,
            expected_answer=expected_answer,
            model_response=response,
            correct=correct,
            image_paths=[],
            model_name=model_client.model_name,
        )
        results.append(result)

        # Progress - print every case with flush for immediate display
        running_acc = stats['test_correct'] / stats['total'] if stats['total'] > 0 else 0
        print(f"  [{i+1}/{len(cases)}] {case_id} -> {answer} (expected: {expected_answer}) {'✓' if correct else '✗'}  Running acc: {running_acc:.1%}", flush=True)

        # Rate limiting
        request_count += 1
        if rate_limit_requests > 0 and request_count >= rate_limit_requests:
            if rate_limit_pause > 0 and (i + 1) < len(cases):
                print(f"  Rate limit: pausing {rate_limit_pause}s...")
                time.sleep(rate_limit_pause)
            request_count = 0

    return results, stats


def main():
    parser = argparse.ArgumentParser(
        description="Text-Only Mode Runner for Existing Test Results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--results-dir",
        type=str,
        default="output/rule complexity ladder",
        help="Path to existing results base directory"
    )
    parser.add_argument(
        "--game",
        type=str,
        choices=["chess", "xiangqi"],
        required=True,
        help="Game type"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["predictive", "explicit"],
        required=True,
        help="Test mode"
    )

    level_group = parser.add_mutually_exclusive_group(required=True)
    level_group.add_argument(
        "--levels",
        type=int,
        nargs="+",
        help="Which levels to run (e.g., --levels 3 4 5 6)"
    )
    level_group.add_argument(
        "--all",
        action="store_true",
        help="Run all levels found in source"
    )

    parser.add_argument(
        "--model",
        type=str,
        choices=["dummy", "novita", "dashscope", "xai", "google", "anth", "openai", "sf", "openrouter"],
        default="dummy",
        help="Model for text-only testing"
    )
    parser.add_argument(
        "--source-model",
        type=str,
        required=True,
        help="Source model directory prefix (e.g., qwen30b, gpt5.2). The script appends -{game}-{mode} to locate the directory."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./output/textonly",
        help="Output directory"
    )
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
    parser.add_argument(
        "--dummy-pass-rate",
        type=float,
        default=0.8,
        help="Pass rate for dummy model"
    )

    args = parser.parse_args()

    # Determine levels
    if args.all:
        levels = list(range(1, 7))
    else:
        levels = sorted(args.levels)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 70)
    print("TEXT-ONLY MODE RUNNER")
    print("=" * 70)
    print(f"Game: {args.game}")
    print(f"Mode: {args.mode}")
    print(f"Levels: {levels}")
    print(f"Source model: {args.source_model}")
    print(f"Results dir: {args.results_dir}")
    print(f"Output: {args.output}")
    print("=" * 70)

    # Initialize model
    model_client = get_model_client(args.model, dummy_pass_rate=args.dummy_pass_rate)

    all_level_results = []

    for level in levels:
        print(f"\n{'='*70}")
        print(f"LEVEL {level} - Text-Only")
        print(f"{'='*70}")

        # Step 1: Load reference results
        cases = load_reference_results(
            args.results_dir, args.game, args.mode, args.source_model, level
        )
        if cases is None:
            print(f"  Skipping level {level}: no reference results found")
            continue

        print(f"  Loaded {len(cases)} cases from source")

        # Step 2-6: Run text-only test
        results, stats = run_textonly_level(
            game=args.game,
            mode=args.mode,
            level=level,
            cases=cases,
            model_client=model_client,
            rate_limit_requests=args.rate_limit,
            rate_limit_pause=args.rate_pause,
        )

        if not results:
            print(f"  No results for level {level}")
            continue

        # Step 7: Save results
        level_dir = os.path.join(
            args.output,
            f"{args.game}_{args.mode}_level_{level}_textonly_{timestamp}"
        )
        os.makedirs(level_dir, exist_ok=True)

        summary = create_summary(results, stats)
        output_path = os.path.join(level_dir, f"level_{level}_textonly_results.json")
        save_results(results, output_path, summary=summary)

        # Step 8: Print summary
        accuracy = stats['test_correct'] / stats['total'] if stats['total'] > 0 else 0
        print(f"\n  Level {level} Summary:")
        print(f"    Total cases: {stats['total']}")
        print(f"    Correct: {stats['test_correct']}")
        print(f"    Accuracy: {accuracy:.1%}")

        all_level_results.append({
            "level": level,
            "total": stats['total'],
            "correct": stats['test_correct'],
            "accuracy": round(accuracy, 3),
            "output_dir": level_dir,
        })

    # Save overall summary
    if all_level_results:
        summary_path = os.path.join(args.output, f"textonly_summary_{timestamp}.json")
        os.makedirs(args.output, exist_ok=True)
        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "game": args.game,
            "mode": args.mode,
            "source_model": args.source_model,
            "model_name": model_client.model_name,
            "levels": all_level_results,
        }
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        print(f"\nSummary saved to: {summary_path}")

    print("\n" + "=" * 70)
    print("TEXT-ONLY RUN COMPLETE")
    print("=" * 70)
    for lr in all_level_results:
        print(f"  Level {lr['level']}: {lr['correct']}/{lr['total']} ({lr['accuracy']:.1%})")
    print("=" * 70)


if __name__ == "__main__":
    main()
