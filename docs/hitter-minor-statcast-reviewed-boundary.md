# Official review of minor Statcast contact boundaries

2026-10-04. The initial full capture found twenty-four one-contact player-game
differences. All retained backbone AB/K/SF/SH boundaries agree with current
official boxscores. Thirty official feeds explain the differences and six
split-venue games. Preserve the initial ledger/report and rejection receipts;
produce a separate reviewed source rather than changing raw files.

Thirteen differences are official at-bats ending in batter interference without
a physical in-play pitch. Subtract these from the boxscore physical-contact
boundary; do not infer a batted ball or launch measurement. Seven other missing
plays explicitly describe physical contact but have neither a returned terminal
Savant row nor an in-play pitch in the feed. Preserve a missing-contact inventory
with the official description. Include these known physical opportunities in
coverage denominators, but never fabricate a pitch number or measurement.

Three remaining missing contacts have a matching pitch in Savant with type S
and blank terminal metadata. Unlike the Felix Reyes nonterminal pilot pitch,
the official feed verifies that the SAME pitch ends a physical contact PA:
Steven Duggar in 2022 game 665032 PA 32 pitch 4; Ariel Almonte in 2024 game
760455 PA 78 pitch 1; Carter Mathison in 2024 game 760508 PA 8 pitch 3.
Use the exact official batter/PA/pitch identity and result to restore terminal
metadata in a separate adjusted projection. Retain original Savant EV/angle:
Duggar 81.1/-23, Almonte both missing, Mathison 91.1/8. Match available values
to official hitData, and record both sources. Never turn every measured
nonterminal pitch into a contact. The initial Felix Reyes exclusion still holds.

The one extra contact is Taylor Jones in 2023 game 721872 PA 46, a foul
strikeout that the source AND feed mark in play. It has no EV/angle. The official
strikeout result and narrative determine its exclusion, not the in-play flag
alone. Reject strikeout/walk/HBP/interference outcomes from the contact surface
even if the provider pitch type says X. This correction affects denominators,
not a predictive target or measured talent.

Six games finish in another park. Assign actual venue per terminal PA from
its end timestamp and the completed scheduled original/resumed segments.
Do not use the feed's one final park for every pitch. Keep the original
missing-venue ledger and per-play overrides. No future season is consulted.

The corrected annual table preserves canonical pitch-key contact counts,
measured EV/angle counts and raw metrics separately from seven extra known
physical opportunities lacking canonical pitch evidence. Its `pair_coverage`
uses those complete physical-opportunity denominators; preserve the returned-
contact-only ratio in a separate field. Reconcile every player-game boundary
with the thirteen non-contact AB exclusions, three metadata repairs, seven
explicit missing opportunities and the excluded strikeout. Missingness is not
zero quality. The source remains provider historical data with unverified
original publication vintage and per-row imputation status.

Official schedule names are authoritative: league 112 is Pacific Coast League;
117 is International League in 2022–24. The 2022 sparse-contact context is
International League, not Pacific Coast League. Earlier one-day broad-contact
percentages differ from terminal non-bunt full-season percentages; do not
substitute one denominator for the other.

This review authorizes only the corrected source projection. Actual player
walkthroughs, independent annual checks and chronological profile support
precede any separately contracted future MLB forecast test. No old predictive
result, production forecast or protected artifact is changed.
