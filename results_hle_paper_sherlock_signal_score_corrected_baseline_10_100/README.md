# JEV Sherlock Score corrected baseline, 100 games

This is the corrected version of the current best policy. Clues that make
multiple recipient slots guaranteed now describe multiple play options while
capping immediate next-turn score at one point.

- Seeds 10–109, 100 games, 2-player self-play
- Mean score: **14.61/25** (95% t interval **14.22–15.00**), median 15, range 10–18
- All 100 games retained all 3 lives
- 7,481 JEV decisions
- 0 unoffered selections and 0 selected unsafe plays

Against the previous threshold-0 run using the old clue annotation (14.29/25),
the paired gain is **+0.32 points** (95% paired t interval **−0.08 to +0.72**),
winning 45, tying 21, and losing 34. Against the plain 10% safety baseline
(12.26/25), the paired gain is **+2.35 points** (95% interval **+1.78 to
2.92**), winning 77, tying 8, and losing 15.

The corrected criterion produces the best complete mean so far, but its direct
gain over the old best is not statistically conclusive on this 100-game block.
