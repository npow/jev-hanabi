# JEV full Sherlock prompt, ungated Choice, 100 games

This is the closest JEV baseline to the public Sherlock setup: the full
paper Sherlock prompt is preserved, every legal engine action is offered to
JEV's typed Choice interface, and no safety or Bayesian action is removed
before selection.

## Result

- Seeds 10–109, 100 games, 2-player self-play
- Mean score: **4.52/25** (95% t interval **4.13–4.91**)
- Median 4, range 1–10
- 96/100 games ended with zero lives; 0/100 retained all three lives
- 2,929 JEV decisions

On the same seeds, the Bayesian-gated Choice run averaged 9.57/25. Its
paired advantage was **5.05 points** (95% paired t interval **4.35–5.75**),
winning 93 games, tying 3, and losing 4. This confirms that the safety gate
is a major part of the earlier result; ungated JEV Choice is not a strong
Hanabi policy under this prompt.

The paper's published Sherlock numbers use free-form model completions,
while this run uses JEV's structured Choice API, so it is a fidelity ablation,
not a direct model ranking.
