# Results

## Primary estimate

The primary policy was evaluated on 200 games (seeds 10–209).

| Games | Mean score | Median | Range | Lives retained |
|---:|---:|---:|---:|---:|
| 200 | **14.37 / 25** | 14 | 9–19 | 200 / 200 |

## Published Sherlock references

The environment's published two-player reference scores are shown for
context. Their evaluations use free-form model completions; this evaluation
uses JEV's structured Score interface.

| Model | Score |
|---|---:|
| GPT-4.1 mini | 6.5 |
| GPT-4.1 | 14.8 |
| DeepSeek-R1 | 17.5 |
| o4-mini | 14.6 |
| o3 | 17.6 |

## Policy sensitivity runs

These runs use the same environment and prompt family, with the stated policy
change applied independently.

| Variant | Games | Mean | 95% interval | Lives lost |
|---|---:|---:|---:|---:|
| Discard threshold 0.20 | 50 | 14.52 | 13.87–15.17 | 0 |
| Matched discard threshold 0.10 | 50 | 14.42 | 13.83–15.01 | 0 |
| Risk penalty 0.1 | 50 | 14.64 | 14.05–15.23 | 0 |
| Matched risk penalty 0.0 | 50 | 14.52 | 13.92–15.12 | 0 |

The paired difference for the discard threshold was +0.10 (95% CI −0.50 to
+0.70). The paired difference for the risk penalty was +0.12 (95% CI −0.42 to
+0.66). Neither difference is statistically distinguishable from zero.

All run summaries and manifests are under [`results/runs/`](results/runs/).
