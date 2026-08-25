# Hitter v2 Stage 2d J0 pre-fit implementation checkpoint

Date: 2026-08-24

## Scientific outcome

The terminal-label gate was reviewed and J0 implementation was authorized. The
J0 mechanics and its chronology-safe real-data inputs are complete, but the
candidate has not been fit or scored. No forecast target and no protected 2026
outcome was opened.

The certified input contains 3,657,915 unique 2021–2024 PAs. All four batter-side
by pitcher-hand cells are present. Each pitcher feature uses only earlier game
dates, shrinks toward its contemporaneous league-season-level context, and is
exactly zero when no prior evidence exists. Failed-closed context retains the
existing B1 prediction exactly.

## Implemented J0 mechanics

The implementation covers the frozen nested nodes K, UBB, HBP, HR,
non-HR reach, and 1B/2B/3B hit composition. For each node it fits contextual and
uncontextual empirical-Bayes batter effects on identical observations and with
the same batter-effect variance. The only candidate increment is the difference
between those effects. This design prevents J0 from winning by changing its
cohort or by replacing B1's outcome forecast with a new unmatched model.

The contextual form contains league-season-level, platoon cell, and a strictly
prior pitcher same-node residual. Hit composition uses 1B as the additive-log-
ratio reference. The application function preserves the probability simplex and
isolates changes to the relevant nested component.

## Invariants and implementation finding

Synthetic tests prove same-date and future events cannot affect prior features,
zero evidence produces an exact neutral increment, empty or all-zero increments
return B1 byte-for-byte at the probability level, and composition adjustments do
not alter upstream node mass. They also exercise both matched fitter families.

The first synthetic chronology check exposed a numerical implementation problem:
recency exponents based on absolute calendar year produced unnecessarily huge
intermediate weights. The exponent was rebased to the earliest source season.
This is algebraically equivalent after normalization, target-free, and now makes
same-date/future invariance exact.

## Real input audit

The materialization accepted all 3,657,915 label-and-context-ready PAs without a
join loss. Prior-pitcher evidence is broad for K through non-HR reach. Hit
composition is naturally sparser: 684,479 eligible hits, 329,875 with at least
50 prior pitcher hits, and 143,349 with at least 100. That is a reason for the
frozen shrinkage, not permission to change the candidate after seeing results.

The ignored input parquet is 66,378,802 bytes with SHA-256
`a6cd82a5ac8c9382dc474a968bad6b5e6b48599b7ccfc1c6cfbe7a9a1cba515d`
and schema SHA-256
`5dd04538a5e025c7f9073af855624094e66c5e44c37c6e3c78424857bf5f792d`.
The durable result is `docs/hitter-v2-stage2d-input-result.json`.

## Boundary and next gate

The real-data execution contract is now frozen in
`docs/hitter-v2-stage2d-j0-fit-execution-contract.json`. Real-data fitting,
candidate scoring, validation tuning, J1, tracking, 2026 confirmation, Stage 3,
and WAR remain unauthorized. The exact next gate is review and authorization of
the J0 real-data fit only. Fitting does not authorize scoring.
