# JEV Sherlock safety/signal Score with 5% posterior discard filter, 10-game pilot

This pilot is the same hybrid policy as the 10% discard-filter run, but removes
a discard when its slot has at least **5%** exact joint posterior probability
of being playable.

- Seeds 0–9, 10 games
- Mean score: **11.8/25** (scores 7, 16, 11, 15, 11, 15, 13, 11, 13, 6)
- All games retained all 3 lives

The existing 10% discard-filter pilot scored 13.4/25 on these seeds. This
small pilot does not justify expanding the 5% threshold; the 10% 100-game run
remains the primary result.
