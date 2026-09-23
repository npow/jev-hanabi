#!/usr/bin/env python3
"""Small reproducible 2-player Hanabi benchmark for JEV's Choice API."""
from __future__ import annotations

import hashlib
import json
import os
import random
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
COLORS = ("R", "Y", "G", "B", "W")
COLOR_NAMES = {"R": "red", "Y": "yellow", "G": "green", "B": "blue", "W": "white"}
COPIES = {1: 3, 2: 2, 3: 2, 4: 2, 5: 1}
OUT = Path(__file__).resolve().parent / "results"


def make_deck(seed: int):
    deck = [(c, n) for c in COLORS for n, copies in COPIES.items() for _ in range(copies)]
    random.Random(seed).shuffle(deck)
    return deck


class Game:
    def __init__(self, seed: int):
        self.seed = seed
        self.deck = make_deck(seed)
        self.deck_hash = hashlib.sha256(json.dumps(self.deck).encode()).hexdigest()
        self.hands = [self.deck[:5], self.deck[5:10]]
        self.pos = 10
        self.played = {c: 0 for c in COLORS}
        self.discarded = []
        self.clues = 8
        self.lives = 3
        self.turn = 0
        self.current = 0
        self.final_turns = None
        self.history = []

    @property
    def done(self):
        return self.lives == 0 or all(v == 5 for v in self.played.values()) or self.final_turns == 0

    def legal_actions(self, player):
        actions = [{"id": f"play_{i}", "kind": "play", "index": i} for i in range(len(self.hands[player]))]
        if self.clues < 8:
            actions += [{"id": f"discard_{i}", "kind": "discard", "index": i} for i in range(len(self.hands[player]))]
        other = 1 - player
        for color in COLORS:
            indices = [i for i, card in enumerate(self.hands[other]) if card[0] == color]
            if indices and self.clues:
                actions.append({"id": f"color_{color}", "kind": "color", "value": color, "target": other, "indices": indices})
        for rank in range(1, 6):
            indices = [i for i, card in enumerate(self.hands[other]) if card[1] == rank]
            if indices and self.clues:
                actions.append({"id": f"rank_{rank}", "kind": "rank", "value": rank, "target": other, "indices": indices})
        return actions

    def observation(self, player):
        return {"current_player": player, "own_hand": ["??" for _ in self.hands[player]],
                "other_player_hand": [f"{COLOR_NAMES[c]} {n}" for c, n in self.hands[1-player]],
                "played_top_by_color": {COLOR_NAMES[c]: n for c, n in self.played.items()},
                "discard_pile": [f"{COLOR_NAMES[c]} {n}" for c, n in self.discarded],
                "clue_tokens": self.clues, "lives": self.lives, "deck_cards_remaining": len(self.deck)-self.pos,
                "final_turns_remaining": self.final_turns,
                "public_history": self.history}

    def apply(self, player, action):
        final_round_was_active = self.final_turns is not None
        detail = {"player": player, "action": action["id"]}
        kind = action["kind"]
        if kind in ("play", "discard"):
            i = action["index"]
            card = self.hands[player].pop(i)
            detail["card"] = f"{COLOR_NAMES[card[0]]} {card[1]}"
            if kind == "play":
                if card[1] == self.played[card[0]] + 1:
                    self.played[card[0]] += 1
                    detail["result"] = "success"
                    if card[1] == 5:
                        self.clues = min(8, self.clues + 1)
                else:
                    self.lives -= 1
                    self.discarded.append(card)
                    detail["result"] = "misfire"
            else:
                self.discarded.append(card)
                self.clues = min(8, self.clues + 1)
                detail["result"] = "discard"
            if self.pos < len(self.deck):
                self.hands[player].append(self.deck[self.pos])
                self.pos += 1
                if self.pos == len(self.deck):
                    self.final_turns = 2
        else:
            self.clues -= 1
            detail["target"] = action["target"]
            detail["clue"] = f"{kind} {action['value']} at slots {action['indices']}"
            detail["result"] = "clue"
        # Every action in the final round counts, including clues. The action
        # that draws the last card starts the round but is not counted here;
        # each player then gets exactly one additional turn.
        if final_round_was_active:
            self.final_turns -= 1
        self.history.append(detail)
        self.turn += 1
        self.current = 1 - player


def choose_random(game, player, seed):
    return random.Random(seed + game.turn * 9176).choice(game.legal_actions(player))


def jev_choose(game, player, api_key):
    actions = game.legal_actions(player)
    desc = {}
    for a in actions:
        if a["kind"] == "play":
            label = f"Play your card in slot {a['index']+1}."
        elif a["kind"] == "discard":
            label = f"Discard your card in slot {a['index']+1}."
        else:
            label = f"Tell player {a['target']+1} that slot(s) {', '.join(str(i+1) for i in a['indices'])} have {COLOR_NAMES.get(a['value'], a['value'])} {a['kind']} information."
        desc[a["id"]] = label
    observation = game.observation(player)
    state = ("You are playing cooperative Hanabi, a 2-player game. Your own cards are hidden; "
             "the other player's cards are visible. A play succeeds only if its rank is exactly one above "
             "the current top rank for that color. A failed play loses one life. A clue costs one clue token. "
             "Discarding recovers one token up to 8. Each player gets one action per turn. Maximize the final "
             "score (the sum of completed color stacks, maximum 25); preserve lives and playable cards.\n"
             "Choose one legal action. Do not assume unshown information about your own cards.\nCurrent observation:\n"+
             json.dumps(observation, ensure_ascii=False))
    payload = {"model": MODEL, "state": state, "questions": {"action": {
        "type": "choice", "instructions": "Which single action should you take?", "criteria": desc}}}
    req = urllib.request.Request(API, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer "+api_key, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode())
    action_id = result["answers"]["action"]["choice"]
    selected = next((a for a in actions if a["id"] == action_id), None)
    if selected is None:
        raise ValueError(f"JEV returned invalid action {action_id!r}; valid IDs={list(desc)}")
    audit = {"turn": game.turn, "player": player, "observation": observation,
             "observation_sha256": hashlib.sha256(json.dumps(observation, sort_keys=True).encode()).hexdigest(),
             "action_ids": [a["id"] for a in actions], "request": payload, "response": result,
             "selected_action": action_id}
    return selected, audit


def play(seed, agent, api_key=None):
    game = Game(seed)
    api_calls = 0
    errors = []
    decisions = []
    while not game.done and game.turn < 100:
        player = game.current
        if agent == "jev":
            action, audit = jev_choose(game, player, api_key)
            api_calls += 1
            decisions.append(audit)
            time.sleep(0.12)
        else:
            action = choose_random(game, player, seed)
        game.apply(player, action)
    return {"seed": seed, "deck_sha256": game.deck_hash, "agent": agent,
            "score": sum(game.played.values()), "max_score": 25, "lives_remaining": game.lives,
            "clue_tokens_remaining": game.clues, "turns": game.turn, "api_calls": api_calls,
            "played_by_color": {COLOR_NAMES[c]: v for c, v in game.played.items()},
            "history": game.history, "decisions": decisions, "errors": errors}


def main():
    key = os.environ.get("JEV_API_KEY")
    if not key:
        raise SystemExit("JEV_API_KEY is not set")
    seeds = [int(x) for x in os.environ.get("HANABI_SEEDS", "101,202,303").split(",")]
    OUT.mkdir(parents=True, exist_ok=True)
    raw_path = OUT / "jev_games.jsonl"
    raw_path.write_text("")
    rows = []
    for seed in seeds:
        row = play(seed, "jev", key)
        rows.append(row)
        with raw_path.open("a") as f:
            f.write(json.dumps(row)+"\n")
        print(f"JEV seed={seed}: {row['score']}/25, lives={row['lives_remaining']}, turns={row['turns']}, calls={row['api_calls']}", flush=True)
    # Deterministic low-skill baseline on the exact same fixed deck order.
    baseline = [play(seed, "random") for seed in seeds]
    summary = {"benchmark": "2-player standard Hanabi, JEV controls both players",
        "model": MODEL, "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "seeds": seeds, "seed_count": len(seeds), "games_completed": len(rows),
        "scores": [r["score"] for r in rows], "score_mean": sum(r["score"] for r in rows)/len(rows),
        "score_median": sorted(r["score"] for r in rows)[len(rows)//2],
        "score_range": [min(r["score"] for r in rows), max(r["score"] for r in rows)],
        "total_api_calls": sum(r["api_calls"] for r in rows),
        "baseline_name": "random legal action, same shuffled deck seeds",
        "baseline_scores": [r["score"] for r in baseline],
        "baseline_games": len(baseline),
        "baseline_mean": sum(r["score"] for r in baseline)/len(baseline),
        "score_max": 25, "decision_count": sum(len(r["decisions"]) for r in rows),
        "input_sha256": hashlib.sha256(json.dumps([(r["seed"], r["deck_sha256"]) for r in rows], sort_keys=True).encode()).hexdigest(),
        "score_claim_limit": "Small pilot; 3 fixed seeds are descriptive, not a reliable estimate of general Hanabi strength."}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    manifest = {"model_requested": MODEL, "benchmark": summary["benchmark"], "seeds": seeds,
        "games": len(rows), "api_calls": summary["total_api_calls"], "decision_count": summary["decision_count"],
        "input_sha256": summary["input_sha256"], "deck_sha256_by_seed": {str(r["seed"]): r["deck_sha256"] for r in rows},
        "results_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "baseline_games": len(baseline), "baseline_scores": summary["baseline_scores"],
        "results_file": raw_path.name, "summary_file": "summary.json", "completed_at_utc": summary["evaluated_at_utc"]}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print("Summary:", json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
