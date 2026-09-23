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
from dataclasses import replace
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
from hanabi_sim.players.reactor_deduce_player import ReactorEndgamePlayer  # noqa: E402

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
                # HLE keeps the identity field at ``XX`` for partial clues;
                # derive the upstream simulator's ``clued`` flag from whether
                # either marginal candidate set was narrowed.
                views.append(CardView(
                    order=self.orders[player][slot],
                    card=None if player == observer else card_to_external(card),
                    possible_colors=colors,
                    possible_ranks=ranks,
                    clued=(len(colors) < 5 or len(ranks) < 5),
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


class ConservativeEnsemblePlayer:
    def __init__(self):
        self.players = [DistantSavePlayer(), FocusPlayer(), DeduceFivePlayer()]

    def act(self, obs):
        actions = [player.act(obs) for player in self.players]
        if all(action == actions[0] for action in actions[1:]):
            return actions[0]
        plays = [a for a in actions if a.type is ActionType.PLAY]
        for action in plays:
            if obs.known_playable(action.card_index):
                return action
        clues = [a for a in actions if a.is_clue]
        if clues:
            return clues[0]
        return actions[0]


class EndgameGamblePlayer:
    def __init__(self):
        self.base = DistantSavePlayer()

    def act(self, obs):
        action = self.base.act(obs)
        if obs.deck_size > 2 or action.type is ActionType.PLAY:
            return action
        best = None
        for i, view in enumerate(obs.own_hand):
            total = len(view.possible_colors) * len(view.possible_ranks)
            if not total:
                continue
            playable = sum(1 for color in view.possible_colors for rank in view.possible_ranks
                           if rank == obs.play_stacks[color] + 1)
            probability = playable / total
            if best is None or probability > best[0]:
                best = (probability, i)
        if best is not None and best[0] >= 0.45:
            return Action.play(best[1])
        return action


class SafeConventionPlayer:
    """Veto a play that is neither a direct certainty nor a convention call."""
    def __init__(self, base_cls=DistantSavePlayer):
        self.base = base_cls()

    def act(self, obs):
        action = self.base.act(obs)
        if action.type is not ActionType.PLAY:
            return action
        view = obs.own_hand[action.card_index]
        called = self.base._derive_called(obs, obs.player_index)
        if obs.known_playable(action.card_index) or view.order in called:
            return action
        if obs.clue_tokens < obs.max_clue_tokens:
            return self.base._choose_discard(obs)
        return self.base._stall_clue(obs)


class HLEFilteredStallPlayer(DistantSavePlayer):
    """Choose forced clues by simulating the receiver's convention parser."""
    def safe_stall_actions(self, obs):
        candidates = []
        for p in obs.other_players():
            hand = obs.hands[p]
            for color in obs.colors:
                touched = [cv for cv in hand if cv.card.color == color]
                if touched:
                    candidates.append((Action.clue_color(p, color), p, touched))
            for rank in range(1, 6):
                touched = [cv for cv in hand if cv.card.rank == rank]
                if touched:
                    candidates.append((Action.clue_rank(p, rank), p, touched))
        safe = []
        for action, target, touched in candidates:
            record = ActionRecord(turn=obs.log[-1].turn + 1 if obs.log else 0,
                                  player=obs.player_index, action=action,
                                  touched_orders=tuple(cv.order for cv in touched))
            simulated = replace(obs, log=obs.log + (record,))
            called = self._derive_called(simulated, target)
            if not called:
                safe.append(action)
                continue
            actual = {cv.order: cv.card for cv in touched}
            if all(obs.is_playable(actual[order]) for order in called if order in actual):
                safe.append(action)
        return safe

    def _stall_clue(self, obs):
        safe = self.safe_stall_actions(obs)
        if safe:
            return safe[0]
        return super()._stall_clue(obs)



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
    jev_key = os.environ.get("JEV_API_KEY")
    while True:
        game = state["hanabi_state"]
        if game.is_terminal() or state.get("done") or state.get("turn_count", 0) >= 100:
            break
        actor = game.cur_player()
        obs = shadow.observation(game, actor)
        action = strategies[actor].act(obs)
        move = to_hle_move(action, actor)
        legal = [str(m) for m in game.legal_moves()]
        if (os.environ.get("HANABOT_JEV_STALLS", "0") == "1"
                and jev_key and obs.clue_tokens == obs.max_clue_tokens
                and action.is_clue):
            clue_indices = [i for i, candidate in enumerate(legal)
                            if candidate.startswith("(Reveal")]
            if hasattr(strategies[actor], "safe_stall_actions"):
                safe_actions = strategies[actor].safe_stall_actions(obs)
                safe_moves = {to_hle_move(a, actor) for a in safe_actions}
                filtered = [i for i in clue_indices if legal[i] in safe_moves]
                if filtered:
                    clue_indices = filtered
                if os.environ.get("HANABOT_JEV_EQUIV_ONLY", "0") == "1" and len(filtered) > 1:
                    # Let JEV break ties only within protocol-equivalent clues:
                    # same target, clue kind, and touched card orders.
                    groups = {}
                    for i in filtered:
                        candidate = legal[i]
                        target = (actor + 1) % 2
                        touched = tuple(shadow.orders[target][slot]
                                        for slot, card in enumerate(game.player_hands()[target])
                                        if (("color" in candidate and "RYGWB"[card.color()] == candidate[-2])
                                            or ("rank" in candidate and card.rank() + 1 == int(candidate.split()[-1][:-1]))))
                        kind = "color" if " color " in candidate else "rank"
                        groups.setdefault((target, kind, touched), []).append(i)
                    largest = max(groups.values(), key=len)
                    if len(largest) > 1:
                        clue_indices = largest
                if len(clue_indices) > 1:
                    baseline_move = to_hle_move(action, actor)
                    clue_indices.sort(key=lambda i: legal[i] != baseline_move)
            if len(clue_indices) > 1:
                signals = hle.guaranteed_plays_after_clues(game, 2, legal)
                values = hle.clue_information_values(game, 2, legal)
                selected, _audit = hle.request_jev(
                    state["full_prompt_before_move"], legal, jev_key,
                    clue_indices, signals, None, values,
                    recommended_index=legal.index(move))
                move = legal[selected]
        if move not in legal:
            raise RuntimeError(f"hanabot proposed illegal HLE move {move}; legal={legal}")
        if os.environ.get("HANABOT_TRACE", "0") == "1":
            actual = [f"RYGWB[{c.color()}]{c.rank()+1}" for c in game.player_hands()[actor]]
            views = [(v.order, sorted(x.value for x in v.possible_colors), sorted(v.possible_ranks), v.clued) for v in obs.own_hand]
            raw = hle.extract_knowledge(game, actor, 2)
            partner_actual = [[c.color(), c.rank() + 1] for c in game.player_hands()[(actor + 1) % 2]]
            partner_views = [(v.card, obs.is_playable(v.card) if v.card is not None else None) for v in obs.hands[(actor + 1) % 2]]
            print(f"seed={seed} turn={state.get('turn_count', 0)} actor={actor} move={move} score={game.score()} stacks={game.fireworks()} lives={game.life_tokens()} actual={actual} partner={partner_actual} partner_views={partner_views} raw={raw} views={views}", file=sys.stderr)
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
    parser.add_argument("--strategy", choices=["chopsave", "critsave", "distsave", "focus", "goodtouch", "tempo", "deduce5", "playclue", "ensemble", "conservative_ensemble", "endgame_gamble", "safe_distsave", "filtered_stall", "reactor_endgame", "asym_df", "asym_fd"], default="distsave")
    args = parser.parse_args()
    strategy_cls = {"chopsave": ChopSavePlayer, "critsave": CriticalSavePlayer,
                    "distsave": DistantSavePlayer, "focus": FocusPlayer,
                    "goodtouch": GoodTouchPlayer, "tempo": TempoPlayer,
                    "deduce5": DeduceFivePlayer, "playclue": PlayCluePlayer,
                    "ensemble": EnsemblePlayer, "conservative_ensemble": ConservativeEnsemblePlayer,
                    "endgame_gamble": EndgameGamblePlayer,
                    "asym_df": DistantSavePlayer,
                    "asym_fd": FocusPlayer, "safe_distsave": SafeConventionPlayer,
                    "filtered_stall": HLEFilteredStallPlayer,
                    "reactor_endgame": ReactorEndgamePlayer}[args.strategy]
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
