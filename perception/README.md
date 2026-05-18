# Perception Test Suite

## Diagnostic Dimensions

| Test | Description |
|------|-------------|
| **Density** | Low/Medium/High piece counts. Reports piece-only accuracy to avoid inflation from empty squares. |
| **Patch Alignment** | 4 offset conditions (boundary/quarter/center/three_quarter). Model-specific configs (16×16 for Qwen/GPT, 14×14 for Gemma/GLM). |
| **Resolution** | Divisible vs non-divisible image sizes relative to model's patch size. |
| **Richness** | 2D flat vs 3D rendered visual styles. |

## Installation

create an .env file to add API keys

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Single test
python run/run_tests.py -t density -g chess -m qwen30b -n 100

# Run all tests on both games with dummy model
python run/run_tests.py -t all -g all -m dummy
```
To reproduce the test result run below code with all models
```bash

python run/run_tests.py -t all -g all --model <modelname> -n 100
```

Run `python run/run_tests.py --help` for the full flag list.

## Supported Models

Any model with an OpenAI-compatible API can be easily added to shared/model_configs.py

---

## Analysis & Plotting

Download our released results, then drop the scripts from `tools/` into the `perception/` folder and run:

```bash
python perception/tools/plot.py
```

---

