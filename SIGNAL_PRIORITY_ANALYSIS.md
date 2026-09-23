# Multi-play signal-clue analysis

The complete current-best trajectories (100 games, seeds 10–109) were replayed
through the local Hanabi engine without making JEV requests.

- 1,353 decision states had at least one clue that made a teammate card
  immediately guaranteed playable.
- 158 states had a clue that made at least two cards immediately playable.
- 174 multi-play signal-clue candidates occurred across those states.
- The current policy selected a one-play signal instead in **19 decisions**
  across 13 games.

This motivates the opt-in `HANABI_FORCE_SIGNAL_CLUES=1` plus
`HANABI_MIN_SIGNAL_SLOTS=2` experiment. It would affect a small, defined set of
decisions while leaving ordinary one-card signaling to JEV. It still requires a
fresh JEV run; replay counts are not a score estimate.

The replay also exposed a prompt-criterion issue: multiple guaranteed slots are
multiple options for the recipient, not multiple points on the next turn. The
prompt now states that the immediate opportunity is capped at one point.
