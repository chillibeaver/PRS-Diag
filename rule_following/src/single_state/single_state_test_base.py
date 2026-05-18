"""
Base class for all Single State Tests (formerly Spatial Tests)
Provides common functionality for test execution, verification, and result reporting
"""

import os
import time
from typing import List, Dict, Tuple
from datetime import datetime
from abc import ABC, abstractmethod
from ..data_structures import TestResult, save_results, create_summary


class SingleStateTestBase(ABC):
    """Abstract base class for single state tests (game-agnostic)"""

    def __init__(self,
                 test_name: str,
                 test_layer: int,
                 base_output_dir: str,
                 n_cases: int = 100,
                 seed: int = 42,
                 auto_timestamp: bool = True,
                 rate_limit_requests: int = 0,
                 rate_limit_pause: int = 0):
        """
        Initialize Single State Test Base

        Args:
            test_name: Name of the test (e.g. "Chess No Rule")
            test_layer: Layer/ID (0 for no-rule, 1 for with-rule)
            base_output_dir: Base directory for output files
            n_cases: Total number of test cases
            seed: Random seed
        """
        self.test_name = test_name
        self.test_layer = test_layer
        self.n_cases = n_cases
        self.seed = seed
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_pause = rate_limit_pause

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
        """Generate images for all test cases"""
        if not self.board_gen:
            raise NotImplementedError(
                "Subclass must initialize self.board_gen")

        print(f"\nCreating test images for {self.test_name}...")
        print("="*60)

        for i, case in enumerate(self.test_cases, 1):
            # Check if case has pieces
            if "pieces" in case and case["pieces"]:
                img = self.board_gen.create_board_with_pieces(
                    pieces=case["pieces"],
                    highlighted_squares=case.get("squares", [])
                )
            else:
                img = self.board_gen.create_empty_board(
                    highlighted_squares=case.get("squares", [])
                )

            img_path = os.path.join(self.output_dir, f"{case['case_id']}.png")
            img.save(img_path)
            case["image_path"] = img_path

            if i % 10 == 0 or i == len(self.test_cases):
                print(f"  Progress: {i}/{len(self.test_cases)} images created")

        print(f"✓ All {len(self.test_cases)} images created\n")

    def generate_combined_prompt(self, case: Dict) -> str:
        """Generate prompt with verification + main question"""
        verification_q = case.get('verification_question', '')
        test_q = case['question']

        prompt = f"""Look at this board carefully.

First, a simple verification question to make sure you see the board correctly:
{verification_q}

Now, the main question:
{test_q}

Please answer both questions. Format your response as:
Verification: [your answer to verification question]
Main answer: [yes/no/unknown for the main question]"""
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
                response = model_client.query(prompt, case["image_path"])
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
                    print(
                        f"    Expected keywords: {case.get('verification_keywords', [])}")
                    print(f"    Got: {verification_response[:50]}...")

                # Rate Limit
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
                test_type="single_state",
                test_layer=self.test_layer,
                case_id=case["case_id"],
                piece_type=case.get('type'),
                verification_question=case.get('verification_question', ''),
                verification_expected=case.get('verification_expected', ''),
                verification_response=verification_response,
                verification_passed=verification_passed,
                question=case["question"],
                expected_answer=case["expected"],
                model_response=test_response,
                correct=correct,
                image_paths=[case["image_path"]],
                model_name=model_client.model_name
            )
            results.append(result)

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
        r_lower = response.lower().strip()
        if "yes" in r_lower[:20]:
            return "yes"
        if "no" in r_lower[:20]:
            return "no"
        return "unknown"
