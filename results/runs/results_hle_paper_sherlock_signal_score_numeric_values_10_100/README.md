# JEV Sherlock safety/signal Score with numeric action values, 100 games

This run uses the public Sherlock prompt, guaranteed-safe play and teammate
signal eligibility, the 10% posterior discard filter, and JEV's Score API.
Action descriptions also expose exact engine-derived play probabilities as an
approximate immediate point contribution (`p` points) and annotate guaranteed
signal clues with their immediate next-turn point opportunity. These numeric
annotations are shown to JEV; they do not select actions directly.

## Result

- Seeds 10–109, 100 games, 2-player self-play
- Mean score: **12.84/25**, median 13, range 7–19
- All 100 games retained all 3 lives
- 7,655 JEV decisions
- 0 unoffered selections and 0 selected unsafe plays

Against the original 10% discard-filter policy (12.26/25) on the same seeds,
the paired improvement is **+0.58 points** (95% paired t interval **+0.00 to
+1.16**), winning 49 games, tying 18, and losing 33. Against the unfiltered
Score policy (9.81/25), the paired improvement is **+3.03 points** (95%
interval **+2.41 to +3.65**), winning 76 games, tying 9, and losing 15.

This is currently the strongest tested JEV policy, but the gain over the 10%
filter is modest and should be replicated on a fresh seed block before being
called a robust improvement. It remains a hybrid policy: JEV ranks actions,
while deterministic engine-derived rules filter risky discards and expose
posterior values.
