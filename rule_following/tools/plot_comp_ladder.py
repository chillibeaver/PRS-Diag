#!/usr/bin/env python3
"""
Level 1-6 analysis plotting script - ultimate all-in-one
Features:
1. Includes all features of Figures 1-4 (anti-overlap labels)
2. Includes Figure 5 (per-game comparison)
3. Adds Figure 6: Qwen-series-only scaling trend
"""

from collections import defaultdict
import os
import json
import re
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

# =====
mpl.rcParams['text.usetex'] = True
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times']
mpl.rcParams['text.latex.preamble'] = r'\usepackage{times}'
# ========================================


# ================= Configuration =================
GAMES = ["chess", "xiangqi"]
MODES = ["explicit", "predictive"]
LEVELS = [1, 2, 3, 4, 5, 6]

# Supported model list
MODEL_KEYS = ["qwen8b", "qwen30b", "qwen235b", "gpt5.2"]

MODEL_LABELS = {
    "qwen8b": "Qwen3-VL 8B",
    "qwen30b": "Qwen3-VL 30B",
    "qwen235b": "Qwen3-VL 235B",
    "gpt5.2": "GPT-5.2",
}

COLORS = {
    "qwen8b": "#3498db",
    "qwen30b": "#9b59b6",
    "qwen235b": "#2ecc71",
    "gpt5.2": "#1abc9c",
}

MARKERS = {
    "qwen8b": "o",
    "qwen30b": "s",
    "qwen235b": "D",
    "gpt5.2": "p",
}

LEVEL_LABELS = ['L1', 'L2', 'L3', 'L4', 'L5', 'L6']
PERCEPTION_COLOR = "#f97316"
REASONING_COLOR = "#374151"

# ================= Font Size Configuration (doubled for print) =================
FONT_AXIS_LABEL = 22
FONT_TICK_LABEL = 24
FONT_TITLE = 28
FONT_SUPTITLE = 34
FONT_LEGEND = 22
FONT_ANNOTATION = 16
FONT_ANNOTATION_SMALL = 18
SHARED_LEGEND_Y = 0.01
SHARED_XLABEL_Y = 0.02

# ================= Data Extraction =================


def extract_model_key(folder_name):
    folder_lower = folder_name.lower()
    for key in MODEL_KEYS:
        if key.lower() in folder_lower:
            return key
    return None


def extract_level_from_folder(folder_name):
    match = re.search(r'level_(\d+)', folder_name.lower())
    if match:
        return int(match.group(1))
    return None


def find_json_in_folder(folder_path):
    if not os.path.isdir(folder_path):
        return None
    for f in os.listdir(folder_path):
        if f.endswith('.json'):
            return os.path.join(folder_path, f)
    return None


def get_metrics_from_json(filepath):
    if not filepath or not os.path.exists(filepath):
        return 0.0, 0.0
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        summary = data.get("summary", {})
        ver_rate = summary.get("board_recognition", {}).get(
            "verification_rate", 0.0)
        acc = summary.get("test_accuracy", {}).get(
            "accuracy_given_verified", 0.0)
        return ver_rate * 100, acc * 100
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return 0.0, 0.0


def get_detailed_results_from_json(filepath):
    """Load detailed case-level results from JSON file."""
    if not filepath or not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        results_map = {}
        for case in data.get('detailed_results', []):
            c_id = case.get('case_id')
            verified = case.get('verification_passed', False)
            correct = case.get('correct', False)
            results_map[c_id] = {'verified': verified, 'correct': correct}
        return results_map
    except Exception as e:
        print(f"Error reading detailed results from {filepath}: {e}")
        return {}


def scan_and_load_data(base_dir="."):
    data = {g: {m: {} for m in MODES} for g in GAMES}

    for game in GAMES:
        game_path = os.path.join(base_dir, game)
        if not os.path.isdir(game_path):
            continue
        for mode_folder in os.listdir(game_path):
            mode_path = os.path.join(game_path, mode_folder)
            if not os.path.isdir(mode_path):
                continue

            mode = None
            if 'explicit' in mode_folder.lower():
                mode = 'explicit'
            elif 'predictive' in mode_folder.lower():
                mode = 'predictive'
            else:
                continue

            for model_folder in os.listdir(mode_path):
                model_path = os.path.join(mode_path, model_folder)
                if not os.path.isdir(model_path) or model_folder.startswith('.'):
                    continue

                model_key = extract_model_key(model_folder)
                if model_key is None:
                    continue

                if model_key not in data[game][mode]:
                    data[game][mode][model_key] = {
                        'perception': {l: [] for l in LEVELS},
                        'reasoning': {l: [] for l in LEVELS}
                    }

                for level_folder in os.listdir(model_path):
                    level_path = os.path.join(model_path, level_folder)
                    if not os.path.isdir(level_path):
                        continue
                    level = extract_level_from_folder(level_folder)
                    if level is None or level not in LEVELS:
                        continue

                    json_file = find_json_in_folder(level_path)
                    if json_file:
                        perc, reas = get_metrics_from_json(json_file)
                        data[game][mode][model_key]['perception'][level].append(
                            perc)
                        data[game][mode][model_key]['reasoning'][level].append(
                            reas)
    return data


def scan_and_load_detailed_data(base_dir="."):
    """
    Load detailed case-level data for intersection analysis.
    Structure: data[game][mode][model][level] = {case_id: {verified, correct}}
    """
    data = {g: {m: {} for m in MODES} for g in GAMES}

    for game in GAMES:
        game_path = os.path.join(base_dir, game)
        if not os.path.isdir(game_path):
            continue
        for mode_folder in os.listdir(game_path):
            mode_path = os.path.join(game_path, mode_folder)
            if not os.path.isdir(mode_path):
                continue

            mode = None
            if 'explicit' in mode_folder.lower():
                mode = 'explicit'
            elif 'predictive' in mode_folder.lower():
                mode = 'predictive'
            else:
                continue

            for model_folder in os.listdir(mode_path):
                model_path = os.path.join(mode_path, model_folder)
                if not os.path.isdir(model_path) or model_folder.startswith('.'):
                    continue

                model_key = extract_model_key(model_folder)
                if model_key is None:
                    continue

                if model_key not in data[game][mode]:
                    data[game][mode][model_key] = {}

                for level_folder in os.listdir(model_path):
                    level_path = os.path.join(model_path, level_folder)
                    if not os.path.isdir(level_path):
                        continue
                    level = extract_level_from_folder(level_folder)
                    if level is None or level not in LEVELS:
                        continue

                    json_file = find_json_in_folder(level_path)
                    if json_file:
                        detailed = get_detailed_results_from_json(json_file)
                        if detailed:
                            data[game][mode][model_key][level] = detailed
    return data


def calculate_qwen_intersection_accuracy(detailed_data, qwen_models):
    """
    Calculate accuracy on cases where ALL Qwen models passed verification.
    Returns: {mode: {model: {level: accuracy}}}
    """
    result = {mode: {m: {} for m in qwen_models} for mode in MODES}

    for mode in MODES:
        for level in LEVELS:
            # Collect case data for each model at this mode/level
            model_case_maps = {}
            for model in qwen_models:
                all_cases = {}
                for game in GAMES:
                    if model in detailed_data[game][mode]:
                        if level in detailed_data[game][mode][model]:
                            # Merge with game prefix to avoid collision
                            for cid, cdata in detailed_data[game][mode][model][level].items():
                                all_cases[f"{game}_{cid}"] = cdata
                model_case_maps[model] = all_cases

            # Find intersection: cases where ALL Qwen models have verified=True
            if not all(model_case_maps.values()):
                continue

            # Get common case IDs
            common_ids = set.intersection(
                *[set(m.keys()) for m in model_case_maps.values()])

            # Filter: ALL models must have verified=True for this case
            valid_intersection = []
            for cid in common_ids:
                if all(model_case_maps[m][cid]['verified'] for m in qwen_models):
                    valid_intersection.append(cid)

            if not valid_intersection:
                for model in qwen_models:
                    result[mode][model][level] = 0.0
                continue

            # Calculate accuracy for each model on the intersection
            for model in qwen_models:
                correct_count = sum(
                    1 for cid in valid_intersection
                    if model_case_maps[model][cid]['correct']
                )
                result[mode][model][level] = (
                    correct_count / len(valid_intersection)) * 100

    return result


def merge_all_games(raw_data):
    aggregated = {mode: {} for mode in MODES}
    all_models = set()
    for g in GAMES:
        for m in MODES:
            all_models.update(raw_data[g][m].keys())

    for mode in MODES:
        for model in all_models:
            perc_means = []
            reas_means = []
            for level in LEVELS:
                all_perc_vals = []
                all_reas_vals = []
                for game in GAMES:
                    if model in raw_data[game][mode]:
                        all_perc_vals.extend(
                            raw_data[game][mode][model]['perception'][level])
                        all_reas_vals.extend(
                            raw_data[game][mode][model]['reasoning'][level])
                perc_means.append(np.mean(all_perc_vals)
                                  if all_perc_vals else 0.0)
                reas_means.append(np.mean(all_reas_vals)
                                  if all_reas_vals else 0.0)
            if any(perc_means) or any(reas_means):
                aggregated[mode][model] = {
                    'perception': perc_means, 'reasoning': reas_means}
    return aggregated


def calculate_game_averages(game_raw_data, models):
    x = np.arange(len(LEVELS))
    explicit_vals = []
    predictive_vals = []
    for level_idx, level in enumerate(LEVELS):
        exp_scores = []
        if 'explicit' in game_raw_data:
            for m in models:
                if m in game_raw_data['explicit']:
                    exp_scores.extend(
                        game_raw_data['explicit'][m]['reasoning'][level])
        pred_scores = []
        if 'predictive' in game_raw_data:
            for m in models:
                if m in game_raw_data['predictive']:
                    pred_scores.extend(
                        game_raw_data['predictive'][m]['reasoning'][level])
        explicit_vals.append(np.mean(exp_scores) if exp_scores else 0)
        predictive_vals.append(np.mean(pred_scores) if pred_scores else 0)
    return explicit_vals, predictive_vals


def get_y_limits(data_values, padding=0.1):
    """Calculate Y-axis limits based on data with minimal padding."""
    all_vals = [v for v in data_values if v > 0]
    if not all_vals:
        return 0, 100
    min_val = min(all_vals)
    max_val = max(all_vals)
    range_val = max_val - min_val
    lower = max(0, min_val - range_val * padding)
    upper = min(100, max_val + range_val * padding)
    # Round to nice numbers
    lower = np.floor(lower / 5) * 5
    upper = np.ceil(upper / 5) * 5
    return lower, upper


# ================= Plotting Functions =================


def plot_bar_chart(mode, data_mode, models, output_name, output_format):
    x = np.arange(len(LEVELS))
    n_models = len(models)
    width = 0.8 / n_models
    fig, ax = plt.subplots(figsize=(14, 8))

    all_vals = []
    for model in models:
        if model in data_mode:
            all_vals.extend(data_mode[model]['reasoning'])
    y_min, y_max = get_y_limits(all_vals)

    for i, model in enumerate(models):
        if model not in data_mode:
            continue
        y_values = data_mode[model]['reasoning']
        offset = (i - n_models/2 + 0.5) * width
        rects = ax.bar(x + offset, y_values, width,
                       label=MODEL_LABELS.get(model, model),
                       color=COLORS.get(model, '#888888'),
                       alpha=0.9, edgecolor='white', linewidth=1.5)
        for rect in rects:
            height = rect.get_height()
            if height > 0:
                ax.annotate(f'{height:.1f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', fontsize=FONT_ANNOTATION, fontweight='bold')
    ax.set_ylabel('Accuracy (Given Verified) %',
                  fontsize=FONT_AXIS_LABEL, fontweight='bold')
    ax.set_xlabel('Task Level', fontsize=FONT_AXIS_LABEL, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f'Level {l}' for l in LEVELS], fontsize=FONT_TICK_LABEL)
    ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
    ax.set_ylim(y_min, y_max + 10)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=min(4, n_models),
              fontsize=FONT_LEGEND, framealpha=0.95, edgecolor='black', fancybox=True)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(output_name, format=output_format, bbox_inches='tight')
    print(f"Generated: {output_name}")
    plt.close()


def plot_average_comparison(data, models, output_name, output_format):
    x = np.arange(len(LEVELS))
    explicit_vals, predictive_vals = [], []
    for level_idx in range(len(LEVELS)):
        exp_scores = [data['explicit'][m]['reasoning'][level_idx]
                      for m in models if m in data['explicit']]
        pred_scores = [data['predictive'][m]['reasoning'][level_idx]
                       for m in models if m in data['predictive']]
        explicit_vals.append(np.mean(exp_scores) if exp_scores else 0)
        predictive_vals.append(np.mean(pred_scores) if pred_scores else 0)

    y_min, y_max = get_y_limits(explicit_vals + predictive_vals)

    fig, ax = plt.subplots(figsize=(14, 8))
    ax.plot(x, explicit_vals, label='Average Explicit Mode', color='#e74c3c', marker='o',
            linewidth=3.5, markersize=12, markerfacecolor='#e74c3c', markeredgecolor='white',
            markeredgewidth=2, alpha=0.9, zorder=10)
    ax.plot(x, predictive_vals, label='Average Predictive Mode', color='#3498db', marker='s',
            linewidth=2.5, markersize=12, markerfacecolor='#3498db', markeredgecolor='white',
            markeredgewidth=2, alpha=0.9, zorder=5)
    ax.fill_between(x, explicit_vals, predictive_vals,
                    where=(np.array(explicit_vals) >
                           np.array(predictive_vals)),
                    interpolate=True, color='#e74c3c', alpha=0.1)
    ax.fill_between(x, explicit_vals, predictive_vals,
                    where=(np.array(explicit_vals) <
                           np.array(predictive_vals)),
                    interpolate=True, color='#3498db', alpha=0.1)

    for i in range(len(x)):
        exp_val = explicit_vals[i]
        pred_val = predictive_vals[i]
        gap = abs(exp_val - pred_val)

        if gap < 5:
            if exp_val >= pred_val:
                exp_offset, pred_offset = (0, 20), (0, -28)
            else:
                exp_offset, pred_offset = (0, -28), (0, 20)
        else:
            if exp_val >= pred_val:
                exp_offset, pred_offset = (0, 16), (0, -24)
            else:
                exp_offset, pred_offset = (0, -24), (0, 16)

        ax.annotate(f'{exp_val:.1f}', (x[i], exp_val), xytext=exp_offset,
                    textcoords='offset points', ha='center', color='#e74c3c',
                    fontsize=FONT_ANNOTATION, fontweight='bold')
        ax.annotate(f'{pred_val:.1f}', (x[i], pred_val), xytext=pred_offset,
                    textcoords='offset points', ha='center', color='#3498db',
                    fontsize=FONT_ANNOTATION, fontweight='bold')

    ax.set_ylabel('Average Accuracy (Given Verified) %',
                  fontsize=FONT_AXIS_LABEL, fontweight='bold')
    ax.yaxis.set_label_coords(-0.08, 0.47)
    ax.set_xlabel('Task Level', fontsize=FONT_AXIS_LABEL, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f'Level {l}' for l in LEVELS], fontsize=FONT_TICK_LABEL)
    ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
    ax.set_ylim(y_min, y_max + 5)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=2,
              fontsize=FONT_LEGEND, framealpha=0.95, edgecolor='black', fancybox=True)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(output_name, format=output_format, bbox_inches='tight')
    print(f"Generated: {output_name}")
    plt.close()


def plot_split_game_average(raw_data, models, output_name, output_format):
    fig, axes = plt.subplots(1, 2, figsize=(24, 8), sharey=True)
    x = np.arange(len(LEVELS))

    all_vals = []
    for game in GAMES:
        if game in raw_data:
            exp, pred = calculate_game_averages(raw_data[game], models)
            all_vals.extend(exp + pred)
    y_min, y_max = get_y_limits(all_vals)

    for idx, game in enumerate(GAMES):
        ax = axes[idx]
        if game not in raw_data:
            ax.set_visible(False)
            continue
        explicit_vals, predictive_vals = calculate_game_averages(
            raw_data[game], models)
        ax.plot(x, explicit_vals, label='Explicit Mode', color='#e74c3c', marker='o',
                linewidth=3.5, markersize=12, markerfacecolor='#e74c3c', markeredgecolor='white',
                markeredgewidth=2, alpha=0.9, zorder=10)
        ax.plot(x, predictive_vals, label='Predictive Mode', color='#3498db', marker='s',
                linewidth=2.5, markersize=12, markerfacecolor='#3498db', markeredgecolor='white',
                markeredgewidth=2, alpha=0.9, zorder=5)
        ax.fill_between(x, explicit_vals, predictive_vals,
                        where=(np.array(explicit_vals) >=
                               np.array(predictive_vals)),
                        interpolate=True, color='#e74c3c', alpha=0.1)
        ax.fill_between(x, explicit_vals, predictive_vals,
                        where=(np.array(explicit_vals) <
                               np.array(predictive_vals)),
                        interpolate=True, color='#3498db', alpha=0.1)
        for i in range(len(x)):
            if explicit_vals[i] > 0:
                ax.annotate(f'{explicit_vals[i]:.0f}', (x[i], explicit_vals[i]), xytext=(0, 10),
                            textcoords='offset points', ha='center', color='#e74c3c',
                            fontsize=FONT_ANNOTATION_SMALL, fontweight='bold')
            if predictive_vals[i] > 0:
                ax.annotate(f'{predictive_vals[i]:.0f}', (x[i], predictive_vals[i]), xytext=(0, -16),
                            textcoords='offset points', ha='center', color='#3498db',
                            fontsize=FONT_ANNOTATION_SMALL, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(LEVEL_LABELS, fontsize=FONT_TICK_LABEL)
        ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_xlabel('Task Level', fontsize=FONT_AXIS_LABEL,
                      fontweight='bold')
        ax.set_ylim(y_min, y_max + 5)
    axes[0].set_ylabel('Average Accuracy (Given Verified) %',
                       fontsize=FONT_AXIS_LABEL, fontweight='bold')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.02),
               ncol=2, fontsize=FONT_LEGEND, framealpha=0.95, edgecolor='black', fancybox=True)
    plt.tight_layout()
    plt.subplots_adjust(top=0.85, bottom=0.15)
    plt.savefig(output_name, format=output_format, bbox_inches='tight')
    print(f"Generated: {output_name}")
    plt.close()


def draw_trend_on_axis(ax, mode, data_mode, models, show_ylabel=False, show_xlabel=True, y_limits=None):
    x = np.arange(len(LEVELS))

    if show_ylabel:
        ax.set_ylabel('Accuracy (Given Verified) %',
                      fontsize=FONT_AXIS_LABEL, fontweight='bold')
    if show_xlabel:
        ax.set_xlabel('Task Level', fontsize=FONT_AXIS_LABEL,
                      fontweight='bold')

    for model in models:
        if model not in data_mode:
            continue
        y_values = data_mode[model]['reasoning']
        linewidth = 3.5 if model == "qwen235b" else 2.5
        zorder = 10 if model == "qwen235b" else 5
        ax.plot(x, y_values, label=MODEL_LABELS.get(model, model),
                color=COLORS.get(model, '#888888'), marker=MARKERS.get(model, 'o'),
                linewidth=linewidth, markersize=12, markerfacecolor=COLORS.get(model, '#888888'),
                markeredgecolor='white', markeredgewidth=2, alpha=0.9, zorder=zorder)

    # Increase offsets to avoid labels being covered by markers
    y_offsets = {"qwen8b": -25, "qwen30b": -30, "qwen235b": 23, "gpt5.2": -35}

    for model in models:
        if model not in data_mode:
            continue
        y_values = data_mode[model]['reasoning']
        offset = y_offsets.get(model, 18)
        for i in range(len(x)):
            if y_values[i] > 0:
                ax.annotate(f'{y_values[i]:.0f}', (x[i], y_values[i]),
                            xytext=(0, offset), textcoords='offset points',
                            ha='center', color=COLORS.get(model, '#888888'),
                            fontsize=FONT_ANNOTATION, fontweight='bold')
    if show_ylabel:
        ax.set_ylabel('Accuracy (Given Verified) %',
                      fontsize=FONT_AXIS_LABEL, fontweight='bold')
    ax.set_title(f'{mode.capitalize()} Mode',
                 fontsize=FONT_TITLE, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(
        [f'Level {l}' for l in LEVELS], fontsize=FONT_TICK_LABEL)
    ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
    if y_limits:
        ax.set_ylim(y_limits)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_axisbelow(True)


def plot_combined_trend_lines(data, models, output_name, output_format):
    # Collect all values to determine shared Y limits
    all_vals = []
    for mode in MODES:
        for model in models:
            if model in data[mode]:
                all_vals.extend(data[mode][model]['reasoning'])
    y_min, y_max = get_y_limits(all_vals)
    y_limits = (y_min, y_max + 5)

    fig, axes = plt.subplots(1, 2, figsize=(24, 8), sharey=True)
    draw_trend_on_axis(axes[0], "explicit", data["explicit"],
                       models, show_ylabel=True, y_limits=y_limits)
    draw_trend_on_axis(axes[1], "predictive", data["predictive"],
                       models, show_ylabel=False, y_limits=y_limits)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.02),
               ncol=min(4, len(models)), fontsize=FONT_LEGEND, framealpha=0.95, edgecolor='black', fancybox=True)
    plt.tight_layout()
    plt.subplots_adjust(top=0.84, bottom=0.14)
    plt.savefig(output_name, format=output_format, bbox_inches='tight')
    print(f"Generated: {output_name}")
    plt.close()


def plot_qwen_only_trend(data, models, output_name, output_format, detailed_data=None):
    """
    Plot Qwen series scaling trend using INTERSECTION of verified cases.
    Only counts cases where ALL Qwen models passed verification.
    """
    qwen_models = [m for m in models if 'qwen' in m.lower()]
    qwen_models.sort(key=lambda x: int(
        re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)

    if not qwen_models:
        print("⚠️ No Qwen models found; skipping scaling trend analysis")
        return

    print(
        f"📊 Qwen scaling chart (intersection-based) includes models: {qwen_models}")

    # If detailed_data not provided, fall back to original behavior
    if detailed_data is None:
        print("⚠️ No detailed data provided, using original accuracy (not intersection)")
        # Collect all values to determine shared Y limits
        all_vals = []
        for mode in MODES:
            for model in qwen_models:
                if model in data[mode]:
                    all_vals.extend(data[mode][model]['reasoning'])
        y_min, y_max = get_y_limits(all_vals)
        y_limits = (y_min, y_max + 5)

        fig, axes = plt.subplots(1, 2, figsize=(24, 8), sharey=True)
        draw_trend_on_axis(axes[0], "explicit", data["explicit"],
                           qwen_models, show_ylabel=True, show_xlabel=False, y_limits=y_limits)
        draw_trend_on_axis(axes[1], "predictive", data["predictive"],
                           qwen_models, show_ylabel=False, show_xlabel=False, y_limits=y_limits)
    else:
        # Calculate intersection accuracy
        intersection_acc = calculate_qwen_intersection_accuracy(
            detailed_data, qwen_models)

        # Collect all values for Y limits
        all_vals = []
        for mode in MODES:
            for model in qwen_models:
                for level in LEVELS:
                    if level in intersection_acc[mode][model]:
                        all_vals.append(intersection_acc[mode][model][level])
        y_min, y_max = get_y_limits(all_vals)
        y_limits = (y_min, y_max + 5)

        fig, axes = plt.subplots(1, 2, figsize=(24, 8), sharey=True)

        for ax_idx, mode in enumerate(MODES):
            ax = axes[ax_idx]
            x = np.arange(len(LEVELS))

            for model in qwen_models:
                y_values = [intersection_acc[mode]
                            [model].get(l, 0) for l in LEVELS]
                linewidth = 3.5 if model == "qwen235b" else 2.5
                zorder = 10 if model == "qwen235b" else 5
                ax.plot(x, y_values, label=MODEL_LABELS.get(model, model),
                        color=COLORS.get(model, '#888888'), marker=MARKERS.get(model, 'o'),
                        linewidth=linewidth, markersize=12, markerfacecolor=COLORS.get(model, '#888888'),
                        markeredgecolor='white', markeredgewidth=2, alpha=0.9, zorder=zorder)

            # Annotations
            y_offsets = {"qwen8b": -25, "qwen30b": -30, "qwen235b": 23}
            for model in qwen_models:
                y_values = [intersection_acc[mode]
                            [model].get(l, 0) for l in LEVELS]
                offset = y_offsets.get(model, 18)
                for i in range(len(x)):
                    if y_values[i] > 0:
                        ax.annotate(f'{y_values[i]:.0f}', (x[i], y_values[i]),
                                    xytext=(0, offset), textcoords='offset points',
                                    ha='center', color=COLORS.get(model, '#888888'),
                                    fontsize=FONT_ANNOTATION, fontweight='bold')

            ax.set_title(f'{mode.capitalize()} Mode',
                         fontsize=FONT_TITLE, fontweight='bold', pad=15)
            ax.set_xticks(x)
            ax.set_xticklabels(
                [f'Level {l}' for l in LEVELS], fontsize=FONT_TICK_LABEL)
            ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
            if y_limits:
                ax.set_ylim(y_limits)
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
            ax.set_axisbelow(True)

        axes[0].set_ylabel('Accuracy on Intersection Set (\\%)',
                           fontsize=FONT_AXIS_LABEL, fontweight='bold')

    fig.text(0.5, SHARED_XLABEL_Y, 'Task Level', ha='center',
             fontsize=FONT_AXIS_LABEL, fontweight='bold')

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, SHARED_LEGEND_Y),
               ncol=len(qwen_models), fontsize=FONT_LEGEND, framealpha=0.95, edgecolor='black', fancybox=True)

    plt.tight_layout()
    plt.subplots_adjust(top=0.84, bottom=0.14)
    plt.savefig(output_name, format=output_format, bbox_inches='tight')
    print(f"Generated: {output_name}")
    plt.close()


def plot_dissociation_grid(data, mode, models, output_name, output_format):
    n_models = len(models)
    fig, axes = plt.subplots(1, n_models, figsize=(6*n_models, 7), sharey=True)
    if n_models == 1:
        axes = [axes]

    x = np.arange(len(LEVELS))

    # Collect all values to determine shared Y limits
    all_vals = []
    for model in models:
        if model in data[mode]:
            all_vals.extend(data[mode][model]['perception'])
            all_vals.extend(data[mode][model]['reasoning'])
    y_min, y_max = get_y_limits(all_vals)

    for idx, model in enumerate(models):
        ax = axes[idx]
        if model not in data[mode]:
            ax.set_visible(False)
            continue

        perc_scores = data[mode][model]['perception']
        reas_scores = data[mode][model]['reasoning']

        ax.plot(x, perc_scores, marker='o', color=PERCEPTION_COLOR,
                linewidth=2.5, markersize=12,
                markerfacecolor=PERCEPTION_COLOR, markeredgecolor='white', markeredgewidth=2,
                label='Perception (Verification Rate)', alpha=0.9, zorder=5)
        ax.plot(x, reas_scores, marker='s', color=REASONING_COLOR,
                linewidth=2.5, markersize=12,
                markerfacecolor=REASONING_COLOR, markeredgecolor='white', markeredgewidth=2,
                label='Reasoning (Acc Given Verified)', alpha=0.9, zorder=5)

        ax.fill_between(x, perc_scores, reas_scores, color='gray', alpha=0.15,
                        label='_nolegend_')

        bbox_props = dict(boxstyle="round,pad=0.2",
                          fc="white", ec="none", alpha=0.75)

        for i in range(len(LEVELS)):
            p_val = perc_scores[i]
            r_val = reas_scores[i]
            if p_val <= 0 and r_val <= 0:
                continue

            if p_val >= r_val:
                top_val, top_col = p_val, PERCEPTION_COLOR
                bot_val, bot_col = r_val, REASONING_COLOR
            else:
                top_val, top_col = r_val, REASONING_COLOR
                bot_val, bot_col = p_val, PERCEPTION_COLOR

            gap = top_val - bot_val
            if gap < 2:
                top_offset, bot_offset = (0, 14), (0, -22)
            elif gap < 10:
                top_offset, bot_offset = (0, 10), (0, -18)
            else:
                top_offset, bot_offset = (0, 6), (0, -16)

            if top_val > 0:
                ax.annotate(f'{top_val:.0f}', (x[i], top_val), xytext=top_offset,
                            textcoords='offset points', ha='center', va='bottom',
                            fontsize=FONT_ANNOTATION_SMALL, fontweight='bold', color=top_col, bbox=bbox_props)

            if bot_val > 0:
                ax.annotate(f'{bot_val:.0f}', (x[i], bot_val), xytext=bot_offset,
                            textcoords='offset points', ha='center', va='top',
                            fontsize=FONT_ANNOTATION_SMALL, fontweight='bold', color=bot_col, bbox=bbox_props)

        ax.set_title(f"{MODEL_LABELS.get(model, model)}",
                     fontsize=FONT_TITLE, fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(LEVEL_LABELS, fontsize=FONT_TICK_LABEL)
        ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
        # ax.set_xlabel('Task Level', fontsize=FONT_AXIS_LABEL,
        #               fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)
        ax.set_ylim(y_min, y_max + 5)

    axes[0].set_ylabel('Performance (%)',
                       fontsize=FONT_AXIS_LABEL, fontweight='bold')

    fig.text(0.5, SHARED_XLABEL_Y, 'Task Level', ha='center',
             fontsize=FONT_AXIS_LABEL, fontweight='bold')
    handles, labels = axes[0].get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    fig.legend(by_label.values(), by_label.keys(), loc='upper center', bbox_to_anchor=(0.5, SHARED_LEGEND_Y),
               ncol=3, fontsize=FONT_LEGEND, framealpha=0.95, edgecolor='black', fancybox=True)

    plt.tight_layout()
    plt.subplots_adjust(top=0.84, bottom=0.14)
    plt.savefig(output_name, format=output_format, bbox_inches='tight')
    print(f"Generated: {output_name}")
    plt.close()

# ================= Main Execution =================


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Level 1-6 analysis plotting')
    default_path = os.path.join(os.path.dirname(__file__), '..', 'rule complexity ladder')
    parser.add_argument('path', nargs='?', default=default_path,
                        help='Root directory path (default: <script_dir>/../rule complexity ladder)')
    parser.add_argument('--models', nargs='+',
                        default=None, help='Models to plot')
    parser.add_argument('--output-prefix', default='',
                        help='Output filename prefix')
    parser.add_argument('--format', default='pdf', choices=['pdf', 'eps', 'png'],
                        help='Output format for figures')
    args = parser.parse_args()

    print(f"🔍 Scanning directory: {os.path.abspath(args.path)}")

    raw_data = scan_and_load_data(args.path)
    combined_data = merge_all_games(raw_data)

    all_models = set()
    for g in GAMES:
        for m in MODES:
            all_models.update(raw_data[g][m].keys())

    if not all_models:
        print("❌ No data found")
        return

    models = args.models if args.models else sorted(all_models)
    print(f"✅ Found models: {models}")
    prefix = args.output_prefix
    output_format = args.format

    for mode in MODES:
        if combined_data[mode]:
            plot_bar_chart(
                mode, combined_data[mode], models,
                f"{prefix}1_{mode.capitalize()}_Mode_Bar_Comparison.{output_format}",
                output_format
            )

    plot_average_comparison(
        combined_data, models,
        f"{prefix}explicit_vs_predictive_average.{output_format}",
        output_format
    )
    plot_combined_trend_lines(
        combined_data, models,
        f"{prefix}3_Combined_Trend_Lines.{output_format}",
        output_format
    )

    for mode in MODES:
        if combined_data[mode]:
            output_name = (
                f"{prefix}perception_reasoning_dissociation.{output_format}"
                if mode == "predictive"
                else f"{prefix}4_Dissociation_{mode.capitalize()}.{output_format}"
            )
            plot_dissociation_grid(combined_data, mode,
                                   models, output_name, output_format)

    print("🎨 Generating per-game comparison chart (Figure 5)...")
    plot_split_game_average(
        raw_data, models, f"{prefix}5_Game_Split_Trend.{output_format}", output_format)

    print("🎨 Loading detailed data for Qwen intersection analysis...")
    detailed_data = scan_and_load_detailed_data(args.path)

    print("🎨 Generating Qwen scaling analysis chart (intersection-based)...")
    plot_qwen_only_trend(
        combined_data, models,
        f"{prefix}scaling_trend_analysis.{output_format}",
        output_format,
        detailed_data=detailed_data
    )

    print("\n✅ All charts generated!")


if __name__ == "__main__":
    main()
