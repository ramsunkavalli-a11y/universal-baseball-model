# Distinguish postponed games from played suspended segments

2026-10-07. The first team-aware source repair is preserved but its calendar
classification is superseded. The player review found that `abstractGameState`
is `Final` even on a `detailedState` of `Postponed`. Such a listing is not a
played segment. Game 745927 was postponed April 7 and played August 9; game
746628 was postponed June 5 and played August 26. They do not create early/late
uncertainty for Buxton or Witt.

Before creating game date context, validate the complete schedule's count and
historical scope, then retain only detailed completed-game states beginning
`Final` or `Completed Early`. Exclude postponed, cancelled and unplayed entries
from segment dates. Do not use a rescheduling date as proof of earlier play.
True resumed games keep their explicit resume/original dates and opposing-team
segments; Jansen's June 26/August 26 and Perez's July 13/August 5 records remain
unresolved between the two periods without individual segment evidence.

Produce a new sibling source repair with the same raw captures, annual
comparisons, fixed population, DH corrections and per-measurement unknowns.
Explicitly record both the original and corrected calendar recipes. Recompute
the verifier's calendar directly from detailed schedule states, rather than
sharing the corrected projection. Recheck the nineteen focal and 57 peer walks.
All annual role vectors and fixed forecasts must remain unchanged.

Regression tests cover postponed-versus-resumed games, same-team duplicates,
opposing-team appearances, field-specific coverage and error isolation. Known
early exposure, known late exposure and unplaced exposure are also exported as
conserving bounds; they are not fitted point forecasts or assumed recent roles.
No new model, 2026 outcome query or deployment accompanies this correction.
