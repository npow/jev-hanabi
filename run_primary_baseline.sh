#!/usr/bin/env bash
set -euo pipefail

SEEDS=$(paper_env/.venv/bin/python - <<'PY'
print(','.join(str(i) for i in range(10, 110)))
PY
)

HANABI_RESUME="${HANABI_RESUME:-0}" \
HANABI_MODE=sherlock \
HANABI_PROMPT_VARIANT=paper_sherlock_signal_score \
HANABI_FILTER_RISKY_DISCARDS=1 \
HANABI_DISCARD_MIN_PLAY_PROBABILITY=0.10 \
HANABI_NUMERIC_ACTION_VALUES=1 \
HANABI_NUMERIC_CLUE_VALUES=1 \
HANABI_FILTER_REDUNDANT_CLUES=1 \
HANABI_SCORE_RISK_PENALTY=0 \
HANABI_FORCE_SIGNAL_CLUES=0 \
HANABI_MIN_SIGNAL_SLOTS=1 \
HANABI_SEEDS="$SEEDS" \
HANABI_OUTDIR=results/runs/results_hle_paper_sherlock_signal_score_primary_10_100 \
paper_env/.venv/bin/python benchmark_hle.py
