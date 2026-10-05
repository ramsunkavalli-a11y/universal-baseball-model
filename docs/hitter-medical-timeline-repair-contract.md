# Rebuild medical observation history using actual MLB appearances

2026-10-05. Source repair contract, before reconstruction. No new prediction fit.

Rebuild the timeline, not another open-injury flag sweep. The older status audit
already established stale entries; this checkpoint implements its missing repair.
Preserve all original transactions, ledgers, models and forecasts.

Use the existing 83,300 origin/player population and its January information
cutoffs. Reuse the verified normalized transaction versions from the status
source builder. Add positive dated MLB batting evidence from the already approved
2015–2024 contact-event files. Read only game date, game ID and hitter ID, not exit
velocity or other tracking metrics. A contact proves participation on that date;
absence of a contact is not evidence of absence. These files omit some PA and
games, so their first date is an observed return upper bound, not the exact first
day back. Exclude known resumed/split-game IDs to avoid false date precision.
Use the verified historical positive PA windows as weaker bounded evidence,
especially before 2015. No 2026 inputs/results, current rosters or future labels.

Replay transactions and appearance evidence together. A return may end a pending
observation spell, allowing a subsequent placement to start a separate spell.
Do not truncate the old merged spell and lose later injuries. Transfers without
a captured placement remain left-truncated. Same-day play/placement cannot settle
whether play was before injury. A period total clears a continuing observation
only if its entire period starts after the entry; if it straddles a later scope
boundary it cannot certify activity after that boundary.

Keep four different concepts: reported IL entry, observed MLB use, reported
roster activation, and censored medical follow-up after scope exit. None is
clinical clearance. Do not clear a suspension, administrative restriction or
retirement from medical evidence. Rehab/minor-league contacts do not establish
MLB roster use. No-entry history is not a clean health certificate.

Export observation states, recent entries/surgery reports, observation-span
upper bounds, censored follow-up separately, and unknown coverage. Upper bounds
count the UNION of calendar intervals within the preceding two calendar years;
they are not actual injury days, team games lost or normalized PA. Do not sum
overlaps or include offseason time as learned unavailable playing opportunities.
Missing source years produce unknown burden, not zero. Fully covered recent
history requires both preceding calendar seasons in the annual transaction
coverage (2015 onward). Keep sparse older observations for case context.

Reconstruct all population rows and export an exact joined source table for the
63,314 model rows. Before any future fit, count distinct players in all 70
actual full/active chronological training subsets by observed state, current
MLB workload and age, including censored/no-return profiles. This is source
support only, not calibrated recovery probability or predictive validation.

Fixed source walks: Travis 2016, Tatis 2022, Hoskins 2023, Ellsbury 2018, Alvarez
2022, Maikel Franco 2016, Garlick 2022, Parker 2016, Canha 2016 and Judge 2024.
Add the largest removed follow-up span and largest added episode count among
model rows, selected without future outcomes. Use same-origin old observation
state and nearest age/prior MLB PA for outcome-blind peers. Show dated source
events, earlier and rebuilt evidence, source coverage, supported/unsupported
interpretation, unchanged benchmark heads and actual results for context.

Required tests: future/backdated mutations, positive-only evidence, missing
years, no automatic clearing of later injuries, same-day ambiguity, transfer
left truncation, censored follow-up, bounded-window endpoints and interval union.
Independently check Travis against his already saved complete official game log,
and repeat source reconstruction for the fixed cases. Validate identities and
cutoffs and bind source/output hashes. No future outcome affects any feature.

Completion means the corrected source table and player review are usable for a
separately contracted experiment. It does not close Tatis's unconditional health
forecast, demonstrate accuracy improvement, change the explorer or authorize
another medical penalty test. Stop if source meaning cannot be established.
