# Pitcher value funnel audit

**Status:** MLB workload defect corrected; prospect pitcher ranking still provisional

The playable results were joining the older generic opportunity paths after a better
MLB workload model had already been built. The corrected chain is now
`phase2-workload-paths -> phase2-conditional-war-paths -> uncertainty -> value` and
the source model and exact input hashes are recorded. The build can now reject the
wrong opportunity model instead of silently accepting it.

Across 940 debuted pitchers, the correction changes projected
six-year WAR from 1108.1 to
1325.5. This is a mean correction, not
an uncertainty bonus.

| Player | Old 2027 active | New | Old conditional BF | New | Old 6y WAR | New |
|---|---:|---:|---:|---:|---:|---:|
| Logan Webb | 0.820 | 0.936 | 424 | 493 | 7.45 | 9.21 |
| Tarik Skubal | 0.820 | 0.929 | 424 | 452 | 9.83 | 11.39 |
| Paul Skenes | 0.852 | 0.943 | 323 | 546 | 8.50 | 13.44 |

The prospect problem is not fixed. Among 3,849 pre-MLB pitchers,
the nested model now totals only 68.1 expected WAR and
its maximum is 2.66. The removed age/level/hand
adjustment had a small frozen point-score gain but uncertain bootstrap evidence and
a worse left-handed subgroup; its large effect on current top prospects was not
defensible enough to keep. No manual bonus or outside FV floor replaces it.

The separate four-year horizon audit finds that the hurdle probabilities are already
optimistic, not suppressive. The next required test therefore targets conditional MLB
WAR and linked career production: forecast pitchers at historical cutoffs, retain
every failure and zero, choose any correction on earlier cohorts, and score it once
on an untouched later cohort.

## Binding statistical rules

- Skill rate and playing time remain separate.
- Sparse samples are regressed toward a relevant population.
- Model choice is time-ordered and final evaluation stays untouched.
- Failures and non-arrivals remain in the denominator.
- Wider uncertainty does not lower the mean a second time.
- Outside FV is diagnostic only.
