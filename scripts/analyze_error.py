#!/usr/bin/env python3
"""Summarize action-level behavior in JEV Hanabi game JSONL artifacts."""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path


DEFAULT_INPUTS = [
    Path("results/runs/results_hle_paper_sherlock_signal_score_primary_10_100/games.jsonl"),
    Path("results/runs/results_hle_paper_sherlock_signal_score_primary_110_209/games.jsonl"),
]


def load_games(paths: list[Path]) -> list[dict]:
    games = []
    for path in paths:
        with path.open() as handle:
            games.extend(json.loads(line) for line in handle if line.strip())
    return games


def action_kind(move: str) -> str:
    if move.startswith("(Play"):
        return "play"
    if move.startswith("(Discard"):
        return "discard"
    return "clue"


def summarize(games: list[dict]) -> dict:
    decisions = []
    game_rows = []
    for game in games:
        counts = Counter()
        signal_clues = 0
        ordinary_clues = 0
        missed_safe = 0
        for decision, turn in zip(game["decisions"], game["turn_history"]):
            move = decision["legal_moves"][decision["move_index"]]
            kind = action_kind(move)
            counts[kind] += 1
            if decision.get("safe_play_indices"):
                if decision["move_index"] not in decision["safe_play_indices"]:
                    missed_safe += 1
            if kind == "clue":
                instructions = decision["request"]["questions"].get(
                    decision["choice"], {}).get("instructions", "")
                is_signal_clue = "guaranteed-play option" in instructions
                if is_signal_clue:
                    signal_clues += 1
                else:
                    ordinary_clues += 1
            else:
                is_signal_clue = False
            answers = decision.get("response", {}).get("answers", {})
            selected = answers.get(decision.get("choice"), {})
            scores = sorted(
                float(answer["score"])
                for answer in answers.values()
                if isinstance(answer, dict) and "score" in answer
            )
            decisions.append({
                "kind": kind,
                "signal_clue": is_signal_clue,
                "selected_score": selected.get("score"),
                "harmful_probability": float(selected.get("probabilities", {}).get("0", 0.0)),
                "margin": scores[-1] - scores[-2] if len(scores) > 1 else None,
                "safe_state": bool(decision.get("safe_play_indices")),
                "missed_safe": missed_safe,
                "turn": turn["turn"],
            })
        game_rows.append({
            "seed": game["seed"],
            "score": game["score"],
            "lives_remaining": game["lives_remaining"],
            "plays": counts["play"],
            "clues": counts["clue"],
            "discards": counts["discard"],
            "signal_clues": signal_clues,
            "ordinary_clues": ordinary_clues,
            "missed_safe_plays": missed_safe,
        })

    def mean(rows: list[dict], key: str) -> float:
        return statistics.mean(row[key] for row in rows) if rows else 0.0

    tiers = {
        "low_9_12": [row for row in game_rows if row["score"] <= 12],
        "middle_13_15": [row for row in game_rows if 13 <= row["score"] <= 15],
        "high_16_20": [row for row in game_rows if row["score"] >= 16],
    }
    tier_summary = {}
    for name, rows in tiers.items():
        clues = sum(row["clues"] for row in rows)
        tier_summary[name] = {
            "games": len(rows),
            "mean_score": mean(rows, "score"),
            "mean_plays": mean(rows, "plays"),
            "mean_clues": mean(rows, "clues"),
            "mean_discards": mean(rows, "discards"),
            "signal_clue_fraction": sum(row["signal_clues"] for row in rows) / clues if clues else None,
        }

    by_kind = {}
    for kind in ("play", "clue", "discard"):
        rows = [row for row in decisions if row["kind"] == kind]
        margins = [row["margin"] for row in rows if row["margin"] is not None]
        by_kind[kind] = {
            "decisions": len(rows),
            "mean_harmful_probability": statistics.mean(row["harmful_probability"] for row in rows),
            "mean_top_vs_runner_up_margin": statistics.mean(margins) if margins else None,
        }
    clue_decisions = [row for row in decisions if row["kind"] == "clue"]
    return {
        "games": len(games),
        "score_mean": statistics.mean(game["score"] for game in games),
        "score_median": statistics.median(game["score"] for game in games),
        "score_range": [min(game["score"] for game in games), max(game["score"] for game in games)],
        "games_with_life_loss": sum(game["lives_remaining"] < 3 for game in games),
        "total_decisions": len(decisions),
        "action_counts": dict(Counter(row["kind"] for row in decisions)),
        "signal_clues": sum(row["signal_clue"] for row in decisions),
        "ordinary_clues": len(clue_decisions) - sum(row["signal_clue"] for row in decisions),
        "signal_clue_fraction": sum(row["signal_clue"] for row in decisions) / len(clue_decisions),
        "missed_safe_plays": sum(row["missed_safe"] for row in decisions),
        "decision_behavior": by_kind,
        "score_tiers": tier_summary,
        "game_rows": game_rows,
    }


def write_figure(summary: dict, output: Path) -> None:
    import matplotlib.pyplot as plt

    palette = {"low_9_12": "#D55E00", "middle_13_15": "#0072B2", "high_16_20": "#009E73"}
    labels = {"low_9_12": "9–12", "middle_13_15": "13–15", "high_16_20": "16–20"}
    tiers = list(labels)
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.2), constrained_layout=True)
    rows = summary["game_rows"]
    axes[0].hist([row["score"] for row in rows], bins=range(8, 22), color="#0072B2", edgecolor="white", align="left")
    axes[0].set(xlabel="Final score", ylabel="Games", title="Score distribution")
    axes[0].set_xticks(range(9, 21, 2))
    for key in tiers:
        tier_rows = summary["score_tiers"][key]
        axes[1].bar(labels[key], [tier_rows["mean_clues"], tier_rows["mean_discards"]],
                    color=["#56B4E9", "#E69F00"], alpha=0.85)
    # Replace the intermediate bars with grouped bars for readability.
    axes[1].clear()
    x = list(range(len(tiers)))
    width = 0.34
    axes[1].bar([v - width / 2 for v in x], [summary["score_tiers"][k]["mean_clues"] for k in tiers], width, label="Clues", color="#56B4E9")
    axes[1].bar([v + width / 2 for v in x], [summary["score_tiers"][k]["mean_discards"] for k in tiers], width, label="Discards", color="#E69F00")
    axes[1].set(xlabel="Score tier", ylabel="Actions per game", title="Where turns go")
    axes[1].set_xticks(x, [labels[k] for k in tiers])
    axes[1].legend(frameon=False, fontsize=8)
    axes[2].bar([labels[k] for k in tiers], [100 * summary["score_tiers"][k]["signal_clue_fraction"] for k in tiers], color=[palette[k] for k in tiers])
    axes[2].set(xlabel="Score tier", ylabel="Signal clues (%)", title="Targeted communication")
    axes[2].set_ylim(0, 60)
    for ax in axes:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(labelsize=8)
    fig.savefig(output, dpi=220)
    fig.savefig(output.with_suffix(".pdf"))
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", type=Path, dest="inputs")
    parser.add_argument("--output-dir", type=Path, default=Path("analysis"))
    args = parser.parse_args()
    inputs = args.inputs or DEFAULT_INPUTS
    summary = summarize(load_games(inputs))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "error_analysis.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_figure(summary, args.output_dir / "error_analysis.png")
    print(json.dumps({key: summary[key] for key in ("games", "score_mean", "action_counts", "signal_clue_fraction", "missed_safe_plays")}, indent=2))


if __name__ == "__main__":
    main()
