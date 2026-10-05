"""Archive metadata only. Never retrieve the live 2026 ranking or outcomes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/hitter-preseason-2026-archive-probe'
CONTRACT = ROOT/'docs/hitter-2025-source-extension-contract.md'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT/'metadata-probe.json').exists(), 'Preserve probe'
    results = []
    for i, target in enumerate(['www.mlb.com/prospects/2026/top100*',
                                'www.mlb.com/milb/prospects/2026/top100*',
                                'www.mlb.com/prospects/top100*']):
        params = dict(url=target, output='json', **{'from': '20260101', 'to': '20260301'},
            filter=['statuscode:200', 'mimetype:text/html'], fl='timestamp,original,statuscode,mimetype,digest',
            collapse='digest', limit=30)
        expected = requests.Request('GET', 'https://web.archive.org/cdx/search/cdx', params=params).prepare().url
        try:
            response = requests.get(expected, timeout=(15, 30), allow_redirects=False)
            path = OUT/f'metadata-{i}.response'; path.write_bytes(response.content)
            snapshots = response.json() if response.status_code == 200 else None
            if snapshots and len(snapshots) > 1:
                assert snapshots[0][0] == 'timestamp'
                assert all('20260101' <= r[0][:8] <= '20260301' for r in snapshots[1:])
            results.append(dict(target=target, requested_url=expected, status_code=response.status_code,
                response_sha256=sha256_file(path), snapshots=snapshots, body_content_requested=False))
        except (requests.RequestException, ValueError) as exc:
            results.append(dict(target=target, requested_url=expected, error=str(exc), body_content_requested=False))
    report = dict(captured_at=datetime.now(timezone.utc).isoformat(), archive_metadata_only=True,
        live_rankings_accessed=False, protected_outcomes_used=False, source_approved=False,
        input_hashes={str(p): sha256_file(p) for p in [CONTRACT, Path(__file__)]}, results=results)
    (OUT/'metadata-probe.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n', encoding='utf8')
    print([(r['target'], r.get('status_code'), len(r.get('snapshots') or [])) for r in results], flush=True)


if __name__ == '__main__':
    main()
