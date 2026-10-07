# Position history is ready for the defensive opportunity comparison

2026-10-06. The new preparation joins the existing old and current fielding
sources into complete position vectors. It retains 400,020 source records and
214,171 player season level records, rather than using only catcher, shortstop
and center-field summaries. Every one of the 30,506 fixed historical forecasts
gets its own cutoff-known history. No forecast accuracy gain is claimed yet;
defensive opportunities and full player value have not been fitted here.

## What is usable

MLB fielding history covers 2004–2025. Minor history covers 2009–2019 and
2021–2025, with the existing 2019 Appalachian/Pioneer repair included exactly
once. All 66 early minor captures, the 2019 supplement, 224 historical pages
and 58 pages for 2025 reconstruct their saved records and identity metadata.
The 14,312 overlapping recent MLB records agree exactly between the two sources.

The artifact-local receipts match this later acquisition. The original receipts
in `docs` belong to an earlier acquisition; their different hashes are preserved,
not silently substituted. Old captures and exported files are unchanged.

The new view distinguishes explicit DSL history from complex ball. Older
sport-wide rookie captures remain combined rookie history because their attached
league/team labels do not certify exact subleague or club usage. The canceled
2020 minor season is absent, not evidence of zero defensive talent. DH starts
are retained without inventing DH fielding innings. Pitcher outs remain visible
but outside the eight-position defensive total.

## Baseball checks

Seven fixed players and 21 peers are traced from source rows to weighted inputs.
A second review adds current-stage matching without erasing the original broader
peer selection. Independent sums reproduce 1,037,204 weighted position values
across all historical forecasts and all eight-position exposure outcomes.

- Baty in 2019 has 933 third-base outs: 108 in the combined rookie capture, 774
  in the advanced-rookie supplement and 51 in short-season A. Leaving out the
  existing supplement would discard most of this position evidence.
- Álvarez has 687 catcher outs: 93 in the first capture and 594 in the supplement.
  This is evidence that he caught, not a measured MLB receiving grade.
- Betts in 2023 has 2,105 RF outs, 1,455 at 2B and 294 at SS. The new input retains
  all three rather than treating a current SS roster label as his entire history.
- Varsho in 2022 has 525 catcher outs, 1,136 CF outs and 1,625 RF outs. A catcher
  label must not earn a full-time catcher adjustment or all catcher opportunities.
- Schwarber in 2023 has 103 LF starts and 57 DH starts, with 2,617 LF outs. History
  is not a guarantee of his next position; an announced role change would need
  its own dated preseason evidence, not his later realized defensive innings.
- De La Cruz in 2022 has SS and 3B work in A+ and AA. His refined peers are Ángel
  Martínez, Orelvis Martinez and Luisangel Acuña, not a pool restricted to eventual
  successful MLB shortstops.
- Eldridge in 2024 has first-base exposure at four levels. The current-stage
  comparison finds only 13 age/role-matched upper-minor peers before selecting
  Isaac, Clifford and Encarnacion. Actual usage is firmer than a label; future
  MLB position and skill still have uncertainty.

The source conserves all eight MLB positions in every year. Four of 182 requested
scopes have small historical discrepancies: 42 outs in 2014 AAA, 18 in 2012 A,
three in 2013 short-season A and three in 2016 combined rookie ball. Preserve
those source limitations; do not manufacture corrected player counts.

## What the checks rule out

Within returned team labels, 2,600 of 4,376 groups have unequal position totals.
Those totals cannot be treated as exact club defensive usage. Player/sport or
player/league aggregation is supported by the actual request scope; team-level
allocation needs a separate team-split source. Counting the expected number of
teams does not resolve that distinction.

Conditional training for immediate MLB exposure is sparse for many prospects.
At the 2022 origin, 3,459 of 4,244 forecasts have fewer than 20 active training
players in their stage/age/starting-position/sample profile, and 1,802 have none.
The corresponding counts at 2024 are 2,987 and 1,557 of 3,992. These are support
warnings across the full population, not proof that all MLB profiles are sparse.
The next bridge needs explicit coarser role fallbacks; a large overall training
set does not certify those detailed prospect profiles.

Six historical forecast rows have positive defensive outs despite zero MLB PA.
Keep them in full-cohort exposure scoring. A conditional rate trained only on
positive-PA batters does not explain this defense-only opportunity.

## Matched totals are not the entire league

The fixed historical forecast cohort covers 99.47% of actual defensive outs in
2023, 99.87% in 2024 and 99.97% in 2025. The remainder is retained separately.
The 2023 remainder includes Conforto, Yoshida and Schanuel; 2024 includes Lee and
Sanó; 2025 includes Alfaro. Some are known missing-year returns, not inherently
unknowable future entrants. Do not silently invent forecasts for them or call
the cached population a complete current production package.

Every origin's matched and omitted actual outs reconcile to the entire MLB
inventory. That verifies population accounting, not that projected totals are
calibrated. The next comparison must hold the same cohort fixed and show the
remainder; an eventual whole-model claim requires an explicit population bridge.

## Decision and next step

Use this prepared player/scope history for the next defensive position and
opportunity comparison. Keep the older MLB exposure winner as qualified evidence,
not a replay of the present system: it excluded catchers, used different batting
playing time and did not exclude the tested players' earlier seasons from training.
The older raw-persistence bridge remains an anchor, not a universal solution for
prospects without prior MLB innings.

Predeclare one understandable opportunity bridge with fixed playing time and
explicit sparse-role fallback. Compare per-position exposure and native channel
opportunities, then add the already reviewed skill baselines to matched delivered
runs and player value. Catcher pitch, steal and blocking chances are separate;
generic innings must not replace their opportunity definitions. Preserve unknown
minor defensive skill and ABS value scenarios. No learner tournament, prior sweep,
2026 outcome selection or explorer promotion follows automatically.

Thirty-eight focused unit checks pass. They support the source and existing skill
arithmetic; they are not a claim that the integrated defense model has passed.

Evidence: [source receipt](../reports/model-evidence/defense-position-opportunity-v7/source-review.json),
[stage matched player walkthrough](../reports/model-evidence/defense-position-opportunity-v7/stage-matched-source-walkthrough.json),
[independent verification](../reports/model-evidence/defense-position-opportunity-v7/independent-source-verification.json),
[population accounting](../reports/model-evidence/defense-position-opportunity-v7/cohort-coverage-review.json).
