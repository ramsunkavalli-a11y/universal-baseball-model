# Testing whether team record helps prospect playing time

2026-10-03. The user suggested that a club's record could help explain young
prospects' opportunity. This is one bounded opportunity comparison within the
practical hitter plan, not a new talent model or a presumed bad team bonus.
No fits have been run when this contract is saved.

## Question and information available

Does the MLB organization's completed origin-season winning percentage improve
next-calendar-year MLB appearance, expected PA and delivered batting value for
players who have not debuted? Trees can interact this information with existing
age, level, performance and prospect-ranking inputs. The direction is not imposed.
Record in the season being predicted is forbidden. This does not test in-season
deadline opportunity, projected future standings or specific available roster jobs.

Retrieve only 2011–19 and 2021–24 official team and final standings captures.
Map a dated December 31 MLB roster first; otherwise use the player's most recent
primary batting club, using that club's own season affiliation. The latter is a
proxy, not certified year-end rights: later trades without further batting may
be missed. If that club season is older than origin, organization or record is
unknown, or the parent is not MLB, the model record is unknown. Never substitute
current affiliations or assume an unaffiliated player belongs to a losing club.
Retain raw provenance, source season, club ID, parent ID and missingness reason.
Validate changed affiliates against historical club reports before fitting.

## Fixed comparisons

Keep the 63,282-row source and exactly 30,506 held-player forecasts from the
current fresher-ranking candidate. Origins are 2016–18 and 2021–24; target is
the following calendar year. All exits and non-arrivals remain. Known certified
non-arrival means zero PA and zero delivered value, not zero hitting talent.

Fit two opportunity constructions with the same 251 original inputs, training
rows, settings and weights as the fresher-ranking candidate:

- Coverage control adds one record-known indicator.
- Record candidate adds that indicator and winning percentage minus 0.5.
  Unknown records encode zero centered percentage plus known=0, not a .500 claim.

Each construction fits an any-MLB-PA classifier and an active-only PA regression.
Use the existing 250-iteration depth-three histogram trees, minimum leaf 30,
learning rate .05, L2 10, seed 31 and no early stopping. Equal-origin row weights
are unchanged. Preserve the existing dated unavailability/retirement rules and
conditional PA clipping to [1,800]. No tuning or additional context fields.

Primary forecasts replace opportunity only for never-debut players. Established
players remain bit-identical to the current candidate. Predeclare an all-player
sensitivity for both fitted constructions, not a route chosen after scores.
The primary contrast is record candidate versus coverage control; comparison
to the unchanged current candidate checks whether the whole addition is useful.
This prevents a missing-affiliation signal from being called a record effect.

Keep the current hitting forecast bit-identical in every arm. Delivered value
is expected PA times fixed batting yield, in the existing common-origin
fixed-event batting-plus-replacement units. This is not full WAR, six years of
control, trade value, causal evidence about team behavior or proof of MLB talent.
Do not reuse ambiguous rate-label fields to score a new rate model: no rate
model changes here.

## Checks before fitting

Audit affiliation coverage by origin, stage and debut history; inspect named
players and historically changed affiliates. Save source hashes and all actual
full/active chronological held-player preflights before any fits. Preserve
original training IDs: target year no later than origin, no 2020 target, and
exclude the entire held-player fold. Show distinct training people by debut,
stage, age, rank and record band in both subsets, plus winning-percentage range.
Sparse profiles remain scored and cannot support an unqualified DSL claim.

## Scores and player review

Use equal-target-year PA RMSE and MAE, appearance Brier and log loss, delivered
value RMSE, player-clustered nominal 95% paired MSE intervals and raw totals.
Report whole population, never-debut, upper/lower minors, record-known and
record bands, every origin, new draftees and the matched 2,627 public players.
The primary public forecasts are unchanged by definition; the all-player
sensitivity is explicitly separate. Examine 2021 and cohort shortfalls, not
just pooled loss. Exposed historical years remain development evidence.

Fixed cases: Kurtz 2024, Langford 2023, Julio Rodríguez 2021, Alonso 2018,
Bellinger 2016, Holliday 2023, Maitan 2017 and Judge 2024. Add largest PA gain,
harm, false high, false low and ordinary active case. Follow the required
stats-to-inputs-to-saved-model walkthrough, including dated record, actual
classifier/conditional PA outputs, fixed hitting yield, subsequent MLB reality,
training support and four peers selected without future outcomes. Probe the
saved fit at .400/.500/.600 records only as model mechanics, marking sparse
or artificial combinations. No automatic promotion from a noisy pooled win.

Retain only if record versus coverage-control gains are coherent with origin,
stage and player evidence and not merely one COVID-related year. If uncertain,
keep the existing candidate and document what this bounded test cannot reject.
No protected 2026 outcome access, frozen forecast change or explorer deployment.
