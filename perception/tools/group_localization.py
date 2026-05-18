#!/usr/bin/env python3
"""
Structural Shift Analysis
"""

import os
import json
import glob
import argparse
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import shutil
import subprocess
from matplotlib.patches import Circle, Patch
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter, FuncFormatter
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from scipy.optimize import linear_sum_assignment
from scipy.ndimage import label
from scipy import stats
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from datetime import datetime


# =====
def _ensure_miktex_in_path():
    if shutil.which('kpsewhich'):
        return
    candidates = [
        os.path.expandvars(r'%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64'),
        os.path.expandvars(r'%PROGRAMFILES%\MiKTeX\miktex\bin\x64'),
    ]
    for path in candidates:
        if os.path.isdir(path):
            os.environ['PATH'] = path + os.pathsep + os.environ.get('PATH', '')
            return


def _ensure_times_tfm():
    if shutil.which('kpsewhich') is None:
        return
    try:
        result = subprocess.run(
            ['kpsewhich', 'ptmr7t.tfm'],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            subprocess.run(
                ['initexmf', '--update-fndb'],
                capture_output=True,
                text=True,
                check=False,
            )
    except Exception:
        return


_ensure_miktex_in_path()
_ensure_times_tfm()

mpl.rcParams['text.usetex'] = True
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times']
mpl.rcParams['text.latex.preamble'] = r'\usepackage{times}'
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
# ========================================

# Configuration

GAMES = ["chess", "gomoku"]
TEST_TYPES = ["density", "patch", "resolution", "richness"]

MODELS = ['gemma3-27b', 'glm4.1v-9b',
          'gpt5.2', 'qwen8b', 'qwen30b', 'qwen235b']

MODEL_LABELS = {
    'gemma3-27b': 'Gemma-3 27B',
    'glm4.1v-9b': 'GLM-4.1V 9B',
    'gpt5.2': 'GPT-5.2',
    'qwen8b': 'Qwen3-VL 8B',
    'qwen30b': 'Qwen3-VL 30B',
    'qwen235b': 'Qwen3-VL 235B'
}

COLORS = {
    'gemma3-27b': '#e74c3c',
    'glm4.1v-9b': '#3498db',
    'gpt5.2': '#2ecc71',
    'qwen8b': '#9b59b6',
    'qwen30b': '#f1c40f',
    'qwen235b': '#34495e'
}

SHIFT_DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),          (0, 1),
    (1, -1),  (1, 0), (1, 1)
]

SHIFT_COLORS = {
    (0, 0): '#2ecc71',
    (1, 0): '#e74c3c',
    (-1, 0): '#3498db',
    (0, 1): '#f1c40f',
    (0, -1): '#9b59b6',
    (1, 1): '#e67e22',
    (1, -1): '#1abc9c',
    (-1, 1): '#34495e',
    (-1, -1): '#95a5a6',
}

SHIFT_ARROWS = {
    (0, 0): r'$\bullet$',
    (1, 0): r'$\downarrow$',
    (-1, 0): r'$\uparrow$',
    (0, 1): r'$\rightarrow$',
    (0, -1): r'$\leftarrow$',
    (1, 1): r'$\searrow$',
    (1, -1): r'$\swarrow$',
    (-1, 1): r'$\nearrow$',
    (-1, -1): r'$\nwarrow$',
}

FONT = {'title': 30, 'subtitle': 30, 'label': 20,
        'tick': 24, 'legend': 20, 'annotation': 14}

RANDOM_BASELINE = 1.0 / 8.0  # 12.5%


def _percent_tick_formatter(x, pos):
    return f'{x:.0f}\\%'


# Core Matching Algorithm

def compute_identification_localization(pred: np.ndarray, truth: np.ndarray,
                                        radius: int = 1, empty_value: int = 0) -> Dict:
    """Compute piece matching using Hungarian algorithm."""
    pred, truth = np.array(pred), np.array(truth)
    board_size = truth.shape[0]

    truth_pieces = [(i, j, truth[i, j]) for i in range(board_size)
                    for j in range(board_size) if truth[i, j] != empty_value]
    pred_pieces = [(i, j, pred[i, j]) for i in range(board_size)
                   for j in range(board_size) if pred[i, j] != empty_value]

    n_truth, n_pred = len(truth_pieces), len(pred_pieces)

    if n_truth == 0:
        return {"identification_acc": 1.0, "localization_acc": 1.0, "gap": 0.0,
                "total_truth_pieces": 0, "matched_details": []}
    if n_pred == 0:
        return {"identification_acc": 0.0, "localization_acc": 0.0, "gap": 0.0,
                "total_truth_pieces": n_truth, "matched_details": []}

    INF = 1000000
    cost = np.full((n_truth, n_pred), INF, dtype=float)

    for i, (ti, tj, t_color) in enumerate(truth_pieces):
        for j, (pi, pj, p_color) in enumerate(pred_pieces):
            dist = max(abs(ti - pi), abs(tj - pj))
            if t_color == p_color and dist <= radius:
                cost[i][j] = dist

    row_ind, col_ind = linear_sum_assignment(cost)

    id_correct, loc_correct = 0, 0
    matched_details = []

    for i, j in zip(row_ind, col_ind):
        if cost[i][j] < INF:
            id_correct += 1
            dist = int(cost[i][j])
            ti, tj, t_color = truth_pieces[i]
            pi, pj, _ = pred_pieces[j]
            matched_details.append({
                "truth_pos": (ti, tj),
                "pred_pos": (pi, pj),
                "color": int(t_color),
                "distance": dist,
                "shift": (pi - ti, pj - tj)
            })
            if dist == 0:
                loc_correct += 1

    return {
        "identification_acc": float(id_correct / n_truth),
        "localization_acc": float(loc_correct / n_truth),
        "gap": float((id_correct - loc_correct) / n_truth),
        "total_truth_pieces": n_truth,
        "total_pred_pieces": n_pred,
        "matched_pairs": id_correct,
        "localization_correct": loc_correct,
        "matched_details": matched_details,
    }


# Adjacent Same-Direction Analysis

def find_adjacent_pairs(positions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Find all pairs of positions that are adjacent (8-connectivity)."""
    adjacent_pairs = []
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            dist = max(abs(positions[i][0] - positions[j][0]),
                       abs(positions[i][1] - positions[j][1]))
            if dist == 1:
                adjacent_pairs.append((i, j))
    return adjacent_pairs


def compute_adjacent_same_direction_ratio(
    positions: List[Tuple[int, int]],
    shifts: List[Tuple[int, int]]
) -> Dict:
    """Compute the ratio of adjacent piece pairs that shift in the same direction."""
    if len(positions) != len(shifts):
        raise ValueError("positions and shifts must have same length")

    adjacent_pairs = find_adjacent_pairs(positions)
    n_pairs = len(adjacent_pairs)

    if n_pairs < 3:
        return {
            "n_adjacent_pairs": n_pairs,
            "n_same_direction": 0,
            "adjacent_same_dir_ratio": 0.0,
            "random_baseline": RANDOM_BASELINE,
            "ratio_vs_baseline": 0.0,
            "p_value": 1.0,
            "is_significant": False,
            "insufficient_data": True
        }

    same_dir_count = sum(
        1 for (i, j) in adjacent_pairs
        if shifts[i] == shifts[j]
    )

    observed_ratio = same_dir_count / n_pairs

    try:
        binom_result = stats.binomtest(
            same_dir_count, n_pairs, RANDOM_BASELINE, alternative='greater'
        )
        p_value = binom_result.pvalue
    except:
        p_value = stats.binom.sf(same_dir_count - 1, n_pairs, RANDOM_BASELINE)

    return {
        "n_adjacent_pairs": n_pairs,
        "n_same_direction": same_dir_count,
        "adjacent_same_dir_ratio": float(observed_ratio),
        "random_baseline": RANDOM_BASELINE,
        "ratio_vs_baseline": float(observed_ratio / RANDOM_BASELINE) if RANDOM_BASELINE > 0 else 0,
        "p_value": float(p_value),
        "is_significant": p_value < 0.05,
        "insufficient_data": False
    }


# Supporting Metrics

def compute_moran_i(values: np.ndarray, positions: np.ndarray,
                    distance_threshold: int = 3) -> float:
    """Compute Moran's I spatial autocorrelation index."""
    n = len(values)
    if n < 3:
        return 0.0

    W = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                dist = np.max(np.abs(positions[i] - positions[j]))
                if dist <= distance_threshold:
                    W[i, j] = 1

    W_sum = W.sum()
    if W_sum == 0:
        return 0.0

    mean_val = np.mean(values)
    z = values - mean_val

    numerator = n * np.sum(W * np.outer(z, z))
    denominator = W_sum * np.sum(z ** 2)

    return numerator / denominator if denominator != 0 else 0.0


def compute_largest_connected_component(positions: List[Tuple[int, int]],
                                        board_size: int) -> int:
    """Compute size of largest connected component using 8-connectivity."""
    if len(positions) < 2:
        return len(positions)

    mask = np.zeros((board_size, board_size), dtype=int)
    for row, col in positions:
        if 0 <= row < board_size and 0 <= col < board_size:
            mask[row, col] = 1

    structure = np.ones((3, 3), dtype=int)
    labeled, num_features = label(mask, structure=structure)

    if num_features == 0:
        return 0

    return max(np.sum(labeled == i) for i in range(1, num_features + 1))


# Main Structural Analysis Function

def analyze_structural_shift(matched_details: List[Dict],
                             board_size: int) -> Optional[Dict]:
    """Main structural shift analysis function."""
    if len(matched_details) < 3:
        return None

    all_positions = [tuple(m['truth_pos']) for m in matched_details]
    all_shifts = [tuple(m['shift']) for m in matched_details]

    shifted_indices = [i for i, s in enumerate(all_shifts) if s != (0, 0)]
    shifted_positions = [all_positions[i] for i in shifted_indices]
    shifted_shifts = [all_shifts[i] for i in shifted_indices]

    exact_count = len(all_shifts) - len(shifted_indices)
    total_shifted = len(shifted_indices)

    if total_shifted == 0:
        return {
            "total_pieces": len(matched_details),
            "total_shifted": 0,
            "exact_matches": exact_count,
            "dominant_shift": (0, 0),
            "dominant_count": 0,
            "dominance_ratio": 1.0,
            "adjacent_same_dir": {
                "n_adjacent_pairs": 0,
                "adjacent_same_dir_ratio": 1.0,
                "is_significant": False,
                "insufficient_data": True
            },
            "lcc_size": 0,
            "lcc_ratio": 1.0,
            "moran_i": 0.0,
            "structural_score": 0.0,
            "is_structural": False,
            "confidence": "perfect",
            "shift_distribution": {"(0, 0)": exact_count}
        }

    shift_positions = defaultdict(list)
    for pos, shift in zip(shifted_positions, shifted_shifts):
        shift_positions[shift].append(pos)

    dominant_shift = max(shift_positions.keys(),
                         key=lambda s: len(shift_positions[s]))
    dominant_count = len(shift_positions[dominant_shift])
    dominance_ratio = dominant_count / total_shifted

    adjacent_analysis = compute_adjacent_same_direction_ratio(
        shifted_positions, shifted_shifts
    )

    lcc_size = compute_largest_connected_component(
        shift_positions[dominant_shift], board_size)
    lcc_ratio = lcc_size / dominant_count if dominant_count > 0 else 0.0

    if total_shifted >= 3:
        positions_arr = np.array(shifted_positions)
        row_deltas = np.array([s[0] for s in shifted_shifts])
        col_deltas = np.array([s[1] for s in shifted_shifts])
        moran_row = compute_moran_i(row_deltas, positions_arr)
        moran_col = compute_moran_i(col_deltas, positions_arr)
        moran_i = (moran_row + moran_col) / 2
    else:
        moran_i = 0.0

    adj_ratio = adjacent_analysis.get('adjacent_same_dir_ratio', 0)
    adj_significant = adjacent_analysis.get('is_significant', False)

    structural_score = (
        0.25 * min(1.0, dominance_ratio / 0.5) +
        0.40 * min(1.0, adj_ratio / 0.25) +
        0.20 * max(0, moran_i) +
        0.15 * lcc_ratio
    )

    is_structural = adj_significant or structural_score > 0.5

    if structural_score > 0.7 and adj_significant:
        confidence = "high"
    elif structural_score > 0.5 or adj_significant:
        confidence = "medium"
    else:
        confidence = "low"

    shift_dist = {str(k): len(v) for k, v in shift_positions.items()}
    shift_dist["(0, 0)"] = exact_count

    return {
        "total_pieces": len(matched_details),
        "total_shifted": total_shifted,
        "exact_matches": exact_count,
        "dominant_shift": dominant_shift,
        "dominant_count": dominant_count,
        "dominance_ratio": dominance_ratio,
        "adjacent_same_dir": adjacent_analysis,
        "lcc_size": lcc_size,
        "lcc_ratio": lcc_ratio,
        "moran_i": moran_i,
        "structural_score": structural_score,
        "is_structural": is_structural,
        "confidence": confidence,
        "shift_distribution": shift_dist
    }


# Monte Carlo Baseline

def compute_random_baseline_mc(
    original_positions: List[Tuple[int, int]],
    shift_distribution: Dict[Tuple[int, int], int],
    n_simulations: int = 500
) -> Dict:
    """Monte Carlo simulation for random baseline comparison."""
    shifts_list = []
    for shift_str, count in shift_distribution.items():
        if shift_str != "(0, 0)":
            try:
                shift = eval(shift_str) if isinstance(
                    shift_str, str) else shift_str
                shifts_list.extend([shift] * count)
            except:
                continue

    n_shifted = len(shifts_list)
    if n_shifted < 5 or len(original_positions) != n_shifted:
        return {"insufficient_data": True}

    adjacent_pairs = find_adjacent_pairs(original_positions)
    n_pairs = len(adjacent_pairs)

    if n_pairs < 3:
        return {"insufficient_data": True}

    baseline_same_dir_ratios = []
    baseline_dominance_ratios = []

    for _ in range(n_simulations):
        shuffled_shifts = shifts_list.copy()
        np.random.shuffle(shuffled_shifts)

        same_dir_count = sum(
            1 for (i, j) in adjacent_pairs
            if shuffled_shifts[i] == shuffled_shifts[j]
        )
        baseline_same_dir_ratios.append(same_dir_count / n_pairs)

        shift_counts = defaultdict(int)
        for s in shuffled_shifts:
            shift_counts[s] += 1
        max_count = max(shift_counts.values())
        baseline_dominance_ratios.append(max_count / n_shifted)

    return {
        "n_simulations": n_simulations,
        "n_shifted_pieces": n_shifted,
        "n_adjacent_pairs": n_pairs,
        "baseline_adj_same_dir_mean": float(np.mean(baseline_same_dir_ratios)),
        "baseline_adj_same_dir_std": float(np.std(baseline_same_dir_ratios)),
        "baseline_adj_same_dir_95th": float(np.percentile(baseline_same_dir_ratios, 95)),
        "baseline_dominance_mean": float(np.mean(baseline_dominance_ratios)),
        "baseline_dominance_std": float(np.std(baseline_dominance_ratios)),
        "insufficient_data": False
    }


# Parallel Processing

def process_single_case(args) -> Optional[Dict]:
    """Process a single test case."""
    case, board_size, mc_sims = args

    try:
        pred = np.array(case.get('predicted', []))
        truth = np.array(case.get('ground_truth', []))

        if pred.size == 0 or truth.size == 0:
            return None

        loc_result = compute_identification_localization(pred, truth, radius=1)
        matched_details = loc_result['matched_details']

        if len(matched_details) < 3:
            return None

        structural = analyze_structural_shift(matched_details, board_size)

        if structural is None:
            return None

        baseline = None
        if structural['total_shifted'] >= 5 and mc_sims > 0:
            shifted_positions = [
                tuple(m['truth_pos']) for m in matched_details
                if tuple(m['shift']) != (0, 0)
            ]
            baseline = compute_random_baseline_mc(
                shifted_positions,
                structural['shift_distribution'],
                n_simulations=mc_sims
            )

        return {
            'id_acc': loc_result['identification_acc'],
            'loc_acc': loc_result['localization_acc'],
            'gap': loc_result['gap'],
            'matched_details': matched_details,
            'n_pieces': loc_result['total_truth_pieces'],
            'structural': structural,
            'baseline': baseline,
            'test_case': case,
        }
    except Exception as e:
        return None


def scan_and_process_data(base_dir: str, mc_sims: int = 200,
                          num_workers: int = None) -> Dict:
    """Scan directory and process all test cases."""
    if num_workers is None:
        num_workers = max(1, mp.cpu_count() - 1)

    print(f"\n{'='*70}")
    print(f"STRUCTURAL SHIFT ANALYSIS (REVISED)")
    print(f"{'='*70}")
    print(f"📂 Scanning: {base_dir}")
    print(f"⚙️  Workers: {num_workers}")
    print(f"🎲 MC simulations: {mc_sims}")
    print(f"{'='*70}\n")

    data = {m: {g: {t: [] for t in TEST_TYPES} for g in GAMES} for m in MODELS}
    total_processed = 0

    file_tasks = []
    for model in MODELS:
        for game in GAMES:
            for test_type in TEST_TYPES:
                search_path = os.path.join(
                    base_dir, model, game, f"*{test_type}*")
                found_dirs = glob.glob(search_path)
                if not found_dirs:
                    continue
                json_file = os.path.join(
                    sorted(found_dirs)[-1], 'results.json')
                if os.path.exists(json_file):
                    file_tasks.append((model, game, test_type, json_file))

    if not file_tasks:
        print("❌ No results.json files found!")
        return data

    for model, game, test_type, json_file in file_tasks:
        board_size = 15 if game == "gomoku" else 8

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)

            if 'test_cases' not in results:
                continue

            cases = results['test_cases']
            valid_cases = [c for c in cases
                           if 'error' not in c and c.get('parse_success', True)]

            if not valid_cases:
                continue

            print(f"  Processing {model}/{game}/{test_type} ({len(valid_cases)} cases)...",
                  end=" ", flush=True)

            args_list = [(case, board_size, mc_sims) for case in valid_cases]
            processed = []

            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(process_single_case, args)
                           for args in args_list]
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        processed.append(result)

            data[model][game][test_type] = processed
            total_processed += len(processed)
            print(f"✔ {len(processed)}")

        except Exception as e:
            print(f"[ERROR] {json_file}: {e}")

    print(f"\n{'='*70}")
    print(f"Total processed: {total_processed} test cases")
    print(f"{'='*70}\n")

    return data


# Aggregation

def aggregate_by_model(data: Dict) -> Dict[str, Dict]:
    """Aggregate structural metrics by model using two-level weighted averaging.

    Level 1: Average within each test type (density, patch, resolution, richness)
    Level 2: Equal-weight average across the four test types
    """
    model_stats = {}

    for model in MODELS:
        # First level: compute metrics within each test type
        test_type_metrics = {}
        all_baselines = []

        for test_type in TEST_TYPES:
            test_type_structural = []

            # Collect all cases for this test type across both games
            for game in GAMES:
                for case in data[model][game][test_type]:
                    s = case.get('structural')
                    if s and s.get('total_shifted', 0) > 0:
                        test_type_structural.append(s)
                        if case.get('baseline') and not case['baseline'].get('insufficient_data'):
                            all_baselines.append(case['baseline'])

            # Compute metrics for this test type if sufficient data
            if len(test_type_structural) >= 3:
                adj_ratios = [
                    s['adjacent_same_dir']['adjacent_same_dir_ratio']
                    for s in test_type_structural
                    if not s['adjacent_same_dir'].get('insufficient_data', True)
                ]

                adj_significant_count = sum(
                    1 for s in test_type_structural
                    if s['adjacent_same_dir'].get('is_significant', False)
                )

                test_type_metrics[test_type] = {
                    'n_boards': len(test_type_structural),
                    'avg_dominance': float(np.mean([s['dominance_ratio'] for s in test_type_structural])),
                    'std_dominance': float(np.std([s['dominance_ratio'] for s in test_type_structural])),
                    'avg_adj_same_dir': float(np.mean(adj_ratios)) if adj_ratios else 0.0,
                    'std_adj_same_dir': float(np.std(adj_ratios)) if adj_ratios else 0.0,
                    'pct_adj_significant': float(adj_significant_count / len(test_type_structural)),
                    'avg_lcc_ratio': float(np.mean([s['lcc_ratio'] for s in test_type_structural])),
                    'std_lcc_ratio': float(np.std([s['lcc_ratio'] for s in test_type_structural])),
                    'avg_moran_i': float(np.mean([s['moran_i'] for s in test_type_structural])),
                    'std_moran_i': float(np.std([s['moran_i'] for s in test_type_structural])),
                    'avg_structural_score': float(np.mean([s['structural_score'] for s in test_type_structural])),
                    'pct_structural': float(np.mean([s['is_structural'] for s in test_type_structural])),
                }

        if not test_type_metrics:
            continue

        # Second level: equal-weight average across test types
        metrics_list = list(test_type_metrics.values())

        model_stats[model] = {
            'n_boards': sum(m['n_boards'] for m in metrics_list),
            'n_test_types': len(metrics_list),
            'test_type_breakdown': test_type_metrics,
            'avg_dominance': float(np.mean([m['avg_dominance'] for m in metrics_list])),
            'std_dominance': float(np.mean([m['std_dominance'] for m in metrics_list])),
            'avg_adj_same_dir': float(np.mean([m['avg_adj_same_dir'] for m in metrics_list])),
            'std_adj_same_dir': float(np.mean([m['std_adj_same_dir'] for m in metrics_list])),
            'pct_adj_significant': float(np.mean([m['pct_adj_significant'] for m in metrics_list])),
            'avg_lcc_ratio': float(np.mean([m['avg_lcc_ratio'] for m in metrics_list])),
            'std_lcc_ratio': float(np.mean([m['std_lcc_ratio'] for m in metrics_list])),
            'avg_moran_i': float(np.mean([m['avg_moran_i'] for m in metrics_list])),
            'std_moran_i': float(np.mean([m['std_moran_i'] for m in metrics_list])),
            'avg_structural_score': float(np.mean([m['avg_structural_score'] for m in metrics_list])),
            'pct_structural': float(np.mean([m['pct_structural'] for m in metrics_list])),
        }

        if all_baselines:
            model_stats[model]['baseline'] = {
                'adj_same_dir_mean': float(np.mean([b['baseline_adj_same_dir_mean'] for b in all_baselines])),
                'adj_same_dir_95th': float(np.mean([b['baseline_adj_same_dir_95th'] for b in all_baselines])),
                'dominance_mean': float(np.mean([b['baseline_dominance_mean'] for b in all_baselines])),
            }

    return model_stats


def aggregate_shift_distribution(data: Dict) -> Dict[str, int]:
    """Aggregate global shift direction distribution."""
    all_shifts = defaultdict(int)

    for model in MODELS:
        for game in GAMES:
            for test_type in TEST_TYPES:
                for case in data[model][game][test_type]:
                    s = case.get('structural')
                    if s:
                        for shift_str, count in s.get('shift_distribution', {}).items():
                            if shift_str != "(0, 0)":
                                all_shifts[shift_str] += count

    return dict(sorted(all_shifts.items(), key=lambda x: -x[1]))


def plot_dominance_ratio_standalone(model_stats: Dict, output_path: str):
    """
    Plot ONLY the Dominance Ratio as a standalone figure.
    All values displayed as percentages.
    """
    models = list(model_stats.keys())
    if not models:
        print("[SKIP] No model data for dominance ratio plot")
        return

    n = len(models)
    x = np.arange(n)

    fig, ax = plt.subplots(figsize=(14, 8))
    size_scale = 1.15
    label_size = int(FONT['label'] * size_scale + 2)
    tick_size = int(FONT['tick'] * size_scale - 3)
    legend_size = int(FONT['legend'] * size_scale)
    annotation_size = int(FONT['annotation'] * size_scale + 2)
    vals = [model_stats[m]['avg_dominance'] for m in models]
    errs = [model_stats[m]['std_dominance'] for m in models]

    bars = ax.bar(x, [v * 100 for v in vals],
                  yerr=[e * 100 for e in errs],
                  capsize=5,
                  color=[COLORS.get(m, 'gray') for m in models],
                  edgecolor='black', linewidth=1.5)

    baseline_line = ax.axhline(y=RANDOM_BASELINE * 100, color='red', linestyle='--',
                               lw=2.5, label=f'Random baseline ({RANDOM_BASELINE*100:.1f}\\%)')

    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_LABELS.get(m, m) for m in models],
                       rotation=30, ha='right', fontsize=tick_size)
    ax.set_ylabel(r'Dominance Ratio (\%)',
                  fontsize=label_size, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(FuncFormatter(_percent_tick_formatter))

    ax.tick_params(axis='y', labelsize=tick_size)

    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                f'{val*100:.1f}\\%', ha='center', fontsize=annotation_size, fontweight='bold')

    for i, (bar, val) in enumerate(zip(bars, vals)):
        ratio = val / RANDOM_BASELINE
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() / 2,
                f'{ratio:.1f}×', ha='center', va='center',
                fontsize=annotation_size, fontweight='bold', color='white')

    fig.legend(loc='lower center', bbox_to_anchor=(0.5, 0.01),
               ncol=2, fontsize=legend_size, frameon=True)

    plt.tight_layout(rect=[0, 0.06, 1, 1])
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  ✔ Saved: {output_path}")


# Visualization Functions (Updated with Percentage Formatting)

def plot_structural_metrics_summary(model_stats: Dict, output_path: str):
    """Plot summary of structural metrics across models (percentages)."""
    models = list(model_stats.keys())
    if not models:
        print("[SKIP] No model data for summary plot")
        return

    n = len(models)
    x = np.arange(n)

    fig, axes = plt.subplots(2, 2, figsize=(18, 16))

    ax = axes[0, 0]
    vals = [model_stats[m]['avg_dominance'] for m in models]
    errs = [model_stats[m]['std_dominance'] for m in models]
    bars = ax.bar(x, [v * 100 for v in vals],
                  yerr=[e * 100 for e in errs], capsize=5,
                  color=[COLORS.get(m, 'gray') for m in models],
                  edgecolor='black', linewidth=1.5)
    ax.axhline(y=RANDOM_BASELINE * 100, color='red', linestyle='--',
               lw=2.5, label=f'Random baseline ({RANDOM_BASELINE*100:.1f}\\%)')
    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_LABELS.get(m, m) for m in models],
                       rotation=30, ha='right', fontsize=FONT['tick'])
    ax.set_ylabel(r'Dominance Ratio (\%)',
                  fontsize=FONT['label'], fontweight='bold')
    ax.legend(fontsize=FONT['legend'], loc='upper right')
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(FuncFormatter(_percent_tick_formatter))
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                f'{val*100:.1f}\\%', ha='center', fontsize=FONT['annotation'], fontweight='bold')

    ax = axes[0, 1]
    vals = [model_stats[m]['avg_adj_same_dir'] for m in models]
    errs = [model_stats[m]['std_adj_same_dir'] for m in models]
    bars = ax.bar(x, [v * 100 for v in vals],
                  yerr=[e * 100 for e in errs], capsize=5,
                  color=[COLORS.get(m, 'gray') for m in models],
                  edgecolor='black', linewidth=1.5)
    ax.axhline(y=RANDOM_BASELINE * 100, color='red', linestyle='--',
               lw=2.5, label=f'Random baseline ({RANDOM_BASELINE*100:.1f}\\%)')
    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_LABELS.get(m, m) for m in models],
                       rotation=30, ha='right', fontsize=FONT['tick'])
    ax.set_ylabel(r'Adjacent Same-Direction Ratio (\\%)',
                  fontsize=FONT['label'], fontweight='bold')
    ax.legend(fontsize=FONT['legend'], loc='upper right')
    max_val = max(vals) * 100 if vals else 50
    ax.set_ylim(0, max(50, max_val * 1.3))
    ax.yaxis.set_major_formatter(FuncFormatter(_percent_tick_formatter))
    for bar, val in zip(bars, vals):
        color = '#27ae60' if val > RANDOM_BASELINE * 2 else 'black'
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{val*100:.1f}\\%', ha='center', fontsize=FONT['annotation'],
                fontweight='bold', color=color)

    ax = axes[1, 0]
    vals = [model_stats[m]['avg_moran_i'] for m in models]
    errs = [model_stats[m]['std_moran_i'] for m in models]
    colors_mi = ['#27ae60' if v > 0 else '#e74c3c' for v in vals]
    bars = ax.bar(x, vals, yerr=errs, capsize=5, color=colors_mi,
                  edgecolor='black', linewidth=1.5)
    ax.axhline(y=0, color='black', lw=1.5)
    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_LABELS.get(m, m) for m in models],
                       rotation=30, ha='right', fontsize=FONT['tick'])
    ax.set_ylabel("Moran's I", fontsize=FONT['label'], fontweight='bold')
    for bar, val in zip(bars, vals):
        y_pos = bar.get_height() + 0.02 if val >= 0 else bar.get_height() - 0.06
        ax.text(bar.get_x() + bar.get_width()/2, y_pos, f'{val:.2f}',
                ha='center', fontsize=FONT['annotation'], fontweight='bold')

    ax = axes[1, 1]
    vals = [model_stats[m]['pct_adj_significant'] * 100 for m in models]
    bars = ax.bar(x, vals, color=[COLORS.get(m, 'gray') for m in models],
                  edgecolor='black', linewidth=1.5)
    ax.axhline(y=5, color='red', linestyle='--', lw=2.5,
               label=r'Expected under null (5\%)')
    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_LABELS.get(m, m) for m in models],
                       rotation=30, ha='right', fontsize=FONT['tick'])
    ax.set_ylabel(r'Percentage (\%)',
                  fontsize=FONT['label'], fontweight='bold')
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(FuncFormatter(_percent_tick_formatter))
    ax.legend(fontsize=FONT['legend'], loc='upper right')
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f'{val:.1f}\\%', ha='center', fontsize=FONT['annotation'], fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  ✔ Saved: {output_path}")


def plot_adjacent_ratio_vs_baseline(model_stats: Dict, output_path: str):
    """Compare actual adjacent same-dir ratio with Monte Carlo baseline (percentages)."""
    models = [m for m in model_stats if 'baseline' in model_stats[m]]

    if not models:
        print("  [SKIP] No baseline data for comparison plot")
        return

    n = len(models)
    x = np.arange(n)
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 8))

    size_scale = 1.15
    label_size = int(FONT['label'] * size_scale + 2)
    tick_size = int(FONT['tick'] * size_scale - 3)
    legend_size = int(FONT['legend'] * size_scale)
    annotation_size = int(FONT['annotation'] * size_scale + 2)

    actual = [model_stats[m]['avg_adj_same_dir'] * 100 for m in models]
    baseline = [model_stats[m]['baseline']
                ['adj_same_dir_mean'] * 100 for m in models]
    baseline_95 = [model_stats[m]['baseline']
                   ['adj_same_dir_95th'] * 100 for m in models]

    bars1 = ax.bar(x - width/2, actual, width, label='Actual',
                   color=[COLORS.get(m, 'gray') for m in models],
                   edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x + width/2, baseline, width, label='Random Baseline (MC)',
                   color='lightgray', edgecolor='black', linewidth=1.5, hatch='///')

    for i, (b, p95) in enumerate(zip(baseline, baseline_95)):
        ax.plot([x[i] + width/2 - 0.1, x[i] + width/2 + 0.1], [p95, p95],
                'r-', linewidth=2)
        ax.text(x[i] + width/2 + 0.12, p95, r'95\%',
                fontsize=8, va='center', color='red')

    theoretical_line = ax.axhline(y=RANDOM_BASELINE * 100, color='blue', linestyle=':', lw=2,
                                  label=f'Theoretical baseline ({RANDOM_BASELINE*100:.1f}\\%)')

    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_LABELS.get(m, m) for m in models],
                       rotation=30, ha='right', fontsize=tick_size)
    ax.set_ylabel(r'Adjacent Same-Direction Ratio (\%)',
                  fontsize=label_size, fontweight='bold')
    ax.set_ylim(0, max(max(actual), max(baseline_95)) * 1.3)
    ax.yaxis.set_major_formatter(FuncFormatter(_percent_tick_formatter))
    ax.tick_params(axis='y', labelsize=tick_size)

    for bar, val in zip(bars1, actual):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}\\%', ha='center', fontsize=annotation_size,
                fontweight='bold', color='black')

    for bar, val in zip(bars2, baseline):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}\\%', ha='center', fontsize=annotation_size,
                fontweight='bold', color='gray')

    for i, (a, b) in enumerate(zip(actual, baseline)):
        ratio = a / b if b > 0 else 0
        y_pos = max(a, b) + 5
        ax.annotate(f'{ratio:.1f}×', xy=(x[i], y_pos),
                    ha='center', fontsize=annotation_size, fontweight='bold',
                    color='#1b5e20')

    legend_els = [
        Patch(facecolor='gray', edgecolor='black', label='Actual'),
        Patch(facecolor='lightgray', edgecolor='black',
              hatch='///', label='Random Baseline (MC)'),
        Line2D([0], [0], color='blue', linestyle=':', lw=2,
               label=f'Theoretical baseline ({RANDOM_BASELINE*100:.1f}\\%)')
    ]

    fig.legend(handles=legend_els, loc='lower center', bbox_to_anchor=(0.5, 0.01),
               ncol=3, fontsize=legend_size, frameon=True)

    plt.tight_layout(rect=[0, 0.08, 1, 1])
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  ✔ Saved: {output_path}")


def plot_shift_preference_heatmap(data: Dict, output_path: str):
    """Plot shift direction preference heatmap for each model (percentages)."""
    model_shift_dist = {}

    for model in MODELS:
        shift_counts = defaultdict(int)
        total_shifted = 0

        for game in GAMES:
            for test_type in TEST_TYPES:
                for case in data[model][game][test_type]:
                    s = case.get('structural')
                    if s:
                        for shift_str, count in s.get('shift_distribution', {}).items():
                            if shift_str != "(0, 0)":
                                try:
                                    shift = eval(shift_str)
                                    shift_counts[shift] += count
                                    total_shifted += count
                                except:
                                    continue

        if total_shifted > 0:
            shift_pct = {k: v / total_shifted *
                         100 for k, v in shift_counts.items()}
            model_shift_dist[model] = shift_pct

    if not model_shift_dist:
        print("  [SKIP] No shift data for heatmap")
        return

    n_models = len(model_shift_dist)
    n_cols = min(3, n_models)
    n_rows = (n_models + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6 * n_cols, 5 * n_rows))
    if n_models == 1:
        axes = np.array([[axes]])
    elif n_rows == 1:
        axes = axes.reshape(1, -1)
    elif n_cols == 1:
        axes = axes.reshape(-1, 1)

    shift_to_grid = {
        (-1, -1): (0, 0), (-1, 0): (0, 1), (-1, 1): (0, 2),
        (0, -1): (1, 0),  (0, 0): (1, 1),  (0, 1): (1, 2),
        (1, -1): (2, 0),  (1, 0): (2, 1),  (1, 1): (2, 2),
    }

    direction_labels = {
        (-1, -1): r'$\nwarrow$', (-1, 0): r'$\uparrow$', (-1, 1): r'$\nearrow$',
        (0, -1): r'$\leftarrow$',  (0, 0): r'$\bullet$',  (0, 1): r'$\rightarrow$',
        (1, -1): r'$\swarrow$',  (1, 0): r'$\downarrow$',  (1, 1): r'$\searrow$',
    }

    all_pcts = []
    for shift_pct in model_shift_dist.values():
        all_pcts.extend(shift_pct.values())
    vmax = max(all_pcts) if all_pcts else 100

    for idx, (model, shift_pct) in enumerate(model_shift_dist.items()):
        row, col = idx // n_cols, idx % n_cols
        ax = axes[row, col]

        grid = np.zeros((3, 3))
        for shift, pct in shift_pct.items():
            if shift in shift_to_grid:
                r, c = shift_to_grid[shift]
                grid[r, c] = pct

        grid[1, 1] = np.nan
        masked_grid = np.ma.masked_invalid(grid)

        im = ax.imshow(masked_grid, cmap='YlOrRd',
                       vmin=0, vmax=vmax, aspect='equal')

        for shift, (r, c) in shift_to_grid.items():
            if shift == (0, 0):
                ax.text(c, r, direction_labels[shift], ha='center', va='center',
                        fontsize=20, color='gray', fontweight='bold')
            else:
                pct = shift_pct.get(shift, 0)
                arrow = direction_labels[shift]
                text_color = 'white' if pct > vmax * 0.5 else 'black'

                ax.text(c, r - 0.15, arrow, ha='center', va='center',
                        fontsize=24, color=text_color, fontweight='bold')
                ax.text(c, r + 0.25, f'{pct:.1f}\\%', ha='center', va='center',
                        fontsize=FONT['annotation'] + 6, color=text_color, fontweight='bold')

                # Star marker removed per formatting requirement.

        ax.set_xticks([0, 1, 2])
        ax.set_yticks([0, 1, 2])
        ax.set_xticklabels(['Left', 'Center', 'Right'],
                           fontsize=FONT['annotation'])
        ax.set_yticklabels(['Up', 'Center', 'Down'],
                           fontsize=FONT['annotation'])
        ax.set_title(f'{MODEL_LABELS.get(model, model)}',
                     fontsize=FONT["subtitle"], fontweight='bold')

        ax.set_xticks(np.arange(-0.5, 3, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, 3, 1), minor=True)
        ax.grid(which='minor', color='white', linewidth=2)
        ax.tick_params(which='minor', size=0)

    for idx in range(n_models, n_rows * n_cols):
        row, col = idx // n_cols, idx % n_cols
        axes[row, col].axis('off')

    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_label(r'Percentage of Shifted Pieces (\%)',
                   fontsize=FONT['label'])

    plt.subplots_adjust(left=0.08, right=0.88, top=0.92,
                        bottom=0.08, wspace=0.3, hspace=0.4)
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  ✔ Saved: {output_path}")


def plot_global_shift_distribution(shift_dist: Dict, output_path: str):
    """Plot global shift direction distribution (percentages)."""
    if not shift_dist:
        print("  [SKIP] No shift distribution data")
        return

    top_shifts = list(shift_dist.items())[:8]
    labels = [s[0] for s in top_shifts]
    values = [s[1] for s in top_shifts]
    total = sum(shift_dist.values())
    percentages = [v / total * 100 for v in values]

    fig, ax = plt.subplots(figsize=(14, 8))

    colors = []
    for l in labels:
        try:
            colors.append(SHIFT_COLORS.get(eval(l), '#7f8c8d'))
        except:
            colors.append('#7f8c8d')

    bars = ax.bar(range(len(labels)), percentages, color=colors,
                  edgecolor='black', linewidth=1.5)

    ax.axhline(y=RANDOM_BASELINE * 100, color='red', linestyle='--', lw=2.5,
               label=f'Random expectation ({RANDOM_BASELINE*100:.1f}\\%)')

    arrow_labels = []
    for l in labels:
        try:
            shift = eval(l)
            arrow = SHIFT_ARROWS.get(shift, '?')
            arrow_labels.append(f"{arrow}\n{l}")
        except:
            arrow_labels.append(l)

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(arrow_labels, fontsize=FONT['tick'])
    ax.set_ylabel(r'Percentage of All Shifted Pieces (\%)',
                  fontsize=FONT['label'], fontweight='bold')
    ax.legend(fontsize=FONT['legend'])
    ax.yaxis.set_major_formatter(FuncFormatter(_percent_tick_formatter))

    for bar, pct in zip(bars, percentages):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{pct:.1f}\\%', ha='center', fontsize=FONT['annotation'], fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  ✔ Saved: {output_path}")


# Report Generation

def generate_summary_report(model_stats: Dict, shift_dist: Dict, output_path: str):
    """Generate text summary report (percentages)."""

    lines = [
        "=" * 70,
        "STRUCTURAL SHIFT ANALYSIS REPORT (REVISED)",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        "",
        "PROOF METHODOLOGY",
        "-" * 40,
        "Step 1: Show dominance ratio >> 12.5% (direction preference exists)",
        "Step 2: Show adjacent same-direction ratio >> MC",
        "        This proves adjacent pieces shift TOGETHER, not independently",
        "",
        "EXECUTIVE SUMMARY",
        "-" * 40,
    ]

    if not model_stats:
        lines.append("No valid data found.")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return

    all_dominance = [s['avg_dominance'] for s in model_stats.values()]
    all_adj_ratio = [s['avg_adj_same_dir'] for s in model_stats.values()]
    all_adj_sig = [s['pct_adj_significant'] for s in model_stats.values()]
    all_moran = [s['avg_moran_i'] for s in model_stats.values()]

    lines.extend([
        f"Models analyzed: {len(model_stats)}",
        "",
        f"Step 1 - Dominance Ratio:",
        f"  Average: {np.mean(all_dominance)*100:.1f}% (random baseline: {RANDOM_BASELINE*100:.1f}%)",
        f"  Ratio vs baseline: {np.mean(all_dominance)/RANDOM_BASELINE:.1f}×",
        "",
        f"Step 2 - Adjacent Same-Direction Ratio:",
        f"  Average: {np.mean(all_adj_ratio)*100:.1f}% (random baseline: {RANDOM_BASELINE*100:.1f}%)",
        f"  Ratio vs baseline: {np.mean(all_adj_ratio)/RANDOM_BASELINE:.1f}×",
        f"  Boards with p<0.05: {np.mean(all_adj_sig)*100:.1f}%",
        "",
        f"Supporting - Moran's I: {np.mean(all_moran):.3f}",
        "",
        "CONCLUSION:",
    ])

    dom_ratio = np.mean(all_dominance) / RANDOM_BASELINE
    adj_ratio = np.mean(all_adj_ratio) / RANDOM_BASELINE

    if adj_ratio > 2.0:
        lines.append("✔ STRONG EVIDENCE of structural shift")
        lines.append(
            f"  Adjacent same-direction ratio is {adj_ratio:.1f}× random baseline")
        lines.append("  → Adjacent pieces shift in the SAME direction")
        lines.append("  → This proves errors are STRUCTURAL, not random")
    elif adj_ratio > 1.5:
        lines.append("✔ MODERATE EVIDENCE of structural shift")
        lines.append(
            f"  Adjacent same-direction ratio is {adj_ratio:.1f}× random baseline")
    else:
        lines.append("? WEAK/NO EVIDENCE of structural shift")
        lines.append(
            f"  Adjacent same-direction ratio is only {adj_ratio:.1f}× random baseline")

    if dom_ratio > 2.0:
        lines.append(
            f"✔ Clear direction preference (dominance {dom_ratio:.1f}× baseline)")

    lines.extend(["", "MODEL-BY-MODEL RESULTS", "-" * 40])

    for model, stats in model_stats.items():
        adj_r = stats['avg_adj_same_dir']
        adj_vs_base = adj_r / RANDOM_BASELINE
        lines.extend([
            f"\n{MODEL_LABELS.get(model, model)}:",
            f"  Boards analyzed: {stats['n_boards']}",
            f"  Dominance ratio: {stats['avg_dominance']*100:.1f}% ({stats['avg_dominance']/RANDOM_BASELINE:.1f}× baseline)",
            f"  Adjacent same-dir: {adj_r*100:.1f}% ({adj_vs_base:.1f}× baseline) {'★' if adj_vs_base > 2 else ''}",
            f"  Significant (p<0.05): {stats['pct_adj_significant']*100:.1f}% of boards",
            f"  Moran's I: {stats['avg_moran_i']:.3f}",
        ])

    lines.extend(["", "=" * 70])

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"  ✔ Saved: {output_path}")


# Main Entry Point

def main():
    parser = argparse.ArgumentParser(
        description='Structural Shift Analysis - Prove off-by-1 errors are systematic',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Proof Logic:
  Step 1: Dominance Ratio >> 12.5%  → Direction preference exists
  Step 2: Adjacent Same-Dir >> MC → Adjacent pieces shift TOGETHER
  Step 3: Heatmap visualization

Examples:
    python group_localization.py
    python group_localization.py /path/to/results
    python group_localization.py -j 8 --mc 500
        """
    )

    parser.add_argument('path', nargs='?', default='.',
                        help='Root directory containing model results')
    parser.add_argument('--output-dir', '-o', default='./structural_analysis',
                        help='Output directory for plots and reports')
    parser.add_argument('--workers', '-j', type=int, default=8,
                        help='Number of parallel workers')
    parser.add_argument('--mc', type=int, default=200,
                        help='Number of Monte Carlo simulations')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print verbose output')

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    data = scan_and_process_data(
        args.path, mc_sims=args.mc, num_workers=args.workers)

    print("\n📊 Aggregating results...")
    model_stats = aggregate_by_model(data)
    shift_dist = aggregate_shift_distribution(data)

    if not model_stats:
        print("\n❌ No valid data found!")
        return

    print("\n🎨 Generating visualizations...")

    plot_dominance_ratio_standalone(
        model_stats,
        os.path.join(args.output_dir, 'dominance_ratio.pdf')
    )

    plot_adjacent_ratio_vs_baseline(
        model_stats,
        os.path.join(args.output_dir, 'adjacent_ratio_vs_baseline.pdf')
    )

    plot_shift_preference_heatmap(
        data,
        os.path.join(args.output_dir, 'shift_preference_heatmap.pdf')
    )

    print("\n📝 Generating report...")
    generate_summary_report(
        model_stats,
        shift_dist,
        os.path.join(args.output_dir, 'report.txt')
    )

    output_json = os.path.join(args.output_dir, 'structural_analysis.json')
    with open(output_json, 'w') as f:
        json.dump({
            'model_stats': model_stats,
            'shift_distribution': shift_dist,
            'timestamp': datetime.now().isoformat(),
        }, f, indent=2, default=str)
    print(f"  ✔ Saved: {output_json}")

    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 70)

    avg_dom = np.mean([s['avg_dominance'] for s in model_stats.values()])
    avg_adj = np.mean([s['avg_adj_same_dir'] for s in model_stats.values()])

    print(f"\nKey Results:")
    print(
        f"  Step 1 - Dominance: {avg_dom*100:.1f}% ({avg_dom/RANDOM_BASELINE:.1f}× baseline)")
    print(
        f"  Step 2 - Adjacent Same-Dir: {avg_adj*100:.1f}% ({avg_adj/RANDOM_BASELINE:.1f}× baseline)")

    if avg_adj / RANDOM_BASELINE > 2.0:
        print(f"\n  ✔ PROOF SUCCESSFUL: Adjacent pieces shift TOGETHER")
        print(f"    Off-by-1 errors are STRUCTURAL, not random noise")

    print("=" * 70)


if __name__ == "__main__":
    main()
