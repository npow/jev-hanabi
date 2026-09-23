# JEV Sherlock prompt pilots (pending)

These runs adapt the paper's Sherlock prompt to JEV's structured-decision API.
They are closer prompt comparisons, not identical model interfaces.

JEV's documented interface returns structured decisions rather than generated
strings. The adapter therefore keeps the paper's full game strategy, Bayesian
card-count guidance, and critical-card instructions, while replacing the
incompatible free-form JSON output block with typed JEV questions. The paper
asks its models to rate every legal move, so two JEV variants are available:

- `paper_sherlock_choice`: one Choice question over all legal moves.
- `paper_sherlock_score`: one Score question per legal move, sent in a single
  fan-out request; choose the action with the largest expected score.
- `paper_sherlock_signal_choice`: the full Sherlock prompt plus the earlier
  verified safety/signal protocol; unsafe plays are removed, guaranteed plays
  are prioritized, and signal clues are annotated.

The Score variant more closely follows the paper's move-rating format. The
Choice variant is the simpler direct action-selection baseline. TypeSafe also
describes decomposed, structured questions as its intended workflow pattern.

The earlier 8.96/25, 100-game result used `signal_protocol_sherlock`, whose
prompt construction removed the Sherlock instructions beginning at
"Please think step by step" and replaced them with a shorter policy. Treat that
score as a custom scaffold result, not a direct comparison with the paper's
Sherlock numbers.

## Run

When JEV API access is available, run both variants on the same 10 seeds as the
paper, then expand to 100 paired seeds if the pilots complete:

```sh
HANABI_MODE=sherlock \
HANABI_PROMPT_VARIANT=paper_sherlock_choice \
HANABI_SEEDS=0,1,2,3,4,5,6,7,8,9 \
HANABI_OUTDIR=results/runs/results_hle_paper_sherlock_choice_pilot \
paper_env/.venv/bin/python benchmark_hle.py
```

The pilot was attempted on 2026-09-21, but the first API request returned HTTP
402 (payment required). No games completed and no paid credits were added.
`partial_manifest.json` records the failed Choice attempt; `games.jsonl` is
empty. The Score variant has not been attempted. The benchmark script now
records per-game hashes and a root digest in `results_integrity.json` for every
completed run.

Run the move-rating adaptation in its own output directory:

```sh
HANABI_MODE=sherlock \
HANABI_PROMPT_VARIANT=paper_sherlock_score \
HANABI_SEEDS=0,1,2,3,4,5,6,7,8,9 \
HANABI_OUTDIR=results/runs/results_hle_paper_sherlock_score_pilot \
paper_env/.venv/bin/python benchmark_hle.py
```
