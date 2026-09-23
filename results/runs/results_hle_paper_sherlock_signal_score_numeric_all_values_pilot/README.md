# JEV Sherlock play, clue, and discard value annotations, 10-game pilot

This pilot adds an information-gain annotation to the numeric play/discard
policy. Each clue is annotated with its matched-card count and approximate
reduction in the recipient's possibility-set entropy, in addition to guaranteed
play signals.

- Seeds 0–9, 10 games
- Mean score: **13.5/25** (scores 15, 13, 12, 13, 14, 16, 14, 12, 14, 12)
- All games retained all 3 lives

The discard-value policy without this clue annotation scored 13.8/25 on the
same seeds. This pilot does not justify a 100-game expansion; the clue-value
control remains opt-in for future experiments.
