# Defense v1 source / architecture checkpoint

Last updated: 2026-08-18

Status: **SOURCE ARCHITECTURE GATES COMPLETE — READY FOR PRE-REGISTERED DEFENSE v1 DEVELOPMENT.**

## Downstream need

Defense must produce a player × position defensive-quality forecast that can be combined later with the already-frozen Position/Role and Playing Time channels. Position/Role answers *where* a player may play; Defense answers *how well* he is expected to field there.

Do not collapse defensive skill, positional adjustment, playing-time opportunity, or team allocation into one model.

## Range / OAA — reusable tracked component

Pinned public implementation: SportsDataverse `0.0.75`, upstream commit `1dafadb38c5240d8e29a0f818efbabe04cd6c417`.

### MLB implementation gate

The frozen June-2024 reuse POC passed the upstream Savant oracle gate:

- 116,355 pitches;
- 20,623 balls in play;
- 18,820 usable OAA opportunities (`91.26%` of BIP);
- 263 fielders matched to the full-season 2024 Savant OAA leaderboard;
- Pearson `0.3045`, passing the frozen month-vs-season floor `>= 0.30`.

SportsDataverse's own full-season 2024 test reports Pearson about `0.605` against Savant OAA.

**Architecture decision:** for MLB, prefer the public official Savant leaderboard when available; use SportsDataverse's public OAA implementation as the portable tracked implementation needed for MiLB and as an independent implementation check. Do not rebuild a public catch-probability model from scratch absent a concrete failure.

### Tracked MiLB execution gate

The default SportsDataverse minor-search parameters returned zero rows; the OAA implementation was not the problem. A source diagnostic established the correct public Savant transport for this project: `minors=true`, bounded date chunks, then client-side official team/league classification.

Frozen 2024-06-10 through 2024-06-16 result:

- total tracked MiLB pool: 35,352 pitches;
- AAA: 27,749 pitches / 4,479 BIP / 3,986 usable OAA opportunities (`88.99%`);
- tracked non-AAA: 7,603 pitches / 1,196 BIP / 803 usable opportunities (`67.14%`);
- all required trajectory/responsible-fielder fields present;
- both frozen execution/coverage gates passed.

Observed non-AAA home teams were Clearwater, Daytona, Dunedin, Fort Myers, and Jupiter, consistent with the public Florida State League tracking tier.

**Boundary:** this establishes technical reuse, not proprietary MiLB OAA accuracy.

## Catcher framing — reusable tracked component

Our own frozen framing reuse POC passed:

- MLB June 2024: 33 Savant-matched catchers, Pearson `0.5754` vs frozen `>= 0.50` gate;
- AAA: 14,298 eligible takes, 72 catchers, execution/coverage passed;
- tracked non-AAA: 3,183 eligible takes, 20 catchers, execution/coverage passed.

SportsDataverse framing is therefore the leading portable tracked framing implementation. For MLB, the official public Savant framing leaderboard remains the higher-quality direct Performance source when available.

No production framing projection is frozen yet.

## Catcher blocking / throwing

Do not use the SportsDataverse public throwing reconstruction as a production component merely because code exists: its full-season 2024 correlation with Savant is only about `0.073`, largely because public pitch descriptions recover a minority of actual SB/CS attempts.

Instead, the project's universal official fielding source supplies traditional catcher outcomes at every affiliated level. The forward-target test below shows that two of those simple rates carry meaningful next-season signal into Savant:

- prior `caught_stealing_pct` -> next-year Savant `cs_aa_per_throw`: pooled Spearman `0.2033`, all three folds positive, supported;
- prior `passed_balls_per_9` -> next-year Savant `blocks_above_average_per_game`: pooled Spearman `-0.1524` (correct negative direction), supported.

`catcher_interference_per_9` has no direct Savant target in the frozen source set and is not supported for the first challenger.

**Architecture decision:** first Defense-v1 catcher challenger may use universal CS% and passed-ball rate plus tracked framing where available. Keep throwing, blocking, and framing as separate projected components until a later value-layer combination rule is frozen.

## Universal official fielding source — broad enough for Tier C

The raw 2021–2024 official fielding captures already certified for Position/Role were audited without re-fetching source or opening 2025:

- 64/64 season × league pairs;
- 224 retained fielding pages;
- 100,166 raw fielding splits;
- broad all-level traditional counts including putouts, assists, chances, errors, throwing errors and double plays;
- broad catcher-specific outcomes including caught stealing, stolen bases, passed balls, catcher interference and related fields.

Availability alone was not treated as skill.

## Traditional fielding reliability screen

Eight predeclared rates passed the deliberately low adjacent-year reliability screen, including range factor, fielding percentage, errors, throwing errors, double plays, CS%, passed balls, and catcher interference.

The extremely high raw repeat correlations for some fields were explicitly treated as position-signature contamination, not proof of defensive skill. This triggered the stronger next-year Savant target test with position effects removed.

## Traditional fielding -> next-year Savant target test

Frozen target years: 2022, 2023, 2024. Inputs came only from the prior completed season's all-level official fielding source. No 2025 source or target was accessed.

General target: next-year Savant OAA `diff_success_rate_formatted`. Both input features and target were standardized within exact matched defensive position in each fold before correlation.

### Supported general features

- `range_factor_per_9`: pooled position-adjusted Spearman `0.2277`; all three folds passed directional floor.
- `fielding_pct`: pooled `0.1291`; all three folds passed.
- `throwing_errors_per_9`: pooled signed `0.0991`; all three folds passed in expected negative direction.
- `errors_per_9`: pooled signed `0.0841`; two of three folds passed and pooled gate passed.

### Closed general feature

- `double_plays_per_9`: pooled `0.0372`; zero folds met the directional gate. Closed for the first Defense-v1 traditional challenger without rescue.

### Supported catcher features

- `caught_stealing_pct`: pooled Spearman `0.2033` vs next-year Savant throwing rate; supported.
- `passed_balls_per_9`: pooled signed Spearman `0.1524` vs next-year Savant blocking rate; supported.

### Unsupported / unavailable

- `catcher_interference_per_9`: no direct frozen Savant target; not supported for the first challenger.

**Binding decision:** the first universal traditional Defense-v1 challenger feature set is limited to:

- fielding percentage;
- range factor per 9;
- errors per 9;
- throwing errors per 9;
- catcher caught-stealing percentage;
- catcher passed-balls per 9.

No other traditional fielding feature may be added to the first challenger based on these already-opened 2022–2024 targets.

## Coverage tiers entering model development

The evidence-tier design is now sufficiently supported to freeze a development contract:

- **Tier A — MLB tracked:** official Savant tracked Performance where available plus universal official-fielding features.
- **Tier B — tracked MiLB:** SportsDataverse portable range/framing evidence plus universal official-fielding features; tracking coverage remains explicit and is not treated as a proprietary truth label.
- **Tier C — untracked affiliated MiLB:** universal official-fielding features only, with aggressive shrinkage/uncertainty to be selected in development rather than silently assigning zero defense.

Tracking absence is missing evidence, not neutral talent.

## Minimum eventual Defense v1 output

Before WAR/value, Defense v1 should expose at least:

- player id;
- defensive position;
- projected defensive-quality rate or equivalent skill score;
- exposure basis;
- evidence tier;
- uncertainty / source-coverage metadata;
- component provenance (range and catcher framing/blocking/throwing where applicable).

Positional adjustment belongs to the later value layer, not inside fielding-quality skill.

## Next development gate

Freeze a Defense-v1 development plan **before fitting a multivariate model or opening 2025 defensive targets**. The plan should:

1. treat 2022–2024 as the already-opened development surface and reserve 2025 as untouched confirmation;
2. establish a simple position-neutral universal baseline using only the six supported traditional features above;
3. test whether age and tracked evidence add out-of-development value in a small, predeclared candidate set rather than an open-ended search;
4. keep general range and catcher framing/blocking/throwing components separate;
5. predeclare shrinkage, minimum exposure, missing-evidence behavior, target scaling, metrics, and promotion gates;
6. refit/freeze exact parameters before any 2025 defensive target is opened if a challenger survives development.

## Binding boundaries

- No production Defense v1 projection is frozen yet.
- No 2025 defensive target has been accessed.
- No Tier-C defensive value has been imputed yet.
- No catcher component-combination rule is frozen yet.
- No WAR/value calculation is authorized.
- Playing Time v1 and Position/Role v1 remain frozen and untouched.

## Evidence records

- `docs/defense-sportsdataverse-reuse-poc-result.json`
- `docs/defense-milb-statcast-transport-diagnostic-result.json`
- `docs/defense-catcher-framing-reuse-poc-result.json`
- `docs/defense-universal-fielding-source-audit-result.json`
- `docs/defense-traditional-fielding-stability-result.json`
- `docs/defense-traditional-to-savant-target-result.json`
