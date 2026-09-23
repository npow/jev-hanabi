#!/usr/bin/env bash
set -euo pipefail

# Plain JEV: every legal HLE action is presented to JEV. No convention
# candidate filtering, safety veto, or external policy recommendation is used.
HANABOT_JEV_PLAIN_ALL_TURNS=1 \
HANABI_MODE=sherlock \
HANABI_PROMPT_VARIANT=paper_sherlock_signal_choice \
HANABI_SMART_CONVENTION_PROMPT=0 \
HANABOT_STRATEGY=distsave \
HANABOT_GAMES="${HANABOT_GAMES:-100}" \
./run_hanabot_hle_pilot.sh
