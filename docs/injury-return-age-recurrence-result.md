# Injury return: age and recent recurrence

Status: rejected; retain IL type plus elapsed days.

The test used the same 2022–2023 fit and 2024 selection target as the accepted injury
baseline. It compared age band, recent prior IL placement, and their combination.
Each detailed cell was partially pooled toward its matching IL-type/elapsed-days
cell. Prior strengths of 10, 25, 50 and 100 players were declared before scoring.

The common cohort contains 991 of 1,221 player-cutoffs with a known stable birth
date. Recent recurrence means an earlier IL placement in the 365 days before the
current IL placement, using only transactions known by that cutoff.

No candidate improved all four required 2024 measures. The closest was age with a
100-player prior:

- Brier improved by 0.000263.
- Availability MAE improved by 0.000245.
- Availability RMSE improved by 0.000230.
- Log loss worsened by 0.000174.

Because nothing passed selection, nothing was carried into the untouched 2025
confirmation. This is a rejection, not evidence that age or recurrence can never
matter; the current broad grouping does not justify more complexity.

Reproduce with:

```powershell
.\.venv\Scripts\python.exe scripts\audit_injury_return_age_recurrence.py
```
