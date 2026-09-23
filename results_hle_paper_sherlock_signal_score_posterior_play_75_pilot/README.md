# JEV Sherlock safety/signal Score with 75% posterior-play priority, 10-game pilot

This pilot adds an opt-in rule to the 10% discard-filter policy: when no
certain play exists, JEV is offered only plays with at least 75% exact joint
posterior success probability, if any such plays exist.

- Seeds 0–9, 10 games
- Mean score: **12.0/25** (scores 13, 12, 13, 12, 12, 14, 11, 11, 15, 7)
- All games retained all 3 lives

The existing 10% discard-filter pilot scored 13.4/25 on these seeds. Because
this priority rule was lower in the pilot and changes the policy substantially,
it is not promoted to a larger run.
