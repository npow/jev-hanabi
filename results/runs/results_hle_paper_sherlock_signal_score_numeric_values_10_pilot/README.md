# JEV Sherlock safety/signal Score with numeric action annotations, 10-game pilot

This pilot uses the 10% posterior discard filter and adds approximate numeric
annotations to JEV's action descriptions: immediate expected points for plays
and guaranteed next-turn point opportunities for signal clues.

- Seeds 0–9, 10 games
- Mean score: **12.1/25** (scores 11, 11, 10, 12, 12, 13, 14, 12, 16, 10)
- All games retained all 3 lives

The existing 10% discard-filter pilot scored 13.4/25 on these seeds. The
annotation did not improve the pilot and is not enabled in the primary policy.
