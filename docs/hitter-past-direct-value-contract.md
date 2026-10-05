# Same past inputs, direct future MLB batting value

2026-10-05, written before fitting. The completed count-error diagnosis and its
thirteen player walks are prerequisites. This is one fixed development contrast,
not an algorithm tournament, subgroup hybrid or fresh independent holdout.

Question: can direct batting-rate learning use the exact past-only count source
matrix better than the saved eight-event count likelihood? Targets are next
calendar year's MLB batting wins above that year's league mean per 600 PA,
conditional on MLB batting; delivered value adds the unchanged replacement
contribution at unchanged expected PA. Non-arrivals remain in delivered scoring,
never in conditional talent training. No full-WAR, lifetime, control or trade
claim follows. Do not access 2026 or change its completed evaluation.

Reuse all five sealed count feature matrices, the exact 35 chronological,
held-player training/test cells and three 112/121/175-feature routes. Each route
trains on all eligible active training rows as before, not a favorable subset.
Keep 30,506 original forecasts plus thirteen separately scored additions with
their existing research PA and no invented incumbent. Retain all source/support
warnings, including 2021 reorganization and sparse overseas entrants; the
conditional active-label limitation does not disappear because the fit converges.

Fit exactly one residual Ridge per route/cell: the unchanged past CLR profile
defines a fixed probability baseline, converted into batting-rate units; learn
the difference between future relative batting and that baseline from the exact
saved count covariates. Training baseline uses the completed target environment
only for matured training rows; held inference uses the own-fold origin reference
only, exactly like the count offset. Verify training target counts and labels;
no held target environment enters predictions. Keep safe fixed units and divide
work_0/1/2 by 600, as the count model does. No fitted scaler or selected features.

Use Ridge alpha=100, inherited from the existing scalar learning convention;
future-PA times equal-origin row weights, normalized to active training-row count.
Count NLL uses the same relative PA weighting, normalized to total weighted PA.
No penalty search, new source prior, blend or foreign-specific tuning. This
changes output family, loss and penalty geometry: scalar corrections are linear
and not constrained to event probabilities; their penalty units differ from
count-logit units. A win cannot be attributed purely to loss, nor establish the
best Ridge penalty or isolate the four removed MLB-quality features. Record
training sizes and physical rate-envelope warnings; never silently clip or drop.

Before any fit: verify immutable source/previous review hashes, reconstruct the
fixed-case baselines, independently pair annual MLB counts/labels, and persist
105 preflight checks for actual active training and all test rows. Reuse the
unchanged count full/active profile support and feature-range records, stating
why applicable; do not call inherited sparse profiles adequately supported.
Stop on chronology, missing required features, duplicate rows, label mismatch,
future references in inference or changed evaluation membership.

Primary evaluation is unchanged equal-origin future-PA-weighted hitting RMSE
and delivered batting-plus-replacement RMSE on original forecasts. Also report
MAE, paired player-clustered development intervals, PA/value totals, each origin,
current MLB, upper/lower never-debut, non-arrivals, >=600 weighted recent MLB PA
and overseas history. Keep public Steamer/ZiPS anchors under the existing
environment/vintage qualification. Additions remain separate. No event score
is fabricated for a scalar model. Do not select a favorable cohort after results.

Retain the same thirteen reviewed cases before fitting. Add any new largest
gain/harm, false high/low or ordinary case if not covered. Replay every head,
trace the baseline and full scalar feature contributions, recompute fixed-fit
minor/foreign removal probes and compare to source/model history and origin-only
production peers. Any new case requires that full source and peer walk, not
just a leaderboard. No next fit or disposition before readable review.

Candidate must beat the incumbent in both primary measures, survive origin and
cohort review and explain consequential gains/harms to warrant further
consideration. Worsening by >5% in a nonempty scored cohort triggers explicit
review; empty/sparse labels forbid an unqualified success claim. Near-correct
totals or improvement over the failed count arm alone are insufficient. No
automatic explorer promotion. Stop after this fixed comparison and walks; retain
the incumbent if it fails, and use the contrast to choose one next repair.
