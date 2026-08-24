# Hitter v2 methodology review

Status: **STAGE 0 COMPLETE — AWAITING REVIEW; NO HITTER V2 CANDIDATE SCORED**  
Date: 2026-08-23  
Reviewed base: protected `main` at `197d21a67d707633cb47d720c84a7b126b9c4320`

## Scientific outcome

Position-player v1 is mechanically reproducible but its batting construct is
not suitable as the foundation for Hitter v2. The frozen profile estimates
walk/HBP, strikeout, and ten contact direction/trajectory probabilities. It
does not retain player 1B/2B/3B/HR outcomes, and every player receives the same
pooled run value for a given contact-shape bin. Player-specific power and hit
quality on contact are therefore absent.

Stage 0 changes the active research program, not v1 history:

- position-player v1 and all frozen artifacts remain immutable historical
  prototypes;
- Pitching v1 foundation work remains preserved but new candidate development
  is paused;
- Hitter v2 is active, with ordinary affiliated PBP/official aggregates as the
  universal outcome foundation and tracking as a reliability-weighted optional
  increment;
- full WAR remains unauthorized until the PBP-only batting-rate gate passes.

## Reproductions and verification

### Clean `main`

The repository was clean and aligned with `origin/main`. In a local Python
3.12.13 environment installed from `.[dev]`:

- `python -m ruff check src scripts tests`: passed;
- `python -m pytest`: **819 passed** in 24.05 seconds.

The initial shell did not expose a `python` command and the bundled interpreter
did not contain Ruff/Pytest. Those were environment setup findings, not test
failures. The declared development environment was then installed in the
ignored local `.venv`.

### Frozen pure-batting leaderboard

The v1 leaderboard was rebuilt independently from the immutable
`projection_2023_to_2024/frozen_b2_profile.parquet` and three frozen 2024 MLB
Performance tables. It reproduced the previously generated 3,985-player JSON
and CSV exactly:

- same 3,985 player IDs;
- maximum absolute difference in runs/600: **0.0**;
- same ordered top 20;
- reproduced JSON SHA-256:
  `82c53f4b3e499e4ca285b0004065bb25cc96b49143071f9c09826dd21e8f7c78`;
- reproduced CSV SHA-256:
  `a21e404fc64a10031ba4d2eafa92420b143e5129bf21276e84139e457a8f0e0c`.

This is a reproduction of v1, not an endorsement of its estimand.

### External validity

The attached independent review is treated as evidence, not as an instruction.
Its SHA-256 is
`b91da4855f9bd5ded8902f1f1ad9015013a0fe06c956648a3dd674550e2a7277`.
It used official MLB season outcomes and the published 2024 FanGraphs wOBA
weights (`.689 uBB`, `.720 HBP`, `.882 1B`, `1.254 2B`, `1.590 3B`,
`2.050 HR`; scale `1.242`). The machine record is
`docs/hitter-v2-v1-external-validity-result.json`.

Verified disclosed results:

- 363 hitters with at least 200 official 2024 MLB PA: v1 batting score Pearson
  `0.192`, Spearman `0.170` with actual wOBA; Spearman `-0.012` with HR/PA and
  `-0.540` with K/PA; three of the v1 top 20 overlapped the actual wOBA top 20;
- identical 344-player prior-MLB-history subset: v1 Pearson/Spearman
  `0.185/0.160`, raw 2023 wOBA `0.308/0.286`, and the fixed simple Marcel-style
  outcome baseline `0.458/0.383`.

No new official outcome scoring was performed in this Stage 0 execution. A
network materialization limited in code to 2021–2024 was denied at the runtime
authorization boundary, so the task did not retry or work around it. This is a
provenance limitation, not a change to the disclosed result. The frozen v1
leaderboard reproduction itself was completed locally from immutable artifacts.

## PR #11 audit

Read-only local ref audited: `origin/export-batting-leaderboard` at `b22a368`.
No remote state was changed.

Findings:

- the committed CSV contains 20 data rows and four columns;
- the branch's current exporter emits all 3,985 players, eight columns, names,
  and a JSON companion;
- that JSON is absent from the branch;
- the workflow has automatic `push` and `pull_request` triggers, grants
  `contents: write`, commits generated files, and pushes back to its branch;
- this violates `docs/workflow-lifecycle.md`, under which only non-writing CI
  and CodeQL may run automatically and historical/scientific writers are
  manual-only.

Decision: **do not merge PR #11 as the canonical leaderboard**. Its snapshot is
mechanically inconsistent with its exporter and its workflow lifecycle is
incompatible with repository integrity. The branch remains untouched.

## Existing source capability audit

The repo should promote existing work rather than rebuild parsing:

- `current_talent_contact_value_source.py` already classifies structured
  terminal events and conservative narrative fallbacks into `1B`, `2B`, `3B`,
  `HR`, `ROE`, `FC_REACH`, `SF`, `MULTI_OUT`, and `OUT`;
- 2021–2022 MiLB source materialization supported **900,742 / 901,015** core
  terminal contacts (**99.9697008%**) across AAA through Rookie/complex;
- the 2023 confirmation source supported **595,619 / 595,794** contacts
  (**99.9706274%**) across MiLB and MLB;
- the parser preserves the 273 known 2021–2022 exclusions by explicit status
  rather than guessing (special/interference, ambiguous compound plays, other
  unsupported narratives, bunts, and blanks);
- existing tracking captures retain 142,201 / 171,415 / 206,542 canonical
  result-producing non-bunt BBE in 2021 / 2022 / 2023, with source capability
  tiers and player/game reconciliation;
- Challenger 2 showed stable incremental EV signal but failed its binding 2023
  MAE and calibration-intercept gates, so its result remains a documented
  failure rather than a production rescue candidate;
- canonical state replay, RE24, participant authority overlays, official
  player-game/season reconciliation, actual league/level identity, venue
  metadata, and chronology utilities are reusable.

The missing join is conceptually small but scientifically central: combine the
terminal contact groups with UBB, IBB, HBP, K, bunts, interference, and other
special PA outcomes into an exhaustive outcome table.

## 2025 outcome-access audit

2025 cannot be called untouched or used as the decisive Hitter v2 confirmation:

- official 2025 MLB hitting totals were materialized for Playing Time,
  including 182,926 source PA, and 2025 PA outcomes were scored;
- 2025 MLB/AAA fielding and hitting participation were materialized and
  Position/Role was scored;
- 2025 general range, tracked range, catcher throwing, blocking, and framing
  targets were materialized and scored;
- early source-certification and RE24 work inspected 2025 MLB and affiliated
  PBP slices, including a full-season Retrosheet RE24 audit and level-specific
  PBP/bin-value validation.

There is no evidence in the repository that a Hitter v2 terminal-outcome rate
candidate has been fit or scored on 2025 offense. Nevertheless the observed PA,
PBP, position, and defense surfaces are enough to make 2025 diagnostic-only.
The completed **2026** offense season is preregistered as the protected one-shot
confirmation and must remain unopened until the development gate is frozen and
review explicitly authorizes the source boundary. This Stage 0 did not inspect
2026 outcomes.

## Literature and method review

| Work | Idea adopted now | Deferred or rejected now |
|---|---|---|
| FanGraphs wOBA and position-player WAR | Separate UBB/HBP/1B/2B/3B/HR values; keep batting, baserunning, fielding, position, league, park, replacement, and RPW explicit | No target-season weights in a preseason forecast |
| Baseball-Reference WAR / PBP baserunning / Total Zone | Opportunity-defined advancement; traditional/PBP fielding fallbacks by observable data; neutral low-signal defense | Do not force framing/range precision where location/call context is absent |
| Marcel | Permanent competence floor: multi-year recency, regression to the mean, age kept simple and auditable | Marcel is a baseline, not the universal production specification |
| ZiPS | Multi-year component baselines, minor-league translations, age and comparable-shape thinking, cautious adoption of tracking | Proprietary/comparable-player machinery is not copied |
| OOPSY | Component-specific regression; league, park, age, recency, MLE, and tracking separated | Broad feature search before the outcome construct passes |
| KATOH | Separate MLB participation/opportunity from conditional rate talent | Opportunity modeling before the batting-rate gate |
| Jensen/McShane/Wyner | Hierarchical partial pooling across players/time and component-specific stability | A monolithic Bayesian implementation is not required for the first candidate |
| openWAR | Play-level run conservation, transparent components, simulation uncertainty | Full WAR allocation before batting passes |
| Retrosheet PBP crosswalk | Explicit PA/AB/hit/SH/SF/HBP/BB/IBB/K/interference, outs, runner origins/destinations, errors, batted-ball type/location, and fielding credits | Retrosheet does not redefine MiLB availability |

Primary references:

- https://library.fangraphs.com/offense/woba/
- https://library.fangraphs.com/war/war-position-players/
- https://www.baseball-reference.com/about/war_explained_position.shtml
- https://www.baseball-reference.com/about/marcels.shtml
- https://blogs.fangraphs.com/the-2021-zips-projections-an-introduction/
- https://blogs.fangraphs.com/yet-another-projection-system-a-brief-introduction-to-oopsy/
- https://blogs.fangraphs.com/a-primer-on-a-new-and-improved-katoh/
- https://arxiv.org/abs/0902.1360
- https://arxiv.org/abs/1312.7158
- https://www.retrosheet.org/downloads/pbpcrosswalk.html

## Ideas that change the plan

1. Terminal outcomes replace contact shape as the batting value target.
2. PBP is the universal fallback; validated tracking is an increment against the
   identical target and cohort.
3. Different batting components receive different shrinkage and translation.
4. Neutral batting talent, complete hitter rate value, MLB opportunity, and
   expected MLB WAR become distinct artifacts.
5. Forecast WAR and retrospective value become distinct estimands and pipelines.
6. 2025 is diagnostic-only and completed 2026 is protected confirmation.
7. Player names remain diagnostics only; all promotion gates are aggregate and
   predeclared.

## Deferred until later gates

- baserunning, defense, position exposure, bounded playing time, and WAR
  assembly;
- bat speed, pitch-level discipline, sprint speed, proprietary forecasts, and
  scouting data;
- broad black-box searches;
- any Hitter v2 candidate score;
- any 2026 outcome access.

## Stage 0 decision

Stage 0 passes as an audit/preregistration gate. It does **not** approve a model
or full WAR. The exact next gate, after review approval, is Stage 1 source-only
materialization of the exhaustive terminal-PA table plus reconciliation and
coverage invariants. Stage 2 candidate fitting/scoring and protected 2026 access
remain unauthorized.
