# Extended career workload-path result

Status: complete chronology-support source.

Official 2009-2025 MLB totals and exact debut dates produce 3,945 complete six-year
post-debut workload paths: 2,147 hitters and 1,798 pitchers, covering debut years
2009-2020. The 2020 season is normalized by the frozen `162/60` rule when it appears
inside a path.

This source extension exists to enforce forecast-time maturity: an evaluation year
can use only training paths whose six-year window ended in a prior year. It does not
change current workload priors or player values by itself.

Machine-readable evidence: `docs/career-workload-path-extension-result.json`.
