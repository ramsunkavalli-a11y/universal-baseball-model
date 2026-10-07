"""Fixed source players and origin-blind peers; source effects, no predictions."""
from collections import defaultdict
from datetime import date
from pathlib import Path
import math

import polars as pl
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import read,write
from audit_older_fielding_v24 import fielding_sources,OUT,PUBLIC,ROOT
from run_hitter_finite_return_baseline import protections

FIXED=['Andrelton Simmons','Mike Trout','Nolan Arenado','Brandon Belt','Miguel Rojas','Nick Castellanos']
POS={3:'1B',4:'2B',5:'3B',6:'SS',7:'LF',8:'CF',9:'RF'}


def ages():
    paths=[ROOT/'reports/generated/defensive-talent-position-v2/identity.parquet',
        ROOT/'reports/generated/hitter-2020-cohort/birthdates.parquet',
        ROOT/'reports/generated/multiyear-hitter-components-v1/component-panel.parquet']
    births={}
    for p in paths[:2]:
        for r in pl.read_parquet(p,columns=['player_id','birth_date']).iter_rows(named=True):
            if r['birth_date']:
                b=date.fromisoformat(str(r['birth_date']))
                assert r['player_id'] not in births or births[r['player_id']]==b
                births[r['player_id']]=b
    panel={(r['origin_year'],r['player_id']):r['age'] for r in pl.read_parquet(paths[2],
        columns=['origin_year','player_id','age','age_missing']).iter_rows(named=True) if not r['age_missing']}
    def get(year,pid):
        b=births.get(pid)
        if b:return year-b.year-((7,1)<(b.month,b.day)),'immutable_DOB_July_1'
        v=panel.get((year,pid))
        return (v,'dated_origin_panel') if v is not None else (None,'unknown')
    return get,paths


def distance(focal,other,exposure):
    unknown=other['age'] is None or focal['age'] is None
    return (unknown,abs(other['age']-focal['age']) if not unknown else 0,
            abs(math.log1p(other[exposure])-math.log1p(focal[exposure])),other['player_id'])


def annual(pid,start,end,official,old,native):
    rows=[]
    for year in range(start,end+1):
        positions=[]
        for pos in range(2,10):
            k=year,pid,pos; outs=official.get(k,0); o=old.get(k); n=native.get(k)
            if outs<=0 and o is None and n is None:continue
            positions.append(dict(position=pos,official_outs=outs,
                older=None if o is None else {f:o[f] for f in ['fielding_outs','RngR','ErrR','older_conversion_runs',
                    'older_conversion_rate','UZR','ARM','DPR','BIZ','Plays','OOZ','older_conversion_valid']},
                native=None if n is None else {f:n[f] for f in ['native_outs','range_runs','range_valid']},
                native_rate=1500*n['range_runs']/n['native_outs'] if n is not None and n['range_valid'] else None))
        rows.append(dict(season=year,positions=positions,mlb_outs=sum(p['official_outs'] for p in positions),
            no_recorded_mlb_exposure=not any(p['official_outs']>0 for p in positions)))
    return rows


def main():
    protections()
    assert not (PUBLIC/'player-walks.json.gz').exists()
    audit=read(PUBLIC/'audit-report.json.gz');verified=read(PUBLIC/'independent-review.json.gz')
    for r in [audit,verified]:
        for p,h in r['hashes'].items():assert sha256_file(Path(p))==h,p
    official,old,native=fielding_sources();age,age_paths=ages()
    allorig=pl.read_parquet(ROOT/'reports/generated/defense-minor-counts-v18/origins.parquet').to_dicts()
    origins={(r['origin_year'],r['player_id'],r['position']):r for r in allorig}
    cov={(r['origin_year'],r['player_id'],r['position'],r['window']):r
         for r in pl.read_parquet(OUT/'potential-coverage.parquet').to_dicts()}
    counts=pl.read_parquet(ROOT/'reports/generated/defense-minor-counts-v18/counts.parquet')
    walks=[];manifest=[];resolved={}
    pool=[]
    for (year,pid,pos),r in old.items():
        if year==2015 and r['official_outs'] is not None and r['official_outs']>0:
            a,basis=age(year,pid);pool.append(dict(player_id=pid,position=pos,age=a,age_basis=basis,official_outs=r['official_outs']))
    for name in FIXED:
        pids={r['player_id'] for r in old.values() if r['season']==2015 and r['player_name']==name}
        assert len(pids)==1,(name,pids);pid=pids.pop();resolved[name]=pid
        focal=max([r for r in pool if r['player_id']==pid],key=lambda r:(r['official_outs'],-r['position']))
        peers=sorted([r for r in pool if r['player_id']!=pid and r['position']==focal['position']],
            key=lambda r:distance(focal,r,'official_outs'))[:3]
        ids=[pid,*[p['player_id'] for p in peers]]
        cases=[]
        for selected in [focal,*peers]:
            p=selected['player_id'];pos=selected['position'];r=old[2015,p,pos]
            cases.append(dict(player_id=p,name=r['player_name'],position=pos,origin_year=2015,age=selected['age'],age_basis=selected['age_basis'],
                source_2015_positions=annual(p,2015,2015,official,old,native),
                same_position_old_runs=r['older_conversion_runs'],same_position_old_outs=r['fielding_outs'],
                same_position_old_rate=r['older_conversion_rate'],source_exposure_certified=r['older_conversion_valid'],
                accounting=dict(range=r['RngR'],errors=r['ErrR'],arms=r['ARM'],double_plays=r['DPR'],total_UZR=r['UZR'],
                    conversion_excludes_arms_and_double_plays=True),
                later_overlap_paths=annual(p,2016,2021,official,old,native),forecast=None,accuracy_gain=None))
        walks.append(dict(kind='MLB_2015_source',focal_player_id=pid,origin_year=2015,position=focal['position'],cases=cases,
            peer_rule='Same year/position; known age first, nearest age then log official-outs distance then MLBAM ID; no outcomes',
            interpretation='Measured conversion credit, not a talent forecast. Total UZR includes additional components.'))
        manifest.append(dict(kind='MLB_2015_source',focal=pid,peers=ids[1:],origin_year=2015,position=focal['position']))
    for name,pos in [('Mike Trout',8),('Andrelton Simmons',6),('Miguel Rojas',6)]:
        pid=resolved[name];choices=[r for r in allorig if r['player_id']==pid and r['position']==pos and not r['prior_current_MLB_fielding']]
        assert choices
        focal=min(choices,key=lambda r:r['origin_year'])
        peers=sorted([r for r in allorig if r['origin_year']==focal['origin_year'] and r['level']==focal['level']
            and r['position']==pos and r['player_id']!=pid and not r['prior_current_MLB_fielding']],
            key=lambda r:distance(focal,r,'minor_outs'))[:3]
        assert len(peers)==3
        cases=[]
        for r in [focal,*peers]:
            p=r['player_id'];year=r['origin_year'];key=year,p,pos
            raw=counts.filter((pl.col('player_id')==p)&(pl.col('season')==year)&(pl.col('position_code')==str(pos)))
            paths=set(raw['capture_path']);raw_stats=[]
            for s in raw.to_dicts():
                raw_stats.append({f:s[f] for f in ['season','source_id','usage_scope','normalized_level','fielding_outs',
                    'putOuts','assists','errors','chances','throwingErrors','doublePlays','chances_identity',
                    'capture_path','capture_split_index']})
            cases.append(dict(player_id=p,name=r['player_name'],origin_year=year,position=pos,
                actual_minor_inputs=r,source_rows=raw_stats,source_hashes={str(s):sha256_file(Path(s)) for s in paths},
                future_annual_positions=annual(p,year+1,year+5,official,old,native),
                windows=[cov[*key,w] for w in [3,5]],forecast=None,accuracy_gain=None,
                interpretation='Future exposure/measurement coverage only; nonarrival and other-position play are not zero origin-position ability.'))
        walks.append(dict(kind='earliest_minor_origin',focal_player_id=pid,origin_year=focal['origin_year'],position=pos,cases=cases,
            peer_rule='Same origin/level/position, no prior MLB fielding; known age first, nearest age then log minor-outs distance then MLBAM ID',
            interpretation='No new quality grade or learned prospect forecast; prior/current MLB returners excluded.'))
        manifest.append(dict(kind='earliest_minor_origin',focal=pid,peers=[r['player_id'] for r in peers],origin_year=focal['origin_year'],position=pos))
    paths=[Path(__file__),PUBLIC/'audit-report.json.gz',PUBLIC/'independent-review.json.gz',*age_paths,
        ROOT/'reports/generated/defense-minor-counts-v18/counts.parquet']
    write(PUBLIC/'player-walks.json.gz',dict(manifest=manifest,walks=walks,model_fits=0,quality_labels_created=0,
        player_walkthrough_status='calculations_pending_main_review',gains_and_harms='Not applicable: source/coverage audit has no forecasts',
        hashes={str(p):sha256_file(p) for p in paths}))
    for w in walks:
        print(w['kind'],w['origin_year'],[(c['name'],c['position'],c.get('same_position_old_rate'),
            [(v['window'],v['potential_coverage_available'],v['remaining_unmeasured_official_outs']) for v in c.get('windows',[])]) for c in w['cases']],flush=True)
    protections()


if __name__=='__main__':main()
