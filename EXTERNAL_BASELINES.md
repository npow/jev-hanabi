# Open-source policy baselines

As a feasibility check, the current upstream Quuxplusone Hanabi framework was
compiled at commit `daef9de823119cf930237dfadc1ac4f98234361f` and run with its
native 2-player engine:

| Policy | Games | Mean score | Perfect games |
|---|---:|---:|---:|
| ValueBot | 1,000 | 19.84 | 0.2% |
| HolmesBot | 1,000 | 20.72 | 4.8% |
| SmartBot | 1,000 | 23.20 | 29.5% |

Commands:

```bash
./run_ValueBot --quiet --players 2 --games 1000 --seed 0
./run_HolmesBot --quiet --players 2 --games 1000 --seed 0
./run_SmartBot --quiet --players 2 --games 1000 --seed 0
```

These are feasibility baselines, not direct apples-to-apples scores: the
framework uses its own C++ engine and deal generator. The next implementation
step is to port the SmartBot-style convention state machine into the pinned
Hanabi Learning Environment used by this repository, then evaluate JEV as a
tie-breaker over its candidate actions.

The first local prototype in
[`scripts/rule_policy_baseline.py`](scripts/rule_policy_baseline.py) scored
14.08/25 over 100 fixed seeds with no life loss. It only implements guaranteed
plays, immediate signal clues, information clues, and safest discards; it is
not a SmartBot port and is retained as a failed heuristic baseline.
