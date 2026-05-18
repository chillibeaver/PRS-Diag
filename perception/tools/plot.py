#!/usr/bin/env python3
"""
Final Analysis Plotting Script - ICML 2026 Submission Version
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
from matplotlib.ticker import PercentFormatter
from matplotlib.lines import Line2D

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

# ================= Configuration =================
BASE_DIR = "."
GAMES = ["chess", "gomoku"]
TEST_KEYWORD_DENSITY = "density"
TEST_KEYWORD_PATCH = "patch"
TEST_KEYWORD_RESOLUTION = "resolution"
TEST_KEYWORD_RICHNESS = "richness"

MODELS = ['gemma3-27b', 'glm4.1v-9b',
          'gpt5.2', 'qwen8b', 'qwen30b', 'qwen235b']

MODEL_LABELS = {
    'gemma3-27b': r'Gemma-3 27B',
    'glm4.1v-9b': r'GLM-4.1V 9B',
    'gpt5.2': r'GPT-5.2',
    'qwen8b': r'Qwen3-VL 8B',
    'qwen30b': r'Qwen3-VL 30B',
    'qwen235b': r'Qwen3-VL 235B'
}

COLORS = {'gemma3-27b': '#e74c3c', 'glm4.1v-9b': '#3498db', 'gpt5.2': '#2ecc71',
          'qwen8b': '#9b59b6', 'qwen30b': '#f1c40f', 'qwen235b': '#34495e'}

MARKERS = {'gemma3-27b': 'o', 'glm4.1v-9b': 's', 'gpt5.2': '^',
           'qwen8b': 'D', 'qwen30b': 'P', 'qwen235b': 'X'}

# Resolution configurations per model (patch_size -> resolution pairs)
MODEL_RESOLUTION_CONFIG = {
    'gemma3-27b': {'divisible': ['1008', '896', '392'], 'non_divisible': ['1010', '900', '400']},
    'glm4.1v-9b': {'divisible': ['1008', '896', '392'], 'non_divisible': ['1010', '900', '400']},
    'gpt5.2': {'divisible': ['1024', '512', '384'], 'non_divisible': ['1010', '510', '370']},
    'qwen8b': {'divisible': ['1024', '512', '384'], 'non_divisible': ['1010', '510', '370']},
    'qwen30b': {'divisible': ['1024', '512', '384'], 'non_divisible': ['1010', '510', '370']},
    'qwen235b': {'divisible': ['1024', '512', '384'], 'non_divisible': ['1010', '510', '370']},
}

# Font settings
FONT_AXIS_LABEL = 30
FONT_TICK_LABEL = 24
FONT_TITLE = 30
FONT_SUPTITLE = 34
FONT_LEGEND = 20
FONT_ANNOTATION = 14

# ================= Data Extraction Helpers =================


def get_val(data, keys):
    val = data
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return None
    return val


# ================= 1. Density Analysis =================


def scan_density_data(base_dir):
    print(f"🔍 Scanning Density data...")
    table_data = {m: {'chess': {}, 'gomoku': {}} for m in MODELS}
    scatter_data = {m: {g: {'x': [], 'y': []} for g in GAMES} for m in MODELS}
    for model in MODELS:
        for game in GAMES:
            search_path = os.path.join(
                base_dir, model, game, f"*{TEST_KEYWORD_DENSITY}*")
            found_dirs = glob.glob(search_path)
            if not found_dirs:
                continue
            target_dir = sorted(found_dirs)[-1]
            json_file = os.path.join(target_dir, 'results.json')
            if not os.path.exists(json_file):
                continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'summary' in data:
                    s = data['summary']
                    metrics = {d: get_val(s, [d, 'metrics', 'piece_accuracy', 'mean']) for d in [
                        'low', 'medium', 'high']}
                    valid_vals = [v for v in metrics.values() if v is not None]
                    avg_val = sum(valid_vals) / \
                        len(valid_vals) if valid_vals else None
                    table_data[model][game] = {
                        'low': metrics['low'], 'med': metrics['medium'], 'high': metrics['high'], 'avg': avg_val}
                if 'test_cases' in data:
                    for case in data['test_cases']:
                        p = get_val(case, ['statistics', 'total_pieces'])
                        a = case.get('piece_accuracy')
                        if p is not None and a is not None:
                            scatter_data[model][game]['x'].append(p)
                            scatter_data[model][game]['y'].append(a * 100)
            except:
                pass
    return table_data, scatter_data


def plot_density_scatter(scatter_data, output_name):
    fig, axes = plt.subplots(1, 2, figsize=(24, 10), sharey=True)
    models_with_data = set()
    for ax, game in zip(axes, GAMES):
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_title(game.capitalize(), fontsize=FONT_TITLE,
                     fontweight='bold', pad=20)
        if ax == axes[0]:
            ax.set_ylabel(r'Piece Accuracy (\%)',
                          fontsize=FONT_AXIS_LABEL, fontweight='bold')
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=100))
        ax.tick_params(axis='both', which='major', labelsize=FONT_TICK_LABEL)
        for model in MODELS:
            d = scatter_data[model][game]
            if not d['x']:
                continue
            models_with_data.add(model)
            ax.scatter(d['x'], d['y'], alpha=0.25, s=120,
                       color=COLORS[model], marker=MARKERS[model])
            if len(d['x']) > 2:
                z = np.polyfit(d['x'], d['y'], 1)
                p = np.poly1d(z)
                ax.plot(np.linspace(min(d['x']), max(d['x']), 100), p(np.linspace(
                    min(d['x']), max(d['x']), 100)), color=COLORS[model], linewidth=4)
    fig.text(0.5, 0.12, 'Number of Pieces on Board', ha='center',
             fontsize=FONT_AXIS_LABEL, fontweight='bold')
    legend_els = [Line2D([0], [0], color=COLORS[m], marker=MARKERS[m], label=MODEL_LABELS[m],
                         markersize=14, linewidth=4) for m in MODELS if m in models_with_data]
    fig.legend(handles=legend_els, loc='lower center', bbox_to_anchor=(0.5, 0.02), ncol=len(
        legend_els), fontsize=FONT_LEGEND, frameon=True, edgecolor='black', fancybox=True)

    plt.subplots_adjust(top=0.85, bottom=0.22, wspace=0.05)
    plt.savefig(output_name, dpi=300, bbox_inches='tight')
    plt.close()

# ================= 2. Patch Analysis =================


def scan_patch_data(base_dir):
    print(f"🔍 Scanning Patch data...")
    table_data = {m: {'chess': {}, 'gomoku': {}} for m in MODELS}
    raw_data = {m: {g: {'x': [], 'y': []} for g in GAMES} for m in MODELS}

    POS_MAP = {'boundary': 'bnd', 'quarter': 'qtr',
               'center': 'ctr', 'three_quarter': '3qt'}
    pos_x = {'boundary': 0, 'quarter': 0.25,
             'center': 0.5, 'three_quarter': 0.75}

    for model in MODELS:
        for game in GAMES:
            search_path = os.path.join(
                base_dir, model, game, f"*{TEST_KEYWORD_PATCH}*")
            found_dirs = glob.glob(search_path)
            if not found_dirs:
                continue
            json_file = os.path.join(sorted(found_dirs)[-1], 'results.json')
            if not os.path.exists(json_file):
                continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if 'summary' in data:
                    s = data['summary']
                    table_data[model][game] = {k: get_val(
                        s, [full, 'metrics', 'piece_accuracy', 'mean']) for full, k in POS_MAP.items()}

                if 'test_cases' in data:
                    for case in data['test_cases']:
                        cond = case.get('alignment_condition')
                        acc = case.get('piece_accuracy')
                        if cond in pos_x and acc is not None:
                            raw_data[model][game]['x'].append(pos_x[cond])
                            raw_data[model][game]['y'].append(acc * 100)
            except:
                pass
    return table_data, raw_data


def plot_patch_scatter_trend(patch_data, output_name):
    pos_x = {'bnd': 0, 'qtr': 0.25, 'ctr': 0.5, '3qt': 0.75}
    fig, axes = plt.subplots(1, 2, figsize=(24, 10), sharey=True)
    models_with_data = set()
    for ax, game in zip(axes, GAMES):
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_title(game.capitalize(), fontsize=FONT_TITLE,
                     fontweight='bold', pad=20)
        if ax == axes[0]:
            ax.set_ylabel(r'Piece Accuracy (\%)',
                          fontsize=FONT_AXIS_LABEL, fontweight='bold')
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=100))
        ax.tick_params(axis='both', which='major', labelsize=FONT_TICK_LABEL)

        for model in MODELS:
            d = patch_data[model][game]
            if not d:
                continue

            x_vals = []
            y_vals = []
            for k, x in pos_x.items():
                if d.get(k) is not None:
                    x_vals.append(x)
                    y_vals.append(d[k] * 100)

            if not x_vals:
                continue
            models_with_data.add(model)

            ax.scatter(x_vals, y_vals, alpha=0.6, s=150,
                       color=COLORS[model], marker=MARKERS[model])

            if len(x_vals) > 1:
                z = np.polyfit(x_vals, y_vals, 1)
                p = np.poly1d(z)
                ax.plot(x_vals, p(x_vals), color=COLORS[model], linewidth=4)

        ax.set_xticks([0, 0.25, 0.5, 0.75])
        ax.set_xticklabels(['0', '1/4', '1/2', '3/4'],
                           fontsize=FONT_TICK_LABEL)

    fig.text(0.5, 0.12, 'Patch Alignment Offset', ha='center',
             fontsize=FONT_AXIS_LABEL, fontweight='bold')
    legend_els = [Line2D([0], [0], color=COLORS[m], marker=MARKERS[m], label=MODEL_LABELS[m],
                         markersize=14, linewidth=4) for m in MODELS if m in models_with_data]
    fig.legend(handles=legend_els, loc='lower center', bbox_to_anchor=(0.5, 0.02), ncol=len(
        legend_els), fontsize=FONT_LEGEND, frameon=True, edgecolor='black', fancybox=True)
    plt.subplots_adjust(top=0.85, bottom=0.22, wspace=0.05)
    plt.savefig(output_name, dpi=300, bbox_inches='tight')
    plt.close()


# ================= 3. Resolution Analysis =================


def scan_resolution_data(base_dir):
    print(f"🔍 Scanning Resolution data...")
    table_data = {m: {g: {'divisible': {}, 'non_divisible': {}}
                      for g in GAMES} for m in MODELS}
    for model in MODELS:
        for game in GAMES:
            search_path = os.path.join(
                base_dir, model, game, f"*{TEST_KEYWORD_RESOLUTION}*")
            found_dirs = glob.glob(search_path)
            target_dir = sorted(found_dirs)[-1] if found_dirs else None
            if not target_dir:
                continue
            json_file = os.path.join(target_dir, 'results.json')
            if not os.path.exists(json_file):
                continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'summary' in data:
                    s = data['summary']
                    for group in ['divisible', 'non_divisible']:
                        if group not in s:
                            continue
                        for res_key, res_data in s[group].items():
                            acc = get_val(
                                res_data, ['metrics', 'piece_accuracy', 'mean'])
                            if acc is not None:
                                table_data[model][game][group][res_key] = acc
            except:
                pass
    return table_data


def plot_resolution_trend_lines(table_data, output_name):
    """Plot resolution trends using model-specific resolution pairs."""
    fig, axes = plt.subplots(1, 2, figsize=(24, 11), sharey=True)

    valid_models = [m for m in MODELS if any(
        table_data[m][g]['divisible'] for g in GAMES)]
    if not valid_models:
        return

    x_labels = ['High', 'Medium', 'Low']
    x = np.arange(3)

    for i, game in enumerate(GAMES):
        ax = axes[i]
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_title(game.capitalize(), fontsize=FONT_TITLE,
                     fontweight='bold', pad=25)

        for model in valid_models:
            d = table_data[model][game]

            div_res = MODEL_RESOLUTION_CONFIG[model]['divisible']
            ndiv_res = MODEL_RESOLUTION_CONFIG[model]['non_divisible']

            div_vals = [d['divisible'].get(r, 0) * 100 for r in div_res]
            ndiv_vals = [d['non_divisible'].get(r, 0) * 100 for r in ndiv_res]

            if any(v > 0 for v in div_vals):
                ax.plot(x, div_vals, color=COLORS[model], marker=MARKERS[model],
                        linestyle='-', linewidth=4, markersize=14)
            if any(v > 0 for v in ndiv_vals):
                ax.plot(x, ndiv_vals, color=COLORS[model], marker=MARKERS[model],
                        linestyle='--', linewidth=3, markersize=12, alpha=0.7)

        ax.set_xticks(x)
        ax.set_xticklabels(x_labels, fontsize=FONT_TICK_LABEL)
        ax.tick_params(axis='y', which='major',
                       labelsize=FONT_TICK_LABEL)
        if i == 0:
            ax.set_ylabel(r'Piece Accuracy (\%)',
                          fontsize=FONT_AXIS_LABEL, fontweight='bold')
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=100))
        ax.set_ylim(0, 105)

    legend_els = [Line2D([0], [0], color=COLORS[m], marker=MARKERS[m], label=MODEL_LABELS[m],
                         markersize=14, linewidth=4) for m in valid_models]
    legend_els.extend([
        Line2D([0], [0], color='gray', linestyle='-',
               linewidth=3, label='Divisible (Solid)'),
        Line2D([0], [0], color='gray', linestyle='--',
               linewidth=3, label='Non-divisible (Dashed)')
    ])
    fig.legend(handles=legend_els, loc='lower center', bbox_to_anchor=(0.5, 0.02),
               ncol=4, fontsize=FONT_LEGEND, frameon=True, edgecolor='black')

    fig.text(0.5, 0.12, 'Relative Resolution', ha='center',
             fontsize=FONT_AXIS_LABEL, fontweight='bold')

    plt.subplots_adjust(top=0.85, bottom=0.22, wspace=0.15)
    plt.savefig(output_name, dpi=300, bbox_inches='tight')
    plt.close()

# ================= 4. Visual Richness Analysis =================


def scan_richness_data(base_dir):
    print(f"🔍 Scanning Richness data...")
    table_data = {m: {g: {} for g in GAMES} for m in MODELS}
    RICH_MAP = {'2d_flat': '2D', '3d_rendered': '3D'}

    for model in MODELS:
        for game in GAMES:
            search_path = os.path.join(
                base_dir, model, game, f"*{TEST_KEYWORD_RICHNESS}*")
            found_dirs = glob.glob(search_path)
            if not found_dirs:
                continue
            json_file = os.path.join(sorted(found_dirs)[-1], 'results.json')
            if not os.path.exists(json_file):
                continue
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'summary' in data:
                    s = data['summary']
                    table_data[model][game] = {RICH_MAP[full]: get_val(
                        s, [full, 'metrics', 'piece_accuracy', 'mean']) for full in RICH_MAP.keys() if full in s}
            except:
                pass
    return table_data


def plot_richness_analysis(rich_data, output_name):
    fig, axes = plt.subplots(1, 2, figsize=(22, 11), sharey=True)
    rich_keys = ['2D', '3D']

    valid_models = [m for m in MODELS if any(rich_data[m][g] for g in GAMES)]
    if not valid_models:
        return

    n_models = len(valid_models)
    x = np.arange(len(rich_keys))
    width = 0.8 / n_models

    for i, game in enumerate(GAMES):
        ax = axes[i]
        ax.grid(True, axis='y', linestyle='--', alpha=0.3)
        ax.set_title(game.capitalize(), fontsize=FONT_TITLE,
                     fontweight='bold', pad=25)

        for j, model in enumerate(valid_models):
            d = rich_data[model][game]
            vals = [d.get(k, 0) * 100 if d.get(k)
                    is not None else 0 for k in rich_keys]

            offset = (j - (n_models - 1) / 2) * width
            rects = ax.bar(x + offset, vals, width, label=MODEL_LABELS[model],
                           color=COLORS[model], edgecolor='black', linewidth=1)

            for rect in rects:
                if rect.get_height() > 0:
                    ax.text(rect.get_x() + rect.get_width()/2., rect.get_height() + 0.5,
                            f'{rect.get_height():.1f}', ha='center', va='bottom', fontsize=17)

        ax.set_xticks(x)
        ax.set_xticklabels(
            rich_keys, fontsize=FONT_TICK_LABEL, fontweight='bold')
        ax.tick_params(axis='y', which='major',
                       labelsize=FONT_TICK_LABEL)
        if i == 0:
            ax.set_ylabel(r'Piece Accuracy (\%)',
                          fontsize=FONT_AXIS_LABEL, fontweight='bold')
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=100))
        ax.set_ylim(0, 110)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles[:n_models], labels[:n_models], loc='lower center', bbox_to_anchor=(
        0.5, 0.02), ncol=3, fontsize=FONT_LEGEND, frameon=True, edgecolor='black')

    fig.text(0.5, 0.12, 'Rendering Style', ha='center',
             fontsize=FONT_AXIS_LABEL, fontweight='bold')

    plt.subplots_adjust(top=0.85, bottom=0.22, wspace=0.15)
    plt.savefig(output_name, dpi=300, bbox_inches='tight')
    plt.close()


# ================= 5. Empty Bias Analysis =================


def scan_empty_bias_data(base_dir):
    """
    Scan density test results to extract empty bias metrics.
    Computes metrics per density level for each model and game.
    """
    print(f"🔍 Scanning Empty Bias data...")

    bias_data = {m: {g: {} for g in GAMES} for m in MODELS}

    for model in MODELS:
        for game in GAMES:
            board_size = 15 if game == 'gomoku' else 8
            total_cells = board_size ** 2

            search_path = os.path.join(
                base_dir, model, game, f"*{TEST_KEYWORD_DENSITY}*")
            found_dirs = glob.glob(search_path)
            if not found_dirs:
                continue
            json_file = os.path.join(sorted(found_dirs)[-1], 'results.json')
            if not os.path.exists(json_file):
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if 'test_cases' not in data:
                    continue

                by_density = {'low': [], 'medium': [], 'high': []}

                for case in data['test_cases']:
                    if 'error' in case or not case.get('parse_success', True):
                        continue

                    density = case.get('density_level')
                    if density not in by_density:
                        continue

                    pred = np.array(case.get('predicted', []))
                    truth = np.array(case.get('ground_truth', []))

                    if pred.size == 0 or truth.size == 0:
                        continue

                    actual_pieces = int(np.sum(truth != 0))
                    predicted_pieces = int(np.sum(pred != 0))
                    actual_empty = total_cells - actual_pieces
                    predicted_empty = total_cells - predicted_pieces

                    breakdown = case.get('detection_breakdown', {})
                    missed = breakdown.get('missed', 0)
                    false_positive = breakdown.get('false_positive', 0)

                    by_density[density].append({
                        'actual_pieces': actual_pieces,
                        'predicted_pieces': predicted_pieces,
                        'actual_empty': actual_empty,
                        'predicted_empty': predicted_empty,
                        'missed': missed,
                        'false_positive': false_positive,
                    })

                for density, cases in by_density.items():
                    if not cases:
                        continue

                    avg_actual_pieces = np.mean(
                        [c['actual_pieces'] for c in cases])
                    avg_pred_pieces = np.mean(
                        [c['predicted_pieces'] for c in cases])
                    avg_actual_empty = np.mean(
                        [c['actual_empty'] for c in cases])
                    avg_pred_empty = np.mean(
                        [c['predicted_empty'] for c in cases])
                    avg_missed = np.mean([c['missed'] for c in cases])
                    avg_fp = np.mean([c['false_positive'] for c in cases])

                    # Empty rate (as percentage)
                    actual_empty_rate = (avg_actual_empty / total_cells) * 100
                    predicted_empty_rate = (avg_pred_empty / total_cells) * 100

                    miss_rate = (avg_missed / avg_actual_pieces *
                                 100) if avg_actual_pieces > 0 else 0
                    fp_rate = (avg_fp / avg_actual_empty *
                               100) if avg_actual_empty > 0 else 0

                    bias_data[model][game][density] = {
                        'actual_empty_rate': actual_empty_rate,
                        'predicted_empty_rate': predicted_empty_rate,
                        'empty_rate_diff': predicted_empty_rate - actual_empty_rate,
                        'miss_rate': miss_rate,
                        'fp_rate': fp_rate,
                    }
            except:
                pass

    return bias_data


def plot_miss_proportion(bias_data, output_name):
    """
    Figure: Miss Proportion = Miss / (Miss + FP)

    Shows what proportion of errors are "missing pieces" (predicting empty 
    when there's a piece) vs "hallucinating pieces" (predicting piece when empty).

    - Value > 50%: Model errors lean toward predicting empty
    - Value = 50%: Balanced errors (same as random baseline)
    - Value < 50%: Model errors lean toward hallucinating pieces

    Key insight: Random baseline is ALWAYS 50% regardless of density,
    making this metric directly comparable across density levels.
    """
    fig, ax = plt.subplots(figsize=(18, 12))

    densities = ['low', 'medium', 'high']
    density_labels = ['Low', 'Medium', 'High']

    valid_models = [m for m in MODELS if any(bias_data[m][g] for g in GAMES)]
    if not valid_models:
        return

    n_models = len(valid_models)
    x = np.arange(len(densities))
    width = 0.8 / n_models

    ax.grid(True, axis='y', linestyle='--', alpha=0.3)

    for j, model in enumerate(valid_models):
        miss_proportions = []

        for density in densities:
            total_miss = 0
            total_fp = 0

            for game in GAMES:
                d = bias_data[model][game].get(density, {})
                if d:
                    miss_rate = d.get('miss_rate', 0)
                    fp_rate = d.get('fp_rate', 0)
                    actual_empty_rate = d.get('actual_empty_rate', 50)

                    # Reconstruct raw counts based on board size
                    board_size = 15 if game == 'gomoku' else 8
                    total_cells = board_size ** 2
                    actual_empty = total_cells * (actual_empty_rate / 100)
                    actual_pieces = total_cells - actual_empty

                    # Raw counts (miss_rate and fp_rate are in percentage)
                    miss_count = (miss_rate / 100) * actual_pieces
                    fp_count = (fp_rate / 100) * actual_empty

                    total_miss += miss_count
                    total_fp += fp_count

            # Miss proportion
            if total_miss + total_fp > 0:
                proportion = total_miss / (total_miss + total_fp)
            else:
                proportion = 0.5
            miss_proportions.append(proportion * 100)

        offset = (j - (n_models - 1) / 2) * width
        rects = ax.bar(x + offset, miss_proportions, width,
                       label=MODEL_LABELS[model],
                       color=COLORS[model], edgecolor='black', linewidth=1)

        # Add value annotations
        for rect in rects:
            h = rect.get_height()
            ax.text(rect.get_x() + rect.get_width()/2., h + 1,
                    f'{h:.1f}\\%', ha='center', va='bottom',
                    fontsize=17, fontweight='bold')

    # Reference line at 50% (random baseline - constant across all densities)
    ax.axhline(y=50, color='red', linestyle='--', linewidth=3,
               label=r'Random Baseline (50\%)', zorder=0)

    ax.set_xticks(x)
    ax.set_xticklabels(
        density_labels, fontsize=FONT_TICK_LABEL, fontweight='bold')
    ax.set_xlabel('Density Level', fontsize=FONT_AXIS_LABEL, fontweight='bold')
    ax.set_ylabel(r'Miss Proportion Among Errors (\%)',
                  fontsize=FONT_AXIS_LABEL, fontweight='bold')
    ax.tick_params(axis='both', which='major', labelsize=FONT_TICK_LABEL)
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=100))

    # Legend at bottom
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 0.02),
               ncol=4, fontsize=FONT_LEGEND, frameon=True, edgecolor='black')

    plt.subplots_adjust(bottom=0.18)
    plt.savefig(output_name, dpi=300, bbox_inches='tight')
    plt.close()


# ================= Main =================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    default_path = os.path.join(os.path.dirname(__file__), '..')
    parser.add_argument('path', nargs='?', default=default_path,
                        help='Root dir containing <model>/<game>/<test>/ subfolders (default: <script_dir>/..)')
    parser.add_argument('--output-prefix', default='', help='Prefix')
    args = parser.parse_args()

    # 1. Density Analysis
    t_dens, s_dens = scan_density_data(args.path)
    plot_density_scatter(s_dens, f"{args.output_prefix}density_piece_acc.pdf")

    # 2. Patch Analysis
    t_patch, r_patch = scan_patch_data(args.path)
    plot_patch_scatter_trend(
        t_patch, f"{args.output_prefix}patch_scatter_trend.pdf")

    # 3. Resolution Analysis
    t_res = scan_resolution_data(args.path)
    plot_resolution_trend_lines(
        t_res, f"{args.output_prefix}resolution_trend_lines.pdf")

    # 4. Visual Richness Analysis
    t_rich = scan_richness_data(args.path)
    plot_richness_analysis(
        t_rich, f"{args.output_prefix}richness_analysis.pdf")

    # 5. Empty Bias Analysis
    t_bias = scan_empty_bias_data(args.path)
    plot_miss_proportion(
        t_bias, f"{args.output_prefix}density_empty_miss_proportion.pdf")
    print("\n✅ All analysis tasks completed successfully.")
