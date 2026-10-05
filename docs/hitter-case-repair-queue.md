# Fix individual baseball logic failures before more model comparisons

2026-10-05. The user's correction governs the next work. A repeated named miss
must become a repaired mechanism or an explicitly unresolved case, not another
forecast walkthrough labeled progress. A negative pooled score cannot excuse a
forecast that ignores cutoff-known facts. Do not override individual players
using later outcomes, and do not force good-looking totals through opposite errors.

## Tatis is the first case and remains open

His original suspension was 80 games; the reported 2023 absence was 20 games,
with April 20 tentative eligibility. [Dated MLB report](https://www.mlb.com/padres/news/fernando-tatis-jr-return-date-from-suspension-in-2023).

The old source had the dated return report, yet the classifier never used its
restriction/timing inputs. It assigned 15.35% appearance probability and 400
conditional PA, giving 61 expected PA. His preceding MLB record was 546 PA and
42 HR. The saved Steamer archive gives about 545 PA, although its exact vintage
is unknown. That is a smell test, not an input or a same-date accuracy claim.
The new employment-age variant's 112 PA still fails the baseball check.

The implemented remaining-game component now separates the original sentence
from forecast-season suspension exposure. For a planned 162-game season it
gives 142 potentially eligible games, or 87.65% of the season. It cannot certify
health or a job. Applying this to an already penalized 61-PA forecast is explicitly
rejected; otherwise we would make the original mistake worse and double-count
the absence. Suspensions reduce eligible work, not batting rate or appearance
probability by the same fraction a second time.

My prior statement that he missed 2022 simply because of suspension was incomplete:
he also had wrist and shoulder problems. [Contemporaneous medical context](https://www.mlb.com/news/fernando-tatis-jr-left-shoulder-surgery).
The clinical record ends at a suspension-related scope exit; that does not certify
medical recovery. Surgery and return expectations need their own dated evidence,
not the assumption that an empty current IL flag means healthy.

Tatis is **not fully fixed**. The outstanding piece is an independent role and
health baseline that retains his pre-interruption career and does not learn
non-arrival merely from suspension-caused zero PA. Separate this from the finite
game-budget adjustment. Do not invent a 97% return probability or a 600-PA
baseline; those values in unit arithmetic are examples, not fitted estimates.
No new healthy-role forecast or accuracy improvement is claimed here.

The [component contract](known-suspension-budget-contract.md) and
[five source/control walks](../reports/model-evidence/known-suspension-budget/report.json)
keep the fitted old forecasts intact. Ordinary unit tests check math and source
selection; they are not predictive validation. Sparse origin-known peer groups
remain sparse, including no exact restriction peer for the Tatis source case.

## Cases after the Tatis baseline repair

| Case | Specific question to resolve | Avoid repeating |
| --- | --- | --- |
| Hoskins before 2024 | Return probability is already 92%; why is expected active workload only 399 PA after prior 672? | Claiming the earlier employment correction is a new gain |
| Ellsbury before 2019 | What health evidence distinguishes a rostered but still unavailable player from a credible return? | Treating 40-man membership as recovery |
| Kang before 2018 and Franco before 2024 | How should unresolved eligibility/return uncertainty be represented without inventing clearance or a permanent ban? | Blanket link boosts or later-outcome overrides |
| Kwan before 2022 | Why do known upper-minor contact/role evidence produce only 158 conditional PA and weak fixed hitting? | Another level-exposure inventory or an arbitrary prospect boost |

These are not new source sweeps or permission to refit them together. Resolve
one mechanism, show its effect on the focal case and origin-known comparison
players, then evaluate the same historical cohort before adoption. Rejecting a
candidate and fixing a known baseball defect are different tasks.

The first five controls are Tatis before 2023 (known finite absence), Tatis before
2024 (observed return), Franco before 2024 (unresolved parallel channels), Marcano
before 2025 (permanent exclusion), and Duran before 2025 (explicit resolution).
The new component returns a numerical suspension budget only where justified;
it does not turn Franco into a factual zero or erase Tatis's medical uncertainty.
Old source-to-model-to-reality receipts and their origin-selected comparisons
remain linked rather than repeatedly refitted. Since no full forecasts change,
new predictive gain/harm categories are empty; no example gain is manufactured.

Both frozen forecasts, the completed one-time 2026 evaluation and the explorer
stay unchanged. The selected model remains a historical benchmark with known
failures, not a certified production forecast simply because its scores reproduce.
