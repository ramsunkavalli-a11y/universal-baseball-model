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
- **Defense v1 catcher channel:** **quarantined for source repair** after discovering that the legacy Savant catcher query returned the same payload for multiple requested seasons.
- **Player Value architecture:** frozen; run-conversion/exposure/positional-adjustment research active where independent of the catcher repair.
- **WAR/value and Overall Ranking:** not authorized yet.

## Catcher source repair

Binding contract: [`docs/defense-v1-catcher-source-repair-contract.md`](docs/defense-v1-catcher-source-repair-contract.md).

The repair changes only the broken catcher target source. It preserves the original preregistered C1/C2 candidate families, development folds, eligibility, promotion thresholds, and one-shot confirmation rules.

The prior catcher development and 2025 confirmation results remain in the repo as audit evidence but are not binding until rerun against genuinely year-specific targets.

**General Defense is unaffected and must not be reopened.**

## Player Value v1

Architecture contract: [`docs/player-value-v1-architecture-contract.md`](docs/player-value-v1-architecture-contract.md).

Key rules:

- reuse the existing Performance RE24/bin-value foundation for batting;
- keep defensive skill separate from run conversion;
- do not assign arbitrary `runs per z` constants;
- use frozen Playing Time and the full Position/Role share vector for exposure;
- keep positional adjustment separate from position-relative Defense skill;
- keep replacement level and runs per win as later explicit decisions;
- do not calculate WAR until every component is independently frozen.

The Defense native-scale audit is at [`docs/player-value-v1-defense-native-scale-audit.json`](docs/player-value-v1-defense-native-scale-audit.json). Its general-range diagnostics remain usable; its catcher diagnostics are quarantined because they exposed the source problem.

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
- [`docs/defense-v1-catcher-source-repair-contract.md`](docs/defense-v1-catcher-source-repair-contract.md) — active catcher repair gate.
- [`docs/savant-catcher-year-filter-diagnostic.json`](docs/savant-catcher-year-filter-diagnostic.json) — direct source diagnostic.
- [`docs/player-value-v1-architecture-contract.md`](docs/player-value-v1-architecture-contract.md) — frozen downstream architecture.
- [`docs/player-value-v1-defense-native-scale-audit.json`](docs/player-value-v1-defense-native-scale-audit.json) — pre-2025 native-scale diagnostic.
- [`docs/defense-v1-2025-confirmation-result.json`](docs/defense-v1-2025-confirmation-result.json) — general Defense result remains binding; catcher portion quarantined.
- [`docs/position-role-2025-confirmation-result.json`](docs/position-role-2025-confirmation-result.json) — frozen Position / Role v1 confirmation.
- [`docs/playing-time-v1-confirmation-result.json`](docs/playing-time-v1-confirmation-result.json) — frozen Playing Time v1 confirmation.
- [`docs/projection-batting-v1-development-result.json`](docs/projection-batting-v1-development-result.json) — frozen Projection v1 decision.
- [`docs/current-talent-results-only-baseline-freeze.md`](docs/current-talent-results-only-baseline-freeze.md) — frozen Current Talent baseline.
- [`docs/performance-2024-affiliated-checkpoint.md`](docs/performance-2024-affiliated-checkpoint.md) — completed-2024 affiliated batting Performance checkpoint.

## Development workflow

1. Reuse certified public work and existing repo adapters before rebuilding source ingestion.
2. Work in small verified batches and verify each batch before expanding scope.
3. Freeze model form/search space/validation rules before opening held-out outcomes.
4. Preserve invalid-source artifacts as audit evidence rather than rewriting history.
5. Update `docs/project-status.md` whenever a major gate or blocker changes.
