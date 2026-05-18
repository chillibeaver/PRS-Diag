"""
Run CoT (Chain-of-Thought) Ablation Experiment
Re-runs temporal level tests (L3-L6) with a structured CoT scratchpad prompt appended.
Reuses exact same samples/images from prior experiment results.
"""

import sys
import os
import re
import glob
import json
import argparse
import time
from typing import List, Dict, Tuple, Optional
from datetime import datetime

sys.path.append('.')

from src.model_client import (
    DummyModelClient, NovitaModelClient, DashScopeModelClient,
    XAIModelClient, GoogleModelClient, AnthropicModelClient,
    OpenAIModelClient, SiliconFlowModelClient, OpenRouterModelClient
)
from src.data_structures import TestResult, save_results, load_results, create_summary
from src.temporal_levels.chess.verification_generator import ChessVerificationGenerator
from src.temporal_levels.xiangqi.verification_generator import XiangqiVerificationGenerator

# Import rule clarification constants
from src.temporal_levels.chess.standard_temporal_level import (
    RULE_CLARIFICATIONS as CHESS_RULE_CLARIFICATIONS,
    LEVEL_RULE_MAPPING as CHESS_LEVEL_RULE_MAPPING,
)
from src.temporal_levels.xiangqi.standard_temporal_level import (
    RULE_CLARIFICATIONS as XIANGQI_RULE_CLARIFICATIONS,
    LEVEL_RULE_MAPPING as XIANGQI_LEVEL_RULE_MAPPING,
)


# ===== CoT Scratchpad Template =====
# Step 5 uses {question} placeholder to be filled per-case
COT_TEMPLATE = """Analyze this step-by-step using the following scratchpad format:
1. State Identification: List the exact start and end coordinates of the moving piece.
2. Rule Retrieval: State the exact movement and capture rules for this specific piece type.
3. Trajectory Mapping: List every square the piece will pass through.
4. Constraint Checking: Check the start, path, and end squares against all rules and constraints identified in Step 2.
5. Final Conclusion: Based on the above, {question} (Yes/No/Unknown)"""


# ===== Piece symbol mappings for verification reconstruction =====
CHESS_PIECE_SYMBOLS = {
    ('white', 'king'): 'K', ('white', 'queen'): 'Q', ('white', 'rook'): 'R',
    ('white', 'bishop'): 'B', ('white', 'knight'): 'N', ('white', 'pawn'): 'P',
    ('black', 'king'): 'k', ('black', 'queen'): 'q', ('black', 'rook'): 'r',
    ('black', 'bishop'): 'b', ('black', 'knight'): 'n', ('black', 'pawn'): 'p',
}

XIANGQI_PIECE_SYMBOLS = {
    ('red', 'king'): 'K', ('red', 'advisor'): 'A', ('red', 'bishop'): 'B',
    ('red', 'knight'): 'N', ('red', 'rook'): 'R', ('red', 'cannon'): 'C', ('red', 'pawn'): 'P',
    ('black', 'king'): 'k', ('black', 'advisor'): 'a', ('black', 'bishop'): 'b',
    ('black', 'knight'): 'n', ('black', 'rook'): 'r', ('black', 'cannon'): 'c', ('black', 'pawn'): 'p',
}


def get_model_client(model_type: str, dummy_pass_rate: float = 0.8):
    """Get model client based on type (matches run_comp_ladder.py pattern)"""
    if model_type == 'dummy':
        print(f"\n  Using Dummy Model Client (pass_rate={dummy_pass_rate})")
        return DummyModelClient(verification_pass_rate=dummy_pass_rate)
    elif model_type == 'novita':
        print("\n  Using Novita Model Client")
        return NovitaModelClient()
    elif model_type == 'dashscope':
        print("\n  Using DashScope Model Client")
        return DashScopeModelClient()
    elif model_type == 'xai':
        print("\n  Using XAI Model Client")
        return XAIModelClient()
    elif model_type == 'google':
        print("\n  Using Google Model Client")
        return GoogleModelClient()
    elif model_type == 'anth':
        print("\n  Using Anthropic Model Client")
        return AnthropicModelClient()
    elif model_type == 'openai':
        print("\n  Using OpenAI Model Client")
        return OpenAIModelClient()
    elif model_type == 'sf':
        print("\n  Using SiliconFlow Model Client")
        return SiliconFlowModelClient()
    elif model_type == 'openrouter':
        print("\n  Using OpenRouter Model Client")
        return OpenRouterModelClient()
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def find_results_file(input_base: str, game: str, mode: str, source_model: str, level: int) -> str:
    """
    Discover the results JSON file from prior experiment runs.

    Mirrors run_textonly.load_reference_results: matches level_<N>_results.json
    at any depth under the source-model directory.

    Returns:
        Absolute path to the level_N_results.json file
    """
    model_dir = os.path.join(input_base, game, f"{mode} mode", f"{source_model}-{game}-{mode}")
    if not os.path.isdir(model_dir):
        raise FileNotFoundError(f"Source model directory not found: {model_dir}")

    pattern = os.path.join(model_dir, "**", f"level_{level}_results.json")
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        pattern = os.path.join(model_dir, "**", f"*level_{level}*results.json")
        matches = glob.glob(pattern, recursive=True)
    if not matches:
        raise FileNotFoundError(f"No results file for level {level} found under {model_dir}")
    if len(matches) > 1:
        print(f"  Warning: Multiple results files found for level {level}, using first: {matches[0]}")

    return matches[0]


def resolve_image_paths(image_paths: List[str], level_dir: str) -> List[str]:
    """
    Convert image paths from results JSON to absolute paths.

    The relative paths stored in results JSON have inconsistent prefixes across
    models, so we extract just the filename and look for it in the level directory
    (where the results JSON and images live together).

    Args:
        image_paths: Paths from results (may have unreliable relative prefixes)
        level_dir: Directory containing the results JSON and image files

    Returns:
        List of absolute image paths
    """
    resolved = []
    for rel_path in image_paths:
        # Extract just the filename (ignore unreliable directory prefix)
        normalized = rel_path.replace("\\", "/")
        filename = os.path.basename(normalized)
        abs_path = os.path.join(level_dir, filename)
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"Image not found: {abs_path}")
        resolved.append(abs_path)
    return resolved


def reconstruct_verification_data(verification_expected: str, game: str) -> Dict:
    """
    Reconstruct verification_keywords and verification_pieces from verification_expected string.

    The expected format is: "State 1: Color Piece at sq, Color Piece at sq; State 2: ..."
    """
    if game == "chess":
        color_pattern = r"(White|Black)"
        piece_pattern = r"(King|Queen|Rook|Bishop|Knight|Pawn)"
        symbol_map = CHESS_PIECE_SYMBOLS
    else:  # xiangqi
        color_pattern = r"(Red|Black)"
        piece_pattern = r"(King|Advisor|Bishop|Knight|Rook|Cannon|Pawn)"
        symbol_map = XIANGQI_PIECE_SYMBOLS

    # Match "Color PieceType at position" patterns
    full_pattern = rf'{color_pattern}\s+{piece_pattern}\s+at\s+([a-i]\d+)'

    keywords = []
    pieces = []

    # Split by state boundaries
    state_sections = re.split(r';\s*State\s+', verification_expected)
    # First section starts with "State N: ..."
    for state_idx, section in enumerate(state_sections):
        # Extract state number
        state_match = re.match(r'(?:State\s+)?(\d+):\s*(.*)', section)
        if not state_match:
            continue
        state_num = int(state_match.group(1))
        state_content = state_match.group(2)

        for match in re.finditer(full_pattern, state_content):
            color = match.group(1).lower()
            piece_type = match.group(2).lower()
            position = match.group(3).lower()

            keywords.append(position)
            keywords.append(piece_type)
            keywords.append(color)

            symbol = symbol_map.get((color, piece_type), '?')
            pieces.append({
                'color': color,
                'type': piece_type,
                'position': position,
                'state_index': state_num,
                'symbol': symbol,
            })

    return {
        'verification_keywords': keywords,
        'verification_pieces': pieces,
    }


def get_rule_clarification(game: str, level: int) -> Optional[str]:
    """Get rule clarification text for a given game and level."""
    if game == "chess":
        rule_type = CHESS_LEVEL_RULE_MAPPING.get(level)
        if rule_type:
            return CHESS_RULE_CLARIFICATIONS.get(rule_type)
    else:  # xiangqi
        rule_type = XIANGQI_LEVEL_RULE_MAPPING.get(level)
        if rule_type:
            return XIANGQI_RULE_CLARIFICATIONS.get(rule_type)
    return None


def build_image_ref(num_images: int) -> str:
    """Build image-to-state reference text."""
    refs = [f"Image {i+1} shows State {i+1}" for i in range(num_images)]
    return ". ".join(refs) + "."


def build_cot_prompt(verification_question: str, question: str,
                     num_images: int, game: str, level: int) -> str:
    """
    Build the full prompt with CoT scratchpad inserted.

    Faithfully reconstructs the original prompt template, adding the CoT
    scratchpad between the main question and the answer format instruction.
    """
    image_ref = build_image_ref(num_images)

    # Get rule clarification (prepended to question, matching original behavior)
    rule_clarification = get_rule_clarification(game, level)

    # Build test question with rule clarification
    if rule_clarification:
        test_q = f"{rule_clarification}\n{question}"
    else:
        test_q = question

    # Build CoT with the actual question in step 5
    cot_scratchpad = COT_TEMPLATE.format(question=question)

    prompt = f"""Look at these board states carefully.

{image_ref}

The images are shown in chronological order and represent consecutive states.

First, a verification question to ensure you see the states correctly:
{verification_question}

For verification, use this format:
- List pieces as: [Color] [Piece Type] at [square]
- Separate states with semicolons

Now, the main question:
{test_q}

{cot_scratchpad}

Please answer both questions. Format your response exactly as:
Verification: [your answer]
Main answer: [yes/no/unknown]"""

    return prompt


def parse_combined_response(response: str) -> Tuple[str, str]:
    """
    Parse model response into verification answer and test answer.
    Standalone reimplementation of TemporalLevelBase._parse_combined_response().

    Handles the case where the model puts multi-line CoT reasoning after
    "Main answer:" instead of a single-line yes/no.
    """
    lines = response.split('\n')
    verification_response = ""
    test_response = ""
    main_answer_line_idx = -1

    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if line_lower.startswith('verification:'):
            verification_response = line.split(':', 1)[1].strip()
        elif line_lower.startswith('main answer:') or line_lower.startswith('main:'):
            main_answer_line_idx = i
            test_response = line.split(':', 1)[1].strip()

    # If main answer was found but is multi-line (model put CoT after "Main answer:"),
    # capture everything from that line onwards
    if main_answer_line_idx >= 0 and main_answer_line_idx < len(lines) - 1:
        remaining = '\n'.join(lines[main_answer_line_idx:])
        test_response = remaining.split(':', 1)[1].strip()

    # Fallback if parsing failed
    if not verification_response or not test_response:
        non_empty = [l.strip() for l in lines if l.strip()]
        if len(non_empty) >= 2:
            verification_response = verification_response or non_empty[0]
            test_response = test_response or non_empty[-1]
        else:
            verification_response = verification_response or response[:len(response)//2]
            test_response = test_response or response[len(response)//2:]

    return verification_response, test_response


def extract_answer(response: str) -> str:
    """
    Extract yes/no/unknown answer from model response.
    Standalone reimplementation of TemporalLevelBase._extract_answer().

    Uses word-boundary matching to avoid false positives (e.g., "cannot" -> "no",
    "eyes" -> "yes"). For long responses (CoT), prioritizes the tail (conclusion)
    over the head (start of reasoning may contain contradictory yes/no).
    """
    response_lower = response.lower().strip()

    # Short response: just check the whole thing
    if len(response_lower) < 50:
        if re.search(r'\byes\b', response_lower):
            return "yes"
        elif re.search(r'\bno\b', response_lower):
            return "no"
        return "unknown"

    # Long response (likely CoT): check tail first (conclusion), then head
    tail = response_lower[-60:]
    if re.search(r'\byes\b', tail):
        return "yes"
    elif re.search(r'\bno\b', tail):
        return "no"

    # Fallback: check head
    head = response_lower[:30]
    if re.search(r'\byes\b', head):
        return "yes"
    elif re.search(r'\bno\b', head):
        return "no"

    return "unknown"


def run_cot_ablation(args):
    """Main orchestrator for CoT ablation experiment."""

    print("\n" + "=" * 70)
    print("CoT ABLATION EXPERIMENT")
    print("=" * 70)
    print(f"Model: {args.model}")
    print(f"Game: {args.game}")
    print(f"Mode: {args.mode}")
    print(f"Levels: {args.levels}")
    print(f"Source model: {args.source_model}")
    print(f"Input base: {args.input_base}")
    print(f"Output base: {args.output_base}")
    print("=" * 70)

    # ===== Pre-flight check: verify all JSON files and images exist =====
    print("\nPre-flight check: verifying all data files...")
    preflight_ok = True
    total_images = 0
    level_data = {}  # level -> (results_file, level_dir, prior_results)

    for level in args.levels:
        # Check results JSON exists
        try:
            results_file = find_results_file(
                args.input_base, args.game, args.mode, args.source_model, level
            )
        except FileNotFoundError as e:
            print(f"  FAIL: Level {level} - {e}")
            preflight_ok = False
            continue

        level_dir = os.path.dirname(results_file)
        prior_results = load_results(results_file)
        prior_results = [r for r in prior_results if r.test_layer == level]

        if not prior_results:
            print(f"  FAIL: Level {level} - no test cases found in {results_file}")
            preflight_ok = False
            continue

        # Check all images exist
        missing = []
        for r in prior_results:
            for rel_path in r.image_paths:
                filename = os.path.basename(rel_path.replace("\\", "/"))
                abs_path = os.path.join(level_dir, filename)
                if not os.path.isfile(abs_path):
                    missing.append(abs_path)
                total_images += 1

        if missing:
            print(f"  FAIL: Level {level} - {len(missing)} images missing:")
            for m in missing[:5]:
                print(f"    {m}")
            if len(missing) > 5:
                print(f"    ... and {len(missing) - 5} more")
            preflight_ok = False
        else:
            print(f"  OK: Level {level} - {len(prior_results)} cases, all images found")
            level_data[level] = (results_file, level_dir, prior_results)

    if not preflight_ok:
        print("\nPre-flight check FAILED. Aborting.")
        sys.exit(1)

    print(f"\nPre-flight check passed: {len(level_data)} levels, {total_images} images verified.")

    # Initialize model client
    model_client = get_model_client(args.model, args.dummy_pass_rate)

    # Select verification generator
    if args.game == "chess":
        verification_gen = ChessVerificationGenerator()
    else:
        verification_gen = XiangqiVerificationGenerator()

    all_level_results = []

    for level in args.levels:
        if level not in level_data:
            continue

        results_file, level_dir, prior_results = level_data[level]

        print(f"\n{'=' * 60}")
        print(f"LEVEL {level} - {args.game} - {args.mode} - {len(prior_results)} cases")
        print(f"{'=' * 60}")

        # 2. Process each test case
        results = []
        stats = {
            'total': 0,
            'verification_passed': 0,
            'verification_failed': 0,
            'test_correct': 0,
            'test_incorrect': 0,
            'test_correct_given_verified': 0,
        }

        for i, prior in enumerate(prior_results, 1):
            stats['total'] += 1
            print(f"  [{i}/{len(prior_results)}] {prior.case_id}...", end=" ")

            # Resolve image paths
            try:
                abs_image_paths = resolve_image_paths(prior.image_paths, level_dir)
            except FileNotFoundError as e:
                print(f"IMAGE MISSING: {e}")
                stats['verification_failed'] += 1
                result = TestResult(
                    test_type="temporal_level",
                    test_layer=level,
                    case_id=prior.case_id,
                    verification_question=prior.verification_question,
                    verification_expected=prior.verification_expected,
                    verification_response="error: image not found",
                    verification_passed=False,
                    question=prior.question,
                    expected_answer=prior.expected_answer,
                    model_response="error: image not found",
                    correct=False,
                    image_paths=prior.image_paths,
                    model_name=model_client.model_name,
                )
                results.append(result)
                continue

            # Build CoT prompt
            prompt = build_cot_prompt(
                verification_question=prior.verification_question,
                question=prior.question,
                num_images=len(abs_image_paths),
                game=args.game,
                level=level,
            )

            # Query model
            try:
                raw_response = model_client.query(prompt, abs_image_paths)

                # Parse response
                verification_response, test_response = parse_combined_response(raw_response)

                # Reconstruct verification data for checking
                verif_data = reconstruct_verification_data(
                    prior.verification_expected, args.game
                )
                case_for_verification = {
                    'verification_keywords': verif_data['verification_keywords'],
                    'verification_pieces': verif_data['verification_pieces'],
                }

                # Check verification
                verification_passed = verification_gen.check_verification_answer(
                    verification_response, case_for_verification
                )

                if verification_passed:
                    stats['verification_passed'] += 1
                    model_answer = extract_answer(test_response)
                    correct = (model_answer.lower() == prior.expected_answer.lower())
                    if correct:
                        stats['test_correct'] += 1
                        stats['test_correct_given_verified'] += 1
                        print(f"V:pass A:correct ({prior.expected_answer})")
                    else:
                        stats['test_incorrect'] += 1
                        print(f"V:pass A:wrong (exp={prior.expected_answer}, got={model_answer})")
                else:
                    stats['verification_failed'] += 1
                    correct = False
                    print(f"V:fail")

            except Exception as e:
                print(f"ERROR: {e}")
                raw_response = f"error: {e}"
                verification_response = "error"
                test_response = "error"
                verification_passed = False
                correct = False
                stats['verification_failed'] += 1

            # Record result (store full raw response)
            result = TestResult(
                test_type="temporal_level",
                test_layer=level,
                case_id=prior.case_id,
                verification_question=prior.verification_question,
                verification_expected=prior.verification_expected,
                verification_response=verification_response,
                verification_passed=verification_passed,
                question=prior.question,
                expected_answer=prior.expected_answer,
                model_response=raw_response,  # Full raw response for logging
                correct=correct,
                image_paths=prior.image_paths,
                model_name=model_client.model_name,
            )
            results.append(result)

            # Rate limiting
            if args.rate_limit > 0 and i % args.rate_limit == 0 and i < len(prior_results):
                print(f"  Rate limit: pausing {args.rate_pause}s...")
                time.sleep(args.rate_pause)

        # Print level summary
        print(f"\n  --- Level {level} Summary ---")
        if stats['total'] > 0:
            v_rate = stats['verification_passed'] / stats['total']
            print(f"  Verification: {stats['verification_passed']}/{stats['total']} ({v_rate:.1%})")
        if stats['verification_passed'] > 0:
            a_rate = stats['test_correct_given_verified'] / stats['verification_passed']
            print(f"  Accuracy (verified): {stats['test_correct_given_verified']}/{stats['verification_passed']} ({a_rate:.1%})")
        if stats['total'] > 0:
            overall = stats['test_correct'] / stats['total']
            print(f"  Overall accuracy: {stats['test_correct']}/{stats['total']} ({overall:.1%})")

        # Save results (with timestamp to avoid overwriting previous runs)
        timestamp = datetime.now().strftime("%m%d_%H%M%S")
        output_dir = os.path.join(
            args.output_base, args.game, args.mode, args.source_model
        )
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"level_{level}_cot_results_{timestamp}.json")

        summary = create_summary(results, stats)
        save_results(results, output_file, summary=summary)

        all_level_results.append({
            "level": level,
            "stats": stats,
            "output_file": output_file,
        })

    # Final summary across all levels
    if all_level_results:
        print(f"\n{'=' * 70}")
        print("OVERALL SUMMARY")
        print(f"{'=' * 70}")
        for lr in all_level_results:
            s = lr['stats']
            v_rate = s['verification_passed'] / s['total'] if s['total'] > 0 else 0
            a_rate = s['test_correct_given_verified'] / s['verification_passed'] if s['verification_passed'] > 0 else 0
            overall = s['test_correct'] / s['total'] if s['total'] > 0 else 0
            print(f"  Level {lr['level']}: V={v_rate:.1%}  A(verified)={a_rate:.1%}  Overall={overall:.1%}")
            print(f"    Saved to: {lr['output_file']}")
        print(f"{'=' * 70}")


def main():
    parser = argparse.ArgumentParser(
        description="Run CoT Ablation Experiment - Re-runs temporal level tests with CoT scratchpad",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Required arguments
    parser.add_argument(
        "-m", "--model",
        type=str,
        required=True,
        choices=["dummy", "novita", "dashscope", "xai", "google", "anth", "openai", "sf", "openrouter"],
        help="Model provider to use"
    )
    parser.add_argument(
        "-l", "--levels",
        type=int,
        nargs="+",
        required=True,
        help="Levels to run (e.g., -l 3 4 5 6)"
    )
    parser.add_argument(
        "--source-model",
        type=str,
        required=True,
        help="Directory prefix for source data (e.g., gpt5.2, qwen235b)"
    )

    # Game and mode
    parser.add_argument(
        "-g", "--game",
        type=str,
        choices=["chess", "xiangqi"],
        default="chess",
        help="Game type (default: chess)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["predictive", "explicit"],
        default="predictive",
        help="Test mode (default: predictive)"
    )

    # Paths
    parser.add_argument(
        "--input-base",
        type=str,
        default="./output/rule complexity ladder",
        help="Base path for prior results (default: ./output/rule complexity ladder)"
    )
    parser.add_argument(
        "--output-base",
        type=str,
        default="./output/cot_ablation",
        help="Output path for CoT results (default: ./output/cot_ablation)"
    )

    # Model config
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
    run_cot_ablation(args)


if __name__ == "__main__":
    main()
