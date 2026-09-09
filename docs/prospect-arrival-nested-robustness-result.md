# Prospect arrival nested robustness result

**Run date:** 2026-09-09  
**Status:** retrospective process audit; draft pedigree helps arrival, not established-role selection

The audit now tests 176 bounded combinations for three outcomes: any arrival, a
meaningful 200 PA/BF season, and an established role. The last means one 400 PA/BF
season or two lower-workload seasons (300 PA for hitters, 200 BF for pitchers). The
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
rate regression for the four arrival/meaningful-role outcomes. It did not select
pedigree for either established-role outcome.

| Population / target | Core log loss | Candidate | Core Brier | Candidate |
|---|---:|---:|---:|---:|
| Hitters / arrival | .16663 | .15529 | .04651 | .04471 |
| Hitters / meaningful role | .07886 | .06888 | .01804 | .01693 |
| Pitchers / arrival | .17208 | .16607 | .04861 | .04703 |
| Pitchers / meaningful role | .07075 | .06802 | .01780 | .01734 |
| Hitters / established role | .03986 | .03856 | .00863 | .00844 |
| Pitchers / established role | .03520 | .03405 | .00816 | .00787 |

The cleanest incremental comparison holds the baseball interactions and `C=1`
fixed, then adds pedigree. Hitter log loss improved by .00869 for arrival and .00649
for meaningful role; both 95% paired-bootstrap intervals exclude zero. Pitcher gains
were smaller and both intervals cross zero. Pedigree is therefore supported for the
hitter research model and promising, not proven, for pitchers.

For established roles, hitter selection kept baseball development/role interactions
without pedigree. Pitcher selection used the combined baseball/demographic family;
its uncertainty remains mixed. Only 30 hitters and 34 pitchers in the 2023 outer
cohorts reached the established threshold, so this result correctly limits how much
can be claimed.

## Limits and decision

The candidate still worsens some supported groups, most notably older players. This
is not a universal win and does not authorize direct WAR bonuses. The failure to
select pedigree for established roles is direct evidence against turning draft status
into an FV floor. Current production values remain unchanged.

Rule 4 draft evidence cannot distinguish high-value international amateurs. Signing
bonus evidence for those players remains a genuine data gap. Publication FV and rank
remain outside model inputs and are used only as an external diagnostic.

The machine-readable result is
[`prospect-arrival-nested-robustness-result.json`](prospect-arrival-nested-robustness-result.json).
