**Table 4. Human-vs-Gemini judge score comparison across the full dataset.**

| Metric | Human Mean | Gemini Mean | Mean Gap | Wilcoxon `p` |
| --- | ---: | ---: | ---: | ---: |
| Prompt Adherence | 7.78 | 8.31 | +0.53 | 0.0678 |
| Functional Correctness | 7.58 | 8.37 | +0.78 | 0.0016 |
| UI Quality | 7.43 | 7.72 | +0.29 | 0.3426 |
| Overall Performance | 7.63 | 8.18 | +0.56 | 0.0162 |

The `p` values are two-sided Wilcoxon signed-rank tests over paired Gemini-minus-human score differences across model outputs, with zero differences omitted from the signed-rank statistic.
