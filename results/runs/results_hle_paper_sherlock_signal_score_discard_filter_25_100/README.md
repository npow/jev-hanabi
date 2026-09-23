# JEV Sherlock safety/signal Score with 25% posterior discard filter, 100 games

This run uses the public Sherlock prompt, the safe-play and teammate-signal
eligibility layer, and JEV's Score interface. When no guaranteed-safe play is
available, it removes a discard only when that card slot has at least **25%**
joint posterior probability of being playable now. The filter falls back to
the eligible set if filtering would otherwise leave no action.

## Result

- Seeds 10–109, 100 games, 2-player self-play
- Mean score: **12.06/25** (95% t interval **11.60–12.52**)
- Median 12, range 6–18
- All 100 games retained all 3 lives
- 7,714 JEV decisions
- 0 unoffered selections and 0 selected unsafe plays

Against the 50% discard-filter run (10.48/25) on the same seeds, the paired
improvement is **+1.58 points** (95% paired t interval **+1.02 to +2.14**),
winning 67 games, tying 12, and losing 21. Against the unfiltered Score run
(9.81/25), the paired improvement is **+2.25 points** (95% interval **+1.64
to +2.86**), winning 72, tying 11, and losing 17.

The filter removed 20,489 high-risk discard alternatives. This remains a
hybrid policy: JEV chooses actions, while engine-derived posterior rules
protect likely-playable cards. Published paper results use free-form
completions and are not direct head-to-head comparisons.
