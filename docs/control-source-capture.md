# Control source capture

**Status:** implemented and league-scale verified 2026-09-09

The dated league-control build now retains every official API response used to
construct the player universe, current rights owner and service path. The
2026-09-08 build writes 230 files below `source-captures/`: one MLB-team list,
one season calendar, 60 dated roster responses and 168 batched people/history
responses.

Each response is stored as deterministic UTF-8 JSON. The manifest records its
request URL, HTTP status, retained size and SHA-256 hash, and the build verifies
all hashes before completing. This makes the parsed source values reusable after
the live API changes.

The boundary is explicit: the existing adapters expose parsed JSON, not the
server's original response bytes or a trustworthy retrieval timestamp. The
manifest therefore labels the representation
`canonical_utf8_json_from_parsed_response`, sets
`original_response_bytes_retained` to false and leaves retrieval time unavailable.
These hashes prove the retained files did not change; they are not hashes of the
original HTTP byte stream.

This closes current-checkpoint source retention. It does not create historical
FanGraphs payroll/service snapshots. Historical value replay still requires
then-known contract terms and a defensible dated opening-service baseline.

Implementation: `src/universal_baseball/source_capture.py` and
`scripts/build_league_control_snapshot.py`.
