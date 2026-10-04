# Minor contact requests can return nonterminal pitches

2026-10-04. Preserve the initial rejected 2023-07-01 pilot and the original
collector. The source returns two pitches for Felix Reyes in game 729589,
PA 71. Pitch 1 has description `hit_into_play`, type S, missing events/des,
EV 71.4 and angle 15. Pitch 2 is the actual terminal sacrifice fly, type X,
EV 89.2 and angle 24. A request filter is not a terminal-contact definition.

The source contract already requires type X plus nonblank terminal events
for launch evidence. Correct the capture check to require unique full pitch
keys on raw responses and unique PA keys only on their terminal subset.
Retain all nonterminal responses, even those carrying measured EV/angle,
in the raw and exclusion ledgers. Preserve missing measurements on terminal
contacts. Never deduplicate the PA by choosing the fastest, first or last
measured pitch. The terminal flag determines which contact belongs to the PA.

The corrected runner reuses byte-verified accepted pilot receipts and the
exact retained rejected response; it does not overwrite original receipts or
redownload that response to conceal the failure. New receipts name the
amendment, adapter and executing collector. This is a source-design repair,
not a feature change, predictive improvement or deployment authorization.
