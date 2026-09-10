# Pitcher event-context readiness

Status: source review complete; no pitcher candidate scored.

The earlier matchup-source gate already established 3,691,876 exactly reconciled
terminal PAs across MLB and every affiliated level in 2021-2024. Those records retain
pitcher ID, batter side, and pitcher hand, with strict prior-date evidence counts.
That is enough to build a strongly regressed pitcher platoon summary once the ignored
generated sidecar is rematerialized.

The current checkout does not contain that 23 MB generated sidecar or its multi-GB
quarantined source archives. This is expected for source-data licensing/storage, but
it means the next event-level model cannot be reproduced from tracked files alone.

Current field decisions:

- **Platoon:** source design passed. Rematerialize the sidecar, join only exact
  accepted player-games, and give unsupported rows an exact neutral fallback.
- **Lineup band:** not ready. The certified sidecar never retained batting order and
  the MiLB PBP projection used to build it does not include that field. Source it from
  dated official boxscores or a separately validated reconstruction before testing.
- **Times through order / pitch process:** not universal. Outcome-minimal synthetic
  sequences at several lower levels prohibit interpreting intermediate pitches or
  reconstructing full batter-order cycles as comparable data.
- **Contact trajectory/direction:** terminal-contact classifications are available in
  the retained source design, but pitcher attribution must be joined through the
  rematerialized sidecar and audited by season and level before fitting.

No missing context may be imputed as favorable pitcher skill. Missingness must retain
the current aggregate baseline exactly. No 2026 outcome was inspected.
