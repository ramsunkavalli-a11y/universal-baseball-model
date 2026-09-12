# Present hitter talent checkpoint

Last updated: 2026-09-12  
Status: **PARTIAL DIAGNOSTIC; READY AS THE FUTURE-TALENT BASELINE**

The confirmed Current Talent Baseline 2 now runs on the locally accepted 2024 MLB,
Triple-A, Double-A, High-A and Single-A evidence. It produces translated, recency-
weighted and regressed profiles for 2,609 hitters. The output converts each profile to
an MLB-neutral batting rate using the existing certified RE24 method.

This is deliberately a talent rate, not projected value. It excludes playing time,
position, defense, running, future aging, MLB arrival, replacement, contracts and all
public ranks/FV. FanGraphs is joined only after scoring as an outside audit label.

The diagnostic ranks 2,091 hitters with at least 100 effective events. The other 518
remain unresolved even if their point rate is extreme. Every row shows evidence,
reliability, level, the largest positive component and the largest negative component.

Important limitation: this is present batting skill, not future prospect ceiling.
The MLB names sensibly dominate the present-skill top. Only 28 hitters from the attached
FanGraphs top 100 have any supported profile here, and 22 clear the 100-event ranking
line. Their current-skill ordering differs sharply from the publication list because
age-based development and future ceiling have not yet been learned. That disagreement
is expected and must not be "fixed" by importing FV.

Next build: use historical cutoffs to predict one- and two-year future translated skill
from this profile, age relative to level, level, recency and evidence. Compare unchanged
talent, a transparent Tango/Marcel age baseline, and a regularized age/level/component
model on identical later player rows. Public prospect lists remain audit only.
