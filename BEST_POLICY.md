# Best current JEV Hanabi policy

Use the public Sherlock two-player environment with the paper prompt, JEV's
structured Score interface, guaranteed-safe play and teammate-signal rules, and
the 10% posterior discard filter:

```sh
HANABI_MODE=sherlock \
HANABI_PROMPT_VARIANT=paper_sherlock_signal_score \
HANABI_FILTER_RISKY_DISCARDS=1 \
HANABI_DISCARD_MIN_PLAY_PROBABILITY=0.10 \
HANABI_NUMERIC_ACTION_VALUES=1 \
HANABI_NUMERIC_CLUE_VALUES=1 \
HANABI_FILTER_REDUNDANT_CLUES=1 \
HANABI_SEEDS='10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109' \
HANABI_OUTDIR=results_hle_paper_sherlock_signal_score_numeric_redundant_clue_filter_10_100 \
paper_env/.venv/bin/python benchmark_hle.py
```

Across two 100-game blocks under the old clue annotation, this policy averages
**14.31/25**, a +2.01-point paired improvement over the plain 10% filter (95%
CI +1.46 to +2.55). All 400 games in that paired comparison retained all 3
lives. This is a hybrid policy:
JEV ranks actions, while deterministic engine-derived rules remove avoidably
risky discards and enforce guaranteed-safe plays.

The corrected criterion runs average **14.37/25 over 200 games** (14.61 on
seeds 10–109 and 14.12 on 110–209). The combined paired difference from the
old-criterion best is +0.06 (95% CI −0.21 to +0.33), so the corrected
annotation does not establish a reliable score improvement. Use
`./run_corrected_baseline.sh` for the first block; the second block is recorded
in `results_hle_paper_sherlock_signal_score_corrected_baseline_110_209`.
`HANABI_FORCE_POSTERIOR_PLAYS` and `HANABI_SHOW_POSTERIOR_PROBS` remain
experimental. `HANABI_NUMERIC_CLUE_VALUES` also remains experimental after a
10-game pilot.
