# JEV Sherlock safety/signal protocol with Score interface, 100 games

This run preserves the public paper's Sherlock prompt and uses the same
programmatic safe-play and teammate-signal eligibility layer as the earlier
Choice run. JEV's typed Score API independently rates each eligible action;
the highest score is applied. No unsafe play is offered when a guaranteed-safe
play exists.

## Result

- Seeds 10–109, 100 games, 2-player self-play
- Mean score: **9.81/25** (95% t interval **9.22–10.40**)
- Median 10, range 3–18
- All 100 games retained all 3 lives
- 7,855 JEV decisions
- 0 unoffered selections and 0 selected unsafe plays

On the same seeds, Score's paired difference was **+0.09** versus the
signal Choice run (95% paired t interval **−0.72 to +0.90**; 54 wins, 7 ties,
39 losses), and **+0.24** versus Bayesian Choice (interval **−0.54 to +1.02**;
48 wins, 12 ties, 40 losses). The interfaces are therefore statistically
indistinguishable at this sample size; Score is the current numerical leader,
but not a demonstrated improvement.

The paper's published results use free-form model completions. These are
structured JEV ablations with an explicit safety controller, not direct
head-to-head model rankings.
