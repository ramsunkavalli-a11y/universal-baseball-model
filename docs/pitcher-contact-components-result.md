# Pitcher contact-component expansion result

Status: rejected in development; confirmation was not scored.

The audit reprojected 22,069 saved official StatsAPI pitching-season rows into
eight mutually exclusive batters-faced outcomes: strikeout, unintentional walk,
hit by pitch, single, double, triple, home run, and other out. It compared that
richer profile with the incumbent five-component model expanded onto the same
eight-outcome target.

On the frozen 2024 development target (173 pitchers and 23,129 MLB batters
faced), the incumbent scored 1.490572 component log loss and 0.705979 Brier.
Every richer candidate was worse on both proper scores:

| Regression prior | Log loss | Brier |
| ---: | ---: | ---: |
| 800 BF | 1.491140 | 0.706100 |
| 1,600 BF | 1.491504 | 0.706348 |
| 2,400 BF | 1.491899 | 0.706518 |
| 4,000 BF | 1.492398 | 0.706710 |

No candidate cleared the development gate, so the runner did not calculate or
expose a 2025 challenger score. The current broad contact bucket and 800-BF
regression remain in place.

This does not mean singles, doubles, and triples are unavailable. They are
present in the saved official captures. It means their observed minor-league
split did not add reliable future MLB pitcher signal beyond the simpler model.
Pitch-sequence features remain excluded because the available feeds are not
certified consistently across all affiliated levels.

Machine-readable evidence: `docs/pitcher-contact-components-result.json`.
Frozen protocol: `docs/pitcher-contact-components-plan.md`.
