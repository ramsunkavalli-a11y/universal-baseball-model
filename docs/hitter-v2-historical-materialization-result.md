# Hitter v2 historical materialization result

Date: 2026-08-25

Scientific result: full 2019 MiLB source materialization and independent 2020
MLB source certification passed; historical model use remains closed

## Result

The older sources are now more than a promising inventory. Complete 2019 MiLB
PBP and player-game files were processed across all five affiliated level
groups, and the shortened 2020 MLB season independently reconciled to official
outcome totals.

No candidate was fit or scored. These artifacts are not yet predictors, and no
protected 2026 outcome or participant payload was opened.

## 2019 MiLB

The full materialization produced:

- 3,722,608 PBP rows and 895,950 regular-season terminal PAs;
- 893,333 official PA across 225,197 player-game rows;
- 221,241 model-ready player-game rows, a 98.2433% readiness rate;
- 5,778 player-season rows, 4,538 players, 11,835 games, and 14 actual leagues;
- 217,555 exact rows and 3,686 accepted official unique repairs; and
- 3,956 retained failed-closed rows rather than imputed outcomes.

The failed-closed population consists of one unresolved official snapshot, 154
PBP-overcount rows, and 3,801 other reconciliation rows. The output retains all
of them as exceptions. Model-ready accounting covers 877,869 PA exactly; the
remaining source rows are not silently treated as neutral or zero.

The strongest structural lesson is that the 2019 topology is not the modern
topology. For example, the `aaa` filename partition contains actual leagues
112, 117, and 125, while `a+` contains 110, 122, and 123. Same-game structured
league identity was therefore essential; applying the post-2021 level map would
have mislabeled historical environments.

## 2020 MLB

The official regular-season window was July 23 through September 27. Seventeen
Savant chunks produced 66,506 PA across 17,963 player-game rows and 581 players
in both AL and NL. Those outcomes reconcile exactly to the official league-
season hitting backbone: zero PA, strikeout, walk/HBP, expected-contact, or
special-event mismatch rows.

The official schedule lists 900 games while player-game batting evidence
contains 898; games without batting evidence do not create PA. A one-contact
physical residual remains a declared diagnostic and does not alter the exact
outcome accounting.

The first 2020 execution correctly stopped on Oakland's source display label:
current Savant emits `ATH`, while the season-specific official authority emits
`OAK`. The repo already had this explicit mapping for 2021-2024. The correction
extended only the season-scoped alias to 2020; unknown teams still fail closed.

## Incidents preserved

The first 2019 attempt hit GitHub's public metadata rate limit before any source
payload was downloaded. Execution was corrected to use the prior hash-pinned
2019 filename matrix and direct release files. The scientific scope did not
change.

Both incidents and their pre-correction failures are committed. Neither involved
model fitting, scoring, or target access.

## Validation and evidence

Canonical lint passed and all 1,015 repository tests passed. Generated evidence
is ignored by git and pinned by SHA-256:

- 2019 MiLB report:
  `ffd39306f5ea215fc287f4a24afc3f95fc06dada3aac4ac43b3cc316df40e83f`;
- 2020 MLB report:
  `f342d06016b650d4d3203684b306f196915e9b42b117b3a0d7ad4d49d2e21287`.

## Exact stop and next gate

This gate stops here. The artifacts may not enter a projection until a separate
contract freezes chronology, the missing 2020 MiLB gap, shortened-season
reliability, folds, baselines, and promotion metrics.

The next source-only option is full 2017 MiLB materialization, now that the 2019
workflow has passed. Alternatively, the next modeling option is to preregister
exactly how 2019 MiLB and 2020 MLB history would be added to raw C0 and compared
with Marcel—before any fit or score.
