<div align="center">

🎉 **Accepted at ICML 2026**

# Seeing Without Understanding
**Disentangling Perception, Reasoning, and Simulation in VLM Gameplay**

[![ICML](https://img.shields.io/badge/ICML_2026-Page-4b44ce?style=flat-square)](https://icml.cc/virtual/2026/poster/61694)
[![OpenReview](https://img.shields.io/badge/OpenReview-29022-b31b1b?style=flat-square)](https://openreview.net/forum?id=nfuGwj5rr5)
[![arXiv](https://img.shields.io/badge/arXiv-Coming_Soon-lightgrey?style=flat-square&logo=arxiv)]()
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](./LICENSE)

</div>

## Overview

PRS-Diag(Perception, Reasoning, and Simulation Diagnostics) provides two test suites that evaluate VLM capabilities in structured game environments:

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
