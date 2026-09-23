# Corrected risk-penalty 0.1 pilot

This 10-game pilot subtracts `0.1 * harmful_probability * 4` from each JEV
score before selecting an action. All safety and corrected-criterion filters
remain enabled.

- Mean: **14.4/25**
- Scores: 17, 17, 14, 13, 12, 17, 13, 12, 17, 12
- All 10 games retained all 3 lives
- Seeds: 0–9

A 50-game replication on seeds 50–99 is defined by
`run_risk_penalty_01_replication.sh`.
