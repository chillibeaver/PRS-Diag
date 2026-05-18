"""
Base class for Temporal Level Tests
Provides common functionality for test execution and verification
This is a GAME-AGNOSTIC base class.
"""

import os
from typing import List, Dict, Tuple
from datetime import datetime
from abc import ABC, abstractmethod
from PIL import Image, ImageDraw, ImageFont
from ..data_structures import TestResult, save_results, create_summary
# NOTE: Do NOT import board_generator here - each game provides its own
import time


class TemporalLevelBase(ABC):
    """Abstract base class for temporal level tests (game-agnostic)"""

    def __init__(self,
                 level: int,
                 base_output_dir: str,
                 n_cases: int = 100,
                 seed: int = 42,
                 auto_timestamp: bool = True,
                 rate_limit_requests: int = 0,
                 rate_limit_pause: int = 0):
        """
        Initialize Temporal Level Base

        Args:
            level: Level number (1-6)
            base_output_dir: Base directory for output files
            n_cases: Total number of test cases
            seed: Random seed for reproducibility
            auto_timestamp: If True, append timestamp to output directory
            rate_limit_requests: Number of requests before pausing
            rate_limit_pause: Seconds to pause
        """
        self.level = level
        self.rate_limit_pause = rate_limit_pause
        self.rate_limit_requests = rate_limit_requests

        if auto_timestamp:
            timestamp = datetime.now().strftime("%m%d_%H%M%S")
            self.output_dir = f"{base_output_dir}_{timestamp}"
        else:
            self.output_dir = base_output_dir

        os.makedirs(self.output_dir, exist_ok=True)

        # Board generator - MUST be set by subclass
        # Subclasses should set: self.board_gen = SomeBoardGenerator()
        self.board_gen = None

        self.test_cases = []
        self.n_cases = n_cases
        self.seed = seed

        # Verification generator - MUST be set by subclass
        # Subclasses should set: self.verification_gen = SomeVerificationGenerator()
        self.verification_gen = None

    @abstractmethod
    def generate_test_cases(self) -> List[Dict]:
        """
        Generate test cases (must be implemented by subclass)

        Returns:
            List of test case dictionaries
        """
        pass

    def _get_verification_generator(self):
        """
        Get the verification generator.
        Subclasses can override this or set self.verification_gen in __init__
        """
        if self.verification_gen is None:
            raise NotImplementedError(
                "Subclass must set self.verification_gen or override _get_verification_generator()"
            )
        return self.verification_gen

    def _get_board_generator(self):
        """
        Get the board generator.
        Subclasses must set self.board_gen in __init__
        """
        if self.board_gen is None:
            raise NotImplementedError(
                "Subclass must set self.board_gen in __init__"
            )
        return self.board_gen

    def create_test_images(self):
        """Generate images for all test cases with State labels"""
        board_gen = self._get_board_generator()

        print(f"\nCreating test images for Level {self.level}...")
        print("=" * 60)

        for i, case in enumerate(self.test_cases, 1):
            image_paths = []

            # Get states from case
            states = case.get('states', [])

            for state_idx, state in enumerate(states):
                pieces = state.get('pieces', {})
                squares = state.get('squares', [])

                if pieces:
                    img = board_gen.create_board_with_pieces(
                        pieces=pieces,
                        highlighted_squares=squares
                    )
                else:
                    img = board_gen.create_empty_board(
                        highlighted_squares=squares
                    )

                # Add "State N" label to the image
                img = self._add_state_label(img, state_idx + 1)

                img_path = os.path.join(
                    self.output_dir,
                    f"{case['case_id']}_state_{state_idx+1}.png"
                )
                img.save(img_path)
                image_paths.append(img_path)

            case["image_paths"] = image_paths

            if i % 10 == 0 or i == len(self.test_cases):
                print(f"  Progress: {i}/{len(self.test_cases)} cases created")

        print(f"✓ All {len(self.test_cases)} test cases created\n")

    def _add_state_label(self, img: Image.Image, state_num: int) -> Image.Image:
        """
        Add 'State N' label to the top of the image

        Args:
            img: Original board image
            state_num: State number (1, 2, 3, etc.)

        Returns:
            New image with label at the top
        """
        # Create a new image with extra space at the top for label
        label_height = 50
        new_img = Image.new(
            'RGB', (img.width, img.height + label_height), 'white')

        # Paste original image below the label area
        new_img.paste(img, (0, label_height))

        # Draw the label
        draw = ImageDraw.Draw(new_img)

        # Try to load a font, fall back to default if needed
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except:
            try:
                font = ImageFont.truetype("Arial.ttf", 28)
            except:
                try:
                    font = ImageFont.truetype(
                        "/System/Library/Fonts/Helvetica.ttc", 28)
                except:
                    font = ImageFont.load_default()

        # Draw "State N" text
        text = f"State {state_num}"

        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (new_img.width - text_width) // 2
        y = (label_height - text_height) // 2

        draw.text((x, y), text, fill='black', font=font)

        return new_img

    def generate_combined_prompt(self, case: Dict) -> str:
        """
        Generate combined prompt with verification question first, then test question
        """
        verification_q = case.get('verification_question', '')
        test_q = case['question']

        # Count the number of states
        num_states = len(case.get('states', []))

        # Create explicit image-to-state mapping
        if num_states == 2:
            image_ref = "Image 1 shows State 1. Image 2 shows State 2."
        elif num_states == 3:
            image_ref = "Image 1 shows State 1. Image 2 shows State 2. Image 3 shows State 3."
        elif num_states == 4:
            image_ref = "Image 1 shows State 1. Image 2 shows State 2. Image 3 shows State 3. Image 4 shows State 4."
        else:
            image_refs = [
                f"Image {i+1} shows State {i+1}" for i in range(num_states)]
            image_ref = ". ".join(image_refs) + "."

        prompt = f"""Look at these board states carefully.

{image_ref}

The images are shown in chronological order and represent consecutive states.

First, a simple verification question to make sure you see the states correctly:
{verification_q}

For verification, use this format:
- List pieces as: [Color] [Piece Type] at [square]
- Separate states with semicolons

Now, the main question:
{test_q}

Please answer both questions. Format your response exactly as:
Verification: [your answer]
Main answer: [yes/no/unknown]"""

        return prompt

    def run_test(self, model_client, save_results_flag: bool = True) -> Tuple[List[TestResult], Dict]:
        """
        Run the test with per-case verification

        Args:
            model_client: Model client for querying
            save_results_flag: Whether to save results to file

        Returns:
            Tuple of (results_list, statistics_dict)
        """
        results = []
        stats = {
            'total': 0,
            'verification_passed': 0,
            'verification_failed': 0,
            'test_correct': 0,
            'test_incorrect': 0,
            'test_correct_given_verified': 0,
        }

        verification_gen = self._get_verification_generator()

        print(f"{'=' * 60}")
        print(f"Running Temporal Level {self.level}")
        print("(Each case includes verification question + test question)")
        print(f"{'=' * 60}\n")

        for i, case in enumerate(self.test_cases, 1):
            print(f"[{i}/{len(self.test_cases)}] Testing {case['case_id']}...")

            stats['total'] += 1

            prompt = self.generate_combined_prompt(case)

            try:
                # Query model with combined prompt and ALL images
                response = model_client.query(prompt, case["image_paths"])

                # Parse response
                verification_response, test_response = self._parse_combined_response(
                    response)

                # Check verification
                verification_passed = verification_gen.check_verification_answer(
                    verification_response,
                    case
                )

                if verification_passed:
                    stats['verification_passed'] += 1
                    print(f"  ✓ Verification passed")

                    # Extract test answer
                    model_answer = self._extract_answer(test_response)
                    correct = (model_answer.lower() ==
                               case["expected"].lower())

                    if correct:
                        stats['test_correct'] += 1
                        stats['test_correct_given_verified'] += 1
                        print(
                            f"  ✓ Test correct (Expected: {case['expected']}, Got: {model_answer})")
                    else:
                        stats['test_incorrect'] += 1
                        print(
                            f"  ✗ Test incorrect (Expected: {case['expected']}, Got: {model_answer})")

                else:
                    stats['verification_failed'] += 1
                    correct = False
                    model_answer = "N/A (verification failed)"
                    print(f"  ✗ Verification failed")
                    print(
                        f"    Expected: {case.get('verification_expected', 'N/A')}")
                    print(f"    Got: {verification_response[:50]}...")

                # Rate limiting
                if self.rate_limit_requests > 0 and i % self.rate_limit_requests == 0 and i < len(self.test_cases):
                    print(
                        f"\n  ⏸️  Rate limit: Processed {i} requests, pausing for {self.rate_limit_pause} seconds...")
                    time.sleep(self.rate_limit_pause)
                    print(f"  ▶️  Resuming...\n")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                verification_response = "error"
                test_response = "error"
                verification_passed = False
                model_answer = "error"
                correct = False
                stats['verification_failed'] += 1

            # Record result
            result = TestResult(
                test_type="temporal_level",
                test_layer=self.level,
                case_id=case["case_id"],
                verification_question=case.get('verification_question', ''),
                verification_expected=case.get('verification_expected', ''),
                verification_response=verification_response,
                verification_passed=verification_passed,
                question=case["question"],
                expected_answer=case["expected"],
                model_response=test_response,
                correct=correct,
                image_paths=case["image_paths"],
                model_name=model_client.model_name
            )
            results.append(result)

        # Print results
        self._print_results_summary(results, stats)

        if save_results_flag:
            output_file = os.path.join(
                self.output_dir, f"level_{self.level}_results.json")
            summary = create_summary(results, stats, self.test_cases)
            save_results(results, output_file, summary=summary)

        return results, stats

    def _parse_combined_response(self, response: str) -> Tuple[str, str]:
        """
        Parse model response into verification answer and test answer
        """
        lines = response.split('\n')

        verification_response = ""
        test_response = ""

        for line in lines:
            line_lower = line.lower().strip()

            if line_lower.startswith('verification:'):
                verification_response = line.split(':', 1)[1].strip()
            elif line_lower.startswith('main answer:') or line_lower.startswith('main:'):
                test_response = line.split(':', 1)[1].strip()

        # If parsing failed, try to extract from full response
        if not verification_response or not test_response:
            non_empty = [l.strip() for l in lines if l.strip()]
            if len(non_empty) >= 2:
                verification_response = non_empty[0]
                test_response = non_empty[1]
            else:
                verification_response = response[:len(response)//2]
                test_response = response[len(response)//2:]

        return verification_response, test_response

    def _extract_answer(self, response: str) -> str:
        """Extract answer from model response"""
        response_lower = response.lower().strip()

        if "yes" in response_lower[:20]:
            return "yes"
        elif "no" in response_lower[:20]:
            return "no"
        else:
            return "unknown"

    def _print_results_summary(self, results: List[TestResult], stats: Dict):
        """Print detailed results summary"""
        if not results:
            return

        print(f"\n{'=' * 60}")
        print(f"RESULTS SUMMARY - Level {self.level}")
        print(f"{'=' * 60}")

        # Verification statistics
        verification_rate = stats['verification_passed'] / \
            stats['total'] if stats['total'] > 0 else 0
        print(f"\nBoard Recognition:")
        print(
            f"  Verified correctly: {stats['verification_passed']}/{stats['total']} ({verification_rate:.1%})")
        print(
            f"  Failed to recognize: {stats['verification_failed']}/{stats['total']} ({1-verification_rate:.1%})")

        # Test accuracy (only among verified cases)
        if stats['verification_passed'] > 0:
            accuracy_given_verified = stats['test_correct_given_verified'] / \
                stats['verification_passed']
            print(f"\nTest Accuracy (among recognized cases):")
            print(
                f"  Correct: {stats['test_correct_given_verified']}/{stats['verification_passed']} ({accuracy_given_verified:.1%})")
        else:
            print(f"\n⚠️  No cases passed verification!")

        # Overall accuracy (including verification failures)
        overall_accuracy = stats['test_correct'] / \
            stats['total'] if stats['total'] > 0 else 0
        print(f"\nOverall Accuracy (all cases):")
        print(
            f"  Correct: {stats['test_correct']}/{stats['total']} ({overall_accuracy:.1%})")

        # Breakdown by type (only verified cases)
        self._print_type_breakdown(results)

        print(f"{'=' * 60}\n")

    def _print_type_breakdown(self, results: List[TestResult]):
        """Print accuracy breakdown by type"""
        print(f"\nAccuracy by type (verified cases only):")
        type_results = {}

        for result in results:
            if not result.verification_passed:
                continue

            case = next(
                (c for c in self.test_cases if c['case_id'] == result.case_id), None)
            if case:
                case_type = case.get('type', 'unknown')
                subtype = case.get('subtype', '')

                # Overall by type
                if case_type not in type_results:
                    type_results[case_type] = {
                        'correct': 0, 'total': 0, 'subtypes': {}}
                type_results[case_type]['total'] += 1
                if result.correct:
                    type_results[case_type]['correct'] += 1

                # By subtype
                if subtype:
                    if subtype not in type_results[case_type]['subtypes']:
                        type_results[case_type]['subtypes'][subtype] = {
                            'correct': 0, 'total': 0}
                    type_results[case_type]['subtypes'][subtype]['total'] += 1
                    if result.correct:
                        type_results[case_type]['subtypes'][subtype]['correct'] += 1

        for case_type in sorted(type_results.keys()):
            stats_item = type_results[case_type]
            acc = stats_item['correct'] / \
                stats_item['total'] if stats_item['total'] > 0 else 0
            print(
                f"  {case_type:20s}: {acc:5.1%} ({stats_item['correct']:2d}/{stats_item['total']:2d})")

            # Show subtypes
            for subtype, sub_stats in sorted(stats_item['subtypes'].items()):
                sub_acc = sub_stats['correct'] / \
                    sub_stats['total'] if sub_stats['total'] > 0 else 0
                print(
                    f"    └─ {subtype:23s}: {sub_acc:5.1%} ({sub_stats['correct']:2d}/{sub_stats['total']:2d})")
