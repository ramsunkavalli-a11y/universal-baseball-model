# Playing time / role methodology review

Last updated: 2026-08-17

Status: **INITIAL REVIEW COMPLETE — design implications recorded before target/feature/model freeze.**

## Question

After freezing batting-rate skill, how should the project model next-season opportunity without contaminating skill with role, organization depth, or zero-opportunity outcomes?

The current stage is not another batting Projection model. Frozen one-year batting rate remains:

`frozen_current_talent_carry_forward_v1`

Playing time / role must be a separate exposure channel.

## Public baseball practice

### FanGraphs Depth Charts / RosterResource

FanGraphs explicitly separates rate projection from playing-time allocation. Its Depth Charts projections combine rate forecasts from ZiPS and Steamer and prorate them to RosterResource playing-time projections; the playing-time layer is maintained separately and updated as roster expectations change.

This is strong architectural evidence for keeping:

1. **player skill/rate**, and
2. **opportunity allocation**

as distinct model objects.

RosterResource also distinguishes the current roster state from expected full-season playing time. A player can be in Triple-A or on the injured list today while still receiving substantial projected seasonal playing time. Therefore `current roster status` is useful predictor context, not the playing-time target itself.

Sources reviewed:

- FanGraphs, **All the 2026 Projections Are In!** (2026);
- FanGraphs, **Introducing RosterResource Depth Charts!** (2019);
- FanGraphs current Depth Charts projection descriptions.

### KATOH / probability of reaching MLB

Chris Mitchell's KATOH work is relevant conceptually because it separates prospect performance from the probability of eventually receiving major-league opportunity/value. The important transferable idea is that **reach probability is itself an estimand**, rather than treating a player who never reaches MLB as if he produced a terrible MLB batting rate.

For this project, next-season `P(any MLB PA)` should therefore be explicit rather than hidden inside one continuous PA regression.

### Roster mechanics as predictors

MLB roster mechanics constrain near-term opportunity. Public Stats API surfaces support date/season-specific team-roster queries and transaction queries; the public MLB-StatsAPI wrapper documents historical `40Man` roster calls using a supplied date.

Potentially useful snapshot predictors therefore include, if historical reproduction proves reliable:

- active-roster status;
- 40-man status;
- injured-list / other roster-list state where unambiguous;
- current organization;
- recent transactions / option context where deterministically reconstructable.

These fields are **not yet authorized** for model development. Historical source behavior must be certified first.

Sources reviewed:

- MLB Stats API `team_roster` / `transactions` endpoint inventory as exposed by MLB-StatsAPI;
- MLB-StatsAPI historical 40-man roster example.

## Statistical-method review

### Why one raw PA regression is a weak starting point

Across the universal MLB-through-minors population, next-season MLB PA is structurally zero-heavy:

- many minor leaguers receive zero MLB PA;
- some MLB players disappear because of performance, injury, retirement, roster decisions, or transaction context;
- positive MLB PA is bounded by a season and strongly overdispersed across bench/part-time/regular roles.

One ordinary regression forces the same mechanism to explain both `whether the hurdle is crossed` and `how much opportunity follows`, even though baseball logic suggests they are different processes.

### Two-part / hurdle architecture

The natural first family is therefore two linked but separately inspectable pieces:

1. **participation model:** `P(next-season MLB PA > 0)`;
2. **positive-count model:** distribution of MLB PA conditional on `MLB PA > 0`.

Derived outputs can then include:

- `P(any MLB PA)`;
- expected positive MLB PA;
- unconditional expected MLB PA;
- probability of exceeding frozen role/PA thresholds;
- later, role-state probabilities.

This is better aligned with the project boundary than converting zero MLB PA into bad skill.

### Mature implementation options

Statsmodels 0.14+ includes production count-model primitives rather than requiring a custom likelihood implementation:

- `HurdleCountModel`;
- `TruncatedLFNegativeBinomialP`;
- Poisson and Negative Binomial count families;
- standard binary Logit.

A promising transparent v1 is **Logit for any MLB PA + zero-truncated Negative Binomial for positive MLB PA**. This permits different predictors/coefficient interpretations for the hurdle and amount processes and directly matches the two estimands above.

A single statsmodels `HurdleCountModel` remains a candidate implementation baseline, but its built-in zero process is count-family based. Before the model contract is frozen, compare the API/diagnostic behavior of:

- one packaged hurdle model; versus
- explicit Logit + truncated NB components.

Do not choose between them by looking at 2025 or other confirmation results.

Sources reviewed:

- statsmodels 0.14.6 `HurdleCountModel` documentation;
- statsmodels 0.14.6 `TruncatedLFNegativeBinomialP` documentation;
- statsmodels discrete/count-model user guide.

## Binding design implications before source feasibility

### 1. Rate skill remains fixed

Playing-time development must not refit Current Talent or the rejected Projection age model.

The frozen batting-rate state may enter as predictor context, but future PA outcomes never alter the player's batting-rate estimate.

### 2. Model MLB opportunity explicitly

The first target surface should be **next-calendar-year MLB regular-season PA** for every eligible snapshot player, including zeros.

MiLB PA remains useful predictor/context evidence, but v1's downstream value purpose requires MLB opportunity to be explicit.

### 3. Separate participation from positive volume

Do not start with a single OLS/Poisson model of all MLB PA.

V1 should first test a transparent two-part family:

- any-MLB-PA probability;
- positive MLB PA amount/distribution.

### 4. Do not hard-code role labels before the count distribution works

`bench`, `part-time`, `regular`, etc. are useful outputs but threshold definitions can be arbitrary.

First produce/calibrate the MLB PA distribution. Role probabilities can then be derived from predeclared PA bands, and later enriched by defensive position/lineup-role information if justified.

### 5. Player opportunity and team allocation are related but not identical

An individual's portable opportunity probability should not be entirely determined by one organization's current depth chart. Trades, injuries, promotions, and roster churn can change the path.

At the same time, independent player PA forecasts can sum to impossible team totals.

Preferred architecture:

- **player opportunity model:** probabilistic individual MLB participation / PA distribution;
- **team/organization allocation layer:** later coherence constraint or scenario layer that allocates finite positional/roster opportunities.

Do not put a full team-depth optimizer into the first individual baseline.

### 6. Historical roster status is valuable only if reproducible

Before adding 40-man/active/injury/transaction predictors, prove that exact historical Oct. 15 snapshots can be reproduced from public sources for the development years.

If the source is inconsistent or retrospective fields leak later information, omit those features from v1 rather than approximating them.

### 7. Preserve chronological evaluation

Candidate chronology should mirror the settled batting Projection design where possible:

- `2021-10-15 -> 2022` development/selection;
- `2022-10-15 -> 2023` out-of-time validation 1;
- `2023-10-15 -> 2024` out-of-time validation 2;
- `2024-10-15 -> 2025` untouched confirmation only after the complete playing-time contract is frozen.

No 2025 opportunity outcomes should be opened before that contract is persisted.

## Next gate

Do **not** fit a playing-time model yet.

First run a small source-feasibility audit for historical date-specific roster/40-man information at the three development snapshots. In parallel, materialize only the already-certified next-year MLB-PA target/predictor surface needed to understand zeros, positive-count dispersion, and coverage.

Then freeze the exact baseline/candidate feature sets, model family, scoring rules, role thresholds (if any), and 2025 confirmation contract before development scoring begins.
