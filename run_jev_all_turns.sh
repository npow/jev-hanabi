#!/usr/bin/env bash
set -euo pipefail

# JEV makes the final action selection on every turn. The executable
# convention is used only to generate a compact safety-filtered candidate set.
HANABOT_JEV_ALL_TURNS=1 \
HANABI_SMART_CONVENTION_PROMPT=1 \
HANABI_MODE=sherlock \
HANABI_PROMPT_VARIANT=paper_sherlock_signal_choice \
HANABOT_STRATEGY=filtered_stall \
HANABOT_GAMES="${HANABOT_GAMES:-100}" \
./run_hanabot_hle_pilot.sh
