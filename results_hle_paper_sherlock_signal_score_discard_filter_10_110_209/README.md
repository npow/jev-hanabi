# JEV Sherlock safety/signal Score with 10% posterior discard filter, fresh 100-game replication

This is the original hybrid policy on seeds 110–209. It uses guaranteed-safe
plays, teammate-signal eligibility, JEV's Score interface, and removes a
discard when its slot has at least 10% exact joint posterior probability of
being playable.

- Mean score: **12.34/25**, median 12, range 7–18
- All 100 games retained all 3 lives
- 7,698 JEV decisions

This is the paired baseline for the numeric-action annotation replication.
