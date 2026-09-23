# JEV Hanabi Watson run (100 games)

This run evaluated 2-player self-play on seeds 10–109 using the public
`mahesh-ramesh/hanabi` Prime environment, version
`nees3rw1f786tt0ojf1ef9m9`, with `hanabi-learning-environment-mahesh==0.0.2`.
It uses the authors' Watson prompt builder and environment parser/step logic.
JEV (`jev-latest`) selected among indexed legal moves through the JEV Choice
API. This is a protocol difference from the paper's free-form completions.

`games.jsonl` records the prompts, requests, responses, selected and applied
moves, and final score for each game. `summary.json` records the per-run means,
seeds, action counts, and model-comparison reference values. `manifest.json`
records input and result hashes. The 10-game pilot and this 100-game run are
summarized together in `../results_hle_watson_combined.json`.
