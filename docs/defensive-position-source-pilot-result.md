# MLB position splits recover useful defensive evidence

2026-10-06. The official position grouping supplies actual position-specific
range runs and innings, not a primary-position label or an allocation of season
totals. The 2022/2025 pilot can recover evidence lost by the earlier purity rule.
This is a verified measurement source for its observed rows, not an improved
talent forecast. No fit, scoring comparison or production change occurred.

## Source checks

The pilot requests explicit historical years and `groupBy=position`, confirming
the embedded query. It captures 1,454 player-position rows for 679 people in
2022 and 1,366 rows for 661 people in 2025, alongside same-vintage unsplit totals.
Every observed position exposure matches both the unsplit source's position
column and the dated official usage ledger exactly. Summed non-null split range
runs reproduce season totals within 1.3e-14 runs, below the fixed 1e-6 tolerance.

Total outs do not recompose without accounting for omitted exposures. The source
omits 74 positive-exposure positions totaling 441 outs in 2022, and 57 totaling
319 outs in 2025; the largest omitted stint is 24 and 18 outs respectively.
Their quality remains unknown, not zero. The aggregate also includes pitching
appearances absent from the position splits: all 65/70 native nonpitcher-position
gaps match official pitching outs. Together those two categories account for
every exposure recomposition discrepancy.

This qualifies the contract's all-outs requirement: the pilot does not certify
a complete observation at every positive-exposure position. It certifies the
present split measurements and records the absent positions explicitly. The
near-exact run sum does not justify assigning measured zero talent to omissions.
One observed 2025 infield row also has null range and must retain that null.

The live source makes small revisions to old captures: 368/348 player range
scores differ in 2022/2025, with largest changes 0.034/0.054 runs. Total outs are
unchanged. Use same-vintage split/aggregate pairs for source certification; do
not call these revisions a modeling improvement or overwrite the old anchors.

## Fixed player walkthrough

These four players were specified before the download. The numbers below are
measured 2025 MLB range, not origin talent estimates, full defense or WAR.

| Player and position | Native defensive outs | Range runs |
| --- | ---: | ---: |
| Edwards at 2B | 2,443 | +6.568 |
| Edwards at SS | 1,079 | −5.203 |
| Rafaela at CF | 3,502 | +19.404 |
| Rafaela at 2B | 495 | +0.015 |
| Mateo at SS | 207 | −2.168 |
| Mateo at 2B | 147 | −0.518 |
| Mateo at CF | 246 | −0.651 |
| Mateo at LF | 27 | +0.011 |
| Mateo at 3B | 6 | approximately 0 |
| Witt at SS | 4,020 | +18.165 |

**Edwards:** the previous aggregate +1.366 obscured very different results at
second and short. The split source supplies the separate observations without
pretending his SS results measure second-base quality. Age/development and
measurement uncertainty still matter before these become a projection target.

**Rafaela:** almost all his +19.419 aggregate comes from center field. A minor
SS input predicting that total would not establish SS talent. The split keeps
the infield/outfield distinction explicit; his 495 second-base outs remain
limited evidence even though the position join is now correct.

**Mateo:** the earlier rule discarded every mixed-position season. We now have
real SS measurements separately from other positions. The 2025 SS stint is
still small and poor; recovering it does not prove a good talent forecast.
His clean 2022 SS measurement is 3,772 outs and +7.578 range runs, reproducing
the unsplit total. A multiyear target must include the whole fixed path, not
select that favorable season and ignore later results.

**Witt:** his 2022 aggregate −8.658 separates into −6.884 SS runs over 2,477
outs and −1.773 third-base runs over 1,332 outs. The new source makes that
season usable by position rather than discard it. His later positive SS scores
must still be treated as development over time, not proof that origin talent
was already identical to his mature performance.

Edwards and Rafaela have no 2022 MLB rows; the walkthrough reports absence,
not invented comparisons. Gains, forecast errors and full-WAR effects do not
apply to this source-only pilot. Present-row exposure, run recomposition and
source vintages are checked for the whole pilot, not just the four names.

## Next step and limits

Extend this exact source design to completed 2016–2025 seasons, retaining all
positive-exposure position inventory and missing/null quality flags. Rebuild
fixed-window measurements on the unchanged minor-origin cohort and repair
dated origin context, then recount chronological support. Do not replace this
work with another play-share tuning sweep.

Better labels can recover utility players; they cannot create pre-2016 minor
features or turn five/seven-year historical windows into supported chronological
tests. Position-specific innings remain an exposure proxy, not individual
fielding chances. A retrospective held-player measurement study, if later
chosen, must be labeled differently from a real historical forecast test.
No component has been promoted and no accuracy gain is established yet.
