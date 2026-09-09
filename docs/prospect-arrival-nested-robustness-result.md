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

Earlier-origin selection chose `baseball_pedigree`, `C=1`, and no extra production-
rate regression for arrival, meaningful role, hitter established role, and both
positive-component outcomes. Pitcher established-role selection used the combined
baseball/demographic family.

| Population / target | Core log loss | Candidate | Core Brier | Candidate |
|---|---:|---:|---:|---:|
| Hitters / arrival | .16663 | .15529 | .04651 | .04471 |
| Hitters / meaningful role | .07642 | .06841 | .01778 | .01706 |
| Pitchers / arrival | .17208 | .16607 | .04861 | .04703 |
| Pitchers / meaningful role | .07060 | .06849 | .01772 | .01748 |
| Hitters / established role | .03896 | .03637 | .00852 | .00831 |
| Pitchers / established role | .03540 | .03450 | .00813 | .00796 |
| Hitters / positive components | .03506 | .03205 | .00714 | .00725 |
| Pitchers / positive components | .04895 | .04804 | .01101 | .01097 |

The cleanest incremental comparison holds the baseball interactions and `C=1`
fixed, then adds pedigree. Hitter log loss improved by .00869 for arrival and .00649
for meaningful role; both 95% paired-bootstrap intervals exclude zero. Pitcher gains
were smaller and both intervals cross zero. Pedigree is therefore supported for the
hitter research model and promising, not proven, for pitchers.

Established-role and positive-component uncertainty is mixed. Most intervals cross
zero, and hitter positive-component Brier worsens in the point estimate. The stricter
quality challenger is rejected.

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
