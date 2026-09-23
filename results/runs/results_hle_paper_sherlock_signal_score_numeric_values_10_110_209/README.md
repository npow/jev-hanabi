# JEV Sherlock numeric action values, fresh 100-game replication

This is a fresh replication on seeds 110–209 of the numeric action annotation
policy. It uses the 10% posterior discard filter and exposes exact play
probabilities as approximate immediate point values, plus guaranteed signal
clue opportunities, in JEV's action descriptions.

- Mean score: **12.79/25**, median 13, range 7–19
- All 100 games retained all 3 lives
- 7,680 JEV decisions
- 0 unoffered selections and 0 selected unsafe plays

Against the paired 10% baseline on the same seeds (12.34/25), the improvement
is **+0.45 points** (95% paired t interval **−0.03 to +0.93**), winning 47
games, tying 17, and losing 36. The fresh block alone is inconclusive.

Combining both 100-game blocks (seeds 10–209), the paired improvement is
**+0.52 points** (95% interval **+0.14 to +0.89**; 96 wins, 35 ties, 69
losses). This supports a modest average benefit, while leaving substantial
seed-to-seed variance.
