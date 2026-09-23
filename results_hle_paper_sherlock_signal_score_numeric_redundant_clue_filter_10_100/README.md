# JEV Sherlock Score with numeric values and redundant-clue filtering, 100 games

This policy combines the 10% posterior discard filter with numeric posterior
values for plays and discards, guaranteed-play signal annotations, and a
programmatic filter that removes clues producing zero possibility-set
reduction for the recipient. If filtering would remove every action, the
eligible set is restored.

- Seeds 10–109, 100 games, 2-player self-play
- Mean score: **14.29/25**, median 14, range 9–18
- All 100 games retained all 3 lives
- 7,503 JEV decisions
- 0 unoffered selections and 0 selected unsafe plays
- 842 redundant clue alternatives filtered

Against the previous numeric play/discard policy (13.32/25) on the same seeds,
the paired improvement is **+0.97 points** (95% paired t interval **+0.54 to
+1.40**), winning 58 games, tying 22, and losing 20. Against the plain 10%
safety filter (12.26/25), the paired improvement is **+2.03 points** (95%
interval **+1.43 to +2.63**), winning 73, tying 7, and losing 20.

This is the strongest tested run so far. It still needs replication on a fresh
seed block before being treated as a robust capability estimate.
