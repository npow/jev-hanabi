#!/usr/bin/env python3
"""Run hanabot's executable convention policy inside the pinned HLE engine.

The adapter keeps stable card orders and reconstructs the observation/log shape
expected by hanabot from HLE's public state after every move.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANABOT_ROOT = Path(os.environ.get("HANABOT_ROOT", str(ROOT / ".cache/hanabot")))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HANABOT_ROOT))
import benchmark_hle as hle  # noqa: E402

from hanabi_sim.actions import Action, ActionRecord, ActionType  # noqa: E402
from hanabi_sim.cards import Card, Color  # noqa: E402
from hanabi_sim.observation import CardView, Observation  # noqa: E402
from hanabi_sim.players.chop_save_player import ChopSavePlayer  # noqa: E402
from hanabi_sim.players.critical_save_player import CriticalSavePlayer  # noqa: E402
from hanabi_sim.players.distant_save_player import DistantSavePlayer  # noqa: E402
from hanabi_sim.players.focus_player import FocusPlayer  # noqa: E402
from hanabi_sim.players.good_touch_player import GoodTouchPlayer  # noqa: E402
from hanabi_sim.players.tempo_player import TempoPlayer  # noqa: E402
from hanabi_sim.players.deduce_five_player import DeduceFivePlayer  # noqa: E402
from hanabi_sim.players.play_clue_player import PlayCluePlayer  # noqa: E402

COLOR_TO_EXTERNAL = {
    "R": Color.RED, "Y": Color.YELLOW, "G": Color.GREEN,
    "B": Color.BLUE, "W": Color.PURPLE,
}
EXTERNAL_TO_HLE = {
    Color.RED: "R", Color.YELLOW: "Y", Color.GREEN: "G",
    Color.BLUE: "B", Color.PURPLE: "W",
}


def card_to_external(card):
    return Card(COLOR_TO_EXTERNAL["RYGWB"[card.color()]], card.rank() + 1)


def parse_knowledge(entry):
    _identity, rest = entry.split("||", 1)
    known, possibilities = rest.split("|", 1)
    colors = frozenset(COLOR_TO_EXTERNAL[c] for c in "RYGWB" if c in possibilities)
    ranks = frozenset(int(r) for r in "12345" if r in possibilities)
    return known, colors, ranks


class Shadow:
    def __init__(self, game_state):
        if os.environ.get("HANABOT_REVERSE_INITIAL_ORDER", "0") == "1":
            self.orders = [list(range(4, -1, -1)), list(range(9, 4, -1))]
        else:
            self.orders = [list(range(0, 5)), list(range(5, 10))]
        self.next_order = 10
        self.log: list[ActionRecord] = []
        self.turn = 0

    def observation(self, game_state, observer):
        hands = []
        for player, hand in enumerate(game_state.player_hands()):
            knowledge = hle.extract_knowledge(game_state, player, 2)
            views = []
            for slot, card in enumerate(hand):
                known, colors, ranks = parse_knowledge(knowledge[slot])
                views.append(CardView(
                    order=self.orders[player][slot],
                    card=None if player == observer else card_to_external(card),
                    possible_colors=colors,
                    possible_ranks=ranks,
                    clued=(known != "XX" if os.environ.get("HANABOT_CLUED_MODE", "known") == "known" else False),
                ))
            hands.append(tuple(views))
        stacks = {COLOR_TO_EXTERNAL[c]: rank for c, rank in zip("RYGWB", game_state.fireworks())}
        return Observation(
            num_players=2,
            player_index=observer,
            current_player=game_state.cur_player(),
            hands=tuple(hands),
            play_stacks=stacks,
            discard_pile=tuple(card_to_external(c) for c in game_state.discard_pile()),
            clue_tokens=game_state.information_tokens(),
            max_clue_tokens=8,
            strikes=3 - game_state.life_tokens(),
            max_strikes=3,
            deck_size=game_state.deck_size(),
            colors=tuple(COLOR_TO_EXTERNAL[c] for c in "RYGWB"),
            score=game_state.score(),
            log=tuple(self.log),
        )

    def record(self, before_hands, before_fireworks, before_score, after, actor, move):
        action = self._action(actor, before_hands, move)
        record = ActionRecord(turn=self.turn, player=actor, action=action)
        if action.type in (ActionType.PLAY, ActionType.DISCARD):
            index = action.card_index
            old_card = before_hands[actor][index]
            record.acted_order = self.orders[actor][index]
            if action.type is ActionType.PLAY:
                record.played_card = card_to_external(old_card)
                record.success = after.score() > before_score
            else:
                record.discarded_card = card_to_external(old_card)
        else:
            target = action.target
            target_hand = before_hands[target]
            for slot, card in enumerate(target_hand):
                if ((action.type is ActionType.CLUE_COLOR and
                    "RYGWB"[card.color()] == EXTERNAL_TO_HLE[action.color]) or
                    (action.type is ActionType.CLUE_RANK and card.rank() + 1 == action.rank)):
                    record.touched_orders += (self.orders[target][slot],)
        if action.type in (ActionType.PLAY, ActionType.DISCARD):
            old_orders = self.orders[actor]
            new_orders = old_orders[:]
            new_orders.pop(action.card_index)
            if len(after.player_hands()[actor]) > len(new_orders):
                new_orders.append(self.next_order)
                record.drew_order = self.next_order
                self.next_order += 1
            self.orders[actor] = new_orders
        self.log.append(record)
        self.turn += 1

    def _action(self, actor, before_hands, move):
        if move.startswith("(Play "):
            return Action.play(int(move[6:-1]))
        if move.startswith("(Discard "):
            return Action.discard(int(move[9:-1]))
        if move.startswith("(Reveal player +1 color "):
            color = COLOR_TO_EXTERNAL[move[-2]]
            return Action.clue_color((actor + 1) % 2, color)
        if move.startswith("(Reveal player +1 rank "):
            return Action.clue_rank((actor + 1) % 2, int(move.removeprefix("(Reveal player +1 rank ").removesuffix(")")))
        raise ValueError(f"unsupported HLE move: {move}")


class EnsemblePlayer:
    """Conservative portfolio of the strongest convention variants."""
    def __init__(self):
        self.players = [DistantSavePlayer(), FocusPlayer(), DeduceFivePlayer()]

    def act(self, obs):
        actions = [player.act(obs) for player in self.players]
        if all(action == actions[0] for action in actions[1:]):
            return actions[0]
        plays = [a for a in actions if a.type is ActionType.PLAY]
        if plays:
            return min(plays, key=lambda a: a.card_index)
        clues = [a for a in actions if a.is_clue]
        if clues:
            return clues[0]
        return actions[0]


def to_hle_move(action: Action, actor: int):
    if action.type is ActionType.PLAY:
        return f"(Play {action.card_index})"
    if action.type is ActionType.DISCARD:
        return f"(Discard {action.card_index})"
    target = (action.target - actor) % 2
    if target != 1:
        raise ValueError("adapter only supports 2-player target offsets")
    if action.type is ActionType.CLUE_COLOR:
        return f"(Reveal player +1 color {EXTERNAL_TO_HLE[action.color]})"
    return f"(Reveal player +1 rank {action.rank})"


async def run(seed: int, strategy_cls=DistantSavePlayer, pair=None):
    env = hle.hanabi.load_environment(
        num_players=2, mode="sherlock", use_dataset=False, num_games=1,
        seeds=[seed], max_turns=100, judge_model="",
        engine_random_start_player=os.environ.get("HANABI_RANDOM_START", "0") == "1",
        final_score_mode="fireworks")
    state = await env.setup_state({"info": {"seed": seed}, "prompt": []})
    shadow = Shadow(state["hanabi_state"])
    strategies = [strategy_cls(), strategy_cls()] if pair is None else [pair[0](), pair[1]()]
    messages = state["prompt"]
    while True:
        game = state["hanabi_state"]
        if game.is_terminal() or state.get("done") or state.get("turn_count", 0) >= 100:
            break
        actor = game.cur_player()
        obs = shadow.observation(game, actor)
        action = strategies[actor].act(obs)
        move = to_hle_move(action, actor)
        legal = [str(m) for m in game.legal_moves()]
        if move not in legal:
            raise RuntimeError(f"hanabot proposed illegal HLE move {move}; legal={legal}")
        before_hands = [list(hand) for hand in game.player_hands()]
        before_fireworks = list(game.fireworks())
        before_score = game.score()
        messages = list(messages) + [{
            "role": "assistant",
            "content": json.dumps({"action": legal.index(move), "reason": "hanabot convention adapter"}),
        }]
        messages = await env.env_response(messages, state)
        after = state["hanabi_state"]
        shadow.record(before_hands, before_fireworks, before_score, after, actor, move)
    score = state.get("final_score")
    if score is None:
        score = env._compute_score(state["hanabi_state"])
    return {"seed": seed, "score": int(score), "lives": state["hanabi_state"].life_tokens(),
            "turns": state.get("turn_count", 0)}


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--strategy", choices=["chopsave", "critsave", "distsave", "focus", "goodtouch", "tempo", "deduce5", "playclue", "ensemble", "asym_df", "asym_fd"], default="distsave")
    args = parser.parse_args()
    strategy_cls = {"chopsave": ChopSavePlayer, "critsave": CriticalSavePlayer,
                    "distsave": DistantSavePlayer, "focus": FocusPlayer,
                    "goodtouch": GoodTouchPlayer, "tempo": TempoPlayer,
                    "deduce5": DeduceFivePlayer, "playclue": PlayCluePlayer,
                    "ensemble": EnsemblePlayer, "asym_df": DistantSavePlayer,
                    "asym_fd": FocusPlayer}[args.strategy]
    pair = None
    if args.strategy == "asym_df":
        pair = (DistantSavePlayer, FocusPlayer)
    elif args.strategy == "asym_fd":
        pair = (FocusPlayer, DistantSavePlayer)
    rows = [await run(args.seed + i, strategy_cls, pair) for i in range(args.games)]
    scores = [r["score"] for r in rows]
    print(json.dumps({"strategy": args.strategy, "games": len(rows), "mean": sum(scores) / len(scores),
                      "min": min(scores), "max": max(scores),
                      "all_lives": all(r["lives"] == 3 for r in rows),
                      "strikeouts": sum(r["lives"] == 0 for r in rows),
                      "lives_mean": sum(r["lives"] for r in rows) / len(rows)}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
