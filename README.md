# JEV Hanabi benchmark

Reproducible evaluation of JEV on the public Sherlock Hanabi environment from
the Sparks of Cooperative Reasoning benchmark. The harness uses the paper
environment and JEV's structured **Score** interface: JEV independently rates
each legal action, then the highest expected score is applied.

## Current result

The corrected policy uses:

- Sherlock, 2-player self-play
- paper-style signal prompt
- guaranteed-safe play gate
- 10% posterior discard safety filter
- redundant-clue filter
- corrected one-action clue criterion (`one_action_cap_v2`)

It scored **14.37/25 over 200 games** (seeds 10–209), with all games retaining
all three lives. The published Sherlock references in the harness are GPT-4.1
mini 6.5, GPT-4.1 14.8, DeepSeek-R1 17.5, o4-mini 14.6, and o3 17.6. These
comparisons are contextual: the paper runs use free-form completions while
this benchmark uses JEV's structured Score API.

The latest risk-penalty candidate (0.1) scored **14.64/25 on 50 games** versus
**14.52/25** for its matched zero-penalty control; the difference was not
statistically established. See
[`REPLICATION_SUMMARY.md`](REPLICATION_SUMMARY.md) and
[`CORRECTED_200_ANALYSIS.md`](CORRECTED_200_ANALYSIS.md) for the full audit.

## Setup

```sh
git clone https://github.com/npow/jev-hanabi.git
cd jev-hanabi
cp .env.example .env       # edit only in your local copy, or export directly
export JEV_API_KEY='...'
cd paper_env
uv sync                    # Python >=3.11; creates the local environment
cd ..
```

The scripts invoke `paper_env/.venv/bin/python`. If `uv` is unavailable,
install the dependencies described in [`paper_env/pyproject.toml`](paper_env/pyproject.toml)
inside another Python 3.11+ environment.

## Reproduce the corrected baseline

The 100-game block is defined by [`run_corrected_baseline.sh`](run_corrected_baseline.sh):

```sh
./run_corrected_baseline.sh
```

Set `HANABI_RESUME=1` only when resuming the exact output directory after a
transient API failure. Every run writes `summary.json`, `manifest.json`, and
`results_integrity.json`; the manifest commits the environment, policy, seed,
source, harness, and result hashes.

## Repository layout

- `benchmark_hle.py`: main paper-environment harness and policy gates.
- `paper_env/`: pinned public Hanabi environment source and lockfile.
- `run_*.sh`: declared experiments.
- `results_hle_*/summary.json`, `manifest.json`, and `README.md`: compact result
  artifacts. Raw JSONL transcripts are intentionally ignored because they are
  large and contain full prompts.
- `CRITERION_FIX.md`: correction to the clue opportunity criterion.
- `REPLICATION_SUMMARY.md`: experiment table and statistical comparisons.

No API key is committed. Live runs require `JEV_API_KEY` in the process
environment.
