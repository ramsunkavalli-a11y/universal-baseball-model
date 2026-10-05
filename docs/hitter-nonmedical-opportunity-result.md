# Corrected availability inputs produced exactly the same forecasts

Completed 2026-10-05. Historical development only, through target season 2025.
The selected 2026 forecast and its completed one-time evaluation are unchanged.

The [observation repair](hitter-nonmedical-observation-result.md) corrected records
that could describe a suspension as continuing after the player had played again.
This comparison substituted eight consistently reconstructed current-observation
inputs, including dependent duration and return timing. Legal history stayed intact.
The repair changed 122 model-source origins and 89 evaluated forecasts for 28 people.
It did not change hitting talent, employment, medical evidence, permanent-status
overrides, eligibility, training identities, target maturity or player folds.

## What the test establishes

All 30,519 forecasts are exactly identical to the complete employment V2 baseline.
This includes raw participation probability, raw conditional PA, delivered
probability, conditional PA, expected PA, hitting rate and batting contribution.
Inspection of all 140 saved heads found zero tree splits on any of the eight
tested inputs. Seventy paired initial predictions and 17,500 paired tree-node
arrays also match. These are unrounded mechanical comparisons, not merely a
small change hidden by sampling uncertainty.

The source correction is useful and retained. This particular model cannot tell
us whether the corrected availability evidence predicts better: it never used
that evidence in either version. The zero loss-change intervals [0, 0] describe
identical predictions, not certainty that availability has no baseball value.
The matched contrast is closed. No settings variants or deployment follow from it.

## Matched scores and existing limitations

The executed [contract](hitter-nonmedical-opportunity-contract.md) kept seven
chronological origins and five whole-player folds, 35 cells and 70 new heads.
Target 2020 was excluded. Full and active-only profile support was checked before
fitting; sparse and zero-support cases remained in the test. All 30,506 original
forecasts and thirteen additions remain. Origin 2021 uses the existing March 18,
2022 information cutoff after the lockout, not an invented January cutoff.

| Original-cohort measure | Employment V2 baseline | Corrected observation |
| --- | ---: | ---: |
| PA RMSE | 60.2698 | 60.2698 |
| PA mean absolute error | 20.5180 | 20.5180 |
| Participation Brier | 0.032487 | 0.032487 |
| Participation log loss | 0.111430 | 0.111430 |
| Batting-contribution RMSE | 0.435456 | 0.435456 |
| Expected PA | 1,236,263 | 1,236,263 |
| Expected batting contribution | 4,182.94 | 4,182.94 |

Actual original-cohort PA are 1,270,493 and contribution is 4,185.43. Contribution
is this project's compatible batting-plus-replacement accounting, not full WAR.
The current full-model anchor has PA RMSE 60.4991 but slightly better contribution
RMSE 0.435133. Any difference from that anchor already existed in employment V2;
none is a benefit from the new observation repair.

On the unchanged 2,627-player qualified prior-MLB public overlap, our PA RMSE is
137.7704 versus Steamer's 135.3795, and mean absolute error is 105.2844 versus
92.0828. Ordinary ZiPS PA are not treated as an unconditional team playing-time
forecast. Archive timing and cohort qualifications remain those of the existing
public-source comparison. Fixed hitting was not reranked here.

Good-looking pooled contribution totals still mask cohort problems. Never-debuted
upper-minors players receive 74,213 expected PA versus 92,891 actual; lower-minors
players receive 8,108 versus 5,194. These errors and every origin/stage score are
unchanged, not solved. In the 89 changed forecasts, expected PA are 16,030 versus
16,041 actual, but player PA RMSE is 119.79. The total alone is misleading.

## Player-level reasonability and disposition

The [43-case review](hitter-nonmedical-opportunity-player-review.md) examines actual
source histories, the probability-times-workload calculation, saved tree paths,
both training subsets and origin-only peers. Tatis's pre-2023 projection remains
61 PA versus 635 actual; Franco's pre-2024 projection remains 545 versus zero.
The unused restriction fields did not produce those predictions. Current roster,
recent MLB workload and employment-linked work inputs did. Neither rare profile
has training support sufficient to certify the forecast.

Kurtz, Kwan, Alvarez and the foreign professionals remain substantive missed-readiness
cases. Pedigree and upper-minors records were not wholly absent; their influence
was too weak to overcome other workload signals. Their misses cannot justify an
arbitrary prospect bonus or importing later knowledge into the historical cutoff.

Independent source/matrix checks, saved-head replay, label and score reconstruction,
focused tests and both frozen-package checks are required by the completion
receipt at `reports/model-evidence/hitter-nonmedical-opportunity/report.json`.
Raw captures, matrices, models and detailed player traces stay private and are
hash-bound by that receipt.

Next apply the [source-correction impact gate](source-correction-impact-gate.md)
before another fitting batch. Inventory earlier workload/readiness tests first.
Then diagnose the influential inputs that conflate temporary interruption of an
established career, a ready upper-minors prospect and a foreign professional with
an ordinary player lacking MLB evidence. That is a bounded diagnostic step, not
permission for another status-feature refit or reopening 2026.
