# Corrected 200-game trajectory audit

The corrected one-action clue criterion was evaluated on seeds 10–209 (200
games total). It scored **14.37/25** on average, with scores from 9 to 19.
Every game retained all three life tokens, so the current limiting factor is
throughput rather than catastrophic play errors.

Mean action counts per game were:

- 28.73 plays (the final score equals the number of successful plays)
- 68.00 clues
- 53.42 discards

The two targeted pilots did not improve this pattern: requiring at least two
guaranteed-play slots for a signal clue scored 13.8/25 on 10 games, and adding
a 0.5 harmful-probability penalty scored 13.9/25. Neither should be expanded
without a new hypothesis.

The next useful experiment is therefore a calibrated increase in play
throughput, with explicit life-loss monitoring, rather than another clue
priority threshold. Any candidate should first run as a paired 10-game pilot
on fixed seeds and be promoted only if it improves score without introducing
life losses.

A 0.90 posterior-play pilot was run on seeds 0–9. It scored 13.6/25 with no
life losses, below the corrected baseline and the risk-penalty pilot, so this
particular throughput intervention is rejected.

Raising the discard play-probability filter from 0.10 to 0.20 scored
**14.52/25 over 50 games** (95% interval 13.87–15.17), with no life losses.
This is numerically above the 14.37/25 corrected 200-game baseline, but the
intervals overlap and the samples used independent JEV calls. It is therefore
the leading candidate for a matched same-seed comparison, not yet the new
official policy.

The matched 0.10 control on the same 50 seeds scored 14.42/25. The nominal
candidate difference was +0.10 (95% interval −0.50 to +0.70; 21 wins, 11 ties,
18 losses), so the threshold change is rejected as unproven.

Risk penalty 0.1 was then tested on seeds 50–99: 14.64/25 versus 14.52/25 for
the matched zero-penalty control. The nominal difference was +0.12 (95% CI
−0.42 to +0.66; 21 wins, 14 ties, 15 losses), so the unpenalized policy remains
the official configuration.
