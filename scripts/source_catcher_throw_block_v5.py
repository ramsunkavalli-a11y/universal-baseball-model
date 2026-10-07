"""Immutable year-specific catcher source capture; never 2026 or a model fit."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import io
from pathlib import Path

import requests

from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/catcher-throw-block-v5'


def capture(item):
    kind,year=item
    assert kind in ('throwing','blocking') and (2016 if kind=='throwing' else 2018)<=year<=2025
    path=OUT/f'{kind}-{year}.response'
    params=dict(game_type='Regular',n=1,season_start=year,season_end=year,split='no',
                team='',type='Cat',with_team_only=1,csv='true')
    if kind=='throwing':params['target_base']='All'
    if not path.exists():
        response=requests.get(f'https://baseballsavant.mlb.com/leaderboard/catcher-{kind}',params=params,timeout=45)
        response.raise_for_status()
        assert 'csv' in response.headers.get('content-type','').lower()
        assert response.content.strip() and not response.content.lstrip().startswith(b'<')
        path.write_bytes(response.content)
    rows=list(csv.DictReader(io.StringIO(path.read_text(encoding='utf-8-sig'))))
    assert rows and {int(r['start_year']) for r in rows}=={year}
    # Blocking CSV intentionally leaves end_year blank for a single year.
    # Any populated end year must agree; a blank is preserved, not fabricated.
    ends={int(r['end_year']) for r in rows if r['end_year'].strip()}
    assert not ends or ends=={year}
    assert len({r['player_id'] for r in rows})==len(rows)
    return dict(kind=kind,year=year,requested=params,path=str(path),sha256=sha256_file(path),
                observed_start_years=sorted({int(r['start_year']) for r in rows}),observed_end_years=sorted(ends),
                rows=len(rows),columns=list(rows[0]),sample=rows[:2])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--extend',action='store_true');args=parser.parse_args()
    protected=protections();OUT.mkdir(parents=True,exist_ok=True)
    if args.extend:
        import json
        review=json.loads((OUT/'pilot-review.json').read_text(encoding='utf8'))
        assert review['source_integrity']=='pass' and review['player_walkthrough_status']=='complete'
        for path,expected in review['hashes'].items():assert sha256_file(Path(path))==expected
        items=[(k,y) for k in ('throwing','blocking') for y in range(2016 if k=='throwing' else 2018,2026)]
    else:items=[(k,y) for k in ('throwing','blocking') for y in (2022,2025)]
    with ThreadPoolExecutor(max_workers=3) as pool:captures=list(pool.map(capture,items))
    report=OUT/('extension-capture.json' if args.extend else 'pilot-capture.json')
    assert not report.exists()
    save(report,dict(captures=captures,protections=protected,model_fit=False,no_2026_outcomes=True))
    for c in captures:print(c)


if __name__=='__main__':main()
