# JEV Sherlock Score with numeric play and discard values, 100 games

This policy uses the 10% posterior discard filter and annotates every offered
play and discard with the exact joint posterior play probability for that slot.
It also annotates guaranteed signal clues with their next-turn point
opportunity. JEV still ranks the actions; the annotations do not select one
directly.

- Seeds 10–109, 100 games, 2-player self-play
- Mean score: **13.32/25**, median 13, range 8–18
- All 100 games retained all 3 lives
- 7,565 JEV decisions
- 0 unoffered selections and 0 selected unsafe plays

Against numeric play/clue annotations without discard values (12.84/25) on the
same seeds, the paired improvement is **+0.48 points** (95% paired t interval
**−0.03 to +0.99**), winning 49 games, tying 17, and losing 34. Against the
plain 10% safety filter (12.26/25), the paired improvement is **+1.06 points**
(95% interval **+0.54 to +1.58**).

This is the strongest single 100-game run so far, but the refinement still
needs a fresh seed-block replication before being treated as robust.
