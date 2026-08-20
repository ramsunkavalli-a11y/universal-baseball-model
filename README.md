# Universal Baseball Model

A public-data baseball player evaluation and projection system covering MLB through affiliated minor leagues.

## Start here

Read [`docs/project-status.md`](docs/project-status.md) first. `main` is the latest integrated branch; active work newer than the last integration is on `source-certification-poc`.

## Current stage

- **Performance:** retained.
- **Current Talent:** frozen at `translated_multiseason_recency_empirical_bayes_v1`.
- **Projection v1 batting:** frozen at `frozen_current_talent_carry_forward_v1`.
- **Playing Time v1:** frozen and 2025-confirmed at `playing_time_recent_opportunity_40man_b2_hurdle_v1`.
- **Position / Role v1:** frozen and 2025-confirmed at `primary_share_thresholded_transition_mean_v1`.
- **Defense v1 general range:** frozen and 2025-confirmed; tracked MLB range when eligible, universal range otherwise.
- **Defense v1 catcher channel:** repaired, frozen, and verified with corrected throwing, blocking, and framing sources.
- **Player Value v1:** all batting, baserunning, Defense, position, centering, park, replacement, and runs-to-wins layers are frozen and verified.
- **WAR/value and Overall Ranking:** final 3,051-player 2024 point-estimate table is frozen and verified.
- **Forecast uncertainty:** deterministic 80% and 95% interval sidecar is frozen and verified; point rank remains binding.

## Player Value v1 result

Final aggregation contract: [`docs/player-value-v1-final-aggregation-contract.md`](docs/player-value-v1-final-aggregation-contract.md).

Frozen point result: [`docs/player-value-v1-final-2024.json`](docs/player-value-v1-final-2024.json).

Forecast-uncertainty result: [`docs/player-value-v1-uncertainty-2024.json`](docs/player-value-v1-uncertainty-2024.json).

The final additive form is:

`RAR = Rbat + Rbr + Rdef + Rpos + Rlg + Rpark + Rrep`

`WAR = RAR / RPW`

The verified population contains 3,045 players with complete frozen component surfaces plus six mandated official-MLB structural-zero rows. The final aggregate is `4610.597400956516` runs above replacement and `476.17201420774313` WAR at `9.682629939156854` runs per win. Ranking uses unrounded WAR descending and MLBAM player ID ascending only as the deterministic tie-break.

Key boundaries:

- reuse the existing Performance RE24/bin-value foundation for batting;
- keep defensive skill separate from run conversion;
- do not assign arbitrary `runs per z` constants;
- use frozen Playing Time and the full Position/Role share vector for exposure;
- keep positional adjustment separate from position-relative Defense skill;
- keep replacement level, MLB centering, park, and runs per win explicit;
- preserve every component, fallback flag, and provenance field;
- do not refit or reselect frozen upstream models from ranking or interval outcomes.

The repaired catcher integration and its superseded source history are documented in [`docs/project-status.md`](docs/project-status.md) and the Defense production handoff.

## Core principles

- Keep Performance, Current Talent, Projection, Playing Time, Position/Role, Defense, positional adjustment, run conversion, and Player Value separate.
- Prefer mature public datasets, parsers, and packages over rebuilding raw-source cleanup.
- Preserve uncertainty, coverage, provenance, and measurement quality.
- Validate chronologically and prevent hindsight leakage.
- Fail closed on unresolved source ambiguity.
- Promote only on fixed out-of-time evidence; do not rescue a challenger after a frozen gate fails.
- Repair only the scope affected by a concrete implementation failure.

## Current milestone documents

- [`docs/project-status.md`](docs/project-status.md) — canonical live handoff.
- [`docs/player-value-v1-final-aggregation-contract.md`](docs/player-value-v1-final-aggregation-contract.md) — frozen final population and arithmetic.
- [`docs/player-value-v1-final-2024.json`](docs/player-value-v1-final-2024.json) — verified point-estimate ranking summary.
- [`docs/player-value-v1-uncertainty-contract.md`](docs/player-value-v1-uncertainty-contract.md) — frozen forecast-interval method.
- [`docs/player-value-v1-uncertainty-2024.json`](docs/player-value-v1-uncertainty-2024.json) — verified interval summary.
- [`docs/player-value-v1-mlb-centering-2024.json`](docs/player-value-v1-mlb-centering-2024.json) — verified fixed-reference numerical centering.
- [`docs/player-value-v1-park-neutrality-audit-result.json`](docs/player-value-v1-park-neutrality-audit-result.json) — verified `Rpark = 0` decision.
- [`docs/player-value-v1-defense-production-handoff.md`](docs/player-value-v1-defense-production-handoff.md) — frozen repaired Defense machinery.
- [`docs/position-role-2025-confirmation-result.json`](docs/position-role-2025-confirmation-result.json) — frozen Position / Role v1 confirmation.
- [`docs/playing-time-v1-confirmation-result.json`](docs/playing-time-v1-confirmation-result.json) — frozen Playing Time v1 confirmation.
- [`docs/projection-batting-v1-development-result.json`](docs/projection-batting-v1-development-result.json) — frozen Projection v1 decision.
- [`docs/current-talent-results-only-baseline-freeze.md`](docs/current-talent-results-only-baseline-freeze.md) — frozen Current Talent baseline.
- [`docs/performance-2024-affiliated-checkpoint.md`](docs/performance-2024-affiliated-checkpoint.md) — completed-2024 affiliated batting Performance checkpoint.

## Development workflow

Install the complete local development environment and run the same checks as
the pull-request CI job:

```bash
python -m pip install -e ".[dev]"
python -m ruff check src scripts tests
python -m pytest
```

Install `.[playing-time]` instead when only the Playing Time model's
scikit-learn/statsmodels runtime is needed.

Historical certification and materialization workflows are retained for audit
and explicit manual use, but they do not run automatically after the v1 freeze.
See [`docs/workflow-lifecycle.md`](docs/workflow-lifecycle.md).

1. Reuse certified public work and existing repo adapters before rebuilding source ingestion.
2. Work in small verified batches and verify each batch before expanding scope.
3. Freeze model form/search space/validation rules before opening held-out outcomes.
4. Preserve invalid-source artifacts as audit evidence rather than rewriting history.
5. Update `docs/project-status.md` whenever a major gate or blocker changes.
