# Explorer for frozen forecasts and completed 2026 results

Open the separate local explorer at <http://127.0.0.1:8810/>. It contains all
4,030 fixed forecasts, actual 2026 MLB outcomes, a 2025 organization filter,
stage filter, hitting-only sorting and player details. The old explorer is
unchanged. This local server serves only the new display folder and binds to
127.0.0.1, not an external network interface.

The display separates chance of appearing, PA if appearing, expected PA,
conditional hitting above average per 600 PA, and delivered batting
contribution. Zero-PA players have an unobserved actual hitting rate, not zero
talent. Seven actual participants without forecasts are shown separately,
not silently assigned zero predictions. The team filter describes the captured
2025 source affiliation, not 2026 destinations, roster capacity or team WAR.

Player detail includes actual 2023–25 source counts. The 129 replayed diagnostic
players also have fitted rate terms, exact workload paths, profile support and
arithmetic separation of workload/rate error. These are explanations of saved
calculations, not causal effects or confidence intervals. Other players are
explicitly labeled as not individually reviewed in the final case selection.

Independent headless Edge tests passed: full membership, pagination, Giants
upper-minors filtering, hitting-only sort, Judge's exact displayed predictions
and outcomes, Made's sparse warning and unobserved rate, non-arrival/empty
search, all cohort/coverage rows and missing-name handling. Desktop and mobile
screenshots were visually inspected; the initial mobile table overflow was
fixed and tested again without whole-page overflow.

The in-app browser connector failed twice before initialization. Opening the
page in Codex was queued through the supported panel tool; direct inspection
of the user's in-app tab was not possible. This does not prevent the local
browser-independent tests or a user opening the URL.

Two display defects were caught before handoff: only MLB team listings were
initially loaded, and null source names broke search. Existing same-season
minor-team listings complete the affiliation filter; 136 genuinely missing
source names/affiliations remain labeled by ID or unknown rather than invented.
The mobile grid repair affects layout only. Earlier builds and additive
correction receipts remain; frozen forecasts, outcomes and scores are unchanged.

Read the [completed evaluation](hitter-final-2026-result.md) and
[player review](hitter-final-2026-player-review.md) before using the numbers as
a model endorsement. This is batting only, not full WAR, six-year upside,
control value or trade value. The matched 2026 public benchmark is unavailable.
