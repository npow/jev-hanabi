#!/usr/bin/env python3
"""Fast deterministic convention-style baseline in the pinned HLE engine."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import benchmark_hle as bench  # noqa: E402


def choose(state, legal_moves):
    game_state = state["hanabi_state"]
    safe, _ = bench.guaranteed_play_indices(game_state, bench.PLAYERS, legal_moves)
    posterior = bench.joint_play_probabilities(game_state, bench.PLAYERS, legal_moves)
    safe = sorted(set(safe) | {i for i, p in posterior.items() if p >= 1.0 - 1e-12})
    if safe:
        return min(safe)
    # Critical-save convention: a rank clue on an unplayable rank protects a
    # last surviving 2/3/4 on the partner's oldest unclued card.
    partner = (game_state.cur_player() + 1) % bench.PLAYERS
    partner_knowledge = bench.extract_knowledge(game_state, partner, bench.PLAYERS)
    chop = next((i for i, entry in enumerate(partner_knowledge)
                 if entry.split("||", 1)[1].split("|", 1)[0] == "XX"), None)
    if chop is not None:
        card = game_state.player_hands()[partner][chop]
        rank = card.rank() + 1
        color = "RYGWB"[card.color()]
        copies = 3 if rank == 1 else (1 if rank == 5 else 2)
        discarded = sum(1 for c in game_state.discard_pile()
                        if c.color() == card.color() and c.rank() + 1 == rank)
        rank_playable = any(top == rank - 1 for top in game_state.fireworks())
        partner_has_safe = any(
            slot < len(partner_knowledge) and all(
                int(r) == game_state.fireworks()["RYGWB".index(c)] + 1
                for c in "RYGWB" if c in entry.split("||", 1)[1].split("|", 1)[1]
                for r in "12345" if r in entry.split("||", 1)[1].split("|", 1)[1]
            )
            for slot, entry in enumerate(partner_knowledge)
        )
        if rank in (2, 3, 4) and not rank_playable and discarded >= copies - 1 and not partner_has_safe:
            for i, move in enumerate(legal_moves):
                if move == f"(Reveal player +1 rank {rank})":
                    return i
    play_threshold = float(os.environ.get("RULE_PLAY_THRESHOLD", "0"))
    if play_threshold:
        eligible = [i for i, p in posterior.items() if p >= play_threshold]
        if eligible:
            return max(eligible, key=lambda i: posterior[i])
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
