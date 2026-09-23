# JEV Hanabi policy replication summary

| Policy / seeds | Mean | Paired comparison |
|---|---:|---:|
| Plain 10% safety filter, 10–109 | 12.26 | baseline |
| Plain 10% safety filter, 110–209 | 12.34 | fresh baseline |
| Numeric play/clue values, 10–109 | 12.84 | +0.58 vs plain |
| Numeric play/clue values, 110–209 | 12.79 | +0.45 vs fresh plain |
| Numeric play/clue/discard values, 10–109 | 13.32 | +1.06 vs plain |
| Numeric play/clue/discard values, 110–209 | 13.10 | +0.76 vs fresh plain |
| Numeric values + redundant-clue filter, 10–109 | 14.29 | +2.03 vs plain |
| Numeric values + redundant-clue filter, 110–209 | 14.32 | +1.98 vs fresh plain |
| Complete policy, combined 200 games | **14.31** | **+2.01 vs plain (95% CI +1.46 to +2.55)** |
| Numeric values + 5% information-clue threshold, 10–109 | 14.26 | −0.03 vs threshold-0 (95% CI −0.44 to +0.38) |
| Corrected one-action clue criterion, 10–109 | 14.61 | +0.32 vs old best (95% CI −0.08 to +0.72) |
| Corrected one-action clue criterion, 110–209 | 14.12 | fresh replication |
| Corrected criterion, combined 200 games | **14.37** | **+0.06 vs old best (95% CI −0.21 to +0.33)** |
| Corrected discard threshold 0.20, seeds 0–49 | **14.52** | candidate; 95% CI 13.87–15.17 |

Against the prior numeric play/discard policy over both blocks, redundant-clue
filtering adds **+1.10 points** (95% CI +0.67 to +1.52). All 400 games in the
plain-versus-complete paired comparison retained all 3 lives and selected no
ineligible actions.

The redundant-clue rule removes only clues whose exact recipient possibility
domains do not shrink. It is now replicated on both 100-game seed blocks.

A stricter 5% relative-reduction threshold was evaluated on the same 100 seeds.
It did not improve the threshold-0 policy, so the threshold-0 rule remains the
current best configuration.

A risk-sensitive score selector (penalty 0.5 on JEV's harmful-rating
probability) completed 85/100 planned games before the API returned HTTP 402.
Its partial paired gain was +0.29 (95% CI −0.13 to +0.71), so it is not a
promoted policy; the run can resume from its existing JSONL artifact when API
credits are available.

The clue opportunity annotation was corrected after replay analysis: multiple
guaranteed recipient slots are now described as multiple options with at most
one immediate point. The corrected baseline scored **14.61/25** on seeds
10–109 and **14.12/25** on the fresh 110–209 block, for **14.37/25 over 200
games**. Its combined paired gain over the old-criterion best is +0.06 (95% CI
−0.21 to +0.33), so the criterion correction does not establish a reliable
score improvement.

The corrected discard threshold 0.20 candidate scored 14.52/25 on seeds 0–49;
its matched 0.10 control scored 14.42/25. The nominal difference was +0.10
(95% CI −0.50 to +0.70), so the candidate was not promoted.

Corrected risk-sensitive scoring (penalty 0.5) scored 13.9/25 in a 10-game
pilot and was not expanded.

Risk penalty 0.1 scored 14.64/25 on seeds 50–99. Its matched zero-penalty
control scored 14.52/25; the nominal difference was +0.12 (95% CI −0.42 to
+0.66; 21 wins, 14 ties, 15 losses). The penalty was not promoted.
