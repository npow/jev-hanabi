# JEV Hanabi Watson pilot (10 games)

This was the initial 2-player self-play pilot on seeds 0–9, using the public
`mahesh-ramesh/hanabi` Prime environment, version
`nees3rw1f786tt0ojf1ef9m9`, with `hanabi-learning-environment-mahesh==0.0.2`.
JEV (`jev-latest`) selected among indexed legal moves through the JEV Choice
API. This is a protocol difference from the paper's free-form completions.

This pilot is retained separately and should not be treated as the primary
estimate. The 100-game expansion on seeds 10–109 and combined audited results
are documented in `../results_hle_watson_expanded/README.md` and
`../results_hle_watson_combined.json`.
