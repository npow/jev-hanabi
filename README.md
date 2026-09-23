# JEV Hanabi benchmark

Reproducible evaluation of JEV on the public Sherlock Hanabi environment from
the Sparks of Cooperative Reasoning benchmark. The harness uses the paper
environment and JEV's structured **Score** interface: JEV independently rates
each legal action, then the highest expected score is applied.

## Current result

The primary evaluation setup uses:

- Sherlock, 2-player self-play
- paper-style signal prompt
- guaranteed-safe play gate
- 10% posterior discard safety filter
- redundant-clue filter
- one-action clue opportunity accounting

It scored **14.37/25 over 200 games** (seeds 10–209), with all games retaining
all three lives. See [`METHODS.md`](METHODS.md) for the setup and
[`RESULTS.md`](RESULTS.md) for the complete comparison table.

The primary estimate and sensitivity runs are summarized in
[`RESULTS.md`](RESULTS.md). Run-level manifests are retained under
[`results/runs/`](results/runs/) for reproducibility.

The action-level diagnostic is in [`ERROR_ANALYSIS.md`](ERROR_ANALYSIS.md),
with a generated figure and reproducible analysis script.

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

## Reproduce the baseline

The 100-game block is defined by [`run_primary_baseline.sh`](run_primary_baseline.sh):

```sh
./run_primary_baseline.sh
```

Set `HANABI_RESUME=1` only when resuming the exact output directory after a
transient API failure. Every run writes `summary.json`, `manifest.json`, and
`results_integrity.json`; the manifest commits the environment, policy, seed,
source, harness, and result hashes.

## Repository layout

- `benchmark_hle.py`: main paper-environment harness and policy gates.
- `paper_env/`: pinned public Hanabi environment source and lockfile.
- `run_*.sh`: declared experiments.
- `results/runs/`: compact result artifacts and manifests. Raw JSONL transcripts
  are intentionally ignored because they are large and contain full prompts.
- `METHODS.md`: experimental setup and reproduction details.
- `RESULTS.md`: consolidated findings and comparisons.

No API key is committed. Live runs require `JEV_API_KEY` in the process
environment.
