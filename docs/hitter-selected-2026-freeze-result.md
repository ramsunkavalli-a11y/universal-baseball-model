# Selected hitter candidate frozen for the final 2026 evaluation

2026-10-05. A separate candidate is now frozen for 4,030 hitters, with 25 fitted
heads and a 53-file checked package. All forecasts replay, and 37 real players
have exact source-to-model construction walks. No completed 2026 outcomes have
been accessed. This is construction approval, not an accuracy win, deployment
approval or completion of the full player-value project.

The model preserves the strongest tested route: measured MLB hitting for prior
major leaguers with tracking, numeric hitting for those without it, and translated
production plus scouting for never-debuted prospects. Participation and workload
are separate. The fixed population contains 3,116 never-debuted hitters, 797
tracked prior major leaguers and 117 untracked prior major leaguers. All talent
heads train on all qualifying future-active training players, not just their route.

## Errors caught and repaired before fitting

The initial new base adapter reproduced raw V31 career PA, which missed MLB
appearances in split-level seasons. It now reproduces the tested full-count
correction. The repair affected 765 forecast records; Judge's observed career
MLB exposure is 5,002 PA, Kurtz's 489 and Caminero's 866.

The preparation notes also wrongly said to exclude origin 2020. Every retained
family actually used the repaired canceled-season cohort admitted after the
original incomplete cohort was withdrawn. All 140 saved training memberships
match. Separate source reconstruction reproduces all 5,133 special-origin
inputs; normal-origin base construction reproduces the other 58,149. Target
2020 remains excluded. No canceled MiLB games are invented.

All five translation folds reproduce the old 63,282 profiles and graphs exactly;
2025 evidence enters only its own and later origins. Base, actual 251 job inputs
and 262 measured-hitting inputs reproduce across the full historical frame.
Ten fixed base cases and their thirty peer walks, 160 independent translation
walks, and 26 focused unit tests support the source gates.

The 68,660 dated 2025 transactions leave all 30,506 historical overrides
unchanged. Twenty-two reported retirees and two definitively unavailable hitters
receive zero participation, not fabricated zero talent. Injury, release and
free agency do not automatically mean zero. An initial nullable-table schema
failure was repaired in a separate consumer, preserving the collector/captures.

## What the actual frozen forecasts look like

Judge projects for 588 expected PA and +4.69 hitting wins above league average
per 600 PA; Kurtz 535 PA and +2.65; Yordan 463 and +2.64; Lee 516 and −0.09.
These are MLB hitting forecasts, not total WAR. Expected batting-plus-replacement
contributions are respectively 6.43, 4.03, 3.48 and 1.53 wins.

Made and De Vries remain in the model despite no MLB history: approximately
34%/40% next-year participation, 89/121 expected PA, and −0.17/−0.16 conditional
MLB hitting wins per 600. These are next-calendar-year estimates—not their peak
talent, lifetime ceiling, six control years or trade values. Detailed saved fit
terms and actual-head support accompany them; these numbers are not validated
by reputation or by future results.

Total expected PA is 181,374 and contribution 578.73 batting/replacement wins.
For context, the completed 2025 source had 182,926 league PA. Similar volume is
a useful sanity check, not validation: cohort membership and actual 2026 league
coverage can differ. Sparse/unseen conditional-player profiles remain flagged
and in the evaluation population. The 132 unknown-age rows retain explicit
fallback flags; absence of a transaction is not certified health.

## Coverage and next step

Every December roster identity outside the cohort is accounted for: 662 saved
pitchers, five dated pitcher-role hints and three unmodeled non-pitchers—Tyler
Austin, Sung-Mun Song and Munetaka Murakami. Their forecasts remain missing, not
zero. Later January signings are not inventoried by the December population.
Foreign talent integration and universal player coverage remain unresolved.

The [final evaluation contract](hitter-2026-final-evaluation-contract.md) fixes
primary future-season-relative contribution and secondary common-origin
contribution, alongside participation, workload and hitting scores. With the
user's authorization, the next step is certified completed 2026 outcome retrieval
and one evaluation, including big misses and coverage failures. No post-result
retuning can turn this into another attempt to pass that same test. The requested
separate team-filtered explorer follows with clear units and support warnings.

[Machine-readable construction evidence](../reports/model-evidence/hitter-selected-2026-freeze/report.json)
contains checksums, support counts and compact source/fit/intermediate walks.
The private freeze manifest SHA-256 is
`a1d819ffcdd98a9ee62feecf5637b5ebe1f93b6e931d77d2b7d692ed928da67a`.
The original 31-file legacy package still verifies byte-for-byte. The long-range
goal remains active; this candidate is not full WAR or a complete value system.
