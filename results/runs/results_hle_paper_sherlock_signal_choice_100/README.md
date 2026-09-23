# JEV full Sherlock prompt + safety/signal protocol, 100 games

## Result

JEV averaged **9.72/25 over 100 games** (seeds 10–109), median 9, range
3–20. Every game retained all three lives; all 972 selected plays were safe.
The 95% t interval for the mean is **[9.02, 10.42]**.

This is the best current JEV configuration. It keeps the public environment's
complete Sherlock prompt, including its probability and critical-card guidance,
then applies a programmatic safety and signaling protocol: unsafe plays are
removed; guaranteed plays are offered alone; otherwise clue descriptions mark
clues that create guaranteed teammate plays. It uses JEV Choice over the
remaining actions.

Against the earlier 100-game `signal_protocol_sherlock` run on the same seeds,
the paired difference is **+0.76 points** (95% paired t interval **[-0.14,
1.66]**; wins/ties/losses 48/13/39). This does not establish a significant
improvement. The earlier run averaged 8.96/25.

## Audits

`audit.json` verifies 100 games, 7,623 decisions, zero selected unsafe plays,
zero unoffered actions, zero engine move mismatches, zero failed plays, and
3,510 clues / 972 plays / 3,141 discards. `results_integrity.json` commits each
JSONL row and its root hash; `manifest.json` records the whole-file hash.

## Paper comparison

The paper's 2-player Sherlock averages over 10 seeds are GPT-4.1 mini 6.5,
GPT-4.1 14.8, DeepSeek-R1 17.5, o4-mini 14.6, and o3 17.6. This JEV run uses
the paper's environment and state scaffold but adds the safety/signal protocol
and uses JEV Choice, so these are contextual comparisons rather than a
controlled head-to-head test.

See [`comparison.json`](comparison.json) and the
[paper results](https://kaousheik-26.github.io/llms-hanabi-cooperative-reasoning/).
