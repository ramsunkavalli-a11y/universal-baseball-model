# Linked pitcher common-distribution plan

Status: frozen before scoring.

## Question

Does the linked historical pitcher performance path improve zero-inclusive CRPS after
the cutoff-reconstructed incumbent is also given workload and conditional-rate
uncertainty?

## Frozen method

- Reuse the identical 3,642-player 2021 forecast cohort, 2018 hurdle fit, 2022–2025
  outcomes and path library complete by the 2021 cutoff.
- Candidate remains the arrival-only pooled historical component-WAR path mixture.
- Incumbent retains its tiered historical workload paths and each player's cutoff-safe,
  Tango-aged annual WAR rate.
- Add the incumbent's existing event and posterior run-rate variance with 21 fixed
  midpoint normal quadrature nodes. Do not tune the spread to these outcomes.
- Keep the exact non-arrival zero mass in both distributions.
- Compare player-paired CRPS with 2,000 deterministic bootstrap draws and verify that
  each distribution mean equals its existing expected-WAR prediction.

This is an exposed development cohort. Any result can refine architecture but cannot
promote a model or change current values. Genuinely fresh confirmation remains a
separate requirement.
