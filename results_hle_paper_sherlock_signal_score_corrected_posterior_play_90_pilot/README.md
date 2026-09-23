# Corrected posterior-play threshold pilot

This 10-game pilot enabled `HANABI_FORCE_POSTERIOR_PLAYS=1` with an exact
joint-play threshold of 0.90, while retaining the corrected one-action clue
criterion and the current discard/clue filters.

- Mean: **13.6/25**
- Scores: 14, 12, 13, 15, 15, 15, 12, 15, 16, 9
- All 10 games retained all 3 lives
- Seeds: 0–9
- API calls: 758

The pilot is below the corrected 200-game baseline (14.37/25) and the
corrected risk-penalty pilot (13.9/25), so this policy is not promoted.
