# Recovering earlier MLB launch measurements

2026-10-04. The cached 2023 and 2024 launch source leaves the earlier forecast
folds without measured training profiles. Recover MLB 2015 through 2022 before
fitting the new next-year hitting contrast. This extends source coverage, not
the closed Current Talent challenger and not team-record testing.

## Bounded source request

Use the repo's official Baseball Savant detail-query template, restricted to
regular-season in-play pitches, one calendar month at a time from March through
October, in these eight explicit seasons. The in-play filter must still return
contacts without launch measurements; do not filter on EV/LA availability. Never
request 2025 or 2026. Retain the exact response bytes compressed locally, original
byte hashes, request URLs, retrieval time, raw row counts and projected hashes.
Use at most two concurrent requests and bounded retries. Save completed chunks
and resume rather than redownloading a successful response after interruption.

Project only ordinary identity/results plus launch speed and angle; all other
columns are excluded from the modeling surface. Check that every projected
row is regular-season and within the requested dates. Preserve all returned
in-play result rows, including bunts and incomplete measurements. Build the
non-bunt measurement summaries separately. Provider-estimated historical values
cannot be distinguished solely from these fields; preserve that limitation and
tracking-era indicators. 2020 MLB is a short season, not a canceled season.

## Source completeness checks

For each fully captured year, compare every player's 1B, 2B, 3B and HR counts
before excluding bunts against the existing independently reconciled MLB season
counts. Check the full in-play-result denominator against dated official AB minus
strikeouts plus sacrifice flies and bunts. Do not quietly waive differences or
correct readings to match official totals. Preserve discrepancy tables; an
unreconciled year is not approved for fitting even if most measurements look good.
Check unique game, physical hitter, PA and pitch identities and one in-play
terminal result per PA. Count no-result and unusual results explicitly.

The initial transport probe is the first declared monthly request. Inspect the
CSV schema, date/type restrictions, contact count, missing readings and memory
footprint before completing the remaining requests. A rejected filter/HTML
response, truncated response, repeated transport failure or disk headroom below
500 MB stops collection without deleting captured evidence. No alternate
unrecorded query is substituted. Data already cached for 2023 and 2024 is reused,
not redownloaded. A prior GitHub tracking-materialization run returned no retained
artifacts when checked in this session; that is not evidence its original data
or methodology was defective.

## Use boundary

This capture does no fitting, selection or prediction. Existing player, time and
source review requirements still apply before use. After capture, extend the
measurement adapter in a new version rather than editing the sealed two-season
pilot. Join to actual historical official game/venue authority before learned
park/opponent adjustment. Trace selected players through newly added history,
missingness and unchanged forecasts. Only then count training support and freeze
the direct future-MLB forecast contrast. Keep protected outcomes, current forecasts
and explorers unchanged throughout source acquisition.
