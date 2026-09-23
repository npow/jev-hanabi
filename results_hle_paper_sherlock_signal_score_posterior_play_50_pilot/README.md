# JEV Sherlock safety/signal Score with 50% posterior-play priority, 10-game pilot

This pilot adds an opt-in rule to the 10% discard-filter policy: when no
certain play exists, JEV is offered only plays with at least 50% exact joint
posterior success probability, if any such plays exist.

- Seeds 0–9, 10 games
- Mean score: **12.6/25** (scores 16, 14, 10, 11, 13, 13, 11, 12, 17, 9)
- All games retained all 3 lives

The existing 10% discard-filter pilot scored 13.4/25 on these seeds. This
small pilot does not justify expanding the forced-play rule; the 10% filter
100-game run remains the primary result.
