# Historical record source checks before fitting

2026-10-03. Source checks found that the 63,282-row feature table includes
2020 forecast origins. These are legitimate predictors of 2021 outcomes;
excluding 2020 *targets* does not mean excluding 2020 *origin information*.
Amend the original collection range to all origins 2011–24. No models have
been fitted and no target, forecast membership, arm or tuning setting changes.

For 2020 use actual MLB wins divided by wins plus losses, not wins divided by
162. Only the MLB team listing is needed for that canceled minor-league season.
An older minor club remains stale evidence and its current ownership is not
invented. The baseline already distinguishes canceled MiLB and short MLB
schedules; this record feature does not replace those inputs.

Source completeness checks also caught endpoint assumptions before fitting:
team listings need separate sport requests, final historical standings need
separate league requests without a December 31 filter that returns no rows,
and season is carried in each team record rather than its containing division.
The abolished short-season league is not requested after 2020. Capture request
parameters and actual row seasons are both retained and verified. These are
source retrieval corrections, not evidence for or against the baseball idea.

The existing 2020 forty-man and full-roster captures must also be used: the
older all-years roster table omits that separately repaired source. Freitas
exposed this join discrepancy; the original source team fields remain unchanged.
New 2020 entrants without batting may use their historical full-roster proxy.

The initial eight-player source walkthrough found a substantive ownership
problem: Maitan's Danville batting club implied Atlanta, but a captured
December 16, 2017 free-agent signing identifies the Angels. Apply a general
dated acquisition/release reconciliation using the existing 2015–24 transaction
captures, not a named-player override. Take the latest known event no later
than origin end, at least as recent as club-season evidence, for non-forty-man
players. A dated December 31 forty-man listing still takes precedence. Explicit
acquisitions can identify a parent; releases, elected free agency, unresolved
targets or conflicting same-day owners produce unknown record, not old-owner
context. Use the latest of reported, effective and resolution dates to avoid
early access. Keep transaction IDs and overrides beside the original club.
Season totals do not date the last batting appearance: the transaction rule
means in or after the last *club source season*, not necessarily after every
game played. Draft signings can confirm the same parent before that season's
batting. Do not describe these confirmations as proven late-season moves.

Transaction coverage is incomplete, especially before 2015 and in the low
minors. This does not certify every player's actual year-end rights. Preserve
that qualification and unknowns in the test, rather than excluding difficult
people. [The Angels report](https://www.mlb.com/angels/news/angels-agree-with-kevin-maitan-livan-soto-c262892874)
independently confirms the signing. The original contract's last-club proxy
is amended by this general rule before fitting; no forecast or outcome changes.
