"""Retrieve two exact preseason archive bodies; no live page fallback."""
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.parse import urlparse
import requests
from universal_baseball.historical_prospect_rank import _State
from universal_baseball.storage import sha256_file
import probe_hitter_preseason_2026_archive as probe

OUT = probe.OUT


def parse(html):
    parser = _State(); parser.feed(html)
    if len(parser.states) != 1:
        raise ValueError('Missing/ambiguous archived state')
    s = parser.states[0]
    assert s['context']['year'] == '2026' and s['context']['list'] == 'top100'
    entries = s['payload']['ROOT_QUERY']['getPlayerRankingsFromSelection({"limit":100,"slug":"sel-pr-2026-top100"})']
    assert sorted(x['rank'] for x in entries) == list(range(1, 101))
    rows = []
    for e in entries:
        ref = e['playerEntity']['player']['__ref']; assert ref.startswith('Person:') and ref[7:].isdigit()
        pid = int(ref[7:]); person = s['payload'][ref]; assert int(person['id']) == pid
        rows.append(dict(season=2026, player_id=pid, rank=int(e['rank']), list_capacity=100,
                         list_complete=True, player_name=person['useName']+' '+person['useLastName']))
    assert len({r['player_id'] for r in rows}) == 100
    return sorted(rows, key=lambda r: r['rank'])


def main():
    assert not (OUT/'archived-rank-review.json').exists(), 'Preserve review'
    metadata = json.loads((OUT/'metadata-probe.json').read_text(encoding='utf8'))
    candidates = metadata['results'][1]['snapshots'][1:]
    dates = ['20260126003740', '20260201193617']
    receipts = []
    for stamp in dates:
        row = next(r for r in candidates if r[0] == stamp)
        assert '20260124' <= stamp[:8] <= '20260201' and row[2] == '200'
        url = f'https://web.archive.org/web/{stamp}id_/{row[1]}'
        path = OUT/f'archive-{stamp}.html'; receipt_path = path.with_suffix('.receipt.json')
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text(encoding='utf8'))
            assert receipt['response_sha256'] == sha256_file(path)
        else:
            assert not path.exists(), 'Unreceipted response'
            response = requests.get(url, timeout=(20, 60), allow_redirects=False)
            # A redirect could silently select a different date or live resource. Never follow it.
            path.write_bytes(response.content)
            receipt = dict(requested_url=url, returned_url=response.url, status_code=response.status_code,
                location=response.headers.get('Location'), archive_record=row, captured_at=datetime.now(timezone.utc).isoformat(),
                response_sha256=sha256_file(path), metadata_sha256=sha256_file(OUT/'metadata-probe.json'),
                collector_sha256=sha256_file(Path(__file__)), protected_outcomes_used=False, live_fallback=False)
            receipt_path.write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf8')
        if receipt['status_code'] != 200:
            raise ValueError(f'Archive capture requires review: {receipt["status_code"]}; no live fallback')
        receipt['ranks'] = parse(path.read_text(encoding='utf8')); receipts.append(receipt)
    assert receipts[0]['ranks'] == receipts[1]['ranks'], 'Preseason ranks differ; inspect before approval'
    report = dict(source_approved_for_preseason_rank=True, original_publication_date_unknown=True,
        verified_available_by='2026-01-26', information_cutoff='Preseason January 26, 2026; other statistics through 2025',
        captures=receipts, exact_same_100_ranks=True, protected_outcomes_used=False,
        live_2026_rankings_accessed=False, retained_fields='Identity and publisher rank only; no biography or statistics')
    (OUT/'archived-rank-review.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print('Two exact preseason captures contain identical complete 100-player ranks; no live body accessed', flush=True)


if __name__ == '__main__':
    main()
