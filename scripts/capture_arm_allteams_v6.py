"""Preserve a separate all-team arm pilot after the scope amendment."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
from run_hitter_finite_return_baseline import protections, save
from source_defensive_positions_v2 import embedded
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/arm-receiving-v6'


def capture(year):
    assert year in (2022, 2025)
    params = dict(type='Fld', game_type='Regular', n=1, season_start=year,
                  season_end=year, split='no', team='', with_team_only=0)
    path = OUT / f'arm-allteams-{year}.response'
    if not path.exists():
        response = requests.get('https://baseballsavant.mlb.com/leaderboard/baserunning',
                                params=params, timeout=45)
        response.raise_for_status()
        path.write_bytes(response.content)
    content = path.read_text(encoding='utf8')
    meta = embedded(content, 'serverParams')
    assert meta['season_start'] == meta['season_end'] == year
    assert meta['entity_code'] == 'Fld' and meta['game_type'] == 'Regular'
    assert meta['with_team_only'] is False
    rows = embedded(content, 'data')
    report = dict(year=year, requested=params, metadata=meta, rows=len(rows),
                  path=str(path), sha256=sha256_file(path), model_fit=False)
    save(OUT / f'arm-allteams-{year}-capture.json', report)
    return report


if __name__ == '__main__':
    protections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(capture, (2022, 2025)))
    save(OUT / 'arm-allteams-capture.json', dict(captures=results, no_2026_outcomes=True,
         contract_sha256=sha256_file(ROOT / 'docs/arm-receiving-v6-team-scope-amendment.md')))
    print([(r['year'], r['rows']) for r in results])
