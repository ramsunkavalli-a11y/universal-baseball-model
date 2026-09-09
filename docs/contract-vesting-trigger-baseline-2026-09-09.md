# Contract vesting trigger baseline — 2026-09-09

Four of the 13 vesting-option rows now have exact, sourced trigger definitions. The
machine input uses plate appearances or pitching outs, both available from official
StatsAPI results. Pitching outs avoid errors from decimal innings notation.

- Aroldis Chapman: 120 pitching outs in 2026, plus a postseason physical condition.
- Kyle Freeland: 510 pitching outs in 2026.
- Yandy Diaz: 500 plate appearances in 2026; otherwise a $10M club option.
- Luis Castillo: 540 pitching outs in 2027, with a separate UCL/IL contract branch.

The evaluator is intentionally conservative. Reaching a simple counting threshold is
irreversible and can be marked vested. Missing a threshold is final only when that
season is complete. A satisfied stat threshold with a medical or other condition stays
pending. Missing observations never become zero.

This establishes the reusable StatsAPI calculation path but does not yet remove these
rows from economics review. The current 2026 season is incomplete, two triggers have
additional conditions, and the remaining nine vesting rows still need exact contract
language. The next integration should consume official season totals and schedule
completion, then translate only final trigger outcomes into contract states.
