# Weak low-level hitter negative control

Status: **accepted as a guardrail; not a complete value model**.

The rule uses only broad baseball evidence known at the origin date: a hitter is age
23 or older, received at least 100 PA, played primarily at A-ball or below, and had
no more than 0.06 extra-base hits per PA. Every player stays in the outcome cohort;
players who did not reach MLB are scored as zero.

| Origin | Players | Reached MLB in four years | Mean positive batting-component WAR | Reached 1 WAR |
|---:|---:|---:|---:|---:|
| 2018 | 140 | 3.6% | 0.000 | 0.0% |
| 2021 | 117 | 4.3% | 0.005 | 0.0% |

This is stable enough to reject clearly implausible positive batting projections for
this profile. It does not prove that every matching player has no baseball value, and
it does not include defense. It means the proper batting baseline is approximately
zero expected positive MLB production—not an average MLB hitter prior.

Fernando Gonzalez matches the rule: age 24, nearly 90% of current workload at A-ball
or below, 205 current affiliated PA, 0.049 extra-base hits per PA, and a translated
one-year batting estimate near -27 runs per 600 PA. The foundation explorer therefore
labels his MLB batting outlook **near zero supported by history** while continuing to
withhold FV, total WAR and value.

Machine-readable results are in
`docs/weak-low-level-hitter-negative-control-result.json`.
