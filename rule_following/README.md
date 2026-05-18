# Rule-Following Test Suite

## Overview

Evaluates VLM rule application through generated game states (Chess and Xiangqi) across two complementary test structures:

- **Diagnostic Matrix** — A 2×2 design crossing input modality (single-state vs. multi-state) with knowledge requirement (rule-free vs. rule-based), isolating where rule integration breaks down.

- **Rule Complexity Ladder** — A six-level progression from basic movement patterns (L1) to advanced temporal reasoning (L6), evaluated in both Explicit (verification) and Predictive (simulation) modes with verification gating to separate perception errors from reasoning failures.

## Quick Start

### Installation

```bash
# Install in development mode
pip install -e .
```

### Configuration

Create a `.env` file in the project root:

```env
# For Openrouter
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=qwen/qwen3-vl-8b-thinking

# For OpenAI
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-5.2-2025-12-11
```

## Diagnostic Matrix

```bash
# Run all cases in matrix using dummy model
python run/run_diag_matrix.py -g xiangqi --all -n 100 --mode all

# Reproduce results for a specific model
python run/run_diag_matrix.py -g all --all -n 100 --mode all -m <model name>
```

Run `python run/run_diag_matrix.py --help` for the full flag list.

## Rule Complexity Ladder

```bash
# Testing with chess for all levels (dummy model)
python run/run_comp_ladder.py --all -n 100

# Reproduce results for a specific model
python run/run_comp_ladder.py -g all --all -n 100 -m <model name>
```

Run `python run/run_comp_ladder.py --help` for the full flag list.

---

### Multi-Model Support

Supports any OpenAI-compatible API. Currently wired up:

- **OpenAI**
- **DashScope**
- **Novita AI**
- **XAI**
- **Google**
- **Anthropic**
- **OpenRouter**
- **Custom endpoints**
- **Dummy Model** (for testing only)

---

## Text Only

Re-runs existing Rule Complexity Ladder samples in text-only mode (FEN strings instead of images, no verification step) to isolate rule reasoning from visual perception.

**Expected layout** under `--results-dir` (default `output/rule complexity ladder`):

```
<results-dir>/
└── <game>/                                           # chess | xiangqi
    └── <mode> mode/                                  # "predictive mode" | "explicit mode"  (note the space)
        └── <source-model>-<game>-<mode>/             # e.g. qwen30b-chess-explicit
            └── **/level_<N>_results.json             # level JSON can sit at any depth
```

Pass only the **prefix** to `--source-model` (e.g., `qwen30b`, `gpt5.2`) — the script appends `-<game>-<mode>` to find the directory. The level JSON can sit at any depth under that — the script globs recursively.

**Important:** Run from the `rule_following/` directory so the default `--results-dir` resolves correctly.

```bash
cd rule_following

# Run chess explicit levels 3-6 against a prior result set
python run/run_textonly.py --game chess --mode explicit --levels 3 4 5 6 \
    --model openai --source-model gpt5.2 --output output/textonly

# Custom results directory
python run/run_textonly.py --game xiangqi --mode predictive --levels 1 2 3 \
    --model openrouter --source-model qwen30b
```

Run `python run/run_textonly.py --help` for the full flag list.

---

## CoT Ablation

Re-runs existing Rule Complexity Ladder samples with an explicit chain-of-thought scratchpad prompt to measure the marginal effect of CoT on rule-following accuracy.

**Expected layout** under `--input-base` (default `./output/rule complexity ladder`) — same as [Text Only](#text-only), with one extra requirement: the original `*.png` images must sit **co-located with the level JSON** (CoT reuses them, unlike Text Only which only reads FEN strings).

Pass only the **prefix** to `--source-model` (e.g., `gpt5.2`, `qwen235b`); the script appends `-<game>-<mode>` and globs recursively for the level JSON. A pre-flight check verifies every JSON and image exists before any API calls are made; if it fails, you'll get a list of missing paths to fix manually.

**Important:** Run from the `rule_following/` directory so the default `--input-base` resolves correctly.

```bash
cd rule_following

# Re-run chess predictive levels 3-6 with CoT against a prior result set
python run/run_cot_ablation.py --model openai --source-model gpt5.2 \
    --game chess --mode predictive --levels 3 4 5 6

# Custom input/output paths
python run/run_cot_ablation.py --model openai --source-model qwen235b \
    --game xiangqi --mode explicit --levels 3 4 5 6 \
    --input-base "./output/rule complexity ladder" \
    --output-base "./output/cot_ablation"
```

Run `python run/run_cot_ablation.py --help` for the full flag list.

---

## Analysis & Plotting (`tools/`)

Scripts under `rule_following/tools/` produce all the paper figures and intersection tables from the JSON results files.

### Recommended setup

Download our released data (or use your own) and copy the `tools/` folder alongside `rule complexity ladder/`, in the same parent directory:

```
<workspace>/
├── rule complexity ladder/        # main Level-1..6 results (note the spaces, no underscores)
├── cot_ablation/                  # CoT re-runs    (only needed for CoT plots)
├── textonly/                      # text-only re-runs  (only needed for text-only plots)
└── tools/                         # the scripts, copied or symlinked from rule_following/tools/
    ├── plot_comp_ladder.py
    ├── plot_textonly.py
    ├── plot_cot.py
    ├── intersection_analysis.py
    └── intersection_analysis_cot.py
```

With this layout you can run any script with no arguments and everything resolves. Inside the data directories, the layout is the same one the `run/` scripts produce:

```
<workspace>/<data-dir>/
└── <game>/                        # chess | xiangqi
    └── <mode-folder>/             # any folder name containing "explicit" or "predictive"
        └── <model-folder>/        # any folder name containing one of: qwen8b, qwen30b, qwen235b, gpt5.2
            ├── level_<N>_results.json              # JSON directly here, OR
            └── *level_<N>*/                        # any subdir with "level_<N>" in its name
                └── *.json                          # *_results.json preferred
```

Levels are extracted by regex `level_(\d+)`. Recognized model keys are **hardcoded** in each script's `MODEL_KEYS` list — to plot a new model, edit the list (and the matching `MODEL_LABELS`/`COLORS` dicts).

### How each script resolves its base directory

| Script                          | Base directory(s)                                                              |
| :------------------------------ | :----------------------------------------------------------------------------- |
| `plot_comp_ladder.py`           | `<script_dir>/../rule complexity ladder/` (override via CLI positional arg)    |
| `intersection_analysis.py`      | `<script_dir>/../rule complexity ladder/`                                      |
| `plot_textonly.py`              | `<script_dir>/../textonly/` + `<script_dir>/../rule complexity ladder/`        |
| `plot_cot.py`                   | `<script_dir>/../cot_ablation/` + `<script_dir>/../rule complexity ladder/`    |
| `intersection_analysis_cot.py`  | `<script_dir>/../cot_ablation/`                                                |

Edit the `*_DIR` / `BASE_DIR` constants at the top of each script if you want non-default paths.

Note that the `run/` scripts write to `./output/...` by default — one level deeper than what the plotting scripts look for. **Move, copy, or symlink the data up one level** (or override the constants) before plotting.

### Coverage notes

- `plot_comp_ladder.py` / `intersection_analysis.py`: levels **1–6**, single-source.
- `plot_textonly.py` / `plot_cot.py`: levels **3–6** only, **matched samples** (cases where the image-based / no-CoT verification passed and which exist in both runs). Produces side-by-side comparisons.
- `intersection_analysis_cot.py`: levels **3–6**, intersection of explicit & predictive on CoT data only.
