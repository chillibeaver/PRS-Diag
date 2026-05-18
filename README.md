# PRS-Diag

A diagnostic framework for disentangling perception, reasoning, and simulation failures in Vision-Language Models.

<!-- **Paper:** [Seeing Without Understanding: Disentangling Perception, Reasoning, and Simulation in VLM Gameplay](link) (ICML 2026) -->

## Overview

PRS-Diag(Perception, Reasoning, and Simulation Diagnostics) provides two test suites that systematically evaluate VLM capabilities in structured game environments:

- **Perception Tests** — Controlled evaluation of visual encoding under variations in density, patch alignment, resolution, and visual richness, plus quantification of spatially coordinated localization drift. [Details](./perception/README.md)

- **Rule-Following Tests** — A 2×2 diagnostic matrix and six-level rule complexity ladder evaluated in both explicit verification and predictive simulation modes, with text-only and chain-of-thought ablations. [Details](./rule_following/README.md)
 
## Quick Start

```bash
# Developed and tested with Python 3.11.9

# Install rule-following module
cd rule_following
pip install -e .
cd ..

# Install perception dependencies
cd perception
pip install -r requirements.txt
cd ..
```

See individual READMEs for detailed usage.

## Download Data

https://drive.google.com/file/d/1AjAKDChi7B-Ummdt21Vsxq9CdVImxf11/view?usp=sharing

## Citation

```bibtex
@inproceedings{jin2026seeing,
  title={Seeing Without Understanding: Disentangling Perception, Reasoning, and Simulation in VLM Gameplay},
  author={Jin, Dingyang and He, Jiawei and Lo, Calvin and Hu, Steven and Rad, Ryan},
  booktitle={Proceedings of the 43rd International Conference on Machine Learning (ICML)},
  year={2026}
}
```
