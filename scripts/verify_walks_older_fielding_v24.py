"""Verify chosen peers, raw minor counts and every annual position in source walks."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import math

import polars as pl
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import read,write
from run_hitter_finite_return_baseline import protections

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-older-quality-v24'
PUBLIC=ROOT/'reports/model-evidence/defense-older-quality-v24'


def main():
    protections()
    assert not (PUBLIC/'walk-replay.json.gz').exists()
    walks=read(PUBLIC/'player-walks.json.gz')
    for p,h in walks['hashes'].items():assert sha256_file(Path(p))==h,p
    official=defaultdict(int)
    for r in pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet').iter_rows(named=True):
        if r['is_mlb'] and r['position_code'].isdigit():
            official[r['season'],r['player_id'],int(r['position_code'])]+=r['fielding_outs']
    old={(r['season'],r['player_id'],r['position']):r for r in pl.read_parquet(OUT/'older-conversion-ledger.parquet').iter_rows(named=True)}
    native={(r['season'],r['player_id'],r['position']):r for r in pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').iter_rows(named=True)}
    qualified={(r['season'],r['player_id'],r['position']):r['older_conversion_valid'] for r in pl.read_parquet(OUT/'exposure-qualification.parquet').iter_rows(named=True)}
    origins=pl.read_parquet(ROOT/'reports/generated/defense-minor-counts-v18/origins.parquet').to_dicts()
    age_lookup={}
    for w in walks['walks']:
        for c in w['cases']:
            if w['kind']=='MLB_2015_source':age_lookup[c['player_id']]=c['age']
    # Rebuild the full origin-known age pool, not just the selected peer list.
    from datetime import date
    births={}
    for name in ['defensive-talent-position-v2/identity.parquet','hitter-2020-cohort/birthdates.parquet']:
        for r in pl.read_parquet(ROOT/'reports/generated'/name,columns=['player_id','birth_date']).iter_rows(named=True):
            if r['birth_date']:births[r['player_id']]=date.fromisoformat(r['birth_date'])
    panel={r['player_id']:r['age'] for r in pl.read_parquet(ROOT/'reports/generated/multiyear-hitter-components-v1/component-panel.parquet',
        columns=['origin_year','player_id','age','age_missing']).iter_rows(named=True) if r['origin_year']==2015 and not r['age_missing']}
    def age(pid):
        b=births.get(pid)
        return 2015-b.year-((7,1)<(b.month,b.day)) if b else panel.get(pid)
    captures={};annual_rows=raw_rows=0;identities=set()
    for w in walks['walks']:
        focal=w['cases'][0];assert focal['player_id']==w['focal_player_id']
        exposure='official_outs' if w['kind']=='MLB_2015_source' else 'minor_outs'
        if w['kind']=='MLB_2015_source':
            pool=[dict(player_id=k[1],age=age(k[1]),official_outs=official.get(k,0)) for k,r in old.items()
                if k[0]==2015 and k[2]==w['position'] and official.get(k,0)>0 and k[1]!=w['focal_player_id']]
            base=dict(age=focal['age'],official_outs=focal['same_position_old_outs'])
            assert focal['age']==age(focal['player_id'])
        else:
            base=focal['actual_minor_inputs']
            pool=[r for r in origins if r['origin_year']==base['origin_year'] and r['level']==base['level']
                and r['position']==base['position'] and r['player_id']!=base['player_id'] and not r['prior_current_MLB_fielding']]
            assert not any(r['origin_year']<base['origin_year'] and r['player_id']==base['player_id']
                and r['position']==base['position'] and not r['prior_current_MLB_fielding'] for r in origins)
        def dist(r):
            unknown=r['age'] is None or base['age'] is None
            return (unknown,abs(r['age']-base['age']) if not unknown else 0,
                abs(math.log1p(r[exposure])-math.log1p(base[exposure])),r['player_id'])
        peers=[r['player_id'] for r in sorted(pool,key=dist)[:3]]
        assert peers==[c['player_id'] for c in w['cases'][1:]],w
        for c in w['cases']:
            pid=c['player_id'];identities.add((pid,c['origin_year']))
            assert c['forecast'] is None and c['accuracy_gain'] is None
            if 'actual_minor_inputs' in c:
                origin=next(r for r in origins if r['player_id']==pid and r['origin_year']==c['origin_year'] and r['position']==c['position'])
                assert origin==c['actual_minor_inputs']
                assert sum(r['fielding_outs'] for r in c['source_rows'])==origin['minor_outs']
                for field in ['putOuts','assists','errors','chances','throwingErrors','doublePlays']:
                    assert sum(r[field] or 0 for r in c['source_rows'])==origin[field]
                for s in c['source_rows']:
                    path=Path(s['capture_path']);assert sha256_file(path)==c['source_hashes'][str(path)]
                    if str(path) not in captures:
                        captures[str(path)]=json.load(gzip.open(path,'rt')) if path.suffix=='.gz' else json.loads(path.read_text(encoding='utf8'))
                    data=captures[str(path)];splits=data['splits'] if 'splits' in data else data['stats'][0]['splits']
                    raw=splits[s['capture_split_index']]
                    assert int(raw['player']['id'])==pid and int(raw['season'])==c['origin_year'] and str(raw['position']['code'])==str(c['position'])
                    for field in ['putOuts','assists','errors','chances','throwingErrors','doublePlays']:
                        assert raw['stat'].get(field)==s[field],(pid,field)
                    raw_rows+=1
                paths=c['future_annual_positions']
            else:
                r=old[2015,pid,c['position']]
                assert c['same_position_old_rate']==1500*(r['RngR']+r['ErrR'])/r['fielding_outs']
                paths=c['source_2015_positions']+c['later_overlap_paths']
            for y in paths:
                positions={p['position'] for p in y['positions']}
                expected={p for p in range(2,10) if official.get((y['season'],pid,p),0)>0
                    or (y['season'],pid,p) in old or (y['season'],pid,p) in native}
                assert positions==expected
                assert y['mlb_outs']==sum(official.get((y['season'],pid,p),0) for p in expected)
                for p in y['positions']:
                    k=y['season'],pid,p['position'];assert p['official_outs']==official.get(k,0)
                    if p['older'] is not None:
                        for field,v in p['older'].items():assert v==(qualified[k] if field=='older_conversion_valid' else old[k][field])
                    if p['native'] is not None:
                        for field,v in p['native'].items():assert v==native[k][field]
                        n=native[k];rate=1500*n['range_runs']/n['native_outs'] if n['range_valid'] else None
                        assert p['native_rate']==rate
                    annual_rows+=1
    write(PUBLIC/'walk-replay.json.gz',dict(player_origins=len(identities),groups=len(walks['walks']),
        annual_position_rows=annual_rows,raw_minor_splits=raw_rows,origin_blind_peer_groups_replayed=len(walks['walks']),
        calculations_pass=True,main_baseball_review_pending=True,model_fits=0,quality_labels_created=0,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),PUBLIC/'player-walks.json.gz']}))
    protections()
    print(f'{len(identities)} player origins, {annual_rows} annual positions, {raw_rows} raw minor splits and all nine peer groups replay.',flush=True)


if __name__=='__main__':main()
