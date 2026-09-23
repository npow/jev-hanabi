# JEV paper Sherlock move-rating pilot (pending)

This run adapts the paper's Sherlock setup to JEV's Score API. It preserves the
paper environment's Bayesian card-count and strategy instructions, replaces the
free-form JSON response block with five ordered action-value levels, and asks
one Score question for each legal move in a single fan-out request. The chosen
move is the legal action with the highest expected score.

The first pilot uses the same seeds as the paper (0–9). The Choice version and
its HTTP 402 attempt are documented in
`../results_hle_paper_sherlock_choice_pilot/README.md`. This Score variant has
not been run; no score estimate is available until JEV accepts requests.

```sh
HANABI_MODE=sherlock \
HANABI_PROMPT_VARIANT=paper_sherlock_score \
HANABI_SEEDS=0,1,2,3,4,5,6,7,8,9 \
HANABI_OUTDIR=results_hle_paper_sherlock_score_pilot \
paper_env/.venv/bin/python benchmark_hle.py
```
