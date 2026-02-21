# The Single-File Test

Longitudinal evaluation of frontier LLM web generation under a first-output-only protocol, plus supervised analysis of what predicts social reach.

## Quick Links
- Research notebook: [`research_supervised_ml.ipynb`](./research_supervised_ml.ipynb)
- Paper archive (placeholder): [`paper/`](./paper/)

## Abstract
This repository contains the analysis for a study of how frontier LLMs perform on single-file HTML generation tasks and whether technical generation metrics predict 24-hour social engagement.

The study uses a real-world workflow (public model UIs, first response only, no iterative correction) and links model-side properties (reasoning time, code length, score quality, audio packaging) to distribution outcomes on X, TikTok, and YouTube.

## Study Setup
- Data window: 2025-12-10 to 2026-02-04
- Scope: 17 experiments, 68 model runs (4 model outputs per experiment)
- Model families: GPT, Gemini, Grok, Opus
- Protocol: same prompt per experiment, first output only, raw outputs preserved, no post-edit before evaluation

## Research Questions
- Does more model compute (reasoning time / response time) improve output quality?
- Are AI-as-judge scores aligned with human scoring?
- Do technical generation features predict 24-hour impressions?

## Methods (Notebook)
- Notebook: [`research_supervised_ml.ipynb`](./research_supervised_ml.ipynb)
- Data is analyzed at two levels:
- `df`: model-level rows (68 rows)
- `exp_df`: experiment-level aggregation (17 rows)
- Target for virality modeling: `log(1 + X_Impressions_24h)`
- Main regression model: Ridge (L2) with Leave-One-Out Cross-Validation (LOOCV)
- Final four model inputs for prediction:
- `ReasonTime_mean`
- `Reasoning_Ratio_mean`
- `Suno_version`
- `Song_BPM`

## Key Findings
- Compute does not reliably improve quality across models.
- For Gemini, higher reasoning/inference time correlated with lower performance (Spearman `r=-0.540, p=0.025` for reasoning time; `r=-0.577, p=0.015` for response time).
- AI judging showed measurable self-bias/leniency.
- Gemini vs human functional correctness: Wilcoxon `p=0.0372` (significant), with higher Gemini self-scores on average.
- Virality was poorly predicted from technical pre-publication features.
- Ridge LOOCV out-of-sample performance: MAE `+/- 46,221` impressions, `R^2 = -0.331`.
- Strongest correlation with impressions was account-timeline related (starting followers), not code/compute quality (`X_followers r=-0.828`).
- Prompt length, song BPM, and most posting/audio variables showed weak or non-significant relationships in this sample.

## Repository Map
- [`research_supervised_ml.ipynb`](./research_supervised_ml.ipynb): full analysis notebook (EDA, stats tests, modeling, prediction playground)
- [`paper/`](./paper/): paper assets and archive placeholder
- `paper/experiment_tracker.xlsx`: experiment tracker data source used in analysis
- `experiments/`: per-experiment model outputs and assets
- `data_collection_program/`: collection utilities and scripts used in the broader workflow

## Reproducibility
- Open `research_supervised_ml.ipynb` and run cells top to bottom.
- Python packages used in the notebook include:
- `pandas`
- `numpy`
- `scipy`
- `scikit-learn`
- `matplotlib`
- `seaborn`
- `gradio`

## Notes
- Sample size is intentionally small (`n=17` experiments), so inferential results should be treated as directional.
- This repo tracks an ongoing longitudinal process; metrics and conclusions may evolve as new experiments are added.
