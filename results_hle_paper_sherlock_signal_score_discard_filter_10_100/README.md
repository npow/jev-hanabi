# JEV Sherlock safety/signal Score with 10% posterior discard filter, 100 games

This run uses the public Sherlock prompt, the safe-play and teammate-signal
eligibility layer, and JEV's Score interface. When no guaranteed-safe play is
available, it removes a discard only when that card slot has at least **10%**
joint posterior probability of being playable now. The filter falls back to
the eligible set if filtering would otherwise leave no action.

## Result

- Seeds 10–109, 100 games, 2-player self-play
- Mean score: **12.26/25** (sample SD 2.74)
- Median 12, range 5–18
- All 100 games retained all 3 lives
- 7,716 JEV decisions
- 0 unoffered selections and 0 selected unsafe plays

Against the 25% discard-filter run (12.06/25) on the same seeds, the paired
improvement is **+0.20 points** (95% paired t interval **−0.37 to +0.77**),
winning 48 games, tying 12, and losing 40. Against the unfiltered Score run
(9.81/25), the paired improvement is **+2.45 points** (95% interval **+1.76
to +3.14**), winning 71 games, tying 3, and losing 26.

The filter removed 27,996 high-risk discard alternatives. This remains a
hybrid policy: JEV chooses actions, while engine-derived posterior rules
protect likely-playable cards. Published paper results use free-form
completions and are not direct head-to-head comparisons.
