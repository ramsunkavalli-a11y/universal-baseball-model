# Linked historical career-state path source

Status: source ready for historical replay; no current value changed.

The next simulator now has 3,945 complete six-year hitter/pitcher donor paths covering
23,670 annual rows. Every path retains its actual workload sequence, inactive seasons,
returns, pitcher role, cumulative observed career state and the prior raw MLB workload
relative to that season's active-player environment.

The shortened 2020 season is handled in two different, intentional ways: career-state
thresholds use the existing 162/60 full-season equivalent, while workload relative to
the 2020 MLB environment uses raw workload on both sides. This prevents a 2.7x error in
the progression input.

Historical demographics supply birth dates for 3,091 donor player/type paths. The
remaining 854 older paths are retained with explicit missing-age evidence. They are
not deleted and no age is invented; the replay must use a declared pooled fallback
when source-age reweighting requires it.

This completes the donor-data side of the integration. The next replay must preserve
whole path blocks while applying the prospect-specific transition process. It must not
sample isolated seasons, multiply the same workload evidence twice, or select a final
career tier before the simulated years unfold.

The reconstructed year-six state matches the existing frozen terminal tier for all
3,945 paths. There are zero definition mismatches.
