# Pitcher event-context readiness

Status: compact contact source built and first candidate scored; candidate rejected.

The reproducible streaming path is now
`scripts/materialize_pitcher_contact_panel.py`. It downloaded and hashed 84 public
2021-2023 PBP assets one at a time, retained only compact pitcher contact summaries,
and deleted each raw asset after processing. Exact asset IDs, sizes, hashes and row
counts are frozen in `pitcher-contact-increment-result.json`; the raw download totaled
about 7.05 GB. This avoids requiring that much free disk for a permanent copy.

The first [contact increment audit](pitcher-contact-increment-result.md) used 2021 to
select among a fixed ground/popup/pull sequence, 2022-to-2023 as the outer test and
2023-to-2024 as untouched confirmation. The development-selected ground-rate signal
helped the first later period but did not repeat in confirmation, including after
season/level outcome adjustment and pre-MLB restriction. It is rejected. This does
not rule out a later opponent-, park- and handedness-adjusted contact residual; those
controls would be a new candidate and no longer have an untouched 2022-2024 test.

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
