# JEV Hanabi Sherlock run (100 games)

JEV 1.13.0 played 2-player self-play on seeds 10–109 using the paper's pinned
Prime environment and `hanabi-learning-environment-mahesh==0.0.2`. Sherlock
provides engine-generated per-card possibility sets. The adapter asks one
structured Choice question over legal moves and applies the selected move
through the environment's Sherlock parser and step logic.

`games.jsonl` contains full per-turn prompts, JEV requests/responses, and engine
trajectories. `summary.json` contains the aggregate run; `manifest.json` records
hashes. `comparison.json` includes paired results against Watson variants and
checks all selected-to-applied move mappings.
