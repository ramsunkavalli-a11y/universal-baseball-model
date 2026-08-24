# Hitter v2 forecast-membership correction

Recorded: 2026-08-23  
Implementation commit: `b0e1a8e70f1ce96989931871aa74c89869d40629`

No candidate had been fit or scored when this correction was made.

The first pre-score report correctly isolated training rows from target rows,
but it did not separately freeze the population that would receive forecasts.
If prediction rows had later been created from the observed target roster,
target-season participant membership would have leaked into forecast
eligibility. The report with SHA-256
`0b47c0aa8654f84b78c457f77672c61e661f39149649e15b784b500ac0325c24`
is therefore superseded, not deleted.

The corrected rule is: define the forecast population from accepted
pre-cutoff evidence, create forecasts for that population, and only then join
target outcomes for evaluation. This produces forecast populations of 4,705,
5,568 and 6,381 players in V2022, V2023 and V2024. Their target-evaluation
overlaps are 3,176, 3,172 and 3,088 players. The 863, 813 and 671 target-only
players are explicit coverage exclusions; observing their future participation
does not retroactively make them preseason forecast members.

The corrected pre-score report is schema `0.2`, SHA-256
`445cf12e4fce1299b105bb56281a9102644edf5fd83171585a4dfe9035104d66`.

The repository-pinned Chadwick Register commit
`2e8e73355f9c77b963115377bd98c784cfeec10f` supplies exact birth dates for
100% of every corrected forecast population. Ages are derived as of July 1 of
the target season from immutable birth date; target membership is not used.

C1 is not ready to fit. Training history supports 6,297 adjacent-season
movement pairs (2,310 promotions and 368 demotions), but the current canonical
player-game table lacks venue/home-away context and observed GIDP-opportunity
counts. Those fields must be source-enriched and frozen rather than guessed.
Candidate scoring remains closed.
