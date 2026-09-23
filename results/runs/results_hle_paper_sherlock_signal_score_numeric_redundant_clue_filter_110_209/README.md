# JEV Sherlock numeric values with redundant-clue filtering, fresh replication

This is the fresh 110–209 replication of the current policy: exact numeric
posterior values for plays, clues, and discards; the 10% posterior discard
filter; guaranteed-safe play and signal rules; and removal of clues that do
not shrink any recipient possibility set.

- Mean score: **14.32/25**, median 14, range 9–18
- All 100 games retained all 3 lives
- 7,499 JEV decisions
- 0 unoffered selections and 0 selected unsafe plays
- 789 redundant clue alternatives filtered

Against the plain 10% safety baseline on the same seeds (12.34/25), the paired
improvement is **+1.98 points** (95% paired t interval **+1.49 to +2.47**),
winning 72 games, tying 15, and losing 13. Combining both 100-game blocks,
the improvement is **+2.01 points** (95% interval **+1.46 to +2.55**; 145
wins, 22 ties, 33 losses).

Against the prior numeric play/discard policy across both blocks, the paired
improvement is **+1.10 points** (95% interval **+0.67 to +1.52**).
