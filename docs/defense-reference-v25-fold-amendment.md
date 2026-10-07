# Separate assembly folds from reference folds

The first accounting execution stopped on its first player because it assumed
the saved assembly's `outer_fold` was player ID modulo five. It is a different
player grouping: every testing year has all five saved assembly folds. Native
range fits and this contract's reference estimate use ID modulo five instead.
The original executable and preflight remain unchanged; no accounting result
or score was written by that invocation.

The sibling runner uses an explicit modulo-five reference fold for the offset
calculation while retaining the original assembly fold in the final walkthrough.
It never changes source parquets, saved rates, opportunities, predictions or
assembly membership. Both labels are shown. All people in the reference fold
are excluded across years and positions as originally contracted. This does
not certify or alter the separate assembly model's historical fold design.

The main conversation initially called the saved label a testing-year label.
That was incorrect: inspection showed all five labels within each year. The
actual correction is to distinguish two player grouping schemes.
