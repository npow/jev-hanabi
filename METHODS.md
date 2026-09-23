# Experimental setup

## Environment

- Public Sherlock Hanabi environment from Sparks of Cooperative Reasoning
- Two-player self-play
- Five colors, maximum score 25
- Engine: `hanabi-learning-environment-mahesh==0.0.2`
- Environment version: `nees3rw1f786tt0ojf1ef9m9`

## JEV interface

At each turn, JEV receives the complete legal action set through the
structured Score interface. Each action is scored independently; the action
with the highest expected score is applied. The request uses model
`jev-latest` and the paper Sherlock prompt.

## Policy used for the primary estimate

The primary estimate applies deterministic policy gates around JEV:

1. Guaranteed-play actions are selected when available.
2. Discards with posterior play probability at least 0.10 are removed.
3. Clues that do not reduce the recipient's possibility domain are removed.
4. Clue opportunity is counted as at most one immediate point because the
   recipient can take one action on the next turn.

The policy does not force a posterior-play threshold or risk penalty.

## Reproduction

```sh
export JEV_API_KEY='your-key'
./run_primary_baseline.sh
```

Each run records its seeds, policy configuration, source hashes, result hash,
and completion status in `summary.json`, `manifest.json`, and
`results_integrity.json`.
