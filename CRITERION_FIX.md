# Clue score criterion correction

The original numeric clue annotation described a clue revealing `n` guaranteed
recipient slots as an immediate opportunity of `n` points. A Hanabi player can
take only one action on the next turn, so that wording overstated the immediate
score value when `n > 1`.

The annotation now reports the number of guaranteed-play options and explicitly
caps the immediate opportunity at one point. New manifests record
`clue_opportunity_annotation: one_action_cap_v2` so runs using the corrected
criterion are distinguishable from the earlier 14.31/25 policy result.

The existing result remains valid for its original prompt, but a corrected
baseline rerun is required before claiming that the new criterion improves JEV.

Use `./run_corrected_baseline.sh` for the 100-game corrected baseline and
`./run_multi_signal_pilot.sh` for the 10-game targeted signal pilot.
