# Completed 2026 defensive inputs for the 2027 model

2026-10-08. The current source layer is ready for estimation, not a finished
forecast or proof of improved prediction. It adds 1,377 native player-position
records, 219 catcher throwing/blocking records, 111 framing records, 410 arm
records and 159 first-base receiving records. The previous historical inputs
and frozen forecasts are unchanged. Eight named source cases and same-position,
similar-exposure peers are retained in the linked machine review.

## What matters for the model

All eight native defensive components sum to published fielding run value,
both by position and by player. The eighth component is **ABS challenges**.
MLB assigns framing from the initial call and challenge value separately;
the challenge component must not disappear from the ledger or be counted as
framing twice. See [MLB's ABS definition](https://baseballsavant.mlb.com/abs-metrics-documentation).
There is only one MLB season here, so this does not validate persistent
individual challenge skill. The future rules scenario remains explicit.

There are 60 positive-out official position stints without a corresponding
native position measurement. Aggregate exposure also includes some pitching.
These differences do not invalidate exact run additivity, but they do mean we
must qualify each position's exposure independently. José Tena's zero-out SS
record has a tiny range numerator; it cannot define a per-inning skill rate.
Missing position quality stays unknown, not measured zero defense.

All arm numerators match native credit. Receiving opportunities and their
six throw categories reconcile, but 159 receiving rows have small differences
between 0.75 times receiving OAA and the separately retrieved native run total.
The largest is 0.008122 run (Alonso), below 0.001 WAR. Use the published native
run numerator and the independently verified throw count, retaining both
versions and their discrepancy. The .01-run source materiality limit is not
a fitted skill threshold. We do not claim an explanation or exact equality.
[Savant documents the 0.75 conversion](https://baseballsavant.mlb.com/leaderboard/fielding-run-value?seasonEnd=2026&seasonStart=2026).

## Player checks

- **Bailey:** 2,484 catcher outs; +4.551 framing, +3.464 throwing,
  -2.003 blocking and +1.460 challenges = +7.472 measured runs. Throwing uses
  62 attempts, blocking 3,727 chances, framing 7,174 received pitches. Those
  denominators must remain different in the projection.
- **Lindor:** 2,683 SS outs and +0.371 total native runs. His +0.956 arm credit
  comes from six opportunities at shortstop; do not call it an outfield-arm
  grade or infer a reliable elite rate from six chances.
- **Olson:** 4,272 first-base outs match official innings. Three other-position
  outs explain the larger aggregate. Range +8.505, DP +2.409 and receiving
  +1.376 sum to +12.291 runs; receiving is not range counted twice.
- **Trevino:** 1,107 catcher outs, not his full aggregate 1,137. Twenty-seven
  pitching outs and three omitted other-position outs cannot increase his
  catcher exposure. His catcher components sum to +4.153 runs.
- **Judge:** RF range -1.693 and arm +0.646 give -1.047 runs; throwing uses
  136 runner opportunities, not his 285 batting PA.
- **Eldridge:** 1,016 MLB first-base outs now supply real measured evidence:
  +0.212 range, +0.443 DP and +1.210 receiving. A 2027 model should update his
  evidence status rather than keep the old blanket prospect fallback.
- **Ohtani:** absence from the position-fielding table does not indicate a
  missing everyday defensive record. DH role and two-way economics remain
  separate from measured position defense.
- **Lovich:** no MLB defensive record means unknown MLB fielding talent. His
  2026 minor-league evidence can inform role/profile estimates, not manufactured
  measured MLB range.

The 2026 run environment reconciles batting runs with pitching runs allowed.
It gives 9.821815 runs per win. The existing 570-WAR replacement convention,
adjusted for 2,429 actual games and 183,849 PA, gives 18.263239 replacement
runs per 600 PA. These are source-season accounting inputs; next-season league
environment and centering must be explicit, not assumed realized 2027 totals.

## Evidence and disposition

[Reconciliation](../reports/model-evidence/hitter-2027-v1/nonbatting-source-reconciliation.json)
preserves gaps and exact checks. The subsequent
[player review](../reports/model-evidence/hitter-2027-v1/nonbatting-source-player-review.json)
authorizes these inputs for estimation, including the materiality-qualified
receiving adapter. It does not certify prediction accuracy. Use the existing
reviewed history estimators next; do not start a new algorithm search.
