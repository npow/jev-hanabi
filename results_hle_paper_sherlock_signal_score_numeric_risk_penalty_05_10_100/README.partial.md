# Incomplete risk-sensitive score run

This experiment applies `HANABI_SCORE_RISK_PENALTY=0.5` to the current best
numeric-value policy. It completed **85/100** requested games (seeds 10–94)
before the JEV API returned HTTP 402 Payment Required. No summary or integrity
manifest was generated, so this directory is not a complete benchmark result.

- Partial mean: **14.45/25**
- Paired difference versus threshold-0 policy on the 85 completed seeds:
  **+0.29** (95% paired t interval **−0.13 to +0.71**)
- Paired wins/ties/losses: **37/15/33**
- All 85 completed games retained all 3 lives

The harness supports resuming this exact output directory with
`HANABI_RESUME=1` after the API account can accept requests again. Do not use
the partial mean as a final policy comparison.
