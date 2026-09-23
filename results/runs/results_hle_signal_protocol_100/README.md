# JEV Hanabi: signal protocol, 2-player Sherlock

## Result

JEV 1.13.0 averaged **8.96/25 over 100 games** (seeds 10–109). The paired clean-Choice JEV control averaged 3.83/25 on the same seeds: mean paired gain **5.13 points** (95% paired t interval 4.52–5.74; bootstrap interval 4.54–5.73). The protocol run retained all three lives in 100/100 games.

## Protocol

The run uses the paper's Sherlock observation scaffold: engine-computed per-card possibility sets, visible teammate cards, discards, and fireworks. It adds a shared signal rule: if any guaranteed-safe play is available, the action set contains only those safe plays; otherwise, clue descriptions identify clues that would make a teammate card guaranteed playable. JEV selects among the offered actions through the Choice API.

## Audit and data

`games.jsonl` contains 100 complete game trajectories, prompts, JEV requests/responses, and engine actions. `comparison.json` gives the paired analysis, decision-level probability summaries, and audit counts. `manifest.json` records sample counts and SHA-256 hashes. All 7,356 selected actions mapped to the engine-applied move; there were zero protocol violations and zero failed plays. The mean JEV chosen-option probability was 0.405; this is not a calibration estimate because optimal-action labels are unavailable.

## Limits of the paper comparison

The authors' 2-player Sherlock means include 6.5 for GPT-4.1 mini, 14.8 for GPT-4.1, 17.5 for DeepSeek-R1, 14.6 for o4-mini, and 17.6 for o3. Those are averages over 10 seeds using free-form reasoning. This is a 100-seed JEV run with a structured Choice interface and an explicit safe-play scaffold, so scores are informative context, not a controlled head-to-head comparison. See the [paper results](https://kaousheik-26.github.io/llms-hanabi-cooperative-reasoning/).

## Bayesian calibration for the next iteration

The initial independent slot estimate was replaced with a joint hand posterior that accounts for duplicate-card competition. On the saved trajectories, 78/83 non-guaranteed slot-turns with posterior probability at least 90% were playable. This is a descriptive threshold diagnostic, not an outcome estimate for the new policy; see `bayes_calibration_audit.json`.

## Integrity audit note

The whole-file SHA-256 in `manifest.json` is valid. I initially mistook its
`e3b0ce...` prefix for the empty-file digest; the actual empty-file digest is
`e3b0c4...`, and independent implementations reproduce the recorded non-empty
file hash. `integrity_audit.json` adds per-row hashes and a root as a second,
more granular way to verify all 100 JSONL records.
