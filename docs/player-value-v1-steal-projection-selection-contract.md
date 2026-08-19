# Player Value v1 steal projection selection contract

Status: **PREDECLARED BEFORE MODEL FITTING — BASERUNNING NOT FROZEN — WAR CLOSED**

This contract fixes the portable stolen-base current-talent / projection diagnostic before candidate results are inspected. It is intentionally separate from the richer MLB Statcast advancement component.

## 1. Scope

Select a universal MLB + affiliated-MiLB method for projecting two distinct runner skills:

1. **attempt propensity** — how often the player tries to steal, conditional on a portable first-base opportunity proxy;
2. **success skill** — how often a steal attempt succeeds.

Do not fit a single `SB / PA` rate. That would partially reward hitters for reaching base, even though batting value is already handled separately in `Rbat`.

This gate does not select non-steal advancement value, GIDP residual value, final steal run weights, or final baserunning aggregation.

## 2. Portable observed quantities

For each player-season-environment stint:

- `singles = H - 2B - 3B - HR`
- `steal_opportunity_proxy = singles + BB + HBP - IBB`
- `steal_attempts = SB + CS`
- `steal_successes = SB`

The opportunity proxy follows the mature public wSB exposure convention. It is an **exposure proxy**, not a literal count of pitch-level steal opportunities; therefore `steal_attempts <= steal_opportunity_proxy` is not a required identity.

Required source fields must be observed. Missing values are not silently replaced with zero.

## 3. Environment centering

Stolen-base rules and attempt environments vary materially by season and competitive environment. Player evidence is therefore evaluated relative to the contemporaneous source environment before being carried forward.

### MLB

Use one pooled MLB season baseline across AL + NL because the leagues share the same playing rules:

- baseline attempt rate = total attempts / total opportunity proxy;
- baseline success rate = total SB / total attempts.

### Affiliated MiLB

Use actual `league_id × season` baselines when the source has sufficient observed volume. If an actual league baseline is structurally unavailable, fall back only to the broader certified level × season baseline declared by the diagnostic implementation; do not invent a player-specific environment adjustment.

This centering is intended to isolate relative runner behavior from rule/environment changes. It is not a learned MLB-equivalency translation.

## 4. Candidate family

Keep the search compact. Fit attempt propensity and success skill separately.

For each channel evaluate:

### B0 — neutral environment baseline

No player-specific carry-forward:

- attempt-rate multiplier = 1;
- success odds multiplier = 1.

### B1 — prior-season empirical Bayes

Use only the immediately preceding eligible season, shrunk toward that evidence season's environment baseline.

### B2 — three-season recency empirical Bayes

Use up to the prior three eligible seasons with fixed annual weights:

- most recent season: `1.00`
- two seasons back: `0.50`
- three seasons back: `0.25`

No additional recency weights may be introduced after results are visible.

## 5. Prior-strength grid

For B1 and B2 evaluate exactly three prior strengths per channel:

- `5`
- `15`
- `45`

Interpretation:

- attempt propensity: prior strength is measured in **environment-expected steal attempts** around a neutral rate multiplier of 1;
- success skill: prior strength is measured in **steal attempts** around the contemporaneous environment success rate.

This yields six player-specific candidates per channel (`B1/B2 × 5/15/45`) plus B0. Do not expand the grid based on diagnostic results.

## 6. Estimation semantics

### Attempt propensity

For each evidence season, calculate the environment-expected attempts from the player's opportunity proxy and the corresponding environment baseline attempt rate.

For weighted history:

- observed evidence = weighted steal attempts;
- expected evidence = weighted environment-expected attempts.

Use Gamma-Poisson-style shrinkage around multiplier 1:

`attempt_multiplier = (K + weighted_observed_attempts) / (K + weighted_expected_attempts)`

where `K` is the predeclared prior strength.

For a target season, predicted attempts are:

`predicted_attempts = target_environment_expected_attempts * attempt_multiplier`

The target's observed opportunity exposure is used only for retrospective scoring. Production Player Value must not use realized future opportunities.

### Success skill

For weighted history:

- observed successes = weighted SB;
- observed attempts = weighted `(SB + CS)`;
- evidence baseline success probability is the environment-expected success count divided by evidence attempts.

Shrink success probability toward that evidence baseline with a Beta-style prior of strength `K`, then express the resulting player skill as a **log-odds residual** from the evidence baseline.

For a target season, add that residual to the target environment's baseline log odds and transform back to a probability. This preserves environment changes without assuming raw success rates are directly portable.

Zero-attempt evidence carries no player-specific success information and must resolve to the neutral target baseline, not to 0% success.

## 7. Chronological selection firewall

Use no 2025 evidence for parameter selection.

### Development targets

Use completed **2022 and 2023** player seasons as development targets. Predictor evidence must precede the target season.

The source audit has already established nonempty 2021–2024 affiliated assets for the common AAA / AA / High-A / Single-A / Rookie tiers; the diagnostic must still fail closed if a selected asset lacks the required baserunning fields.

### Confirmation target

Completed **2024** is held out from candidate selection.

Select one attempt-propensity candidate and one success-skill candidate using only the predeclared 2022–2023 development results. Then run exactly those selected candidates on 2024.

If 2024 materially reverses the development advantage, do not reselect another candidate on 2024. Record instability and keep the channel unresolved or fall back to the simpler neutral / prior-season alternative according to the freeze rule below.

## 8. Eligibility and grain

Score player seasons only when:

- player identity is a valid MLBAM ID;
- target opportunity proxy is positive for the attempt channel;
- target steal attempts are positive for the success channel;
- all required source fields are observed;
- source environment can be resolved without ambiguity.

A player may have multiple team/league stints within a season. Aggregate expected baseline quantities across stints rather than forcing one arbitrary target environment.

Candidate coverage must be identical within a channel and target year. If a candidate changes who is scoreable, fail the comparison.

## 9. Primary scoring

### Attempt propensity

Primary: Poisson negative log likelihood / deviance for observed target attempts using the candidate's target expected-attempt mean.

Report both:

- total opportunity-weighted predictive score;
- equal-weight mean of target-year scores.

Secondary diagnostics: MAE and RMSE of attempt rate relative to target environment expectation.

### Success skill

Primary: Bernoulli/binomial log loss from target SB and CS counts.

Report both:

- attempt-weighted predictive score;
- equal-weight mean of target-year scores.

Secondary: Brier score / calibration summary where meaningful.

## 10. Selection rule

For each channel:

1. compare B1/B2/K candidates against B0 on 2022–2023 only;
2. select the lowest equal-year mean primary proper score;
3. require no catastrophic reversal by major source tier (MLB, AAA, AA, High-A, Single-A, Rookie) where sample size is meaningful;
4. use simpler B1 over B2 only if primary scores are numerically indistinguishable at displayed precision; otherwise let the predeclared score decide;
5. do not invent a composite objective after seeing results.

## 11. Confirmation / freeze rule

A player-specific channel may be frozen only if the selected development winner:

- beats or meaningfully improves on B0 in development;
- confirms rather than materially reverses on 2024;
- has stable direction across major source tiers where sample size supports comparison;
- produces finite, interpretable multipliers/probabilities without clipping-driven gains.

If a channel fails confirmation, the project must document the failure. It may freeze the neutral B0 fallback for that channel rather than select a different 2024 winner.

## 12. Production scaling boundary

This diagnostic scores against realized target opportunity exposure only to test predictive skill.

Final Player Value production must not allow projected batting quality to create separate baserunning differentiation. The intended downstream structure, to be frozen only after this diagnostic, is:

- derive one common MLB reference first-base-opportunity-proxy rate per projected MLB PA from the certified reference environment;
- multiply that common rate by each player's frozen `projected_expected_mlb_pa`;
- apply the selected player-specific attempt multiplier and success residual to MLB reference baselines.

Thus player differentiation comes from baserunning skill, while total future baserunning opportunity still scales with projected MLB playing time.

## 13. Richer MLB Statcast boundary

Statcast defines true steal opportunities at pitch-level runner/base states and values attempts using pitcher/catcher context. That richer evidence should be evaluated later as an MLB-only enhancement / calibration source.

Do not claim the portable wSB exposure proxy is equivalent to Statcast steal opportunities, and do not fabricate Statcast-equivalent MiLB inputs.

## 14. GIDP boundary

This contract does not reopen the GIDP decision. Raw GIDP value is already non-additive because batting-bin values are means of PA-level RE24. A separate GIDP term remains eligible only as an opportunity-adjusted residual under the separate source/overlap contract.