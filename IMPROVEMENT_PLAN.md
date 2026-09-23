# Gameplay improvement plan

## Objective

Raise the two-player Sherlock score from the current **14.37/25** toward the
16–18 range while preserving the observed zero life-loss rate.

## Diagnosis

The safety layer is already effective: 2,873/2,873 guaranteed-play states took
a safe play and all 200 games retained three lives. The score gap comes after
that gate:

- 6,800 clue decisions and 5,342 discard decisions were made when no safe play
  was available.
- Only 2,756/6,800 clues (40.5%) created an immediate guaranteed-play option.
- Low-scoring games used 36.1 clues and 29.8 discards per game, compared with
  32.3 clues and 24.4 discards in high-scoring games.

The next system should improve decision quality in this branch while leaving
the safety gate unchanged.

## Intervention 1: action frontier

Add an engine-derived action frontier before the JEV request. For every legal
clue, compute:

1. Number of recipient cards that become guaranteed playable.
2. Information reduction in the recipient's possibility domain.
3. Whether the clue preserves a unique or high-value card.

For every discard, compute:

1. Joint posterior probability that the discarded slot is playable.
2. Probability that the discarded identity is a unique remaining copy.
3. Information-token recovery and deck phase.

Keep the Pareto frontier plus one safe discard. This should reduce the current
large pool of low-value ordinary clues without forcing a single clue type.

## Intervention 2: short-horizon rollout

For the frontier actions, evaluate a two-action horizon with the exact engine:

- Apply the candidate clue or discard.
- Enumerate the recipient's next legal safe plays under the resulting
  knowledge state.
- Score immediate play potential, preserved critical cards, and token cost.

Use this rollout to annotate the JEV Score descriptions. JEV still selects the
action, but it sees comparable estimates for every candidate rather than a
qualitative description of information value alone.

## Intervention 3: communication protocol

Encode one explicit protocol in the prompt:

- A clue that creates a guaranteed play is a play signal.
- The recipient plays one signaled card on the next turn.
- If multiple cards are signaled, use the lowest slot index unless a newer
  clue changes the state.

The protocol should be paired with the frontier rather than a blanket “force
all signal clues” gate. The prior multi-signal pilot shows that forcing a
coarse subset is insufficient.

## Experiment schedule

Use the same 40–50 fixed deal seeds for every arm, with independent JEV calls
and the seed recorded in every result row.

| Arm | Change | Pilot | Promotion gate |
|---|---|---:|---|
| A | Current policy | 30 games | Control |
| B | Action frontier | 30 games | Mean gain ≥0.5, no life loss |
| C | Frontier + rollout annotations | 30 games | Mean gain ≥0.75, no life loss |
| D | Frontier + rollout + protocol | 30 games | Mean gain ≥1.0, no life loss |

The action-frontier pilot (B) scored 14.60/25 on seeds 0–29 versus 14.80/25
for the paired current-policy control (12 wins, 5 ties, 13 losses; all games
finished with three lives). It did not meet the promotion gate, so it is not
promoted. The next run should add two-action rollout annotations before
retesting the frontier.

The rollout-annotation pilot (C) scored 15.00/25 versus 14.80/25 on the same
paired seeds (11 wins, 8 ties, 11 losses; all games finished with three lives).
The +0.20 gain is below the +0.75 promotion gate, so it remains an exploratory
arm rather than the default policy.

The posterior-certain gate pilot scored 15.17/25 versus 14.80/25 on the same
seeds (13 wins, 6 ties, 11 losses; all games finished with three lives). It
produced one 20-point game, but the mean remains well below the target and is
not promoted as the final policy.

The convention-prompt pilot scored 14.93/25 versus 14.80/25 (13 wins, 5 ties,
12 losses; all games finished with three lives). Verbal convention guidance did
not help; the next improvement must port executable convention state, not add
more prose to JEV's prompt.

Promote only the best pilot to a 100-game confirmation. Report mean, bootstrap
or t interval, score distribution, lives, plays/game, clues/game, discards/game,
signal-clue fraction, and the fraction of turns where the frontier removed the
chosen baseline action.

## Error labels for the next audit

The next run should label each non-play decision as one of:

- missed immediate signal
- useful information without immediate play
- redundant information
- discard of a playable or critical card
- productive discard
- token-starved endgame action

This converts the current descriptive pattern into intervention-specific error
counts and shows which mechanism actually changes score.

## Video / replay

After a winning arm is confirmed, generate a short replay using one low-score
and one high-score seed. Annotate each turn with the selected action, frontier
features, and the first divergence between the two trajectories. The replay is
for explanation; the 100-game evaluation remains the performance evidence.
