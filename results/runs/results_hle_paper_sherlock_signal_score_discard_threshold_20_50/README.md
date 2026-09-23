# discard threshold replication

This 50-game replication raises `HANABI_DISCARD_MIN_PLAY_PROBABILITY` from
0.10 to 0.20 while retaining the one-action clue criterion and all
other current policy settings.

- Mean: **14.52/25**
- 95% normal interval: **13.87–15.17**
- Median: 14
- Range: 10–20
- Seeds: 0–49
- Games: 50/50 complete
- All games retained all 3 lives

The result is a promising candidate relative to the 200-game mean of
14.37/25, but it is not a confirmed improvement because JEV sampling makes
independent same-seed runs noisy. A matched replication is required before
promotion.
