"""Trace saved future MLB-quality corrections and unchanged sparse fallbacks."""
from collections import defaultdict
from pathlib import Path
import json
import math

import numpy as np
import polars as pl

from verify_minor_range_correction_v21 import ROOT,PUBLIC,OUT,V20,read,write,close,design,key
from universal_baseball.storage import sha256_file

POSITIONS={3:'1B',4:'2B',5:'3B',6:'SS',7:'LF',8:'CF',9:'RF'}
FIELDS=('putOuts','assists','errors','chances','throwingErrors')


def main():
    replay=read(PUBLIC/'independent-review.json.gz')
    assert replay['real_fallback_replayed'] and replay['baseline_unchanged']
    for p,h in replay['hashes'].items():assert sha256_file(Path(p))==h,p
    preds=pl.read_parquet(OUT/'predictions.parquet').to_dicts();bykey={key(r):r for r in preds}
    focal={}
    def select(r,reason):focal.setdefault(key(r),dict(row=r,reasons=[]))['reasons'].append(reason)
    for year,pid,pos in [(2022,686527,9),(2022,687518,5),(2022,696285,8),(2022,683011,6),
                         (2022,678882,8),(2021,677951,6),(2021,665161,6)]:
        assert (year,pid,pos) in bykey,(year,pid,pos)
        select(bykey[year,pid,pos],'fixed diagnostic')
    measured=[r for r in preds if r['origin_year']==2022 and r['quality_rate'] is not None]
    gain=lambda r:abs(r['baseline']-r['quality_rate'])-abs(r['candidate']-r['quality_rate'])
    select(min(measured,key=lambda r:(-gain(r),key(r))),'largest primary absolute-error gain')
    select(min(measured,key=lambda r:(gain(r),key(r))),'largest primary harm or unchanged tie')
    stress=[r for r in preds if r['origin_year']==2021 and r['quality_rate'] is not None and r['applied']]
    select(min(stress,key=lambda r:(gain(r),key(r))),'largest changed stress deterioration')
    select(max(measured,key=lambda r:(r['candidate']-r['quality_rate'],-r['player_id'])),'largest primary false high')
    select(min(measured,key=lambda r:(r['candidate']-r['quality_rate'],r['player_id'])),'largest primary false low')
    ordered=sorted(measured,key=lambda r:(abs(r['candidate']-r['quality_rate']),key(r)))
    select(ordered[len(ordered)//2],'median primary absolute error')
    thin=[r for r in preds if r['origin_year']==2022 and r['level'] in ('DSL','COMPLEX') and r['quality_rate'] is None]
    select(min(thin,key=lambda r:(r['minor_outs'],key(r))),'origin-selected thin unmeasured lower minor')
    selections=[];people=set()
    for k,v in focal.items():
        r=v['row'];pool=[s for s in preds if s['origin_year']==r['origin_year'] and s['position']==r['position']
                        and s['level']==r['level'] and s['player_id']!=r['player_id']]
        peers=sorted(pool,key=lambda s:(abs(s['age']-r['age']) if s['age'] is not None and r['age'] is not None else 999.,
                    abs(math.log1p(s['minor_outs'])-math.log1p(r['minor_outs'])),s['player_id']))[:3]
        selections.append(dict(identity=list(k),name=r['player_name'],reasons=v['reasons'],peer_keys=[list(key(s)) for s in peers]))
        people.update((s['origin_year'],s['player_id']) for s in (r,*peers))
    manifest=PUBLIC/'player-selection.json.gz'
    write(manifest,dict(selections=selections,peer_rule='Same origin position principal level; age distance then log-outs distance then ID; no future outcome selection',
                       primary_changed_harms=sum(gain(r)<0 for r in measured),distinct_player_origins=len(people)))
    features=read(OUT/'features.json.gz');fb={(f['origin'],f['fold'],f['scope'],tuple(f['identity'])):f for f in features}
    cells={(c['origin'],c['fold']):c for c in read(PUBLIC/'cells-preflight.json.gz')}
    fits={(c['origin'],c['fold']):c for c in read(OUT/'correction-fits.json.gz')}
    rawpath=ROOT/'reports/generated/defense-minor-counts-v18/counts.parquet'
    raw=pl.read_parquet(rawpath).filter(pl.col('player_id').is_in(sorted({p for y,p in people}))).to_dicts()
    nativepath=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    native=pl.read_parquet(nativepath).filter(pl.col('season')<=2025).to_dicts()
    officialpath=ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet'
    official=pl.read_parquet(officialpath).filter(pl.col('is_mlb')&(pl.col('season')<=2025)).to_dicts()
    groups={g['group_id']:g for g in read(OUT/'source-groups.json.gz')}
    walks=[]
    for r in sorted((r for r in preds if (r['origin_year'],r['player_id']) in people),key=key):
        k=key(r);cell=cells[r['origin_year'],r['fold']];f=fb[r['origin_year'],r['fold'],'test',k];model=cell['baseline_fit']
        x=design([r],cell['age_median'],model['names'])[0]
        base_terms=(x-np.array(model['mean']))/np.array(model['scale'])*np.array(model['coefficients'])
        close(model['target_mean']+base_terms.sum(),r['baseline'])
        levels=defaultdict(lambda:dict(outs=0,**{field:0 for field in FIELDS}))
        current=[s for s in raw if s['season']==k[0] and s['player_id']==k[1] and int(s['position_code'])==k[2]]
        for s in current:
            levels[s['normalized_level']]['outs']+=s['fielding_outs']
            for field in FIELDS:levels[s['normalized_level']][field]+=s[field]
        traces=[]
        for t in f['count_trace']:
            counts=levels[t['level']];c=t['channel']
            count=counts['errors']-counts['throwingErrors'] if c==0 else counts['throwingErrors'] if c==1 else counts['assists'] if c==2 else counts['putOuts']
            exposure=counts['chances'] if c<2 else counts['outs']
            assert (count,exposure)==(t['count'],t['exposure'])
            g=groups[t['group_id']]
            traces.append(dict(**t,reference_scope=g['scope'],reference_people=len(g['people']),excluded_folds=g['excluded_folds']))
        annual=[];outs=0;runs=0.;missing=0;years=0
        for year in range(k[0]+1,k[0]+4):
            nr=[s for s in native if s['player_id']==k[1] and s['season']==year and s['position']==k[2]]
            legal=[s for s in nr if s['range_valid']];no=sum(s['native_outs'] for s in legal);run=sum(s['range_runs'] for s in legal)
            context=[s for s in official if s['player_id']==k[1] and s['season']==year]
            of=sum(s['fielding_outs'] for s in context if int(s['position_code'])==k[2]);outs+=no;runs+=run;years+=int(no>0);missing+=of if not legal else 0
            annual.append(dict(season=year,native_same_position=nr,official_all_positions=context,
                measured_runs=run,measured_outs=no,measured_annual_rate=1500*run/no if no else None,
                same_position_official_outs=of,unmeasured_official_outs=of if not legal else 0))
        assert outs==r['future_opportunities'];close(runs,r['future_runs'])
        assert (outs>=1500 and years>=2 and missing==0)==(r['quality_rate'] is not None)
        if r['quality_rate'] is not None:close(1500*runs/outs,r['quality_rate'])
        training=[t for t in features if t['origin']==r['origin_year'] and t['fold']==r['fold'] and t['scope']=='train'
                  and t['identity'][2]==r['position']]
        # These are exact saved generated-label examples, not refitted models.
        training=sorted(training,key=lambda t:(sum(abs(a-b) for a,b in zip(t['signals'],r['signals'])),tuple(t['identity'])))[:3]
        walks.append(dict(identity=list(k),forecast=r,known_source_history=[s for s in raw if s['player_id']==k[1] and k[0]-2<=s['season']<=k[0]],
            current_position_level_totals=dict(levels),count_trace=traces,
            baseline_arithmetic=dict(target_mean=model['target_mean'],terms=dict(zip(model['names'],base_terms.tolist())),prediction=r['baseline']),
            correction_model=fits[r['origin_year'],r['fold']]['fit'],closest_training_signal_examples=training,
            annual_MLB_paths=annual,source_baseline_and_label_replayed=True))
    paths=[Path(__file__),PUBLIC/'independent-review.json.gz',PUBLIC/'fit-report.json.gz',manifest,OUT/'predictions.parquet',
           OUT/'features.json.gz',rawpath,nativepath,officialpath,ROOT/'scripts/verify_minor_range_correction_v21.py']
    write(PUBLIC/'player-walkthrough.json.gz',dict(selection_manifest=selections,walks=walks,distinct_player_origins=len(people),
        positions=len(walks),player_walkthrough_status='pending_main_review',all_current_positions_retained=True,
        hashes={str(p):sha256_file(p) for p in paths}))
    for s in selections:
        w=next(w for w in walks if w['identity']==s['identity']);r=w['forecast']
        print(json.dumps(dict(name=r['player_name'],origin=r['origin_year'],position=POSITIONS[r['position']],reasons=s['reasons'],
            levels=w['current_position_level_totals'],grade=[r['baseline'],r['old_selected'],r['candidate'],r['quality_rate']],
            correction_terms=r['correction_terms'],applied=r['applied'],fallback=r['reasons'],stage=r['stage_people'],joint=r['joint_people'],
            future=[dict(year=a['season'],outs=a['measured_outs'],rate=a['measured_annual_rate']) for a in w['annual_MLB_paths']])),flush=True)
    print(dict(focals=len(selections),people=len(people),positions=len(walks),main_review='pending'),flush=True)


if __name__=='__main__':main()
