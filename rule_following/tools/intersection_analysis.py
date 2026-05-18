import os
import json
import re
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

# ================= Font Configuration (Type 1 fonts) =================
mpl.rcParams['text.usetex'] = True
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times']
mpl.rcParams['text.latex.preamble'] = r'\usepackage{times}'

# ================= Font Size Configuration =================
FONT_AXIS_LABEL = 22
FONT_TICK_LABEL = 24
FONT_LEGEND = 22
FONT_ANNOTATION = 16

# ================= Configuration =================
BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'rule complexity ladder')
GAMES = ["chess", "xiangqi"]
LEVELS = [1, 2, 3, 4, 5, 6]

# Targeted models
TARGET_MODELS = ["qwen8b", "qwen30b", "qwen235b", "gpt5.2"]

MODEL_LABELS = {
    "qwen8b": "Qwen3-VL 8B",
    "qwen30b": "Qwen3-VL 30B",
    "qwen235b": "Qwen3-VL 235B",
    "gpt5.2": "GPT-5.2",
}


def extract_model_key(folder_name):
    """Matches folder names to our target keys."""
    folder_lower = folder_name.lower()
    for key in TARGET_MODELS:
        if key in folder_lower:
            return key
    return None


def extract_level(folder_name):
    match = re.search(r'level_(\d+)', folder_name.lower())
    if match:
        return int(match.group(1))
    return None


def load_detailed_results(base_dir):
    """
    Loads data into structure: 
    data[game][model][level][mode] = {case_id: {verified: bool, correct: bool}}
    """
    # Structure: data[game][model][level][mode]
    data = {}

    for game in GAMES:
        game_path = os.path.join(base_dir, game)
        if not os.path.exists(game_path):
            continue

        if game not in data:
            data[game] = {}

        for mode_dir in os.listdir(game_path):
            if "explicit" in mode_dir.lower():
                mode = "explicit"
            elif "predictive" in mode_dir.lower():
                mode = "predictive"
            else:
                continue

            mode_path = os.path.join(game_path, mode_dir)

            for model_dir in os.listdir(mode_path):
                model_key = extract_model_key(model_dir)
                if not model_key:
                    continue

                if model_key not in data[game]:
                    data[game][model_key] = {}

                model_path = os.path.join(mode_path, model_dir)

                for level_dir in os.listdir(model_path):
                    lvl = extract_level(level_dir)
                    if not lvl:
                        continue

                    if lvl not in data[game][model_key]:
                        data[game][model_key][lvl] = {}

                    # Find JSON
                    json_path = None
                    level_full_path = os.path.join(model_path, level_dir)
                    for f in os.listdir(level_full_path):
                        if f.endswith(".json"):
                            json_path = os.path.join(level_full_path, f)
                            break

                    if json_path:
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                jdata = json.load(f)
                                results_map = {}
                                for case in jdata.get('detailed_results', []):
                                    c_id = case.get('case_id')
                                    verified = case.get(
                                        'verification_passed', False)
                                    correct = case.get('correct', False)
                                    results_map[c_id] = {
                                        'verified': verified, 'correct': correct}

                                data[game][model_key][lvl][mode] = results_map
                        except Exception as e:
                            print(f"Error loading {json_path}: {e}")

    return data


def analyze_verification_rates(data):
    """Calculates overall verification rates for Exp vs Pred."""
    stats = {'explicit': [], 'predictive': []}

    for game in data:
        for model in data[game]:
            for lvl in data[game][model]:
                for mode in ['explicit', 'predictive']:
                    if mode in data[game][model][lvl]:
                        cases = data[game][model][lvl][mode].values()
                        if not cases:
                            continue
                        verified_count = sum(1 for c in cases if c['verified'])
                        total = len(cases)
                        stats[mode].append(verified_count / total)

    avg_exp = np.mean(stats['explicit']) * 100
    avg_pred = np.mean(stats['predictive']) * 100
    return avg_exp, avg_pred


def analyze_intersection(data):
    """
    Calculates accuracy ONLY on cases where BOTH modes passed verification.
    Returns: aggregated_by_level[level] = {'explicit': [], 'predictive': []}
    """
    agg_by_level = {l: {'explicit': [], 'predictive': [],
                        'n_samples': []} for l in LEVELS}

    for game in data:
        for model in data[game]:
            for lvl in LEVELS:
                if lvl not in data[game][model]:
                    continue

                modes_data = data[game][model][lvl]
                if 'explicit' not in modes_data or 'predictive' not in modes_data:
                    continue

                exp_map = modes_data['explicit']
                pred_map = modes_data['predictive']

                # Find intersection of Verification
                common_ids = set(exp_map.keys()) & set(pred_map.keys())

                # Filter: Both must be Verified=True
                valid_intersection = []
                for cid in common_ids:
                    if exp_map[cid]['verified'] and pred_map[cid]['verified']:
                        valid_intersection.append(cid)

                if not valid_intersection:
                    continue

                # Calculate Accuracy on Intersection
                exp_correct = sum(
                    1 for cid in valid_intersection if exp_map[cid]['correct'])
                pred_correct = sum(
                    1 for cid in valid_intersection if pred_map[cid]['correct'])
                total = len(valid_intersection)

                agg_by_level[lvl]['explicit'].append(exp_correct / total)
                agg_by_level[lvl]['predictive'].append(pred_correct / total)
                agg_by_level[lvl]['n_samples'].append(total)

    return agg_by_level


def analyze_intersection_by_model(data):
    """
    Calculates accuracy ONLY on cases where BOTH modes passed verification.
    Returns: per_model[model][level] = {'explicit': acc, 'predictive': acc, 'n_samples': n}
    """
    per_model = {m: {l: {'explicit': [], 'predictive': [], 'n_samples': []}
                     for l in LEVELS} for m in TARGET_MODELS}

    for game in data:
        for model in data[game]:
            if model not in TARGET_MODELS:
                continue
            for lvl in LEVELS:
                if lvl not in data[game][model]:
                    continue

                modes_data = data[game][model][lvl]
                if 'explicit' not in modes_data or 'predictive' not in modes_data:
                    continue

                exp_map = modes_data['explicit']
                pred_map = modes_data['predictive']

                # Find intersection of Verification
                common_ids = set(exp_map.keys()) & set(pred_map.keys())

                # Filter: Both must be Verified=True
                valid_intersection = []
                for cid in common_ids:
                    if exp_map[cid]['verified'] and pred_map[cid]['verified']:
                        valid_intersection.append(cid)

                if not valid_intersection:
                    continue

                # Calculate Accuracy on Intersection
                exp_correct = sum(
                    1 for cid in valid_intersection if exp_map[cid]['correct'])
                pred_correct = sum(
                    1 for cid in valid_intersection if pred_map[cid]['correct'])
                total = len(valid_intersection)

                per_model[model][lvl]['explicit'].append(exp_correct / total)
                per_model[model][lvl]['predictive'].append(
                    pred_correct / total)
                per_model[model][lvl]['n_samples'].append(total)

    return per_model


def plot_intersection_results(agg_data, raw_ver_exp, raw_ver_pred):
    levels = sorted(agg_data.keys())
    exp_means = [np.mean(agg_data[l]['explicit']) *
                 100 if agg_data[l]['explicit'] else 0 for l in levels]
    pred_means = [np.mean(agg_data[l]['predictive']) *
                  100 if agg_data[l]['predictive'] else 0 for l in levels]

    plt.figure(figsize=(10, 6))

    # Styling consistent with your paper
    plt.plot(levels, exp_means, label='Explicit Mode (Intersection)', color='#e74c3c',
             marker='o', linewidth=3, markersize=10, alpha=0.9)
    plt.plot(levels, pred_means, label='Predictive Mode (Intersection)', color='#3498db',
             marker='s', linewidth=3, markersize=10, alpha=0.9)

    # Fill between
    plt.fill_between(levels, exp_means, pred_means, alpha=0.1, color='gray')

    # Annotations
    for i, lvl in enumerate(levels):
        plt.annotate(f"{exp_means[i]:.1f}", (lvl, exp_means[i]), textcoords="offset points", xytext=(
            0, 20), ha='center', color='#e74c3c', fontsize=FONT_ANNOTATION, fontweight='bold')
        plt.annotate(f"{pred_means[i]:.1f}", (lvl, pred_means[i]), textcoords="offset points", xytext=(
            0, -26), ha='center', color='#3498db', fontsize=FONT_ANNOTATION, fontweight='bold')

    plt.xlabel("Task Level", fontsize=FONT_AXIS_LABEL, fontweight='bold')
    plt.ylabel("Accuracy on Intersection Set (\%)",
               fontsize=FONT_AXIS_LABEL, fontweight='bold')
    plt.ylim(30, 105)
    plt.xticks(fontsize=FONT_TICK_LABEL)
    plt.yticks(fontsize=FONT_TICK_LABEL)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(fontsize=14)

    plt.tight_layout()
    plt.savefig("intersection_analysis.pdf")
    print("Chart saved to intersection_analysis.pdf")


def plot_intersection_by_model(per_model_data):
    """Plot intersection accuracy for each model separately."""
    models = [m for m in TARGET_MODELS if any(
        per_model_data[m][l]['explicit'] for l in LEVELS)]
    n_models = len(models)

    if n_models == 0:
        print("No model data available for per-model plot.")
        return

    fig, axes = plt.subplots(1, n_models, figsize=(6*n_models, 7), sharey=True)
    if n_models == 1:
        axes = [axes]

    levels = LEVELS

    for idx, model in enumerate(models):
        ax = axes[idx]

        exp_means = []
        pred_means = []
        for lvl in levels:
            exp_vals = per_model_data[model][lvl]['explicit']
            pred_vals = per_model_data[model][lvl]['predictive']
            exp_means.append(np.mean(exp_vals) * 100 if exp_vals else 0)
            pred_means.append(np.mean(pred_vals) * 100 if pred_vals else 0)

        ax.plot(levels, exp_means, label='Explicit Mode', color='#e74c3c',
                marker='o', linewidth=3, markersize=10, markerfacecolor='#e74c3c',
                markeredgecolor='white', markeredgewidth=2, alpha=0.9)
        ax.plot(levels, pred_means, label='Predictive Mode', color='#3498db',
                marker='s', linewidth=3, markersize=10, markerfacecolor='#3498db',
                markeredgecolor='white', markeredgewidth=2, alpha=0.9)

        # Fill between
        ax.fill_between(levels, exp_means, pred_means, alpha=0.1, color='gray')

        # Annotations
        for i, lvl in enumerate(levels):
            if exp_means[i] > 0:
                ax.annotate(f"{exp_means[i]:.0f}", (lvl, exp_means[i]), textcoords="offset points",
                            xytext=(0, 20), ha='center', color='#e74c3c',
                            fontsize=FONT_ANNOTATION, fontweight='bold')
            if pred_means[i] > 0:
                ax.annotate(f"{pred_means[i]:.0f}", (lvl, pred_means[i]), textcoords="offset points",
                            xytext=(0, -26), ha='center', color='#3498db',
                            fontsize=FONT_ANNOTATION, fontweight='bold')

        ax.set_title(MODEL_LABELS.get(model, model),
                     fontsize=28, fontweight='bold', pad=15)
        ax.set_xticks(levels)
        ax.set_xticklabels([f'L{l}' for l in levels], fontsize=FONT_TICK_LABEL)
        ax.tick_params(axis='y', labelsize=FONT_TICK_LABEL)
        ax.set_ylim(30, 105)
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_axisbelow(True)

    axes[0].set_ylabel("Accuracy on Intersection Set (\\%)",
                       fontsize=FONT_AXIS_LABEL, fontweight='bold')

    # Shared x-label
    fig.text(0.5, 0.02, 'Task Level', ha='center',
             fontsize=FONT_AXIS_LABEL, fontweight='bold')

    # Shared legend
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.01),
               ncol=2, fontsize=FONT_LEGEND, framealpha=0.95, edgecolor='black', fancybox=True)

    plt.tight_layout()
    plt.subplots_adjust(top=0.84, bottom=0.14)
    plt.savefig("intersection_analysis_by_model.pdf", bbox_inches='tight')
    print("Chart saved to intersection_analysis_by_model.pdf")

# ================= Execution =================


if __name__ == "__main__":
    print("Loading data...")
    data = load_detailed_results(BASE_DIR)

    print("Analyzing Raw Verification Rates...")
    ver_exp, ver_pred = analyze_verification_rates(data)
    print(
        f"Global Average Verification Rate -> Explicit: {ver_exp:.2f}%, Predictive: {ver_pred:.2f}%")

    print("Calculating Paired Intersection Accuracy...")
    intersection_results = analyze_intersection(data)

    print("\n=== Intersection Accuracy Table (Same Samples) ===")
    print(f"{'Level':<6} | {'Explicit':<10} | {'Predictive':<10} | {'Gap':<6} | {'N (avg)':<8}")
    print("-" * 55)
    for l in LEVELS:
        e = np.mean(intersection_results[l]['explicit']) * 100
        p = np.mean(intersection_results[l]['predictive']) * 100
        n = np.mean(intersection_results[l]['n_samples'])
        print(f"L{l:<5} | {e:<10.2f} | {p:<10.2f} | {e-p:<6.2f} | {n:<8.1f}")

    plot_intersection_results(intersection_results, ver_exp, ver_pred)

    # Generate per-model chart
    print("\nGenerating per-model intersection chart...")
    per_model_results = analyze_intersection_by_model(data)
    plot_intersection_by_model(per_model_results)
