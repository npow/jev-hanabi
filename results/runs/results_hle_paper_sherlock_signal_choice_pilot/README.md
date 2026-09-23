# Full Sherlock prompt with safety and signal protocol

This exploratory variant preserves the paper's complete Sherlock prompt, while
using the verified earlier protocol: unsafe plays are removed; if a guaranteed
play exists, JEV chooses only among those plays; otherwise signal clues are
annotated and JEV chooses among safe actions. It is a scaffolded result, not a
direct paper baseline.

The 10-seed pilot completed at 9.9/25 (seeds 0–9), with all games retaining
three lives. This is only a pilot; the corresponding 100-game expansion uses
seeds 10–109 in `results/runs/results_hle_paper_sherlock_signal_choice_100`.

```sh
HANABI_MODE=sherlock \
HANABI_PROMPT_VARIANT=paper_sherlock_signal_choice \
HANABI_SEEDS=0,1,2,3,4,5,6,7,8,9 \
HANABI_OUTDIR=results/runs/results_hle_paper_sherlock_signal_choice_pilot \
paper_env/.venv/bin/python benchmark_hle.py
```
