# Hitter v2 Stage 2d J0 fit failure checkpoint

Date: 2026-08-24

## Scientific outcome

J0 did not complete its frozen real-data fit. The deterministic Laplace/EM
batter-variance estimator for a binary component failed to reach the predeclared
1% relative convergence tolerance within 20 variance iterations. The fit runner
exited with code 1 and published no complete or partial model artifact.

This is a real candidate failure, not evidence about predictive performance. No
forecast target was loaded, no player projection was scored, and protected 2026
outcomes remain unopened.

## Exact boundary

The executed command was:

`.venv\Scripts\python.exe scripts/fit_hitter_v2_stage2d_j0.py`

It ran from committed execution package `b093edf` against the frozen 3,657,915-PA
input. The exception was raised at
`src/universal_baseball/hitter_v2_stage2d.py:789` with message:

`J0 batter variance marginal-likelihood iteration did not converge`

The runner creates result artifacts only after all six component fits return.
The result directory was absent after failure, proving no partial fit was
silently accepted.

## What can and cannot be inferred

The failure establishes that the frozen variance-estimation procedure is not
production-capable on the certified full-data surface under its declared
iteration rule. It does not establish that opponent or platoon context lacks
signal, nor that J0 would fail an out-of-time projection test.

The frozen runner did not log the active node before entering each fit. The
traceback therefore identifies the binary family but not the exact node. It
would be scientifically improper to claim K or another component as the cause
without new evidence.

## No rescue

The tolerance, iteration count, priors, and code were not changed after the
failure. The fit was not rerun. Scoring this incomplete candidate, loosening the
rule until it passes, or treating an intermediate variance estimate as final
would violate the frozen contract.

The next legitimate gate is an independent method-and-observability review. A
future candidate would need a new pre-fit contract that first adds node-level
progress/failure diagnostics and justifies a variance estimator with demonstrated
full-data numerical behavior on non-decisional or synthetic surfaces. J1,
scoring, 2026 access, tracking, Stage 3, and WAR remain closed.
