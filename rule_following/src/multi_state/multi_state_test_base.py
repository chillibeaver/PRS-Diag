"""
Base class for all Multi-State Tests (formerly Temporal Tests)
Provides common functionality for test execution, verification, and result reporting
"""

import os
import time
from typing import List, Dict, Tuple
from datetime import datetime
from abc import ABC, abstractmethod
from PIL import Image, ImageDraw, ImageFont
from ..data_structures import TestResult, save_results, create_summary


class MultiStateTestBase(ABC):
    """Abstract base class for multi-state tests (game-agnostic)"""

    def __init__(self,
                 test_name: str,
                 test_layer: int,
                 base_output_dir: str,
                 # Changed from n_cases_per_type to n_cases (total)
                 n_cases: int = 100,
                 n_cases_per_type: int = None,  # Kept for backward compatibility
                 seed: int = 42,
                 auto_timestamp: bool = True,
                 rate_limit_requests: int = 0,
                 rate_limit_pause: int = 0):
        """
        Initialize Multi-State Test Base

        Args:
            test_name: Name of the test
            test_layer: Layer/ID
            base_output_dir: Base directory for output files
            n_cases: Total number of cases to generate
            n_cases_per_type: (Deprecated) Multiplier for backward compatibility
            seed: Random seed
        """
        self.test_name = test_name
        self.test_layer = test_layer
        self.seed = seed
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_pause = rate_limit_pause

        # Handle n_cases vs n_cases_per_type
        if n_cases_per_type is not None:
            # Approximate conversion if old parameter is used
            # Assuming average of ~4 types per test, we scale it up
            self.n_cases = n_cases_per_type * 4
        else:
            self.n_cases = n_cases

        if auto_timestamp:
            timestamp = datetime.now().strftime("%m%d_%H%M%S")
            self.output_dir = f"{base_output_dir}_{timestamp}"
        else:
            self.output_dir = base_output_dir

        os.makedirs(self.output_dir, exist_ok=True)

        self.test_cases = []

        # These must be set by the subclass
        self.board_gen = None
        self.verification_gen = None

    @abstractmethod
    def generate_test_cases(self) -> List[Dict]:
        """Generate test cases (must be implemented by subclass)"""
        pass

    def create_test_images(self):
        """Generate images for all test cases with state labels"""
        if not self.board_gen:
            raise NotImplementedError(
                "Subclass must initialize self.board_gen")

        print(f"\nCreating test images for {self.test_name}...")
        print("="*60)

        for i, case in enumerate(self.test_cases, 1):
            image_paths = []

            for state_idx, state in enumerate(case.get('states', [])):
                pieces = state.get('pieces', {})
                squares = state.get('squares', [])

                if pieces:
                    img = self.board_gen.create_board_with_pieces(
                        pieces=pieces,
                        highlighted_squares=squares
                    )
                else:
                    img = self.board_gen.create_empty_board(
                        highlighted_squares=squares
                    )

                # Add "State N" label
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
        """Add 'State N' label to the top of the image"""
        label_height = 50
        new_img = Image.new(
            'RGB', (img.width, img.height + label_height), 'white')
        new_img.paste(img, (0, label_height))
        draw = ImageDraw.Draw(new_img)

        try:
            # Try common fonts
            try:
                font = ImageFont.truetype("arial.ttf", 28)
            except:
                try:
                    font = ImageFont.truetype("Arial.ttf", 28)
                except:
                    font = ImageFont.truetype(
                        "/System/Library/Fonts/Helvetica.ttc", 28)
        except:
            font = ImageFont.load_default()

        text = f"State {state_num}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (new_img.width - text_width) // 2
        y = (label_height - text_height) // 2
        draw.text((x, y), text, fill='black', font=font)

        return new_img

    def generate_combined_prompt(self, case: Dict) -> str:
        """Generate prompt with verification + main question"""
        verification_q = case.get('verification_question', '')
        label = case.get('label', 'These are chess board states.')
        test_q = case['question']
        num_states = len(case.get('states', []))

        # Create explicit image-to-state mapping text
        if num_states <= 4:
            image_refs = [
                f"Image {i+1} shows State {i+1}" for i in range(num_states)]
            image_ref = ". ".join(image_refs) + "."
        else:
            image_ref = f"Images 1-{num_states} show States 1-{num_states} respectively."

        verification_format_example = "State 1: [pieces]; State 2: [pieces]..."

        # Handle Multiple Choice vs Yes/No
        options_text = ""
        answer_format = "[yes/no/unknown]"
        if 'options' in case:
            options = case['options']
            options_text = "\nOptions:\n" + \
                "\n".join([f"{k}) {v}" for k, v in options.items()])
            answer_format = "[A/B/C/D]"

        prompt = f"""Look at these board states carefully.

{image_ref}

{label}

First, a simple verification question to make sure you see the states correctly:
{verification_q}

For the verification answer, use this exact format:
- For each state, list all pieces as: [Color] [Piece Type] at [square]
- Separate states with semicolons
- Example: {verification_format_example}

Now, the main question:
{test_q}
{options_text}

Please answer both questions. Format your response exactly as:
Verification: [your answer using the format above]
Main answer: {answer_format}"""
        return prompt

    def run_test(self, model_client, save_results_flag: bool = True) -> Tuple[List[TestResult], Dict]:
        """Run the test with per-case verification"""
        if not self.verification_gen:
            raise NotImplementedError(
                "Subclass must initialize self.verification_gen")

        results = []
        stats = {
            'total': 0,
            'verification_passed': 0,
            'verification_failed': 0,
            'test_correct': 0,
            'test_incorrect': 0,
            'test_correct_given_verified': 0,
        }

        print(f"{'='*60}")
        print(f"Running {self.test_name}")
        print(f"{'='*60}\n")

        for i, case in enumerate(self.test_cases, 1):
            print(f"[{i}/{len(self.test_cases)}] Testing {case['case_id']}...")
            stats['total'] += 1

            prompt = self.generate_combined_prompt(case)

            try:
                # Query model with ALL images
                response = model_client.query(prompt, case["image_paths"])
                verification_response, test_response = self._parse_combined_response(
                    response)

                verification_passed = self.verification_gen.check_verification_answer(
                    verification_response, case
                )

                if verification_passed:
                    stats['verification_passed'] += 1
                    print(f"  ✓ Verification passed")

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
                    print(f"    Got: {verification_response[:50]}...")

                if self.rate_limit_requests > 0 and i % self.rate_limit_requests == 0 and i < len(self.test_cases):
                    print(
                        f"\n  ⏸️  Rate limit reached. Pausing for {self.rate_limit_pause}s...")
                    time.sleep(self.rate_limit_pause)

            except Exception as e:
                print(f"  ✗ Error: {e}")
                verification_response = "error"
                test_response = "error"
                verification_passed = False
                correct = False
                stats['verification_failed'] += 1

            result = TestResult(
                test_type="multi_state",
                test_layer=self.test_layer,
                case_id=case["case_id"],
                rule_type=case.get('type'),
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

        # Summary printing
        self._print_results_summary(results, stats)

        if save_results_flag:
            output_file = os.path.join(
                self.output_dir, f"results_{self.test_layer}.json")
            summary = create_summary(results, stats, self.test_cases)
            save_results(results, output_file, summary=summary)

        return results, stats

    def _parse_combined_response(self, response: str) -> Tuple[str, str]:
        lines = response.split('\n')
        v_resp = ""
        t_resp = ""
        for line in lines:
            line_lower = line.lower().strip()
            if line_lower.startswith('verification:'):
                v_resp = line.split(':', 1)[1].strip()
            elif line_lower.startswith('main answer:') or line_lower.startswith('main:'):
                t_resp = line.split(':', 1)[1].strip()

        if not v_resp or not t_resp:
            non_empty = [l.strip() for l in lines if l.strip()]
            if len(non_empty) >= 2:
                v_resp = non_empty[0]
                t_resp = non_empty[1]
            else:
                v_resp = response[:len(response)//2]
                t_resp = response[len(response)//2:]
        return v_resp, t_resp

    def _extract_answer(self, response: str) -> str:
        response_lower = response.lower().strip()

        # Check for multiple choice
        if response_lower.startswith(('a)', 'a.', 'a ', 'a:')):
            return "A"
        if response_lower.startswith(('b)', 'b.', 'b ', 'b:')):
            return "B"
        if response_lower.startswith(('c)', 'c.', 'c ', 'c:')):
            return "C"
        if response_lower.startswith(('d)', 'd.', 'd ', 'd:')):
            return "D"

        first_word = response_lower.split(
        )[0] if response_lower.split() else ""
        if first_word in ['a', 'b', 'c', 'd']:
            return first_word.upper()

        if "yes" in response_lower[:20]:
            return "yes"
        if "no" in response_lower[:20]:
            return "no"
        return "unknown"

    def _print_results_summary(self, results: List[TestResult], stats: Dict):
        """Print detailed results summary"""
        if not results:
            return

        print(f"\n{'='*60}")
        print(f"RESULTS SUMMARY")
        print(f"{'='*60}")

        # Verification statistics
        verification_rate = stats['verification_passed'] / \
            stats['total'] if stats['total'] > 0 else 0
        print(f"\nBoard Recognition:")
        print(
            f"  Verified correctly: {stats['verification_passed']}/{stats['total']} ({verification_rate:.1%})")

        # Overall accuracy
        overall_accuracy = stats['test_correct'] / \
            stats['total'] if stats['total'] > 0 else 0
        print(f"\nOverall Accuracy (all cases):")
        print(
            f"  Correct: {stats['test_correct']}/{stats['total']} ({overall_accuracy:.1%})")
        print(f"{'='*60}\n")
