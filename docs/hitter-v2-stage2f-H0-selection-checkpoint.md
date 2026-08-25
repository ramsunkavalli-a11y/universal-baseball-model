# Hitter v2 Stage 2f H0 training-origin selection checkpoint

## Scientific outcome

H0's configuration is selected and its prescore parameters are frozen. The
selection used only outcomes from seasons already inside each outer fold's
predictor history. It did not load Stage 2 target/evaluation tables, compute a
held-out accuracy metric, compare H0 with Marcel, or make a promotion decision.
This checkpoint therefore says the candidate is ready to test, not that it is
useful yet.

The final settings favor different shrinkage by batting component. In V2024,
recent evidence matters most for overall PA composition, strikeout avoidance,
contact, reaching base, and non-hit reaching outcomes; hit composition and
several sparse conditional branches retain longer histories and stronger
priors. The translation/development surface selected the strongest available
level-translation shrinkage (`1,000` mover PA) and the tighter development
prior (`0.05`). Calibration strength was exactly tied, so the frozen
conservative tie-break selected `0.10`.

V2022 has no earlier origin and therefore uses declared conservative defaults.
V2023 can select component shrinkage from its 2022 origin, but that origin has
no earlier adjacent-season pair from which the translation/development surface
could be identified. All 12 surface settings consequently tie and the same
conservative defaults apply. This is an honest absence of evidence, not a
zero-effect performance claim.

## Selection design

Each of nine nested outcome components evaluated the frozen Cartesian product
of three half-lives and four prior strengths. The surface evaluated three
translation priors, two development priors, and two calibration priors. Scores
are event log loss on strictly earlier training origins. Observed event targets
remain fixed across candidates; a candidate's neutral-reference prediction is
backtranslated to the observed scoring level using only its training-frozen
translation surface. This makes all candidate likelihoods comparable while
preserving the neutral-reference forecast architecture.

The selected fold settings and every grid score are retained in the generated
artifact. The 2024 surface loss was `0.3818505259188169`; this is an internal
training-origin selection score and must not be presented as held-out model
accuracy. All 16,654 final forecasts preserve the frozen populations and have
finite, nonnegative, normalized probabilities with maximum simplex error
`4.44e-16`.

## Prefreeze incidents

Two early attempts were stopped because repeated table scans and row-wise
likelihood calculation made the full grid impractical. Immutable surface maps
and a vectorized likelihood replaced those paths; a direct invariant proves
the vectorized calculation matches the audited primitive.

A later prefreeze run exposed a more important design error: it translated the
observed response using each candidate's translation setting. That would let
candidate configurations change the target they were scored against. The run
was rejected. The final implementation fixes the raw observed event target and
backtranslates predictions instead. No held-out, protected, or disclosed
validation result informed this correction, and no partial winner was retained.

## Reproducibility and boundary

The complete output contains 30 tables plus the report, totaling 7,972,941
bytes. A clean repeat run reproduced the exact report SHA-256
`5d9d45d4343edefda5ddc83ba35baa8f5c95ced80f53a0283bb9257703513a7b`.
Canonical lint passed, the focused authorization/selection suite passed seven
tests, and the full repository suite passed 980 tests.

Stop here for review. The next gate is a separately authorized, one-shot
comparison of this frozen H0 against the permanent baselines, including Marcel,
on the already disclosed validation folds. Retuning after that comparison is
forbidden. H1, tracking, protected 2026, Stage 3, and WAR remain closed.
