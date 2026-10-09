# Historical whole-value integration check

2026-10-09, before assembling/scoring this comparison. The additive 2027
walkthrough is complete. This is one integration check, not another model search.

Use the identity-locked 12,432 forecast rows for target years 2023–25 from the
reviewed joint-role experiment. Join the saved small-sample-repaired batting
rate and its unchanged selected preseason PA by row ID. Reuse the reviewed
position allocator, scaling its opportunities only if the selected batting
anchor's PA differs. Never scale from realized workload. Use the same native
defensive rate estimators and selected running recipes with histories ending
at each origin. Minor profile fits must have cutoff no later than origin and
exclude the player's fold. No new hyperparameter choices or player overrides.

Reconstruct replacement and runs/win from the origin environment. Center on
origin positive-PA MLB membership and projected PA, not future performance or
all minor leaguers. Report any origin reference identities absent from the
locked forecast and their origin PA. Future results supply labels only.

Primary outcome is published realized FanGraphs hitter WAR, obtained from
complete public season tables with MLBAM identities. It is a common external
target, not a claim that the UBM accounting is identical. Report coverage and
missing labels; never infer zero WAR from a missing join when official batting
or fielding participation is present. Certified nonparticipants have zero
delivered WAR, but unknown defensive quality remains unknown.

Compare the combined forecast with (1) its unchanged batting-plus-replacement
anchor as a diagnostic, not a full-WAR model; (2) a simple recent-history
full-WAR-per-PA baseline using the identical forecast PA, three origin seasons
weighted 1/.5/.25 and 600 regression PA toward two WAR per 600 PA; and (3)
historical preseason Steamer WAR on exactly matched archive identities. ZiPS
full WAR is a separate rate/opportunity scenario, not depth-chart playing time.
Do not combine differently dated archives or call the later download date the
original forecast publication date. Existing archive-vintage limitations remain.

Primary reporting is equal-year RMSE and MAE, 2023–25 separately and pooled,
with player-clustered paired uncertainty. Also report all-player errors, current
MLB versus upper/lower/inactive stages, age/position, PA and WAR totals, and
errors conditional on measured MLB participation. Retain exits and nonarrivals.
Apply the finalization plan's 5% existing-baseline and 15% public guardrails;
investigate >10% PA or >15%/5-WAR total differences. These are practical checks,
not statistical significance thresholds.

Keep batting's observed-context qualification visible. Do not subtract a park
factor opportunistically after seeing scores or retune to public outcomes.
Differences in batting weights, park adjustment and defensive definitions can
explain a gap but cannot be used to declare an unmeasured accuracy win. Any
repair requires the intervening player review and an appended contract.

Walk the fixed diagnostic cases where eligible, largest gain and harm, false
high/low, and an ordinary measured case through origin statistics, rate and
workload, component arithmetic, public forecast and actual WAR. Select three
same-origin/stage/position peers by origin PA and age, without future outcomes.
Store their actual source rows and missing evidence. No further modeling
experiment begins until that interpretation is written.
