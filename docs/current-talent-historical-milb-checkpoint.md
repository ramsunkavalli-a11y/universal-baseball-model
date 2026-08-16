# Current Talent historical MiLB checkpoint

## Status

The initial post-reorganization affiliated-MiLB historical evidence gate is complete for **2021–2023**. All five filename level groups (AAA, AA, High-A, Single-A, Rookie/complex) materialized successfully in each season through the shared Current Talent historical evidence path.

Successful full-season validation runs:

- **2021:** `31979609553`
- **2022:** `31971662070`
- **2023:** `31971923778`

This checkpoint certifies the historical evidence foundation needed to build deterministic as-of snapshots and future target windows. It does **not** certify a Current Talent model, environmental translation, Projection, playing time, WAR/value, or an overall ranking.

## 2021 final evidence totals

The final five-level 2021 run produced:

- **180,523** player-game rows
- **9,499** games
- **704,360 PA**
- **438,970** expected result contacts
- **439,034** observed physical contacts
- **+64** net contact residual
- **686,903** core profile events
- **554** unknown contacts
- **+8** summed PA-accounting residual
- **23** outcome-residual player-league cases sent to official adjudication
- **1,087** participant-authority exception games
- **1,100** official participant attribution changes

All five level outputs were accepted.

Level detail:

| Level | Player-games | Games | PA | Expected contacts | Observed contacts | Contact residual | Core profile events | Unknown contacts |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AAA | 37,805 | 1,925 | 145,997 | 94,659 | 94,663 | +4 | 142,327 | 12 |
| AA | 32,387 | 1,741 | 129,504 | 81,962 | 81,976 | +14 | 126,095 | 17 |
| High-A | 32,659 | 1,772 | 133,872 | 82,649 | 82,665 | +16 | 130,473 | 18 |
| Single-A | 32,793 | 1,777 | 135,845 | 82,708 | 82,720 | +12 | 132,652 | 25 |
| Rookie/complex | 44,879 | 2,284 | 159,142 | 96,992 | 97,010 | +18 | 155,356 | 482 |

## Certified 2021 boundary corrections

Two source defects required narrow, fail-closed corrections. Neither changes the general evidence policy.

### 1. Official boxscore identity correction

Game `660171` on `2021-09-23`, league `130`, contains one reusable player identity error. The source attributes a 4-PA batting line to player `703595`; the official boxscore assigns the exact line to **Victor Diaz (`682770`)**. The full game/team reconciliation and batting-order/position evidence isolate a unique correction.

Production policy: `certified_official_boxscore_identity_remap_v1` in `current_talent_identity_corrections.py`. The correction applies only when the exact game, date, outcome vector, and placeholder conditions remain satisfied; otherwise it fails closed.

Diagnostic workflow run: `31976338219`.

### 2. Certified false-positive physical contact

In `2021_7_rk_pbp.csv`, game `657792`, sequence `54`, pitch `1`, a caught-stealing runner event is stamped `type=X` and `hit_location=1` despite having no batting event, batted-ball type, coordinates, launch data, or hit distance. It therefore entered the reusable contact layer as a false physical contact.

Production policy: `certified_raw_false_positive_contact_exclusion_v1` in `armstjc_contacts.py`. The exclusion requires the exact asset, natural key, date, league, batter, pitcher, source codes, narrative, and absent hit-data fingerprint; drift fails closed. No broad narrative or `type=X` exclusion was adopted.

Raw-sequence diagnostic workflow run: `31978717668`.

## Evidence semantics

The historical Current Talent evidence remains **retrospective event-cutoff corrected history, not a vintage information set**. Predictor snapshots must use only events strictly before their cutoff date. Current corrections to historical source records may be used under this label; they must not be described as information known at the historical date unless vintage availability is separately captured.

PA/result-opportunity evidence and contact/profile evidence retain separate denominators and reconciliation diagnostics, per ADR 024. Season aggregates remain residual triggers/checks rather than invented game chronology, per ADR 027.

## Orchestration status

The heavy historical full-season and one-level live-source workflows are **manual-only after certification**. Their deterministic source/identity/contact regression tests remain part of the validation gate and normal CI remains automatic.

## Next gate

1. Assemble deterministic as-of predictor snapshots from the certified player-game evidence.
2. Assemble leakage-safe future windows, with the primary 90-day target and 200-PA aggregate diagnostic cap plus the contracted secondary horizons.
3. Only after those builders are validated, learn environmental translations and fit Baseline 0 / Baseline 1 out of time.
