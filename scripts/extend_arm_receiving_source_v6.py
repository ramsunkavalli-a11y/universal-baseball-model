"""Extend a reviewed source method; no model fits or protected seasons."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
import polars as pl
from source_defensive_positions_v2 import embedded
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.arm_receiving_source import (
    arm_metadata, receiving_metadata, normalize_arm, normalize_receiving)
from universal_baseball.arm_receiving_coverage import arm_record
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/arm-receiving-v6'


def capture(item):
    kind, year = item
    assert (kind == 'arm' and 2016 <= year <= 2025) or (kind == 'receiving' and 2021 <= year <= 2025)
    if kind == 'arm':
        endpoint='baserunning'
        params=dict(type='Fld',game_type='Regular',n=1,season_start=year,season_end=year,
                    split='no',team='',with_team_only=0)
    else:
        endpoint='first-base-scoops-receiving'
        params={'type':'fielder_3','season[]':year,'splitYear':1,'min':1,'minSplit':1,'gameType[]':'R'}
    path=OUT/f'{"arm-allteams" if kind == "arm" else kind}-{year}.response'
    if not path.exists():
        response=requests.get('https://baseballsavant.mlb.com/leaderboard/'+endpoint,params=params,timeout=45)
        response.raise_for_status(); path.write_bytes(response.content)
    content=path.read_text(encoding='utf8')
    meta=embedded(content,'serverParams')
    (arm_metadata(meta,year,False) if kind=='arm' else receiving_metadata(meta,year))
    return dict(kind=kind,year=year,requested=params,metadata=meta,path=str(path),
                sha256=sha256_file(path),rows=embedded(content,'data'))


def main():
    protections()
    import json
    pilot=json.loads((OUT/'pilot-review.json').read_text())
    assert pilot['historical_extension_allowed'] and pilot['player_walkthrough_status']=='complete'
    for group in ('input_hashes','output_hashes'):
        for p,h in pilot[group].items():assert sha256_file(Path(p))==h,p
    assert not (OUT/'extension-capture.json').exists()
    items=[('arm',y) for y in range(2016,2026)]+[('receiving',y) for y in range(2021,2026)]
    with ThreadPoolExecutor(max_workers=3) as pool: captures=list(pool.map(capture,items))
    ledger_path=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    ledger=pl.read_parquet(ledger_path)
    native={(year,pid):g.to_dicts() for (year,pid),g in ledger.group_by(['season','player_id'])}
    annual=[]
    for cap in captures:
        ids=set()
        for raw in cap['rows']:
            pid=int(raw['entity_id'] if cap['kind']=='arm' else raw['player_id'])
            assert pid not in ids;ids.add(pid)
            record=(arm_record if cap['kind']=='arm' else normalize_receiving)(
                raw,native.get((cap['year'],pid),[]),cap['year'])
            annual.append(record)
        cap['rows']=len(ids)
    pl.DataFrame(annual,infer_schema_length=None).write_parquet(OUT/'annual.parquet')
    save(OUT/'extension-capture.json',dict(captures=captures,rows=len(annual),
        native_discrepancies=[r for r in annual if not r['native_match']],
        model_fit=False, no_2026_outcomes=True,player_walkthrough_status='pending',
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),ledger_path,
            ROOT/'src/universal_baseball/arm_receiving_source.py',OUT/'pilot-review.json',
            ROOT/'src/universal_baseball/arm_receiving_coverage.py',
            ROOT/'docs/arm-receiving-v6-missing-measurement-amendment.md',
            ROOT/'docs/arm-receiving-v6-pilot-result.md']},
        output_hashes={str(OUT/'annual.parquet'):sha256_file(OUT/'annual.parquet')}))
    print('Rows:',len(annual),'Native gaps:',sum(not r['native_match'] for r in annual),flush=True)


if __name__=='__main__':main()
