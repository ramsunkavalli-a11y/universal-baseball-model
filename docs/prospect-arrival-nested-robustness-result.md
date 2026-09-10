# Prospect arrival nested robustness result

**Run date:** 2026-09-09  
**Status:** retrospective process audit; pedigree helps arrival more than quality

The audit now tests 176 bounded combinations for four outcomes: any arrival, a
meaningful 200 PA/BF season, and an established role. The last means one 400 PA/BF
season or two lower-workload seasons (300 PA for hitters, 200 BF for pitchers). The
fourth requires meaningful workload and at-least-league-average core batting or
fielding-independent pitching components. The
grid contains 11 feature groups, four logistic
regularization strengths, and four production-rate regression exposures. Selection
uses only the completed 2021 outcome window. The 2022 window remains embargoed and
2023 is the later outer process check. All failures and non-arrivals remain in the
sample.

The new pedigree fields come from the official StatsAPI Rule 4 draft feed: overall
pick, round, slot value, signing bonus, and school class. Narrative scouting reports
are discarded. Draft dollars are converted to within-draft-year ranks, and only
drafts completed by the snapshot year are visible. International and other undrafted
entry paths are explicit; they are not treated as zero-quality draft picks.

## Outer 2023 result

Earlier-origin selection chose `baseball_pedigree`, `C=1`, and no extra production-rate
regression for hitter arrival, meaningful and established roles and for pitcher
arrival and meaningful role. Pitcher
established-role selection used the combined baseball/demographic family. Conditional
quality instead selected origin plus 50 PA of rate regression for hitters and draft
pedigree plus 50 BF of regression for pitchers, both with `C=.1`.

| Population / target | Core log loss | Candidate | Core Brier | Candidate |
|---|---:|---:|---:|---:|
| Hitters / arrival | .16531 | .15355 | .04588 | .04386 |
| Hitters / meaningful role | .07620 | .06821 | .01776 | .01709 |
| Pitchers / arrival | .17208 | .16607 | .04861 | .04703 |
| Pitchers / meaningful role | .07060 | .06849 | .01772 | .01748 |
| Hitters / established role | .03961 | .03693 | .00859 | .00841 |
| Pitchers / established role | .03540 | .03450 | .00813 | .00796 |
| Hitters / positive components, given meaningful role | .71584 | .70508 | .26061 | .25588 |
| Pitchers / positive components, given meaningful role | .69448 | .69373 | .25015 | .25035 |

For hitter arrival, the selected baseball-pedigree model improves log loss by .01176 and
its 95% paired interval excludes zero. Pitcher arrival improves by .00601 with its
interval also below zero. The
selected hitter meaningful-role challenger also improves outer log loss with its
interval below zero, though its Brier interval crosses zero.

Established-role uncertainty is mixed. The hitter and pitcher intervals cross zero.
In the conditional positive-component test, both selected challengers are
indistinguishable from core. Neither quality challenger is promoted.

## Limits and decision

The candidate still worsens some supported groups, most notably older players. This
is not a universal win and does not authorize direct WAR bonuses. Failure to produce
a robust positive-component gain is direct evidence against turning draft status into
an FV floor. Current production values remain unchanged.

Rule 4 draft evidence cannot distinguish high-value international amateurs. Signing
bonus evidence for those players remains a genuine data gap. Publication FV and rank
remain outside model inputs and are used only as an external diagnostic.

The machine-readable result is
[`prospect-arrival-nested-robustness-result.json`](prospect-arrival-nested-robustness-result.json).
