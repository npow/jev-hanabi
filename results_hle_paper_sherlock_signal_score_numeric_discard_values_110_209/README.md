# JEV Sherlock numeric play, clue, and discard values, fresh 100-game replication

This run replicates the numeric action policy on seeds 110–209. JEV sees exact
joint posterior play probabilities for plays and discards, plus guaranteed
signal clue opportunities. The 10% posterior discard filter and guaranteed-safe
play protocol remain enabled.

- Mean score: **13.10/25**, median 13, range 8–20
- All 100 games retained all 3 lives
- 7,588 JEV decisions
- 0 unoffered selections and 0 selected unsafe plays

Against the paired numeric play/clue-only policy (12.79/25), the improvement
is **+0.31 points** (95% paired t interval **−0.12 to +0.74**), winning 44
games, tying 20, and losing 36. This fresh block alone is inconclusive.

Combining both 100-game blocks, discard values improve over numeric play/clue
values by **+0.40 points** (95% interval **−0.08 to +0.87**). Against the
plain 10% safety filter over the same 200 paired games, the complete policy
improves by **+0.91 points** (95% interval **+0.42 to +1.40**), winning 109,
tying 34, and losing 57.
