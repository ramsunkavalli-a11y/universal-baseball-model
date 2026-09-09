# Late-season injured-list return baseline

## Decision

Use official MLB transaction chronology to adjust the point estimate only when a
player's replayed injured-list state agrees with the current official roster status.
Keep a zero-to-unadjusted-WAR range for every ordinary injured-list case. Do not infer
a return date from an injury label, diagnosis, roster depth or contract source.

The production reference uses 2022-2025. The 2021 cohort remains in the saved audit as
a sensitivity, but it is not fitted into the point model because MLB restored the
15-day injured list for pitchers and two-way players during 2022. This makes 2022-2025
the closer rule environment for the 2026 estimate. MLB's rule history is documented in
its [15-day injured-list glossary](https://www.mlb.com/glossary/injuries/15-day-injured-list).

## Evidence

At a September 8 cutoff, the 2022-2025 history contains 1,221 players on an injured
list. Of those, 261 were activated before the regular season ended. The raw return
rate is 21.38%, and the average fraction of the remaining calendar available after
activation is 12.28%. Broad list-type and elapsed-time cells are shrunk toward that
population result with a 25-player prior. This is an activation-timing estimate, not
a claim that an activated player immediately receives a full workload.

The 2021-2025 sensitivity cohort contains 1,719 players, with a 17.45% return rate and
10.06% average remaining availability. Annual results and source hashes are preserved
in the generated report.

For the 2026-09-08 snapshot:

- current official injury status and transaction replay agree for 263 players;
- 261 of those players have a rest-of-season projection and receive the calibrated
  point adjustment;
- after the subsequent current-role update, their 10.92 unadjusted WAR becomes 1.84
  WAR;
- the current league point estimate moves from 114.35 to 105.13 WAR, while the
  availability range is 102.07 to 114.40 WAR;
- 184 of 188 salary-linked injured players have a transaction-derived start date.

The larger current-status-only population is mainly affiliated minor-league status
that the MLB transaction ledger does not cover. Those rows retain the earlier point
estimate and zero-to-baseline sensitivity.

## Phase boundary

Phase 1 uses this simple, auditable activation-timing reference. Phase 2 can add injury
type, age, recurrence, actual post-activation workload and out-of-time calibration,
provided each input is available at prediction time and improves a protected test.
