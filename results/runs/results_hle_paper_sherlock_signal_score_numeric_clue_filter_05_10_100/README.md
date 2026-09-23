# JEV Sherlock Score with a 5% information-clue threshold, 100 games

This run uses the current numeric-value policy and removes eligible clues whose
exact recipient possibility domain shrinks by 5% or less. The 10% posterior
discard filter and zero-reduction clue filter remain enabled.

- Seeds 10–109, 100 games, 2-player self-play
- Mean score: **14.26/25**, median 14, range 9–20
- All 100 games retained all 3 lives
- 7,512 JEV decisions
- 0 unoffered selections and 0 selected unsafe plays

Against the threshold-0 policy on the same seeds (14.29/25), the paired
difference is **−0.03 points** (95% paired t interval **−0.44 to +0.38**),
winning 38 games, tying 20, and losing 42. Against the plain 10% safety filter
(12.26/25), the paired improvement is **+2.00 points** (95% interval **+1.42
to +2.58**), winning 70, tying 8, and losing 22.

The 5% threshold is therefore not promoted: it is statistically indistinguishable
from the simpler threshold-0 policy and has a slightly lower mean on this block.
