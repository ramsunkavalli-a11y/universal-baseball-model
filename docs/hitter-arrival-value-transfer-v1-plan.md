# Arrival-to-playing-time/value transfer v1

Fixed 2026-09-23 before fitting/scoring. No new features, parameter search,
probability calibration, player overrides or 2026 forecast changes.

## Question and target

Does the corrected-source F probability recipe improve annual MLB PA and
delivered player value when substituted into the existing opportunity system?
Fit **playing in the particular future year**, not cumulative arrival by that
deadline. Never multiply a three-year arrival probability by Year-3 workload.

Historical targets remain (a) actual MLB PA; (b) batting-plus-replacement wins;
and (c) the existing expanded component wins target, including position,
running, general fielding and catcher components where labels are complete.
The latter is not interchangeable with published FanGraphs/Baseball-Reference
WAR. No contract, trade, service-control or six-year value claim is possible.

## Fixed inputs and fits

Use the original R and repaired F panels/feature lists from the source-repair
experiment. Fixed LightGBM classifier, seed 417, existing balanced recipe,
equal total training weight per player identity. Outcomes must be complete by
the cutoff; exclude any training/test window spanning 2020. All starting
players, including never-arrivers, remain. Use corrected cohorts for scoring.

Use every normal Year 1–3 fold supported by the existing delivered-value and
conditional-workload archive:

- Year 1: origins 2016, 2017, 2018, 2021, 2022.
- Year 2: origins 2016, 2017, 2021, 2022.
- Year 3: origins 2016, 2021, 2022.
- Three-year totals: origins 2016, 2021, 2022. Expanded complete-component totals
  support only 2021 and 2022; do not present these as independent confirmation.

Reuse exact existing R/F Year-1 predictions where available, fit 16 missing
arm/fold combinations, and perform two F future-mutation replays. Refit one
archived conditional PA/rate pair to verify unchanged-head provenance. Current
2023/2024 arrival results remain in the prior experiment; their complete
delivered-value references are absent here and are not silently fabricated.

## Probability-only intervention

Take accepted C2 participation p0, expected PA w0 and delivered batting value
v0 from the archived opportunity system. Recover conditional PA q0=w0/p0 only
from this documented hurdle product; never infer hitting talent from v0/w0.
Keep the independently trained, horizon-specific conditional batting rate r0
from the same archived research head, clipped by its existing recipe.

For a new probability p:

    PA = p * q0
    batting value = v0 + (PA - w0) * r0 / 600

This is a fixed marginal-value correction, not an assumption that the old
direct-value forecast equals a product of means. No learned blending factor.
It tests this explicit integration rule, not every possible joint model.

Primary scope: replace probabilities only for **cutoff-defined never-debuted
minor leaguers**, where F's prior evidence was established; everyone else stays
exactly unchanged. Arms B (accepted C2), R (old detailed probabilities) and F
(corrected detailed probabilities). A predeclared universal-F diagnostic tests
all-player application but cannot be selected after the primary scope fails.

Expanded B follows the prior C2 component integration: the old nonbatting
component total is scaled by C2 PA / old PA. Primary expanded R/F keeps those
component rates fixed and scales totals with the new PA. Also report a diagnostic
that holds nonbatting totals unchanged. Assert positive baseline denominators;
publish ratio ranges rather than introducing outcome-selected caps. The
nonbatting heads were not retrained; this is opportunity propagation, not new
defense or running talent. Some original component heads are direct totals, so
proportional scaling is a testable approximation, not a structural identity.

Mandatory PA/value benchmark: earlier harmonized ensemble on matched keys,
using its independently archived batting-rate anchor/product. Do not derive
an ensemble batting rate from its unconditional value. No ensemble full-WAR
comparison without an independently specified compatible component forecast.

## Evaluation and decision

Equal-origin RMSE, MAE, signed bias and annual predicted/actual totals; paired
player-history MSE intervals (2,000 draws, seed 417). Score prospects, upper/
lower prospects, under-23 upper prospects, returners, recent debutants,
cutoff current-MLB with >=200 current PA, and all players. Outcome-defined
future-arriver strata are descriptive only, never fitting/adoption populations.

Primary transfer gates:

1. Three-year prospect PA and batting-value MSE intervals favor F versus B and
   R; MAE does not worsen versus B; majority of the three origins improve.
2. In each horizon, prospect PA MSE, batting-value MSE, Brier and log loss are
   no more than 5% worse than B. Corresponding supported stage/age slices
   (>=200 rows, >=10 active outcomes) have no >5% PA/value MSE harm.
3. Prospect PA MSE beats the harmonized ensemble in each horizon. Three-year
   PA and batting-value aggregate absolute error do not worsen versus B.
4. Overall three-year batting-value MSE does not worsen (non-prospects are
   unchanged). Expanded complete-component cumulative error must not worsen
   and each supported annual expanded-value MSE has no >5% harm. Its two-origin
   result is only a safety screen, not full-model confirmation.

Report all failures. Passing is evidence for this research integration, not
automatic deployment. A probability gain without PA/value gain remains a
probability gain. No winner switching, tuning or follow-on repair inside this
contract. Preserve frozen forecasts, input/source hashes, fits, scores and a
plain-language result in the repo.
