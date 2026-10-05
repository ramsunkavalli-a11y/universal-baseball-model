# Source review for separate MLB batting history

2026-10-05, before new fits. All four restored summaries reconstruct from annual
MLB event counts and season-wide observed league references across each of five
63,314-row matrices. That is 1,266,280 field comparisons at tolerance 1e-10, with
identical restored values across matrices and exactly matched annual MLB PA.
All sixteen fixed source cases pass post-origin count/reference mutation checks.
The 105 extended-feature preflight checks are complete. This approves only the
fixed historical fit, not predictive success or deployment.

These are batting summaries, not defense or positional credit. The old
batting-plus-replacement label subtracts its same-season replacement contribution
before computing quality; independent raw-event reconstruction gives the same
values. No future league mean, player result or foreign projection enters these
four fields. The source-year league mean is observable at the origin, not a
fitted translation from later results. Absent MLB years with certified complete
coverage have no batting evidence; existing presence flags distinguish absence
from observed league-average batting. The earliest required source year is 2009.

## What the fixed players receive

Values below are prior-shrunk batting wins above the source year's MLB mean per
600 PA. Annual quality is unshrunk batting rate times PA/(PA+1200); pooled quality
uses 1/.8/.6 weighted batting numerators with one 1200-PA prior. Do not read these
as unshrunk player talent or add replacement/position/defense value to them.

| Player and origin | Latest MLB PA | Latest quality | Previous quality | Two years earlier | Pooled MLB quality |
| --- | ---: | ---: | ---: | ---: | ---: |
| Judge 2016 | 95 | −0.175 | 0 | 0 | −0.175 |
| Thames 2017 | 551 | +0.762 | 0 | 0 | +0.762 |
| Maitan 2017 | 0 | 0 | 0 | 0 | 0 |
| Davis 2018 | 654 | +0.872 | +0.764 | +0.568 | +1.228 |
| Wilkerson 2018 | 49 | −0.202 | 0 | 0 | −0.202 |
| Yordan 2018 | 0 | 0 | 0 | 0 | 0 |
| Nola 2021 | 194 | +0.028 | +0.215 | +0.157 | +0.244 |
| Tatis 2021 | 546 | +1.348 | +0.648 | +0.972 | +1.851 |
| Suzuki 2022 | 446 | +0.318 | 0 | 0 | +0.318 |
| Judge 2023 | 458 | +1.317 | +2.408 | +1.279 | +2.792 |
| Misner 2024 | 15 | −0.153 | 0 | 0 | −0.153 |
| Perdomo 2024 | 388 | +0.050 | −0.105 | −0.873 | −0.417 |
| Kurtz 2024 | 0 | 0 | 0 | 0 | 0 |
| Yoshida 2024 | 421 | +0.370 | +0.356 | 0 | +0.531 |
| Lee 2024 | 158 | −0.133 | 0 | 0 | −0.133 |
| Suzuki 2021 | 0 | 0 | 0 | 0 | 0 |

Judge 2023's enormous 2022 batting year is retained separately instead of only
entering the common blended profile. Davis has substantial positive MLB history
too; this change cannot use advance knowledge of his later decline. Perdomo's
latest year is much better than two years earlier, even though the pooled MLB
summary remains negative. The yearly inputs let the learner see that direction,
not guarantee the later breakout.

Thames, Lee, Yoshida and Suzuki 2022 have genuine recent MLB evidence alongside
foreign histories. Restoring MLB summaries can distinguish those from Suzuki
2021's overseas-only entry. It does not itself calibrate NPB/KBO production to
MLB. For Judge 2016, a poor 95-PA MLB debut is strongly shrunk, not erased; the
new fields could therefore worsen him. Yordan, Kurtz and Maitan have no MLB
production in these years and get no invented positive or zero-talent label.
Their predictions may still move because fitting added fields changes the other
coefficients. Such movements must be accounted for in the post-fit review.

Nola's 184 MLB PA in the shortened 2020 season are 184 observations, not
annualized evidence. Its +0.215 yearly quality has lower sampling precision
than a comparable full-season exposure. Workload normalization remains a separate
existing feature. Canceled 2020 MiLB, 2021 reorganization, source/tracking ranges,
left-truncated old careers and weak foreign entry support remain qualified.

Source details and raw eight-event counts for all sixteen cases are sealed in
`reports/generated/hitter-mlb-detail-restoration/source-walks.json`. Full/active
joint quality-profile support and extended input-range warnings accompany the
preflight. Sparse cells are retained, not passed off as sufficient support.
No park-neutral, full-WAR or independent public-projection claim follows.
