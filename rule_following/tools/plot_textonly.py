#!/usr/bin/env python3
"""
Text-Only vs Image-Based: matched-sample comparison per game.
Only samples that passed verification in the original image-based test.
"""

import os
import json
import re
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

# ============ LaTeX rendering ============
mpl.rcParams['text.usetex'] = True
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times']
mpl.rcParams['text.latex.preamble'] = r'\usepackage{times}'

# ============ Configuration ============
BASE = os.path.join(os.path.dirname(__file__), '..')
TEXTONLY_DIR = os.path.join(BASE, 'textonly')
ORIGINAL_DIR = os.path.join(BASE, 'rule complexity ladder')

GAMES = ["chess", "xiangqi"]
MODES = ["explicit", "predictive"]
LEVELS = [3, 4, 5, 6]
LEVEL_LABELS = ['L3', 'L4', 'L5', 'L6']

MODEL_KEYS = ["gpt5.2", "qwen235b", "qwen30b", "qwen8b"]
MODEL_LABELS = {
    "qwen8b": "Qwen3-VL 8B",
    "qwen30b": "Qwen3-VL 30B",
    "qwen235b": "Qwen3-VL 235B",
    "gpt5.2": "GPT-5.2",
}
GAME_LABELS = {"chess": "Chess", "xiangqi": "Xiangqi"}

FONT_AXIS_LABEL = 22
FONT_TICK_LABEL = 24
FONT_TITLE = 28
FONT_LEGEND = 22
FONT_ANNOTATION = 16
SHARED_LEGEND_Y = 0.01
SHARED_XLABEL_Y = 0.02

OUTPUT_FORMAT = 'pdf'


# ============ Helpers ============
def extract_model_key(folder_name):
    folder_lower = folder_name.lower()
    for key in MODEL_KEYS:
        if key.lower() in folder_lower:
            return key
    return None


def extract_level_from_folder(name):
    match = re.search(r'level_(\d+)', name.lower())
    if match:
        return int(match.group(1))
    return None


def find_json_in_folder(folder_path):
    if not os.path.isdir(folder_path):
        return None
    for f in os.listdir(folder_path):
        if f.endswith('.json') and 'level_' in f and 'results' in f:
            return os.path.join(folder_path, f)
    for f in os.listdir(folder_path):
        if f.endswith('.json'):
            return os.path.join(folder_path, f)
    return None


def load_detailed_results(filepath):
    if not filepath or not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        results = {}
        for case in data.get('detailed_results', []):
            cid = case.get('case_id')
            if cid:
                results[cid] = {
                    'correct': case.get('correct', False),
                    'verified': case.get('verification_passed', False),
                }
        return results
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return {}


def scan_directory(base_dir, levels=LEVELS):
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
                for entry in os.listdir(model_path):
                    entry_path = os.path.join(model_path, entry)
                    if os.path.isdir(entry_path):
                        level = extract_level_from_folder(entry)
                        if level is None or level not in levels:
                            continue
                        json_file = find_json_in_folder(entry_path)
                        if json_file:
                            detailed = load_detailed_results(json_file)
                            if detailed:
                                data[game][mode][model_key][level] = detailed
                    elif entry.endswith('.json') and 'level_' in entry:
                        level = extract_level_from_folder(entry)
                        if level is None or level not in levels:
                            continue
                        detailed = load_detailed_results(entry_path)
                        if detailed:
                            data[game][mode][model_key][level] = detailed
    return data


def get_y_limits(data_values, padding=0.1):
    all_vals = [v for v in data_values if v > 0]
    if not all_vals:
        return 0, 100
    min_val = min(all_vals)
    max_val = max(all_vals)
    range_val = max_val - min_val
    lower = max(0, min_val - range_val * padding)
    upper = min(100, max_val + range_val * padding)
    lower = np.floor(lower / 5) * 5
    upper = np.ceil(upper / 5) * 5
    return lower, upper


# ============ Plot ============
def plot_matched_per_game(textonly_data, original_data, output_dir):
    """
    Matched-sample comparison: Text-Only vs Image-Based per game.
    Only samples that passed verification in original image-based test.
    Layout: 2 rows (models) x 4 cols (game x mode).
    """
    combos = [(g, m) for g in GAMES for m in MODES]
    n_cols = len(combos)
    n_rows = len(MODEL_KEYS)

    fig, axes = plt.subplots(n_rows, n_cols,
                             figsize=(6 * n_cols, 7 * n_rows), sharey=True)
    x = np.arange(len(LEVELS))
    width = 0.35
    textonly_color = "#3498db"
    image_color = "#e74c3c"

    all_vals = []

    for row, model in enumerate(MODEL_KEYS):
        for col, (game, mode) in enumerate(combos):
            ax = axes[row][col]

            textonly_accs = []
            image_accs = []
            sample_counts = []

            for level in LEVELS:
                orig_cases = {}
                text_cases = {}

                if (model in original_data[game][mode] and
                        level in original_data[game][mode][model]):
                    orig_cases = original_data[game][mode][model][level]

                if (model in textonly_data[game][mode] and
                        level in textonly_data[game][mode][model]):
                    text_cases = textonly_data[game][mode][model][level]

                matched_text_correct = 0
                matched_img_correct = 0
                matched_total = 0

                for cid, odata in orig_cases.items():
                    if odata['verified'] and cid in text_cases:
                        matched_total += 1
                        if text_cases[cid]['correct']:
                            matched_text_correct += 1
                        if odata['correct']:
                            matched_img_correct += 1

                if matched_total > 0:
                    textonly_accs.append(
                        matched_text_correct / matched_total * 100)
                    image_accs.append(matched_img_correct /
                                      matched_total * 100)
                else:
                    textonly_accs.append(0)
                    image_accs.append(0)
                sample_counts.append(matched_total)

            all_vals.extend(textonly_accs + image_accs)

            rects1 = ax.bar(x - width / 2, textonly_accs, width,
                            label='Text-Only', color=textonly_color,
                            alpha=0.9, edgecolor='white', linewidth=1.5)
            rects2 = ax.bar(x + width / 2, image_accs, width,
                            label='Image-Based', color=image_color,
                            alpha=0.9, edgecolor='white', linewidth=1.5)

            for rect in rects1:
                h = rect.get_height()
                if h > 0:
                    ax.annotate(f'{h:.1f}',
                                xy=(rect.get_x() + rect.get_width() / 2, h),
                                xytext=(0, 3), textcoords="offset points",
                                ha='center', va='bottom',
                                fontsize=FONT_ANNOTATION - 2,
                                fontweight='bold', color=textonly_color)
            for rect in rects2:
                h = rect.get_height()
                if h > 0:
                    ax.annotate(f'{h:.1f}',
                                xy=(rect.get_x() + rect.get_width() / 2, h),
                                xytext=(0, 3), textcoords="offset points",
                                ha='center', va='bottom',
                                fontsize=FONT_ANNOTATION - 2,
                                fontweight='bold', color=image_color)

            for i, n in enumerate(sample_counts):
                ax.annotate(f'n={n}', (x[i], 0), xytext=(0, -18),
                            textcoords='offset points', ha='center',
                            fontsize=FONT_ANNOTATION - 4, color='gray')

            ax.set_title(
                f'{MODEL_LABELS.get(model, model)}\n'
                f'{GAME_LABELS[game]} --- {mode.capitalize()}',
                fontsize=FONT_TITLE - 4, fontweight='bold', pad=15)
            ax.set_xticks(x)
            ax.set_xticklabels(LEVEL_LABELS, fontsize=FONT_TICK_LABEL)
            ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
            ax.set_axisbelow(True)

    y_min, y_max = get_y_limits(all_vals)
    for ax_row in axes:
        for ax in ax_row:
            ax.set_ylim(y_min, y_max + 12)

    for row in range(n_rows):
        axes[row][0].set_ylabel('Accuracy on Matched Samples (\\%)',
                                fontsize=FONT_AXIS_LABEL, fontweight='bold')

    fig.text(0.5, SHARED_XLABEL_Y, 'Task Level', ha='center',
             fontsize=FONT_AXIS_LABEL, fontweight='bold')

    handles = [
        plt.Rectangle((0, 0), 1, 1, fc=textonly_color, alpha=0.9),
        plt.Rectangle((0, 0), 1, 1, fc=image_color, alpha=0.9),
    ]
    fig.legend(handles, ['Text-Only (Baseline)', 'Image-Based (Verified)'],
               loc='upper center', bbox_to_anchor=(0.5, SHARED_LEGEND_Y),
               ncol=2, fontsize=FONT_LEGEND,
               framealpha=0.95, edgecolor='black', fancybox=True)

    plt.tight_layout()
    plt.subplots_adjust(top=0.88, bottom=0.08, hspace=0.40)
    out = os.path.join(output_dir,
                       f'TextOnly_vs_Image_Matched_PerGame.{OUTPUT_FORMAT}')
    plt.savefig(out, format=OUTPUT_FORMAT, bbox_inches='tight')
    print(f"Generated: {out}")
    plt.close()


# ============ Plot: Per-game trend – 1 row per model, cols = game x mode ============
def plot_matched_trend_per_game(textonly_data, original_data, output_dir):
    textonly_color = "#3498db"
    image_color = "#e74c3c"
    combos = [(g, m) for g in GAMES for m in MODES]
    n_cols = len(combos)
    n_rows = len(MODEL_KEYS)
    x = np.arange(len(LEVELS))

    fig, axes = plt.subplots(n_rows, n_cols,
                             figsize=(6 * n_cols, 7 * n_rows), sharey=True)
    if n_rows == 1:
        axes = [axes]
    all_vals = []

    for row, model in enumerate(MODEL_KEYS):
        for col, (game, mode) in enumerate(combos):
            ax = axes[row][col]

            textonly_accs = []
            image_accs = []

            for level in LEVELS:
                orig_cases = {}
                text_cases = {}
                if (model in original_data[game][mode] and
                        level in original_data[game][mode][model]):
                    orig_cases = original_data[game][mode][model][level]
                if (model in textonly_data[game][mode] and
                        level in textonly_data[game][mode][model]):
                    text_cases = textonly_data[game][mode][model][level]

                mt, tc, ic = 0, 0, 0
                for cid, od in orig_cases.items():
                    if od['verified'] and cid in text_cases:
                        mt += 1
                        if text_cases[cid]['correct']:
                            tc += 1
                        if od['correct']:
                            ic += 1
                if mt > 0:
                    textonly_accs.append(tc / mt * 100)
                    image_accs.append(ic / mt * 100)
                else:
                    textonly_accs.append(0)
                    image_accs.append(0)

            all_vals.extend(textonly_accs + image_accs)

            ax.plot(x, textonly_accs, label='Text-Only',
                    color=textonly_color, marker='o',
                    linewidth=3.5, markersize=14,
                    markerfacecolor=textonly_color,
                    markeredgecolor='white', markeredgewidth=2,
                    linestyle='-', alpha=0.9, zorder=10)
            ax.plot(x, image_accs, label='Image-Based (Verified)',
                    color=image_color, marker='s',
                    linewidth=3.5, markersize=14,
                    markerfacecolor=image_color,
                    markeredgecolor='white', markeredgewidth=2,
                    linestyle='--', alpha=0.9, zorder=5)

            ax.fill_between(x, textonly_accs, image_accs,
                            color='gray', alpha=0.1)

            for i in range(len(x)):
                tv, iv = textonly_accs[i], image_accs[i]
                gap = abs(tv - iv)
                if gap < 3:
                    t_off, i_off = (0, 16), (0, -22)
                elif tv >= iv:
                    t_off, i_off = (0, 12), (0, -20)
                else:
                    t_off, i_off = (0, -20), (0, 12)
                if tv > 0:
                    ax.annotate(f'{tv:.1f}', (x[i], tv),
                                xytext=t_off, textcoords='offset points',
                                ha='center', fontsize=FONT_ANNOTATION - 2,
                                fontweight='bold', color=textonly_color)
                if iv > 0:
                    ax.annotate(f'{iv:.1f}', (x[i], iv),
                                xytext=i_off, textcoords='offset points',
                                ha='center', fontsize=FONT_ANNOTATION - 2,
                                fontweight='bold', color=image_color)

            ax.set_title(
                f'{MODEL_LABELS.get(model, model)}\n'
                f'{GAME_LABELS[game]} --- {mode.capitalize()}',
                fontsize=FONT_TITLE - 4, fontweight='bold', pad=15)
            ax.set_xticks(x)
            ax.set_xticklabels(LEVEL_LABELS, fontsize=FONT_TICK_LABEL)
            ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
            ax.set_axisbelow(True)

    y_min, y_max = get_y_limits(all_vals)
    for ax_row in axes:
        for ax in ax_row:
            ax.set_ylim(y_min, y_max + 8)
    for row in range(n_rows):
        axes[row][0].set_ylabel('Accuracy on Matched Samples (\\%)',
                                fontsize=FONT_AXIS_LABEL, fontweight='bold')
    fig.text(0.5, SHARED_XLABEL_Y, 'Task Level', ha='center',
             fontsize=FONT_AXIS_LABEL, fontweight='bold')
    handles = [
        plt.Line2D([0], [0], color=textonly_color, marker='o', linewidth=3.5,
                   markersize=14, markerfacecolor=textonly_color,
                   markeredgecolor='white', markeredgewidth=2),
        plt.Line2D([0], [0], color=image_color, marker='s', linewidth=3.5,
                   markersize=14, markerfacecolor=image_color,
                   markeredgecolor='white', markeredgewidth=2, linestyle='--'),
    ]
    fig.legend(handles, ['Text-Only (Baseline)', 'Image-Based (Verified)'],
               loc='upper center', bbox_to_anchor=(0.5, SHARED_LEGEND_Y),
               ncol=2, fontsize=FONT_LEGEND,
               framealpha=0.95, edgecolor='black', fancybox=True)
    plt.tight_layout()
    plt.subplots_adjust(top=0.88, bottom=0.08, hspace=0.40)
    out = os.path.join(output_dir,
                       f'TextOnly_vs_Image_Matched_PerGame_Trend.{OUTPUT_FORMAT}')
    plt.savefig(out, format=OUTPUT_FORMAT, bbox_inches='tight')
    print(f"Generated: {out}")
    plt.close()


# ============ Plot: Bar chart – 1 row, cols=[model1_exp, model1_pred, model2_exp, ...] ============
def plot_matched_bar_per_model(textonly_data, original_data, output_dir):
    textonly_color = "#3498db"
    image_color = "#e74c3c"
    x = np.arange(len(LEVELS))
    width = 0.35
    combos = [(m, mode) for m in MODEL_KEYS for mode in MODES]
    n_cols = len(combos)

    fig, axes = plt.subplots(1, n_cols, figsize=(6 * n_cols, 8), sharey=True)
    if n_cols == 1:
        axes = [axes]
    all_vals = []

    for idx, (model, mode) in enumerate(combos):
        ax = axes[idx]
        t_acc, i_acc = _compute_matched_trend(
            textonly_data, original_data, model, mode)
        all_vals.extend(t_acc + i_acc)

        rects1 = ax.bar(x - width / 2, t_acc, width,
                        label='Text-Only', color=textonly_color,
                        alpha=0.9, edgecolor='white', linewidth=1.5)
        rects2 = ax.bar(x + width / 2, i_acc, width,
                        label='Image-Based (Verified)',
                        color=image_color,
                        alpha=0.9, edgecolor='white', linewidth=1.5)

        for rect in rects1:
            h = rect.get_height()
            if h > 0:
                ax.annotate(f'{h:.1f}',
                            xy=(rect.get_x() + rect.get_width() / 2, h),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=FONT_ANNOTATION,
                            fontweight='bold', color=textonly_color)
        for rect in rects2:
            h = rect.get_height()
            if h > 0:
                ax.annotate(f'{h:.1f}',
                            xy=(rect.get_x() + rect.get_width() / 2, h),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=FONT_ANNOTATION,
                            fontweight='bold', color=image_color)

        ax.set_title(
            f'{MODEL_LABELS[model]}\n{mode.capitalize()} Mode',
            fontsize=FONT_TITLE - 4, fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(LEVEL_LABELS, fontsize=FONT_TICK_LABEL)
        ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)

    y_min, y_max = get_y_limits(all_vals)
    for ax in axes:
        ax.set_ylim(y_min, y_max + 10)

    axes[0].set_ylabel('Accuracy on Matched Samples (\\%)',
                       fontsize=FONT_AXIS_LABEL, fontweight='bold')
    fig.text(0.5, SHARED_XLABEL_Y, 'Task Level', ha='center',
             fontsize=FONT_AXIS_LABEL, fontweight='bold')

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center',
               bbox_to_anchor=(0.5, SHARED_LEGEND_Y),
               ncol=2, fontsize=FONT_LEGEND,
               framealpha=0.95, edgecolor='black', fancybox=True)

    plt.tight_layout()
    plt.subplots_adjust(top=0.84, bottom=0.14)
    out = os.path.join(
        output_dir,
        f'TextOnly_vs_Image_Matched_Bar.{OUTPUT_FORMAT}')
    plt.savefig(out, format=OUTPUT_FORMAT, bbox_inches='tight')
    print(f"Generated: {out}")
    plt.close()


# ============ Plot: Per-model trend (game-averaged) ============
def _compute_matched_trend(textonly_data, original_data, model, mode):
    """Return (text_accs, img_accs) per level, averaged across games."""
    text_accs = []
    img_accs = []
    for level in LEVELS:
        g_text, g_img = [], []
        for game in GAMES:
            orig_cases = {}
            text_cases = {}
            if (model in original_data[game][mode] and
                    level in original_data[game][mode][model]):
                orig_cases = original_data[game][mode][model][level]
            if (model in textonly_data[game][mode] and
                    level in textonly_data[game][mode][model]):
                text_cases = textonly_data[game][mode][model][level]
            mt, tc, ic = 0, 0, 0
            for cid, od in orig_cases.items():
                if od['verified'] and cid in text_cases:
                    mt += 1
                    if text_cases[cid]['correct']:
                        tc += 1
                    if od['correct']:
                        ic += 1
            if mt > 0:
                g_text.append(tc / mt * 100)
                g_img.append(ic / mt * 100)
        text_accs.append(np.mean(g_text) if g_text else 0)
        img_accs.append(np.mean(g_img) if g_img else 0)
    return text_accs, img_accs


def plot_matched_trend(textonly_data, original_data, output_dir):
    textonly_color = "#3498db"
    image_color = "#e74c3c"
    x = np.arange(len(LEVELS))
    combos = [(m, mode) for m in MODEL_KEYS for mode in MODES]
    n_cols = len(combos)

    fig, axes = plt.subplots(1, n_cols, figsize=(6 * n_cols, 8), sharey=True)
    if n_cols == 1:
        axes = [axes]
    all_vals = []

    for idx, (model, mode) in enumerate(combos):
        ax = axes[idx]
        t_acc, i_acc = _compute_matched_trend(
            textonly_data, original_data, model, mode)
        all_vals.extend(t_acc + i_acc)

        ax.plot(x, t_acc, label='Text-Only',
                color=textonly_color, marker='o',
                linewidth=3.5, markersize=14,
                markerfacecolor=textonly_color,
                markeredgecolor='white', markeredgewidth=2,
                linestyle='-', alpha=0.9, zorder=10)
        ax.plot(x, i_acc, label='Image-Based (Verified)',
                color=image_color, marker='s',
                linewidth=3.5, markersize=14,
                markerfacecolor=image_color,
                markeredgecolor='white', markeredgewidth=2,
                linestyle='--', alpha=0.9, zorder=5)

        ax.fill_between(x, t_acc, i_acc, color='gray', alpha=0.1)

        for i in range(len(x)):
            tv, iv = t_acc[i], i_acc[i]
            gap = abs(tv - iv)
            if gap < 3:
                t_off, i_off = (0, 16), (0, -22)
            else:
                if tv >= iv:
                    t_off, i_off = (0, 12), (0, -20)
                else:
                    t_off, i_off = (0, -20), (0, 12)
            if tv > 0:
                ax.annotate(f'{tv:.1f}', (x[i], tv),
                            xytext=t_off, textcoords='offset points',
                            ha='center', fontsize=FONT_ANNOTATION,
                            fontweight='bold', color=textonly_color)
            if iv > 0:
                ax.annotate(f'{iv:.1f}', (x[i], iv),
                            xytext=i_off, textcoords='offset points',
                            ha='center', fontsize=FONT_ANNOTATION,
                            fontweight='bold', color=image_color)

        ax.set_title(
            f'{MODEL_LABELS[model]}\n{mode.capitalize()} Mode',
            fontsize=FONT_TITLE - 4, fontweight='bold', pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(LEVEL_LABELS, fontsize=FONT_TICK_LABEL)
        ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)

    y_min, y_max = get_y_limits(all_vals)
    for ax in axes:
        ax.set_ylim(y_min, y_max + 8)

    axes[0].set_ylabel('Accuracy on Matched Samples (\\%)',
                       fontsize=FONT_AXIS_LABEL, fontweight='bold')
    fig.text(0.5, SHARED_XLABEL_Y, 'Task Level', ha='center',
             fontsize=FONT_AXIS_LABEL, fontweight='bold')

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center',
               bbox_to_anchor=(0.5, SHARED_LEGEND_Y),
               ncol=2, fontsize=FONT_LEGEND,
               framealpha=0.95, edgecolor='black', fancybox=True)

    plt.tight_layout()
    plt.subplots_adjust(top=0.84, bottom=0.14)
    out = os.path.join(
        output_dir,
        f'TextOnly_vs_Image_Matched_Trend.{OUTPUT_FORMAT}')
    plt.savefig(out, format=OUTPUT_FORMAT, bbox_inches='tight')
    print(f"Generated: {out}")
    plt.close()


# ============ Main ============
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--format', default='pdf',
                        choices=['pdf', 'eps', 'png'])
    args = parser.parse_args()

    global OUTPUT_FORMAT
    OUTPUT_FORMAT = args.format

    output_dir = os.path.dirname(os.path.abspath(__file__))

    print("Scanning text-only data...")
    textonly_data = scan_directory(os.path.abspath(TEXTONLY_DIR), LEVELS)

    print("Scanning original image-based data...")
    original_data = scan_directory(os.path.abspath(ORIGINAL_DIR), LEVELS)

    for label, dataset in [("Text-Only", textonly_data),
                           ("Original", original_data)]:
        for game in GAMES:
            for mode in MODES:
                for model in MODEL_KEYS:
                    if model in dataset[game][mode]:
                        lvls = sorted(dataset[game][mode][model].keys())
                        counts = [len(dataset[game][mode][model][l])
                                  for l in lvls]
                        print(f"  {label} | {game}/{mode}/{model}: "
                              f"levels={lvls}, samples={counts}")

    print("\nGenerating matched-sample comparison (per game)...")
    plot_matched_per_game(textonly_data, original_data, output_dir)

    print("\nGenerating per-game trend lines...")
    plot_matched_trend_per_game(textonly_data, original_data, output_dir)

    print("\nGenerating matched-sample bar charts (game-averaged, per model)...")
    plot_matched_bar_per_model(textonly_data, original_data, output_dir)

    print("\nGenerating matched-sample trend (game-averaged, per model)...")
    plot_matched_trend(textonly_data, original_data, output_dir)

    print("\nDone!")


if __name__ == "__main__":
    main()
