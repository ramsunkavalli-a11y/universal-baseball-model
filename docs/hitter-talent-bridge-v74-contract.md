# Testing prospect rankings and translated hitting evidence

2026-10-03. This is the locked V74 development comparison under the practical
hitter plan. The question is whether the hitting head can use the fresher
prospect rankings and a coherent, historically learned cross-level event
profile to forecast actual next-calendar-year MLB batting. Playing time stays
fixed at V68, and V53/V63 remains the hitting/value anchor. This does not
certify full WAR, career value or six years of club control.

## What earlier tests actually established

The prior tests do not settle this question. The audit read each result and
the relevant source construction before choosing this comparison.

| Earlier test | What it measured | What it does not establish |
| --- | --- | --- |
| V35 relative exposure | Future MLB rate with a different exposure encoding | That the legacy quality representation or every translation is optimal |
| V36 joint event logit | Actual future MLB events and rate without legacy value predictors | That component modeling is useless; its Judge forecast compressed power |
| V37 event anchor | Future MLB events with a fixed 100 PA MLB anchor | That short MLB stints deserve dominant reliability; Winn exposed that problem |
| V41 contact shape | Actual future MLB rate from available contact shapes | A park neutralized contact model; all 2016 cases fell back and unreconciled contacts were excluded |
| Future translated performance | Next year wherever a player played, on a translated scale | Actual future MLB hitting for the full forecast population |
| Affiliated level translation | Future MLB events for 130 and 112 active recent debutants | Broad historical validation, held-player-clean adjustment fitting, or complete DSL support |
| Component-specific regression | A prior chosen in 2024 and evaluated on 112 active 2025 debutants | A reliable universal prior or rejection of translated components |
| Historical comparables | Four-year contribution and conditional talent of comparable prospects | A drop-in annual batting-rate head |

V53 has 199 hitting inputs and no scouting inputs. V68 changed scouting vintage
in the opportunity heads, not the hitting head. V73 completed the mandatory
player review and leaves the opportunity model unchanged. Repeating its
playing-time/ranking sweeps is not the next step.

## Population and target

Keep all 30,506 evaluation rows, seven origins 2016–18 and 2021–24 and five
whole-player folds. Source histories have 63,282 rows and counts from 2008–25;
only counts through 2024 may enter predictors. Training target years must be
completed by the origin and target 2020 remains excluded. The canceled minor
season and shortened MLB season keep the existing separate treatment.

Fit batting rate only where next-year MLB PA is positive. The target is actual
batting wins above the realized target-season MLB average per 600 PA. Non-arrivals
have zero delivered value, not a measured zero batting talent. Every person,
including non-arrivals and exits, remains in delivered-value scoring. Eligibility,
targets, replacement rates and forecast identities do not change.

## Three fixed hitting alternatives

1. **Scouting ridge:** exact 199 V53 inputs plus the nine V68 list availability,
   listed and rank-score inputs for three lags. Same deterministic input scaling,
   Ridge alpha 100 and equal-origin times actual-PA training weights as V53.
2. **Translated ridge:** scouting ridge inputs plus eight centered translated
   event probabilities, log supported exposure, supported fraction, an exposure
   reliability indicator and a missing-profile indicator. Same ridge settings.
3. **Translated trees:** exactly the translated ridge inputs with histogram
   gradient boosting: 250 iterations, depth 3, minimum leaf 30, learning rate
   0.05, L2 10, random seed 31, no early stopping. Same training weights.

No parameter search or new source collection. Primary assembly replaces rate
only for never-debuted players, retaining the established-player anchor exactly.
All-player replacements are saved and scored as predeclared sensitivity analyses,
not a license to promote a harmful established-player branch. These are three
fits per cell, not six separate tuned models. Rate predictions are not clipped;
report physical-bound violations and empirical extrapolation rather than hide
them. Playing-time probabilities, conditional PA and expected PA are bit-for-bit
V68 in every assembly. Value remains PA times (rate/600 + origin replacement).
This multiplication is a mechanical integration test, not proof that conditional
talent and workload are independent.

## Translation inputs and provenance

Use eight mutually exclusive events: other, K, unintentional BB, HBP, 1B, 2B,
3B and HR. Singles are BABIP hits minus doubles minus triples, not total hits
minus extra-base hits with HR counted twice. Other is the remaining PA.

Build same-player, same-season pairs with at least 30 PA at each bucket. Keep
AAA, AA, A+, A, short-season, DSL, each recorded rookie bucket and MEX distinct.
Smooth each event by 0.5 counts, take centered log ratios and fit a weighted
connected graph anchored at MLB. Pair weight is the harmonic mean of exposures.
Offsets capture pooled bucket differences, including unremoved park/context
effects; do not call them park-neutral true talent. Movers are selected and
in-season development can remain confounded.

For every outer player fold and EVERY feature origin, fit offsets using only
counts through that feature origin and excluding all players assigned to the
held fold. This applies to training features as well as test features. No final
2024 lookup is reused in a 2011 row. Archive dates, included player IDs, pair
counts, connectivity and offsets. Disconnected buckets are unknown, not an
identity translation. Retain their original V53 inputs and expose the unsupported
fraction. MLB itself has zero offset.

For each player's three-year history, translate each supported stint, then average
probabilities using recency weights 1, 0.8, 0.6 times actual PA. No arbitrary
level discount or fitted outcome-selected prior is imposed. Center the eight
probabilities against the fold-excluded origin-year MLB event profile and divide
by 0.1. Additional features: log(1+supported PA)/log(1201), supported/total PA,
supported PA/(supported PA+1200), and a no-supported-evidence flag. The 1200
quantity is only an exposure scale; it does not mix a league prior into the
probabilities. With no supported evidence, centered probabilities are zero and
the missing flag is one. This is explicitly unknown evidence, not average talent.
Age, level-specific counts, draft evidence and ranks remain available to learn
appropriate population regression. Every translated probability must be positive
and sum to one. Sparse graph support is reported, never dropped.

## Checks before model fits

Assert count identities, chronology, source uniqueness and fold assignment.
Save adjustment provenance and source examples. Replay all 35 original hitting
heads on identical test rows. Run actual full/active preflights and save distinct
training people by stage, prior debut, age band, rank band, new draftee and thin
professional sample, including their intersections. Save original/translated
input ranges; fewer than 20 relevant people is a warning, not a sufficiency proof.
Freeze and hash all generated inputs, contracts and runner code before rating
fits. Essential unit tests cover future-count mutation, held-player exclusion,
disconnection, event accounting and normalization.

## Scoring and decision

Primary batting score: never-debuted active MLB players, equal years and actual
PA weights within year. Also report equal active-observation weighting because
future PA selects which performances survive. Score delivered value on all
never-debuted players, all players, upper/lower minors, each origin, rank bands,
new draftees and thin samples. Keep 2021 as an explicit stress year. Save totals,
bias and paired player-clustered nominal development intervals for rate MSE and
delivered-value MSE. These exposed years are not a fresh protected test.

Matched public Steamer/ZiPS scores remain, with their existing environment and
snapshot qualifications. Opportunity metrics must be unchanged. A candidate
needs coherent player behavior and a meaningful batting improvement without
systematic delivered-value harm. An uncertain tiny loss does not reject the
entire idea. Current opportunity MAE still misses the practical benchmark target;
even a good hitting result cannot declare the whole goal achieved.

## Mandatory player review

Before fitting, fix Kurtz 701762/2024, Langford 694671/2023, Bellinger 641355/2016,
Alonso 624413/2018, Julio 677594/2021, Holliday 702616/2023, Maitan 670867/2017,
Winn 691026/2023 and established Judge 592450/2024. Assert names against IDs.
Append each arm's largest value gain, harm, false high and false low and an
ordinary active case. Keep all selected cases. For each select four same-origin,
same-stage peers by origin-known age, exposure and rank, never by future outcome.
Trace raw dated counts, actual inputs, graph effects, source support, saved
model prediction, fixed PA, value and reality. Same-fit input probes are mechanics
only, not causal forecasts. No final disposition until readable reviews are
complete. Protected 2026, frozen forecasts and deployment remain unchanged.

## Literature informing the design

[Tango on MLE limitations](https://www.tangotiger.net/hateMLEs.html) describes
selection, weighting, population priors and context as unresolved issues. This
motivates the separate active-rate and full-population contribution views here;
it does not certify our graph.

[FanGraphs on league equivalencies](https://library.fangraphs.com/principles/league-equivalencies/)
describes component translations using movers, notes park/run-environment
adjustments and warns about low-level walks, repeaters and confusing translations
with future projections. Our graph is therefore an additional predictor with
explicit pooled-context limits, not a finished MLE projection system.
