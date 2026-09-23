#!/usr/bin/env python3
"""Fast deterministic convention-style baseline in the pinned HLE engine."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import benchmark_hle as bench  # noqa: E402


def choose(state, legal_moves):
    game_state = state["hanabi_state"]
    safe, _ = bench.guaranteed_play_indices(game_state, bench.PLAYERS, legal_moves)
    if safe:
        return min(safe)
    signals = bench.guaranteed_plays_after_clues(game_state, bench.PLAYERS, legal_moves)
    signal_indices = [i for i, slots in signals.items() if slots]
    if signal_indices:
        return max(signal_indices, key=lambda i: (len(signals[i]), -i))
    values = bench.clue_information_values(game_state, bench.PLAYERS, legal_moves)
    clues = [i for i in values if legal_moves[i].startswith("(Reveal")]
    if clues:
        return max(clues, key=lambda i: (values[i]["bits_reduction"], values[i]["matched_cards"], -i))
    probabilities = bench.joint_play_probabilities(game_state, bench.PLAYERS, legal_moves)
    discards = [i for i, move in enumerate(legal_moves) if move.startswith("(Discard")]
    return min(discards, key=lambda i: probabilities.get(next(
        j for j, m in enumerate(legal_moves) if m == "(Play " + legal_moves[i][9:-1] + ")"), 0.0))


async def run(seed):
    env = bench.hanabi.load_environment(num_players=2, mode="sherlock", use_dataset=False,
        num_games=1, seeds=[seed], max_turns=100, judge_model="",
        engine_random_start_player=False, final_score_mode="fireworks")
    state = await env.setup_state({"info": {"seed": seed}, "prompt": []})
    messages = state["prompt"]
    while True:
        game = state["hanabi_state"]
        if game.is_terminal() or state.get("done") or state.get("turn_count", 0) >= 100:
            break
        moves = [str(m) for m in game.legal_moves()]
        index = choose(state, moves)
        reply = json.dumps({"action": index, "reason": "deterministic convention baseline"})
        messages = list(messages) + [{"role": "assistant", "content": reply}]
        messages = await env.env_response(messages, state)
    score = state.get("final_score")
    if score is None:
        score = env._compute_score(state["hanabi_state"])
    return int(score), state["hanabi_state"].life_tokens()


async def main():
    seeds = list(range(100))
    rows = [await run(seed) for seed in seeds]
    scores = [row[0] for row in rows]
    print(json.dumps({"games": len(rows), "mean": sum(scores) / len(scores),
                      "min": min(scores), "max": max(scores),
                      "all_lives": all(lives == 3 for _, lives in rows)}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
