# Reconstruct the canceled season training population

2026-10-02. Before source materialization or new model fits. The previous goal
turn made progress: it completed and pushed the corrected working baseline and
its reviewed player evidence. This continuation repairs the missing historical
population rather than reopening the model-library search.

## Question and scope

Can we replace the incomplete 597-person origin-2020 subset with the complete
**observable** hitter cohort at that cutoff? Minor-league cancellation is missing
competition, not thousands of observed career exits. The target remains 2021
MLB PA and batting-plus-replacement wins. This source step does not itself prove
better projections. Later fitting requires a separate locked contract and the
completed source walkthrough first.

Eligibility uses the union of the existing 2019 hitter snapshot, actual 2020
hitting/source-position evidence, historical December 2020 full-roster hitter
listings, and the old 2020 past-debut cohort. Retain exits and non-arrivals.
Roster-only players with no informative historical hitting position remain
explicitly uncertain; do not select hitters using their present-day position.
Draft selections without a historical hitter identity do not establish signed
professional hitter eligibility. Report that remaining entry-coverage gap.

Fetch only historical 2020 team/full-roster/40-man queries, plus immutable birth
dates for missing ages if needed. Save responses, parameters, capture time and
hashes. Historical lists are soft source membership, not certified rights or
accurate medical status. Current-age, active-status, current primary-position,
future debut-date and future organization fields must not enter eligibility or
inputs. Existing draft capture contributes only dated picks and immutable birth
dates; no new college collection or bonus inference.

## Source reconstruction

Keep 2019 known minor levels as last observed levels when no 2020 competition
exists, marking that carry-forward rather than inventing 2020 MiLB performance.
Current MLB PA is actual 2020 PA. Schedule-normalized opportunity is separate
from raw event counts. Retain actual 2018–20 histories, no future backfill.
An empty minor season contributes zero observations, not zero talent.

Construct all season inputs, shrunk rates, quality and cumulative MLB exposure
from the audited all-stint counts. Age comes from cutoff-season reported ages,
an earlier age advanced in years, or immutable birth date; otherwise mark unknown.
Explicit capture coverage accompanies roster membership. Existing non-2020
source rows and all 30,506 evaluation identities/targets remain bit-exact.
Replace the old 2020 subset only in a new artifact, never overwrite its archive.

Outcome coverage is audited against the certified complete 2021 MLB target,
including players outside the observable origin cohort. Missing future labels
are zero only because that full MLB target inventory is present and checked.
Outside-cohort arrivals remain reported, not added using knowledge of success.

## Checks and player review before any fit

Check identity uniqueness, protected-season exclusion, no 2020 MiLB counts,
all-team MLB count reconciliation, membership independent of future outcomes,
no mutable present-day fields, complete requested-team capture, actual roster
duplicate handling, all old non-2020 rows preserved and all old 2020 identities
retained. Do not call an observed source population all international signees.

Walk through Judge, Tatis, Lux, a 2019 upper-minor non-arrival and advancing
minor, and an observed new drafted entrant. Show actual 2018–20 counts,
old/new eligible population and age/level/roster inputs, 2021 outcomes, and
origin-selected peers. Source review completion is not predictive certification.
Only then choose one same-settings, fixed-fold source-extension comparison.

No 2026 outcomes, frozen forecast changes, fitted status penalty, outcome-total
normalization or new hyperparameter search are authorized by this source step.
