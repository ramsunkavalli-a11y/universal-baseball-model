"""Verify archived transport bytes and dates without fetching any live resource."""
import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import gzip
import hashlib
import json
from pathlib import Path
import requests
from universal_baseball.storage import sha256_file
from universal_baseball.historical_prospect_rank import features
import polars as pl
import capture_hitter_preseason_2026_archive as archived

OUT = archived.OUT; ROOT = archived.probe.ROOT


def main():
    assert not (OUT/'transport-and-player-review.json').exists(), 'Preserve review'
    review = json.loads((OUT/'archived-rank-review.json').read_text(encoding='utf8'))
    transports = []
    for c in review['captures']:
        stamp, original, _, _, expected_digest = c['archive_record']
        response = requests.get(c['requested_url'], stream=True, timeout=(20, 60), allow_redirects=False)
        assert response.status_code == 200 and response.url == c['requested_url']
        moment = parsedate_to_datetime(response.headers['memento-datetime'])
        assert moment.strftime('%Y%m%d%H%M%S') == stamp
        assert parsedate_to_datetime(response.headers['x-archive-orig-date']) <= moment
        payload = response.raw.read(decode_content=False)
        wire_path = OUT/f'archive-{stamp}.transport'; assert not wire_path.exists(); wire_path.write_bytes(payload)
        decoded = gzip.decompress(payload) if response.headers.get('content-encoding') == 'gzip' else payload
        assert hashlib.sha256(decoded).hexdigest() == c['response_sha256'], 'Archive body changed'
        digest = base64.b32encode(hashlib.sha1(payload).digest()).decode()
        assert digest == expected_digest, 'Transport bytes differ from archive index digest'
        transports.append(dict(snapshot=stamp, original=original, memento_datetime=moment.isoformat(),
            archived_original_date=response.headers['x-archive-orig-date'], archive_file=response.headers.get('x-archive-src'),
            content_encoding=response.headers.get('content-encoding'), archive_index_digest=expected_digest,
            wire_digest=digest, exact_archive_index_payload_match=True, transport_sha256=sha256_file(wire_path),
            decoded_sha256=hashlib.sha256(decoded).hexdigest()))
    ranks = review['captures'][0]['ranks']; previous = pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v67/ranks.parquet').to_dicts()
    all_ranks = previous+ranks; lookup = {(r['season'], r['player_id']): r['rank'] for r in all_ranks}
    capacity = {r['season']: r['list_capacity'] for r in all_ranks}
    dated = pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    cases = []; byid = {r['player_id']: r for r in ranks}
    # Published top ten plus fixed established/debut/sparse cases; no 2026 outcomes.
    ids = [r['player_id'] for r in ranks[:10]]+[592450, 701762, 808982, 693409]
    for pid in ids:
        inputs = features(pid, 2026, lookup, capacity)
        assert inputs['scout_list_available_0'] == 1.
        assert inputs['scout_list_capacity_0'] == 100.
        assert inputs['scout_listed_0'] == float(pid in byid)
        if pid in byid:
            assert inputs['scout_rank_score_0'] == (101-byid[pid]['rank'])/100
        history = dated.filter((pl.col('player_id') == pid) & pl.col('season').is_between(2023, 2025))
        cases.append(dict(player_id=pid, published_2026_rank=byid.get(pid), input_overlay=inputs,
            actual_2023_to_2025_history=history.select('season', 'bucket', 'position', 'plate_appearances', 'team_id').to_dicts(),
            qualification='No ranked-list membership implies pitcher/hitter role; reconcile roles from dated records before forecast membership.'))
    rank_path = OUT/'preseason-2026-ranks.parquet'; assert not rank_path.exists(); pl.DataFrame(ranks).write_parquet(rank_path)
    report = dict(archive_transport_verified=True, complete_rank_count=100, rank_source_approved=True,
        verified_available_by='2026-01-26', transports=transports, player_walkthrough_status='complete', cases=cases,
        live_2026_rankings_accessed=False, protected_outcomes_used=False, model_fits=0, candidate_frozen=False,
        source_hashes={str(p): sha256_file(p) for p in [Path(__file__), OUT/'metadata-probe.json',
            OUT/'archived-rank-review.json', rank_path]})
    (OUT/'transport-and-player-review.json').write_text(json.dumps(report, indent=2, allow_nan=False, default=str)+'\n', encoding='utf8')
    print(f'Archive wire digests and exact January/February dates verified; {len(cases)} rank-to-input player walks', flush=True)


if __name__ == '__main__':
    main()
