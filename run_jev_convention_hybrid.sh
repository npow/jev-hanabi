#!/usr/bin/env bash
set -euo pipefail

# JEV chooses among state-aware convention-valid stall clues. The executable
# convention handles ordinary play/discard/clue decisions and removes unsafe
# stall candidates before the JEV Choice request.
HANABOT_JEV_STALLS=1 \
HANABOT_JEV_EQUIV_ONLY=1 \
HANABI_SMART_CONVENTION_PROMPT=1 \
HANABI_MODE=sherlock \
HANABI_PROMPT_VARIANT=paper_sherlock_signal_choice \
HANABOT_STRATEGY=filtered_stall \
HANABOT_GAMES="${HANABOT_GAMES:-1000}" \
./run_hanabot_hle_pilot.sh
