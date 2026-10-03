# Prospect graduation and hitter opportunity

2026-10-03. One bounded follow-up to the reviewed V68 comparison. The practical
hitter goal remains controlling; this is not another learner tournament.

## Question and comparison

Does distinguishing removal after MLB graduation from absence on a prospect
list improve next-calendar-year MLB appearance, PA and delivered offense?
Keep all 30,506 evaluation identities, 35 chronological held-player folds,
training memberships, settings, equal-origin weights and fixed hitting from
V68. Retain both the original V53/V63 and fresher-list V68 forecasts. Add only
three deterministic inputs to V68's 251 opportunity inputs; fit the same two
heads once. No blending, player overrides, penalty sweep or new batting fit.

The added inputs are: observed career MLB AB exceeds 130; confirmed AB graduate
absent from a complete latest list; most recent listed score from the preceding
two preseason lists, interacted with that confirmed graduate absence. This last
input records past standing, not an invented current rank or a peak rank. No
forced workload increase follows graduation. The learner can distinguish a
successful graduate from a failed one using the existing production/exposure.

## Source and limits

Use cached V31 dated season totals, sport 1 only, 2008 through each origin, and
reject duplicates, null/negative AB or AB greater than PA. Career AB is an
observed lower bound: older coverage is left truncated. More than 130 observed
AB is sufficient to establish the AB graduation rule, but less is NOT proof
of rookie eligibility. Service days, older missing history and international
eligibility exceptions remain unresolved. Do not infer service days from games.
Partial-list absence remains unknown (-1), never a confirmed disappearance.
Unknown historical rank stays unknown in the added interacted score. Existing
source coverage/retrospective-list dating qualifications remain unchanged.

MLB's [2019 criteria](https://www.mlb.com/news/mlb-s-top-100-prospects-for-2019-c303077544)
support the AB threshold. [2020 rules](https://www.mlb.com/news/mlb-rookie-status-for-2020-amended)
changed roster-day treatment; this test does not reconstruct those days. No
2026 outcomes or rankings are accessed, and the frozen forecast stays unchanged.

## Checks, scoring and disposition

Before fits reconstruct all new inputs independently from raw AB sums and save
actual full/active training checks. Count distinct earlier people by stage,
age, current rank, confirmed graduation and preceding listed history. Keep
unsupported forecasts in every score. Check chronological information dates,
not just label years. Replay both new heads and the V68 heads; retain the
original forecasts exactly. Source-only unit tests cover threshold, missing
AB, future-row exclusion, duplicate totals and unknown lists.

Report equal-origin PA RMSE/MAE, offense RMSE, appearance proper scores, raw
totals, matched Steamer/ZiPS cohorts, every origin including 2021, lower/upper
never-arrivals, current MLB, first-year top picks and previously ranked AB
graduates. Whole-player paired intervals against both anchors are development
evidence, not independent confirmation. Public practical targets remain PA
RMSE within 10% and MAE within 15% of Steamer and offense RMSE within 10%, with
meaningful improvement over the original UBM. Passing execution is not adoption.

Fixed reviews before fitting: Meadows 2018, Fowler 2018 (opposite graduate
risk), Judge 2016, Langford 2023, Kurtz 2024, Moniak 2016, Salas 2024 and Rortvedt
2023. Add largest offense gain/harm versus V68, false high/low and an ordinary
active case. Walk actual AB, statistics, inputs, saved paths, probabilities,
conditional PA and offense through to reality. Select four peers using only
origin-known stage, age, graduation, minor PA and draft standing. Review failed
peers as they arise; do not guarantee all former prospects become regulars.

After that review, retain or reject this representation on cohort and player
evidence together. Do not claim full WAR, calibrated continuous uncertainty,
club control or trade value. Return to the broad playing-time/talent integration
milestone after this bounded check, rather than extending the ranking patch queue.
