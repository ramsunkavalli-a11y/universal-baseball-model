# Accessible international league data sources

2026-10-04. Official Japan and Korea batting histories have been collected and
reviewed for the hitter work. Other public sites below are source leads, not
verified complete historical downloads. Public access does not by itself grant
redistribution rights; keep bulk captures private and respect provider terms.

| League | Source | What is established | Remaining limit |
| --- | --- | --- | --- |
| Japan NPB | [Official NPB](https://npb.jp/bis/2005/stats/) | Collected 2005–2024 first-team batting, 13,154 player-team-season rows | Identity gaps, park exposure and MLB translation remain |
| Korea KBO | [Official KBO](https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx) | Collected 2005–2024 first-team batting, 6,473 player-season rows; no login needed; reviewed English profiles provide 164 exact MLBAM identity joins | Crosswalk is partial; historical roles, park exposure and MLB translation remain |
| Japan and Korea | [FanGraphs NPB announcement](https://blogs.fangraphs.com/weve-added-npb-data-to-the-site/) and [KBO announcement](https://blogs.fangraphs.com/introducing-kbo-stats-on-fangraphs/) | NPB from 2018 and KBO from 2002; common interface, published park-adjusted metrics | Member export requires the user's authenticated session; actual year selection must be verified |
| Taiwan CPBL | [Official records](https://cpbl.com.tw/stats/recordall) and [advanced stats site](https://stats.cpbl.com.tw/) | Public statistical sites; indexed records include ordinary batting, running and advanced columns | Historical extraction, IDs and coverage have not been qualified; direct record-page retrieval failed in the research tool |
| Mexico LMB | [Official MiLB league stats](https://www.milb.com/en/mexican/stats/) | Public batting/pitching controls; the retrieved leaderboard explicitly shows 2024 regular season | All-player historical extraction and earliest usable year are not qualified; do not accept only qualified leaders |
| Dominican winter LIDOM | [Official statistics](https://lidom.com/estadisticas/) | Public official statistics entry point exists | Historical depth and automated extraction not qualified; winter games require game-date cutoffs, not just season labels |

## Priority for the model

Use the collected NPB and KBO history first because it directly addresses missing
professional evidence for MLB newcomers and returning players. Match identities,
preserve uncertainty, and translate walks, strikeouts, power and hits separately.
A country's label is not a substitute for the player's actual professional level
and experience. Japan's first team is not a DSL-equivalent rookie population.

Taiwan, Mexico and winter leagues could add relevant history, but adding more
sources before integrating the two completed ones would not resolve the current
forecast gap. Assess them next where a named missing player or a translation
sample establishes the need. This source survey does not certify international
amateur data, college data, full play-by-play or historical defensive metrics.

See the [NPB source result](hitter-foreign-history-source-result.md) and the
[completed KBO source result](hitter-kbo-history-source-result.md) for actual
collection evidence. No forecast or explorer changed at this source milestone.

The [identity and input review](hitter-foreign-input-readiness-result.md) now
connects the Japan/Korea counts to 641 dated player-origins in the existing
population ledger. This does not approve every source player as a hitter or
claim improved forecasts. FanGraphs' [April 2025 announcement](https://blogs.fangraphs.com/weve-added-npb-data-to-the-site/)
specifically confirms five-year park adjustments for NPB and KBO; do not infer
those adjustments from its older 2020 KBO introduction, which lacked them.
