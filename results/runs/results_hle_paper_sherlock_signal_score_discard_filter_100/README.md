# JEV Sherlock safety/signal Score with posterior discard filter, 100 games

This run uses the public Sherlock prompt, the safe-play and teammate-signal
eligibility layer, and JEV's Score interface. It adds one deterministic rule:
when no guaranteed-safe play is available, a discard is removed if its card
slot has at least 50% joint posterior probability of being playable now.

## Result

- Seeds 10–109, 100 games, 2-player self-play
- Mean score: **10.48/25** (95% t interval **9.97–10.99**)
- Median 10, range 6–17
- All 100 games retained all 3 lives
- 7,835 JEV decisions
- 0 unoffered selections and 0 selected unsafe plays

Against the unfiltered safety/signal Score run on the same seeds (9.81/25),
the paired improvement is **+0.67 points** (95% paired t interval
**+0.06 to +1.28**), winning 52 games, tying 14, and losing 34. The filter
removed 5,171 high-risk discard alternatives across the run.

This is still a hybrid policy: JEV chooses actions, while the engine-derived
posterior filter protects likely-playable cards. Published paper scores use
free-form completions and are not direct head-to-head comparisons.
