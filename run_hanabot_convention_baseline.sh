#!/usr/bin/env bash
set -euo pipefail

# Reproducible external convention baseline. The simulator uses its own
# engine; this is a feasibility check while the policy is being ported to HLE.
ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
CLONE_DIR="${HANABOT_DIR:-$ROOT_DIR/.cache/hanabot}"
COMMIT=a7ef393adbe7ddbcd8c0f9b94c73d67e9256fb67
if [ ! -d "$CLONE_DIR/.git" ]; then
  mkdir -p "$(dirname "$CLONE_DIR")"
  git clone https://github.com/DarthCalculus/hanabot.git "$CLONE_DIR"
fi
git -C "$CLONE_DIR" fetch --depth 1 origin "$COMMIT"
git -C "$CLONE_DIR" checkout --detach "$COMMIT"
PYTHONPATH="$CLONE_DIR" python3 -m hanabi_sim \
  --strategy "${HANABOT_STRATEGY:-distsave}" \
  --players 2 \
  --games "${HANABOT_GAMES:-1000}" \
  --seed "${HANABOT_SEED:-0}"
