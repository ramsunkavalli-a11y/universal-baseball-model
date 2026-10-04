# Source preparation and scoring repairs

2026-10-04. The saved contract and preflight remain intact. None of these
execution repairs changes the declared experiment, fits or forecast outputs.

Two preparation attempts stopped before the preflight was sealed and before
any fit. First, arithmetic rebuilding differed from some unchanged inputs at
floating-point roundoff, although all comparisons were within 1e-12. The
candidate now copies original inputs exactly outside the three affected
origins. Second, the support export tried to stack broad and refined tables
with different columns; the corrected export explicitly preserves both schemas.
The final preparation completed all 70 checks and 35 control replays.

The first scoring attempt replayed the classifiers but stopped before writing
scores: it referenced a ZiPS PA field absent from the saved forecast table.
The [corrected scoring entry point](../scripts/score_hitter_available_season_history.py)
uses the already declared matched public sample: positive origin MLB PA and
both public-system index fields present, exactly 2,627 rows. It verifies the
sealed runner and applies only that one selector replacement in memory.
The original runner remains byte-identical to the prefit hash. The repair
receipt records both instructions and their hashes. Neither forecast models
nor primary prospect scoring change. This is not selection based on results.

Two initial unit checks also stopped on fixture issues: mixed integer widths
in a synthetic future-row stack and a deliberately removed season that
triggered the coverage check before the intended game/count check. Corrected
fixtures test both future invariance and count/game disagreements. Nine checks
then passed. Do not count the failed attempts as successful checks.

The case tracer saved all case evidence and its hash receipt, then stopped
while printing the console summary because its JSON import was missing. Adding
that import and a read-only summary command did not rerun fits or overwrite the
saved cases. The receipt is checked before the final human review.

The first descriptive roster diagnostic reused a highest-level helper that
assigns Mexico the same ordinal level as AA. That mixed group is not a valid
affiliated AA/AAA comparison. The separate-Mexico diagnostic replaces it for
interpretation, with 563 Mexico-without-A-or-higher-affiliated cases explicitly
separate. Both local diagnostics remain preserved. No model or scoring changes.
