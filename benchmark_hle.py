#!/usr/bin/env python3
"""Evaluate JEV in the paper authors' public Hanabi HLE environment."""
from __future__ import annotations

import asyncio
from collections import Counter
import hashlib
import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.request
from statistics import median
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAPER_ENV = ROOT / "paper_env"
sys.path.insert(0, str(PAPER_ENV))

import hanabi  # noqa: E402
from hanabi_prompts import WATSON_SYSTEM_PROMPT  # noqa: E402
from hanabi_utils import extract_knowledge  # noqa: E402

API = "https://api.typesafe.ai/v1/systemone"
MODEL = os.environ.get("HANABI_MODEL", "jev-latest")
SEEDS = [int(x) for x in os.environ.get("HANABI_SEEDS", "0,1,2,3,4,5,6,7,8,9").split(",")]
OUT = Path(os.environ.get("HANABI_OUTDIR", str(ROOT / "results/runs/results_hle_watson")))
MODE = os.environ.get("HANABI_MODE", "watson")
PROMPT_VARIANT = os.environ.get("HANABI_PROMPT_VARIANT", "legacy")
PLAYERS = 2
BAYES_MIN_PLAY_PROBABILITY = float(os.environ.get("HANABI_BAYES_MIN_PLAY_PROBABILITY", "0.90"))
FORCE_PLAY_PROBABILITY = float(os.environ.get("HANABI_FORCE_PLAY_PROBABILITY", "0.75"))
SCORE_RISK_PENALTY = float(os.environ.get("HANABI_SCORE_RISK_PENALTY", "0"))
MIN_SIGNAL_SLOTS = int(os.environ.get("HANABI_MIN_SIGNAL_SLOTS", "1"))
ACTION_FRONTIER = os.environ.get("HANABI_ACTION_FRONTIER", "0") == "1"
FRONTIER_MAX_CLUES = int(os.environ.get("HANABI_FRONTIER_MAX_CLUES", "4"))
USE_POSTERIOR_CERTAIN_PLAYS = os.environ.get("HANABI_USE_POSTERIOR_CERTAIN_PLAYS", "0") == "1"
ENGINE = "hanabi-learning-environment-mahesh==0.0.2"
ENV_VERSION_ID = "nees3rw1f786tt0ojf1ef9m9"
SOURCE_FILES = ["hanabi.py", "pyproject.toml", "src/hanabi_observations.py",
                "src/hanabi_prompts.py", "src/hanabi_parsers.py", "src/hanabi_utils.py"]
PUBLISHED_WATSON_2P = {
    "GPT-4.1 mini": 10.8,
    "GPT-4.1": 12.1,
    "DeepSeek-R1": 14.2,
    "o4-mini": 15.0,
    "o3": 15.9,
}
PUBLISHED_SHERLOCK_2P = {
    "GPT-4.1 mini": 6.5,
    "GPT-4.1": 14.8,
    "DeepSeek-R1": 17.5,
    "o4-mini": 14.6,
    "o3": 17.6,
}


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_results_integrity(path: Path) -> dict:
    """Commit to JSONL rows as well as the whole result file."""
    entries = []
    whole_file_hash = hashlib.sha256()
    total_bytes = 0
    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, 1):
            whole_file_hash.update(raw_line)
            total_bytes += len(raw_line)
            if not raw_line.strip():
                entries.append({"line": line_number, "seed": None,
                                "bytes": len(raw_line), "sha256": sha256(raw_line)})
                continue
            game = json.loads(raw_line)
            entries.append({"line": line_number, "seed": game.get("seed"),
                            "bytes": len(raw_line), "sha256": sha256(raw_line)})
    root = sha256("\n".join(entry["sha256"] for entry in entries).encode())
    digest = whole_file_hash.hexdigest()
    if total_bytes and digest == sha256(b""):
        digest = None
    return {
        "source_file": path.name,
        "source_bytes": total_bytes,
        "source_lines": len(entries),
        "whole_file_sha256": digest,
        "whole_file_hash_note": ("Whole-file SHA-256 unavailable; use line hashes and root."
                                 if digest is None else None),
        "line_hash_definition": "SHA-256 of each exact raw JSONL line, including its line terminator.",
        "root_definition": "SHA-256 of UTF-8 lowercase line digests joined by LF, without trailing LF.",
        "line_hash_root": root,
        "line_hashes": entries,
    }


def adapt_sherlock_prompt_for_jev(prompt: str) -> str:
    """Keep the paper's Sherlock reasoning instructions, adapt only its output format."""
    output_start = "Your output should be in this format:"
    probability_start = "Calculate the probability of each card in your hand"
    if output_start not in prompt or probability_start not in prompt:
        raise ValueError("Sherlock prompt format changed; cannot safely adapt its output section")
    before, remainder = prompt.split(output_start, 1)
    _discarded_output_schema, after = remainder.split(probability_start, 1)
    before = before.replace(
        "Then, output one of the legal action descriptions as your chosen action.",
        "Evaluate the legal actions using the game state and the reasoning guidance below.",
    )
    return (before + "Use the structured JEV answer interface to select or rate the legal action(s). "
            "Do not generate a JSON object or free-form response.\n\n"
            + probability_start + after)


def adapt_mycroft_prompt_for_jev(prompt: str) -> str:
    """Preserve Mycroft's state tracking and override only its output channel."""
    return (prompt + "\n\nUse the structured JEV answer interface for the action. Do not emit the "
            "Mycroft JSON object or a free-form action; select the legal action through the typed interface.")


def clue_information_values(game_state, num_players: int, legal_moves: list[str]):
    """Estimate how much each legal clue narrows the recipient's card domains.

    This is descriptive only. It applies Hanabi's public clue operation to the
    recipient's current possibility sets and reports matched-card count plus a
    log-domain reduction for JEV's action comparison.
    """
    import math
    import re
    player = game_state.cur_player()
    values = {}
    for index, move in enumerate(legal_moves):
        match = re.fullmatch(r"\(Reveal player \+(\d+) (color|rank) (\w+)\)", move)
        if not match:
            continue
        offset, kind, value = match.groups()
        target = (player + int(offset)) % num_players
        knowledge = extract_knowledge(game_state, target, num_players)
        matched = 0
        old_mass = 0.0
        new_mass = 0.0
        for slot, entry in enumerate(knowledge):
            identity, rest = entry.split("||", 1)
            _known, possibilities = rest.split("|", 1)
            possible_colors = {c for c in "RYGWB" if c in possibilities}
            possible_ranks = {int(r) for r in "12345" if r in possibilities}
            old_count = max(1, len(possible_colors) * len(possible_ranks))
            actual = game_state.player_hands()[target][slot]
            actual_color = "RYGWB"[actual.color()]
            actual_rank = actual.rank() + 1
            if (kind == "color" and actual_color == value) or (kind == "rank" and actual_rank == int(value)):
                matched += 1
            if kind == "color":
                if actual_color == value:
                    possible_colors &= {value}
                else:
                    possible_colors.discard(value)
            else:
                if actual_rank == int(value):
                    possible_ranks &= {int(value)}
                else:
                    possible_ranks.discard(int(value))
            new_count = max(1, len(possible_colors) * len(possible_ranks))
            old_mass += math.log2(old_count)
            new_mass += math.log2(new_count)
        reduction = max(0.0, old_mass - new_mass)
        relative = reduction / old_mass if old_mass > 0 else 0.0
        values[index] = {"matched_cards": matched,
                         "bits_reduction": reduction,
                         "relative_reduction": relative}
    return values


def action_frontier_indices(legal_moves, candidate_indices, safe_plays,
                            clue_signal_slots, clue_values, play_probabilities):
    """Keep a small Pareto frontier of useful clues plus the safest discard.

    This is an opt-in action-space reduction. It does not invent actions or
    override the guaranteed-play gate; it only removes dominated no-safe-play
    alternatives before JEV scores them.
    """
    if safe_plays:
        return list(safe_plays), {}
    clue_indices = [i for i in candidate_indices if legal_moves[i].startswith("(Reveal")]
    discard_indices = [i for i in candidate_indices if legal_moves[i].startswith("(Discard")]
    frontier_values = {}
    clue_vectors = {}
    for i in clue_indices:
        info = clue_values.get(i, {}) if clue_values else {}
        slots = len((clue_signal_slots or {}).get(i, []))
        vector = (slots, info.get("bits_reduction", 0.0),
                  info.get("matched_cards", 0))
        clue_vectors[i] = vector
        frontier_values[i] = {"guaranteed_plays": slots,
                              "bits_reduction": vector[1],
                              "matched_cards": vector[2],
                              "rollout_slot": min((clue_signal_slots or {}).get(i, [0]))
                              if slots else None}
    frontier_clues = []
    for i, vector in clue_vectors.items():
        dominated = any(
            all(other[j] >= vector[j] for j in range(3))
            and any(other[j] > vector[j] for j in range(3))
            for j, other in clue_vectors.items() if j != i)
        if not dominated:
            frontier_clues.append(i)
    frontier_clues.sort(key=lambda i: clue_vectors[i], reverse=True)
    frontier_clues = frontier_clues[:max(1, FRONTIER_MAX_CLUES)]

    retained_discard = None
    if discard_indices:
        def discard_probability(index):
            slot = int(legal_moves[index].removeprefix("(Discard ").removesuffix(")"))
            play_index = next((j for j, move in enumerate(legal_moves)
                               if move == f"(Play {slot})"), None)
            return play_probabilities.get(play_index, 0.0) if play_index is not None else 0.0
        retained_discard = min(discard_indices, key=discard_probability)
        frontier_values[retained_discard] = {"play_probability": discard_probability(retained_discard)}
    retained = frontier_clues + ([retained_discard] if retained_discard is not None else [])
    return (retained if retained else list(candidate_indices)), frontier_values


def describe_move(index: int, move: str, clue_signal_slots=None,
                  play_probabilities=None, legal_moves=None, clue_values=None,
                  frontier_values=None) -> str:
    if move.startswith("(Play "):
        slot = move.removeprefix("(Play ").removesuffix(")")
        description = f"Action {index}: Play the card in your hand slot {slot}."
        if play_probabilities is not None and index in play_probabilities:
            description += (f" Estimated success chance from the remaining unseen card copies: "
                            f"{play_probabilities[index]:.0%} (joint belief over your clue-compatible hand).")
            if os.environ.get("HANABI_NUMERIC_ACTION_VALUES", "0") == "1":
                probability = play_probabilities[index]
                description += (f" Approximate immediate score contribution is {probability:.2f} points; "
                                f"failure risk is {1.0 - probability:.0%}.")
        return description
    if move.startswith("(Discard "):
        slot = move.removeprefix("(Discard ").removesuffix(")")
        description = (f"Action {index}: Discard the card in your hand slot {slot}; "
                       "regain an information token if possible.")
        if (legal_moves is not None and play_probabilities is not None
                and os.environ.get("HANABI_NUMERIC_ACTION_VALUES", "0") == "1"):
            try:
                play_index = next(i for i, candidate in enumerate(legal_moves)
                                  if candidate == f"(Play {slot})")
            except StopIteration:
                play_index = None
            if play_index is not None and play_index in play_probabilities:
                description += (f" The discarded slot has {play_probabilities[play_index]:.0%} "
                                "joint posterior chance of being playable now; treat that as "
                                "the approximate immediate point value being discarded.")
        if frontier_values is not None and index in frontier_values:
            value = frontier_values[index]
            description += (f" Frontier features: posterior play probability "
                            f"{value['play_probability']:.0%}; this is the safest retained discard.")
        return description
    if move.startswith("(Reveal "):
        import re
        match = re.fullmatch(r"\(Reveal player \+(\d+) (color|rank) (\w+)\)", move)
        if match:
            offset, kind, value = match.groups()
            colors = {"R": "red", "Y": "yellow", "G": "green", "W": "white", "B": "blue"}
            desc = colors.get(value, value) if kind == "color" else value
            noun = "color" if kind == "color" else "rank"
            description = (f"Action {index}: Give the player {offset} seat(s) ahead a {desc} {noun} clue; "
                           f"it identifies every matching card in their hand and costs one information token.")
            if clue_signal_slots is not None:
                slots = clue_signal_slots.get(index, [])
                if slots:
                    listed = ", ".join(str(slot) for slot in slots)
                    description += (f" This clue would make the card(s) in recipient slot(s) {listed} "
                                   "guaranteed playable on their next turn.")
                    if os.environ.get("HANABI_NUMERIC_ACTION_VALUES", "0") == "1":
                        description += (f" The recipient has {len(slots)} guaranteed-play option(s) "
                                        "on that turn; because the recipient takes one action, the "
                                        "immediate score opportunity is at most 1 point, before later "
                                        "information effects.")
                else:
                    description += " This clue would not make any recipient card guaranteed playable immediately."
                    if os.environ.get("HANABI_NUMERIC_ACTION_VALUES", "0") == "1":
                        description += " Approximate immediate score opportunity: 0 points."
            if frontier_values is not None and index in frontier_values:
                value = frontier_values[index]
                description += (f" Frontier features: {value['guaranteed_plays']} guaranteed next-turn "
                                f"play(s), {value['bits_reduction']:.2f} bits of possibility reduction, "
                                f"{value['matched_cards']} matched card(s).")
                if value['guaranteed_plays']:
                    description += (f" Two-action rollout: the recipient should play slot "
                                    f"{value['rollout_slot']} next, yielding one immediate point "
                                    "before the subsequent state update.")
            if (clue_values is not None
                    and os.environ.get("HANABI_NUMERIC_CLUE_VALUES", "0") == "1"
                    and index in clue_values):
                value = clue_values[index]
                description += (f" Information value: matches {value['matched_cards']} card(s) and "
                                f"narrows the recipient's possibility mass by approximately "
                                f"{value['relative_reduction']:.0%} ({value['bits_reduction']:.2f} bits).")
            return description
    return f"Action {index}: {move}"


def request_jev(prompt: str, legal_moves: list[str], key: str, candidate_indices=None,
                clue_signal_slots=None, play_probabilities=None, clue_values=None,
                frontier_values=None):
    if candidate_indices is None:
        candidate_indices = list(range(len(legal_moves)))
    if PROMPT_VARIANT in {"clean_choice", "action_scores", "paper_mycroft_choice", "paper_mycroft_signal_score", "paper_sherlock_choice", "paper_sherlock_score", "paper_sherlock_signal_choice", "paper_sherlock_signal_score", "paper_sherlock_bayes_choice", "paper_sherlock_bayes_score", "safe_sherlock_choice", "safe_gate_sherlock", "signal_gate_sherlock", "signal_priority_sherlock", "signal_protocol_sherlock", "bayes_protocol_sherlock"}:
        if PROMPT_VARIANT in {"paper_sherlock_choice", "paper_sherlock_score", "paper_sherlock_signal_choice", "paper_sherlock_signal_score", "paper_sherlock_bayes_choice", "paper_sherlock_bayes_score"} and MODE != "sherlock":
            raise ValueError(f"{PROMPT_VARIANT} requires HANABI_MODE=sherlock")
        if PROMPT_VARIANT in {"paper_mycroft_choice", "paper_mycroft_signal_score"} and MODE != "mycroft":
            raise ValueError(f"{PROMPT_VARIANT} requires HANABI_MODE=mycroft")
        if PROMPT_VARIANT in {"safe_sherlock_choice", "safe_gate_sherlock", "signal_gate_sherlock", "signal_priority_sherlock", "signal_protocol_sherlock", "bayes_protocol_sherlock"} and MODE != "sherlock":
            raise ValueError(f"{PROMPT_VARIANT} requires HANABI_MODE=sherlock")
        if PROMPT_VARIANT in {"paper_sherlock_choice", "paper_sherlock_score"}:
            # Use the exact engine move strings; adapt the paper's free-form
            # response schema to JEV's typed decision interface below.
            choices = {f"move_{i}": f"Action {i}: {legal_moves[i]}"
                       for i in candidate_indices}
        else:
            choices = {f"move_{i}": describe_move(i, legal_moves[i], clue_signal_slots,
                                                     play_probabilities, legal_moves, clue_values,
                                                     frontier_values)
                       for i in candidate_indices}
        if MODE == "watson":
            strategy = WATSON_SYSTEM_PROMPT.split("\nExplain your reasoning clearly", 1)[0]
            observation = prompt.split("\nOutput Format:", 1)[0]
        elif MODE == "sherlock":
            if PROMPT_VARIANT in {"paper_sherlock_choice", "paper_sherlock_score", "paper_sherlock_signal_choice", "paper_sherlock_signal_score", "paper_sherlock_bayes_choice", "paper_sherlock_bayes_score"}:
                strategy = ""
                observation = adapt_sherlock_prompt_for_jev(prompt)
            elif PROMPT_VARIANT in {"safe_sherlock_choice", "safe_gate_sherlock", "signal_gate_sherlock", "signal_priority_sherlock", "signal_protocol_sherlock", "bayes_protocol_sherlock"}:
                strategy = (
                    "Hanabi is cooperative; maximize the team's final fireworks score. Use the per-card possibility "
                    "sets, visible teammate hands, fireworks, discards, and clue history. Risk policy: play a card "
                    "only when every identity still possible for that slot is playable now. An unsafe play can cost a "
                    "life and end the game, so do not gamble while a safe clue or discard is available. If there is "
                    "no guaranteed playable card in your hand, prefer a clue that makes a teammate's card "
                    "guaranteed playable on their next turn, or preserves a critical card; avoid repeating "
                    "information they already have. Treat a clue that makes a card guaranteed playable as an "
                    "intentional play signal and take that safe play on your next turn, unless the fireworks have "
                    "changed in the meantime. "
                    "Otherwise discard a card unlikely to be needed, protecting unique critical copies."
                )
                if PROMPT_VARIANT == "bayes_protocol_sherlock":
                    strategy = (
                        "Hanabi is cooperative. Use Sherlock's per-card possibility sets and the exact remaining "
                        "card counts to reason jointly over all cards in your hidden hand. If a play has posterior "
                        "success probability 100%, take a certain play before clues or discards. Otherwise, plays "
                        f"with at least {BAYES_MIN_PLAY_PROBABILITY:.0%} posterior success are eligible risks; compare the point they can score "
                        "against losing a life and card. These probabilities condition on all your card-slot "
                        "possibilities and public visible hands, discards, and fireworks. Prefer a clue that creates "
                        "a certain play for the teammate when no eligible play is better, then discard a card "
                        "unlikely to be needed while protecting critical copies."
                    )
                if PROMPT_VARIANT in {"signal_priority_sherlock", "signal_protocol_sherlock"}:
                    strategy += (
                        "\nDecision priority: if any guaranteed-safe play is available, choose one before any clue "
                        "or discard. Prefer a play that scores a point. If no guaranteed-safe play is available, "
                        "prefer a clue whose description says it creates a guaranteed play for the teammate."
                    )
            elif PROMPT_VARIANT in {"paper_mycroft_choice", "paper_mycroft_signal_score"}:
                strategy = ""
                observation = adapt_mycroft_prompt_for_jev(prompt)
            else:
                strategy = ("Hanabi is cooperative. Use the per-card possibility sets in the state, visible teammate cards, "
                            "fireworks, discards, and clue history to assess risks and signaling value.")
            if PROMPT_VARIANT not in {"paper_mycroft_choice", "paper_sherlock_choice", "paper_sherlock_score", "paper_sherlock_signal_choice", "paper_sherlock_signal_score", "paper_sherlock_bayes_choice", "paper_sherlock_bayes_score"}:
                observation = prompt.split("\nPlease think step by step", 1)[0]
        elif MODE == "mycroft" and PROMPT_VARIANT in {"paper_mycroft_choice", "paper_mycroft_signal_score"}:
            strategy = ""
            observation = adapt_mycroft_prompt_for_jev(prompt)
        else:
            raise ValueError(f"Prompt variant {PROMPT_VARIANT} does not support mode {MODE}")
        if PROMPT_VARIANT in {"paper_mycroft_choice", "paper_mycroft_signal_score", "paper_sherlock_choice", "paper_sherlock_score", "paper_sherlock_signal_choice", "paper_sherlock_signal_score", "paper_sherlock_bayes_choice", "paper_sherlock_bayes_score"}:
            if PROMPT_VARIANT in {"paper_sherlock_score", "paper_sherlock_signal_score", "paper_sherlock_bayes_score", "paper_mycroft_signal_score"}:
                interface_note = ("The independent JEV Score questions below each rate one legal-action index "
                                  "from the mapping above. Apply the full instructions to each action.")
            else:
                interface_note = ("The structured JEV Choice options below correspond exactly to the legal-action "
                                  "indices above. Select the action you judge best after applying the full instructions above.")
            state = observation + "\n\n" + interface_note
        else:
            state = (strategy + "\n\n" + observation + "\n\n"
                     "Choose the single legal action that best maximizes your team's final fireworks score. "
                     "Account for the current card knowledge, public history, information tokens, and how a clue signals intent.")
        if PROMPT_VARIANT in {"clean_choice", "paper_mycroft_choice", "paper_mycroft_signal_score", "paper_sherlock_choice", "paper_sherlock_score", "paper_sherlock_signal_choice", "paper_sherlock_signal_score", "paper_sherlock_bayes_choice", "paper_sherlock_bayes_score", "safe_sherlock_choice", "safe_gate_sherlock", "signal_gate_sherlock", "signal_priority_sherlock", "signal_protocol_sherlock", "bayes_protocol_sherlock"}:
            instructions = "Which single legal action best advances the team toward the highest final fireworks score?"
            if PROMPT_VARIANT in {"signal_priority_sherlock", "signal_protocol_sherlock"}:
                instructions = (
                    "Use this priority order: first choose a guaranteed-safe Play action if one is offered; "
                    "otherwise prefer a clue described as creating a guaranteed play for the teammate; "
                    "otherwise choose a useful discard."
                )
            elif PROMPT_VARIANT == "bayes_protocol_sherlock":
                instructions = (
                    "If a 100% certain Play is offered, choose one. Otherwise compare offered Play actions with "
                    f"at least {BAYES_MIN_PLAY_PROBABILITY:.0%} joint posterior success against clues that create a certain teammate play and "
                    "useful discards; consider both score gain and life/card risk."
                )
            elif PROMPT_VARIANT in {"paper_sherlock_bayes_choice", "paper_sherlock_bayes_score"}:
                instructions = (
                    "Choose among the offered legal actions. A Play description includes its joint posterior success "
                    f"probability. Treat plays at or above {BAYES_MIN_PLAY_PROBABILITY:.0%} as eligible risks; weigh "
                    "their expected score against life and card loss, and prefer a certain play when offered."
                )
            if PROMPT_VARIANT in {"paper_mycroft_signal_score", "paper_sherlock_score", "paper_sherlock_signal_score", "paper_sherlock_bayes_score"}:
                score_levels = [
                    "-1: harmful; likely loses a life or essential card with little gain.",
                    "-0.5: poor; risky, wasteful, or low value.",
                    "0: neutral or mixed; plausible benefit with meaningful opportunity cost.",
                    "+0.5: good; likely advances the team safely toward more points.",
                    "+1: excellent; scores safely now or creates a highly reliable, high-value play.",
                ]
                questions = {
                    name: {
                        "type": "score",
                        "instructions": (f"Rate the expected effect on final team score of taking exactly this action now: {description} "
                                         "Use the complete Sherlock state and probability guidance above."),
                        "criteria": score_levels,
                    }
                    for name, description in choices.items()
                }
            else:
                questions = {"action": {
                    "type": "choice",
                    "instructions": instructions,
                    "criteria": choices,
                }}
        else:
            levels = [
                "Very harmful: likely loses a life or irreversibly loses an essential card, with little benefit.",
                "Poor: risky or wasteful; expected to help the team very little.",
                "Mixed: some possible benefit, but substantial risk or opportunity cost.",
                "Good: likely safe and useful for increasing the team's final score.",
                "Excellent: safely scores a card now or creates a highly reliable, high-value team play.",
            ]
            questions = {
                key_name: {
                    "type": "score",
                    "instructions": (f"Rate the strategic value of taking this exact action now: {description} "
                                     "Judge expected impact on the team's final fireworks score."),
                    "criteria": levels,
                }
                for key_name, description in choices.items()
            }
    elif PROMPT_VARIANT == "legacy":
        choices = {str(i): f"{legal_moves[i]}" for i in candidate_indices}
        state = WATSON_SYSTEM_PROMPT + "\n\n" + prompt + "\n\nSelect exactly one legal move. Choose its numbered index from the list."
        questions = {"action": {
            "type": "choice",
            "instructions": "Which legal move should you choose? Return the index of the selected move.",
            "criteria": choices,
        }}
    else:
        raise ValueError(f"Unknown HANABI_PROMPT_VARIANT: {PROMPT_VARIANT}")
    payload = {
        "model": MODEL,
        "state": state,
        "questions": questions,
    }
    request = urllib.request.Request(API, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    started = time.perf_counter()
    for attempt in range(8):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.loads(response.read().decode())
            break
        except urllib.error.HTTPError as exc:
            if (exc.code < 500 and exc.code != 429) or attempt == 7:
                raise
            wait_seconds = min(2 ** (attempt + 1), 60)
            print(f"JEV HTTP {exc.code}; retry {attempt + 1}/7 in {wait_seconds}s", flush=True)
            time.sleep(wait_seconds)
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.RemoteDisconnected) as exc:
            if attempt == 7:
                raise
            wait_seconds = min(2 ** (attempt + 1), 60)
            print(f"JEV network error {exc}; retry {attempt + 1}/7 in {wait_seconds}s", flush=True)
            time.sleep(wait_seconds)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    if PROMPT_VARIANT in {"action_scores", "paper_sherlock_score", "paper_sherlock_signal_score", "paper_sherlock_bayes_score", "paper_mycroft_signal_score"}:
        action_scores = {}
        for name, answer in result["answers"].items():
            score = float(answer["score"])
            if SCORE_RISK_PENALTY:
                probabilities = answer.get("probabilities", {})
                harmful_probability = float(probabilities.get("0", 0.0))
                score -= SCORE_RISK_PENALTY * harmful_probability * 4.0
            action_scores[int(name.removeprefix("move_"))] = score
        index = max(action_scores, key=action_scores.get)
        choice = f"move_{index}"
    else:
        choice = result["answers"]["action"]["choice"]
        index = int(choice.removeprefix("move_"))
    if index < 0 or index >= len(legal_moves):
        raise ValueError(f"JEV chose out-of-range move {choice}; {len(legal_moves)} legal moves")
    audit = {
        "prompt": prompt,
        "prompt_sha256": sha256(prompt.encode()),
        "legal_moves": legal_moves,
        "request": payload,
        "response": result,
        "choice": choice,
        "latency_ms": elapsed_ms,
    }
    return index, audit


def guaranteed_play_indices(game_state, num_players: int, legal_moves: list[str]):
    """Return play indices safe for every card identity consistent with clues."""
    player = game_state.cur_player()
    knowledge = extract_knowledge(game_state, player, num_players)
    fireworks = game_state.fireworks()
    colors = "RYGWB"
    safe, unsafe = [], []
    for index, move in enumerate(legal_moves):
        if not move.startswith("(Play "):
            continue
        slot = int(move.removeprefix("(Play ").removesuffix(")"))
        _hidden, rest = knowledge[slot].split("||", 1)
        _known, possibilities = rest.split("|", 1)
        possible_colors = [c for c in colors if c in possibilities]
        possible_ranks = [int(r) for r in "12345" if r in possibilities]
        is_guaranteed = bool(possible_colors and possible_ranks) and all(
            rank == fireworks[colors.index(color)] + 1
            for color in possible_colors for rank in possible_ranks
        )
        (safe if is_guaranteed else unsafe).append(index)
    return safe, unsafe


def guaranteed_plays_after_clues(game_state, num_players: int, legal_moves: list[str]):
    """For each clue, report target slots made guaranteed playable by that clue.

    The clue giver can see the target hand in Hanabi. We apply the public clue
    rule to the target's existing possibility sets, without consulting the
    acting player's hidden cards.
    """
    import re
    player = game_state.cur_player()
    fireworks = game_state.fireworks()
    knowledge_by_target = {}
    result = {}
    for index, move in enumerate(legal_moves):
        match = re.fullmatch(r"\(Reveal player \+(\d+) (color|rank) (\w+)\)", move)
        if not match:
            continue
        offset, kind, value = match.groups()
        target = (player + int(offset)) % num_players
        knowledge = knowledge_by_target.setdefault(
            target, extract_knowledge(game_state, target, num_players))
        touched = []
        for slot, entry in enumerate(knowledge):
            identity, rest = entry.split("||", 1)
            _known, possibilities = rest.split("|", 1)
            identity = identity.strip()
            clue_matches = identity[0] == value if kind == "color" else identity[1] == value
            possible_colors = set(c for c in "RYGWB" if c in possibilities)
            possible_ranks = set(r for r in "12345" if r in possibilities)
            if clue_matches:
                touched.append(slot)
                if kind == "color":
                    possible_colors &= {value}
                else:
                    possible_ranks &= {value}
            elif kind == "color":
                possible_colors.discard(value)
            else:
                possible_ranks.discard(value)
            if possible_colors and possible_ranks and all(
                int(rank) == fireworks["RYGWB".index(color)] + 1
                for color in possible_colors for rank in possible_ranks
            ):
                result.setdefault(index, []).append(slot)
        # Preserve an explicit empty annotation for candidate clues without a
        # newly guaranteed play, so the Choice criteria stay comparable.
        result.setdefault(index, [])
    return result


def joint_play_probabilities(game_state, num_players: int, legal_moves: list[str]):
    """Return play probabilities conditioned jointly on all hidden hand slots.

    Remaining physical copies are the acting player's hand plus the deck after
    removing visible teammate hands, discards, and played fireworks. For each
    slot assignment, the dynamic program weights choices by the falling
    factorial of remaining copies, so duplicate-card competition across the
    acting player's own slots is included.
    """
    player = game_state.cur_player()
    fireworks = game_state.fireworks()
    counts = {}
    for color in "RYGWB":
        for rank in range(1, 6):
            counts[(color, rank)] = 3 if rank == 1 else (1 if rank == 5 else 2)
    for other_player, hand in enumerate(game_state.player_hands()):
        if other_player == player:
            continue
        for card in hand:
            counts[("RYGWB"[card.color()], card.rank() + 1)] -= 1
    for card in game_state.discard_pile():
        counts[("RYGWB"[card.color()], card.rank() + 1)] -= 1
    for color_index, top_rank in enumerate(fireworks):
        color = "RYGWB"[color_index]
        for rank in range(1, top_rank + 1):
            counts[(color, rank)] -= 1
    if min(counts.values()) < 0:
        raise ValueError("Public cards exceed the standard Hanabi deck counts")

    knowledge = extract_knowledge(game_state, player, num_players)
    domains = []
    for entry in knowledge:
        _hidden, rest = entry.split("||", 1)
        _known, possibilities = rest.split("|", 1)
        domains.append((
            {color for color in "RYGWB" if color in possibilities},
            {rank for rank in range(1, 6) if str(rank) in possibilities},
        ))

    hand_size = len(domains)
    mask_count = 1 << hand_size
    full_mask = mask_count - 1
    totals = [0.0] * mask_count
    totals[0] = 1.0
    playable_totals = [[0.0] * mask_count for _ in range(hand_size)]

    for color in "RYGWB":
        color_index = "RYGWB".index(color)
        for rank in range(1, 6):
            copies = counts[(color, rank)]
            if copies == 0:
                continue
            allowed_mask = 0
            for slot, (possible_colors, possible_ranks) in enumerate(domains):
                if color in possible_colors and rank in possible_ranks:
                    allowed_mask |= 1 << slot
            if not allowed_mask:
                continue

            is_playable = rank == fireworks[color_index] + 1
            next_totals = [0.0] * mask_count
            next_playable = [[0.0] * mask_count for _ in range(hand_size)]
            for assigned_mask in range(mask_count):
                available_mask = allowed_mask & (full_mask ^ assigned_mask)
                subset = available_mask
                while True:
                    assigned_copies = bin(subset).count("1")
                    if assigned_copies <= copies:
                        weight = 1.0
                        for offset in range(assigned_copies):
                            weight *= copies - offset
                        destination = assigned_mask | subset
                        assignment_weight = totals[assigned_mask] * weight
                        next_totals[destination] += assignment_weight
                        for slot in range(hand_size):
                            next_playable[slot][destination] += (
                                playable_totals[slot][assigned_mask] * weight)
                            if is_playable and subset & (1 << slot):
                                next_playable[slot][destination] += assignment_weight
                    if subset == 0:
                        break
                    subset = (subset - 1) & available_mask
            totals = next_totals
            playable_totals = next_playable

    assignment_total = totals[full_mask]
    if assignment_total <= 0:
        raise ValueError("No physical card assignment is consistent with the Sherlock knowledge")
    slot_probabilities = [playable_totals[slot][full_mask] / assignment_total
                          for slot in range(hand_size)]
    probabilities = {}
    for index, move in enumerate(legal_moves):
        if move.startswith("(Play "):
            slot = int(move.removeprefix("(Play ").removesuffix(")"))
            probabilities[index] = slot_probabilities[slot]
    return probabilities


async def play(seed: int, key: str):
    env = hanabi.load_environment(
        num_players=PLAYERS, mode=MODE, use_dataset=False, num_games=1, seeds=[seed],
        max_turns=100, judge_model="", engine_random_start_player=False, final_score_mode="fireworks")
    state = {"info": {"seed": seed}, "prompt": []}
    state = await env.setup_state(state)
    messages = state["prompt"]
    decisions = []

    while True:
        game_state = state["hanabi_state"]
        if game_state.is_terminal() or state.get("done") or state.get("turn_count", 0) >= 100:
            break
        prompt = state["full_prompt_before_move"]
        legal_moves = [str(move) for move in game_state.legal_moves()]
        candidate_indices = list(range(len(legal_moves)))
        clue_signal_slots = None
        clue_values = None
        frontier_values = None
        play_probabilities = None
        posterior_certain_plays = []
        high_confidence_plays = []
        posterior_play_priority_indices = []
        filtered_risky_discards = []
        filtered_redundant_clues = []
        if PROMPT_VARIANT in {"safe_gate_sherlock", "signal_gate_sherlock", "signal_priority_sherlock", "signal_protocol_sherlock", "paper_sherlock_signal_choice", "paper_sherlock_signal_score", "paper_sherlock_bayes_choice", "paper_sherlock_bayes_score", "paper_mycroft_signal_score", "bayes_protocol_sherlock"}:
            if MODE != "sherlock" and PROMPT_VARIANT != "paper_mycroft_signal_score":
                raise ValueError("safe_gate_sherlock requires HANABI_MODE=sherlock")
            safe_plays, unsafe_plays = guaranteed_play_indices(game_state, PLAYERS, legal_moves)
            if USE_POSTERIOR_CERTAIN_PLAYS:
                play_probabilities = joint_play_probabilities(game_state, PLAYERS, legal_moves)
                posterior_certain = [i for i, p in play_probabilities.items()
                                     if p >= 1.0 - 1e-12]
                safe_plays = sorted(set(safe_plays) | set(posterior_certain))
                unsafe_plays = [i for i in unsafe_plays if i not in safe_plays]
            candidate_indices = [i for i in candidate_indices if i not in unsafe_plays]
            if os.environ.get("HANABI_FILTER_RISKY_DISCARDS", "0") == "1":
                pre_discard_filter_indices = list(candidate_indices)
                if play_probabilities is None:
                    play_probabilities = joint_play_probabilities(game_state, PLAYERS, legal_moves)
                discard_threshold = float(os.environ.get("HANABI_DISCARD_MIN_PLAY_PROBABILITY", "0.50"))
                for index, move in enumerate(legal_moves):
                    if not move.startswith("(Discard "):
                        continue
                    slot = int(move.removeprefix("(Discard ").removesuffix(")"))
                    play_index = next((j for j, candidate in enumerate(legal_moves)
                                       if candidate == f"(Play {slot})"), None)
                    if play_index is not None and play_probabilities.get(play_index, 0.0) >= discard_threshold:
                        filtered_risky_discards.append(index)
                candidate_indices = [i for i in candidate_indices if i not in filtered_risky_discards]
                if not candidate_indices:
                    # Never submit an empty typed decision set to JEV.
                    candidate_indices = pre_discard_filter_indices
            if os.environ.get("HANABI_FILTER_REDUNDANT_CLUES", "0") == "1":
                if clue_values is None:
                    clue_values = clue_information_values(game_state, PLAYERS, legal_moves)
                pre_clue_filter_indices = list(candidate_indices)
                min_clue_reduction = float(os.environ.get("HANABI_MIN_CLUE_RELATIVE_REDUCTION", "0.0"))
                for index, move in enumerate(legal_moves):
                    if (move.startswith("(Reveal")
                            and clue_values.get(index, {}).get("relative_reduction", 0.0) <= min_clue_reduction):
                        filtered_redundant_clues.append(index)
                candidate_indices = [i for i in candidate_indices if i not in filtered_redundant_clues]
                if not candidate_indices:
                    candidate_indices = pre_clue_filter_indices
            if PROMPT_VARIANT in {"signal_protocol_sherlock", "paper_sherlock_signal_choice", "paper_sherlock_signal_score", "paper_mycroft_signal_score"} and safe_plays:
                # Enforce the declared protocol: a guaranteed-safe play takes precedence
                # over clue/discard options. JEV still chooses among all safe slots.
                candidate_indices = safe_plays
            # Optional experiment: when no guaranteed-safe play exists, restrict
            # JEV to plays whose exact engine-derived joint posterior exceeds a
            # configurable threshold. This is deliberately opt-in because it
            # changes the policy beyond the paper-style safety protocol.
            if (os.environ.get("HANABI_FORCE_POSTERIOR_PLAYS", "0") == "1"
                    and not safe_plays):
                if play_probabilities is None:
                    play_probabilities = joint_play_probabilities(game_state, PLAYERS, legal_moves)
                high_confidence_plays = [
                    i for i, probability in play_probabilities.items()
                    if probability >= FORCE_PLAY_PROBABILITY
                ]
                high_confidence_plays = [i for i in high_confidence_plays
                                         if i in candidate_indices]
                if high_confidence_plays:
                    posterior_play_priority_indices = sorted(set(high_confidence_plays))
                    candidate_indices = posterior_play_priority_indices
            if PROMPT_VARIANT in {"bayes_protocol_sherlock", "paper_sherlock_bayes_choice", "paper_sherlock_bayes_score"}:
                play_probabilities = joint_play_probabilities(game_state, PLAYERS, legal_moves)
                posterior_certain_plays = [i for i, probability in play_probabilities.items()
                                           if probability >= 1.0 - 1e-12]
                certain_plays = sorted(set(safe_plays) | set(posterior_certain_plays))
                high_confidence_plays = [i for i, probability in play_probabilities.items()
                                         if probability >= BAYES_MIN_PLAY_PROBABILITY]
                if certain_plays:
                    candidate_indices = certain_plays
                else:
                    candidate_indices = [i for i in candidate_indices
                                         if i not in unsafe_plays or i in high_confidence_plays]
            else:
                # Keep exact posterior play probabilities visible to JEV when
                # a policy layer explicitly computed them. Historically these
                # were discarded before prompt construction, so the filter
                # acted on probabilities JEV could not inspect.
                if (os.environ.get("HANABI_SHOW_POSTERIOR_PROBS", "0") != "1"
                        and os.environ.get("HANABI_FORCE_POSTERIOR_PLAYS", "0") != "1"
                        and os.environ.get("HANABI_NUMERIC_ACTION_VALUES", "0") != "1"):
                    play_probabilities = None
            if PROMPT_VARIANT in {"signal_gate_sherlock", "signal_priority_sherlock", "signal_protocol_sherlock", "paper_sherlock_signal_choice", "paper_sherlock_signal_score", "paper_sherlock_bayes_choice", "paper_sherlock_bayes_score", "paper_mycroft_signal_score", "bayes_protocol_sherlock"}:
                clue_signal_slots = guaranteed_plays_after_clues(game_state, PLAYERS, legal_moves)
                if os.environ.get("HANABI_NUMERIC_CLUE_VALUES", "0") == "1":
                    clue_values = clue_information_values(game_state, PLAYERS, legal_moves)
                if (os.environ.get("HANABI_FORCE_SIGNAL_CLUES", "0") == "1"
                        and not safe_plays and clue_signal_slots):
                    signal_indices = [i for i, slots in clue_signal_slots.items()
                                      if len(slots) >= MIN_SIGNAL_SLOTS]
                    if signal_indices:
                        candidate_indices = signal_indices
            if ACTION_FRONTIER and not safe_plays:
                if clue_signal_slots is None:
                    clue_signal_slots = guaranteed_plays_after_clues(game_state, PLAYERS, legal_moves)
                if clue_values is None:
                    clue_values = clue_information_values(game_state, PLAYERS, legal_moves)
                if play_probabilities is None:
                    play_probabilities = joint_play_probabilities(game_state, PLAYERS, legal_moves)
                candidate_indices, frontier_values = action_frontier_indices(
                    legal_moves, candidate_indices, safe_plays, clue_signal_slots,
                    clue_values, play_probabilities)
        else:
            safe_plays, unsafe_plays = [], []
        move_idx, audit = request_jev(prompt, legal_moves, key, candidate_indices,
                                      clue_signal_slots, play_probabilities, clue_values,
                                      frontier_values)
        audit["eligible_move_indices"] = candidate_indices
        if ACTION_FRONTIER:
            audit["action_frontier_indices"] = candidate_indices
            audit["action_frontier_values"] = frontier_values or {}
        if os.environ.get("HANABI_FILTER_RISKY_DISCARDS", "0") == "1":
            audit["filtered_risky_discard_indices"] = filtered_risky_discards
        if os.environ.get("HANABI_FILTER_REDUNDANT_CLUES", "0") == "1":
            audit["filtered_redundant_clue_indices"] = filtered_redundant_clues
        if os.environ.get("HANABI_FORCE_POSTERIOR_PLAYS", "0") == "1":
            audit["posterior_play_priority_indices"] = posterior_play_priority_indices
            audit["posterior_play_priority_threshold"] = FORCE_PLAY_PROBABILITY
        if PROMPT_VARIANT in {"safe_gate_sherlock", "signal_gate_sherlock", "signal_priority_sherlock", "signal_protocol_sherlock", "paper_sherlock_signal_choice", "paper_sherlock_signal_score", "paper_sherlock_bayes_choice", "paper_sherlock_bayes_score", "paper_mycroft_signal_score", "bayes_protocol_sherlock"}:
            audit["safe_play_indices"] = safe_plays
            audit["filtered_unsafe_play_indices"] = unsafe_plays
        if PROMPT_VARIANT in {"bayes_protocol_sherlock", "paper_sherlock_bayes_choice", "paper_sherlock_bayes_score"}:
            audit["joint_play_probabilities"] = play_probabilities
            audit["posterior_certain_play_indices"] = posterior_certain_plays
        elif (os.environ.get("HANABI_SHOW_POSTERIOR_PROBS", "0") == "1"
              and play_probabilities is not None):
            audit["joint_play_probabilities"] = play_probabilities
            audit["high_confidence_play_indices"] = high_confidence_plays
        audit.update({"turn": state.get("turn_count", 0) + 1,
                      "player": game_state.cur_player(), "move_index": move_idx})
        decisions.append(audit)
        # Route the choice through the paper environment's own parser and step code.
        if MODE == "watson":
            assistant_reply = f"Reasoning: selected through a structured JEV decision.\nChosen Move Number: {move_idx}"
        elif MODE in {"sherlock", "mycroft"}:
            assistant_reply = json.dumps({"action": move_idx, "reason": "Selected through a structured JEV decision."})
        else:
            raise ValueError(f"Unsupported environment mode for reply adapter: {MODE}")
        messages = list(messages) + [{"role": "assistant", "content": assistant_reply}]
        messages = await env.env_response(messages, state)
        time.sleep(0.12)

    final_score = state.get("final_score")
    if final_score is None:
        final_score = env._compute_score(state["hanabi_state"])
    return {
        "seed": seed,
        "score": int(final_score),
        "score_max": 25,
        "lives_remaining": state["hanabi_state"].life_tokens(),
        "clue_tokens_remaining": state["hanabi_state"].information_tokens(),
        "turns": state.get("turn_count", 0),
        "deck_remaining": state["hanabi_state"].deck_size(),
        "fireworks": list(state["hanabi_state"].fireworks()),
        "api_calls": len(decisions),
        "turn_history": state.get("turn_history", []),
        "decisions": decisions,
    }


async def main_async():
    key = os.environ.get("JEV_API_KEY")
    if not key:
        raise SystemExit("JEV_API_KEY is not set")
    if not SEEDS:
        raise SystemExit("HANABI_SEEDS must include at least one seed")
    OUT.mkdir(parents=True, exist_ok=True)
    raw_path = OUT / "games.jsonl"
    resume = os.environ.get("HANABI_RESUME", "0") == "1"
    if resume and raw_path.exists():
        games = [json.loads(line) for line in raw_path.read_text().splitlines() if line.strip()]
        seen = [game["seed"] for game in games]
        if len(seen) != len(set(seen)) or any(seed not in SEEDS for seed in seen):
            raise SystemExit("Existing results do not match requested seeds; refusing resume")
    else:
        raw_path.write_text("")
        games = []
    completed_seeds = {game["seed"] for game in games}
    run_error = None
    for seed in SEEDS:
        if seed in completed_seeds:
            print(f"seed={seed}: already complete; skipping", flush=True)
            continue
        try:
            game = await play(seed, key)
        except Exception as exc:  # preserve partial artifacts for resumable API failures
            run_error = {"type": type(exc).__name__, "message": str(exc)}
            print(f"run interrupted before seed={seed}: {run_error['type']}: {run_error['message']}",
                  flush=True)
            break
        games.append(game)
        with raw_path.open("a") as f:
            f.write(json.dumps(game, ensure_ascii=False) + "\n")
        print(f"seed={seed}: {game['score']}/25, lives={game['lives_remaining']}, "
              f"turns={game['turns']}, calls={game['api_calls']}", flush=True)

    games.sort(key=lambda game: SEEDS.index(game["seed"]))

    scores = [g["score"] for g in games]
    action_counts = Counter()
    for game in games:
        for entry in game["turn_history"]:
            move = entry.get("applied_move", "")
            if move.startswith("(Play"):
                action_counts["play"] += 1
            elif move.startswith("(Discard"):
                action_counts["discard"] += 1
            elif move.startswith("(Reveal"):
                action_counts["clue"] += 1
    summary = {
        "benchmark": f"Sparks of Cooperative Reasoning public environment; {MODE.title()}; 2-player self-play",
        "model": MODEL,
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "engine": ENGINE,
        "environment_id": "mahesh-ramesh/hanabi",
        "environment_version_id": ENV_VERSION_ID,
        "mode": MODE,
        "players": PLAYERS,
        "prompt_variant": PROMPT_VARIANT,
        "policy_config": {
            "filter_risky_discards": os.environ.get("HANABI_FILTER_RISKY_DISCARDS", "0") == "1",
            "discard_min_play_probability": float(os.environ.get("HANABI_DISCARD_MIN_PLAY_PROBABILITY", "0.50")),
            "force_posterior_plays": os.environ.get("HANABI_FORCE_POSTERIOR_PLAYS", "0") == "1",
            "force_play_probability": FORCE_PLAY_PROBABILITY,
            "force_signal_clues": os.environ.get("HANABI_FORCE_SIGNAL_CLUES", "0") == "1",
            "show_posterior_probs": os.environ.get("HANABI_SHOW_POSTERIOR_PROBS", "0") == "1",
            "numeric_action_values": os.environ.get("HANABI_NUMERIC_ACTION_VALUES", "0") == "1",
            "numeric_discard_values": os.environ.get("HANABI_NUMERIC_ACTION_VALUES", "0") == "1",
            "numeric_clue_values": os.environ.get("HANABI_NUMERIC_CLUE_VALUES", "0") == "1",
            "filter_redundant_clues": os.environ.get("HANABI_FILTER_REDUNDANT_CLUES", "0") == "1",
            "min_clue_relative_reduction": float(os.environ.get("HANABI_MIN_CLUE_RELATIVE_REDUCTION", "0.0")),
            "score_risk_penalty": SCORE_RISK_PENALTY,
            "min_signal_slots": MIN_SIGNAL_SLOTS,
            "action_frontier": ACTION_FRONTIER,
            "frontier_max_clues": FRONTIER_MAX_CLUES,
            "use_posterior_certain_plays": USE_POSTERIOR_CERTAIN_PLAYS,
            "clue_opportunity_annotation": "one_action_cap_v2",
        },
        "action_interface": ("JEV Score API rates every legal move independently in one fan-out request; highest expected score is applied"
                             if PROMPT_VARIANT in {"action_scores", "paper_sherlock_score", "paper_sherlock_signal_score", "paper_sherlock_bayes_score", "paper_mycroft_signal_score"} else
                             "JEV Choice API selects among the paper environment's legal moves"),
        "seeds": SEEDS,
        "games_completed": len(games),
        "score_denominator": len(games),
        "scores": scores,
        "score_mean": sum(scores) / len(scores) if scores else None,
        "score_median": median(scores) if scores else None,
        "score_range": [min(scores), max(scores)] if scores else None,
        "requested_games": len(SEEDS),
        "run_status": "complete" if len(games) == len(SEEDS) else "incomplete",
        "run_error": run_error,
        "total_api_calls": sum(g["api_calls"] for g in games),
        "decision_count": sum(len(g["decisions"]) for g in games),
        "action_counts": dict(action_counts),
        "published_2p_reference_scores": (PUBLISHED_SHERLOCK_2P if MODE == "sherlock" else PUBLISHED_WATSON_2P),
        "comparison_note": ("Paper references use 10 seeds and free-form completions; this run uses JEV's structured "
                            f"{'Score' if PROMPT_VARIANT in {'action_scores', 'paper_sherlock_score', 'paper_sherlock_signal_score', 'paper_sherlock_bayes_score', 'paper_mycroft_signal_score'} else 'Choice'} interface."),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    integrity = build_results_integrity(raw_path)
    integrity_path = OUT / "results_integrity.json"
    integrity_path.write_text(json.dumps(integrity, indent=2) + "\n")
    policy_config = summary["policy_config"]
    input_hash = sha256(json.dumps({"env_version_id": ENV_VERSION_ID, "mode": MODE,
        "players": PLAYERS, "seeds": SEEDS, "model": MODEL,
        "prompt_variant": PROMPT_VARIANT, "policy_config": policy_config},
        sort_keys=True).encode())
    manifest = {
        "model_requested": MODEL,
        "environment": "mahesh-ramesh/hanabi",
        "environment_version_id": ENV_VERSION_ID,
        "engine": ENGINE,
        "mode": MODE,
        "players": PLAYERS,
        "prompt_variant": PROMPT_VARIANT,
        "policy_config": policy_config,
        "seeds": SEEDS,
        "games": len(games),
        "requested_games": len(SEEDS),
        "run_status": summary["run_status"],
        "run_error": summary["run_error"],
        "api_calls": summary["total_api_calls"],
        "decision_count": summary["decision_count"],
        "input_sha256": input_hash,
        "environment_source_sha256": {name: sha256((PAPER_ENV / name).read_bytes()) for name in SOURCE_FILES},
        "benchmark_harness_sha256": sha256(Path(__file__).read_bytes()),
        "results_sha256": integrity["whole_file_sha256"],
        "results_sha256_note": integrity["whole_file_hash_note"],
        "results_integrity_file": integrity_path.name,
        "results_integrity_sha256": sha256(integrity_path.read_bytes()),
        "results_line_hash_root": integrity["line_hash_root"],
        "summary_sha256": sha256((OUT / "summary.json").read_bytes()),
        "summary_file": "summary.json",
        "results_file": raw_path.name,
        "completed_at_utc": summary["evaluated_at_utc"],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Summary:", json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main_async())
