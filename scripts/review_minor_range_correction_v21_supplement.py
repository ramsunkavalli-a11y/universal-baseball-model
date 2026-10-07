"""Cover every changed measurable defender without changing the sealed first walk."""
from pathlib import Path
import json
import math

import numpy as np
import polars as pl

from verify_minor_range_correction_v21 import ROOT,PUBLIC,OUT,read,write,key,design,close
from universal_baseball.storage import sha256_file


def main():
    first=read(PUBLIC/'player-walkthrough.json.gz');covered={tuple(w['identity']) for w in first['walks']}
    preds=pl.read_parquet(OUT/'predictions.parquet').to_dicts()
    focal=[r for r in preds if r['applied'] and r['quality_rate'] is not None and key(r) not in covered]
    manifest=[];people=set()
    for r in focal:
        peers=sorted((s for s in preds if s['origin_year']==r['origin_year'] and s['position']==r['position'] and s['level']==r['level'] and s['player_id']!=r['player_id']),
            key=lambda s:(abs(s['age']-r['age']) if s['age'] is not None and r['age'] is not None else 999.,
                          abs(math.log1p(s['minor_outs'])-math.log1p(r['minor_outs'])),s['player_id']))[:3]
        manifest.append(dict(identity=list(key(r)),name=r['player_name'],reason='Changed measurable forecast not in first walkthrough',peer_keys=[list(key(s)) for s in peers]))
        people.update((s['origin_year'],s['player_id']) for s in (r,*peers))
    write(PUBLIC/'supplement-selection.json.gz',dict(selections=manifest,peer_rule='Same origin position level; age/log-outs distance then ID',model_fits=0))
    cells={(c['origin'],c['fold']):c for c in read(PUBLIC/'cells-preflight.json.gz')}
    fits={(c['origin'],c['fold']):c['fit'] for c in read(OUT/'correction-fits.json.gz')}
    features={(f['origin'],f['fold'],tuple(f['identity'])):f for f in read(OUT/'features.json.gz') if f['scope']=='test'}
    rawpath=ROOT/'reports/generated/defense-minor-counts-v18/counts.parquet'
    raw=pl.read_parquet(rawpath).filter(pl.col('player_id').is_in(sorted({p for y,p in people}))).to_dicts()
    nativepath=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet';native=pl.read_parquet(nativepath).filter(pl.col('season')<=2025).to_dicts()
    offpath=ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet';official=pl.read_parquet(offpath).filter(pl.col('is_mlb')&(pl.col('season')<=2025)).to_dicts()
    walks=[]
    for r in sorted((r for r in preds if (r['origin_year'],r['player_id']) in people),key=key):
        k=key(r);cell=cells[k[0],r['fold']];m=cell['baseline_fit'];x=design([r],cell['age_median'],m['names'])[0]
        terms=(x-np.array(m['mean']))/np.array(m['scale'])*np.array(m['coefficients']);close(m['target_mean']+sum(terms),r['baseline'])
        annual=[];outs=0;runs=0.;missing=0;years=0
        for y in range(k[0]+1,k[0]+4):
            nr=[n for n in native if n['player_id']==k[1] and n['position']==k[2] and n['season']==y];legal=[n for n in nr if n['range_valid']]
            no=sum(n['native_outs'] for n in legal);run=sum(n['range_runs'] for n in legal);of=[n for n in official if n['player_id']==k[1] and n['season']==y]
            same=sum(n['fielding_outs'] for n in of if int(n['position_code'])==k[2]);outs+=no;runs+=run;years+=int(no>0);missing+=same if not legal else 0
            annual.append(dict(season=y,native=nr,official_all_positions=of,measured_runs=run,measured_outs=no,annual_rate=1500*run/no if no else None))
        assert outs==r['future_opportunities'];close(runs,r['future_runs'])
        assert (outs>=1500 and years>=2 and missing==0)==(r['quality_rate'] is not None)
        if r['quality_rate'] is not None:close(1500*runs/outs,r['quality_rate'])
        walks.append(dict(identity=list(k),forecast=r,known_source_history=[n for n in raw if n['player_id']==k[1] and k[0]-2<=n['season']<=k[0]],
            count_trace=features[k[0],r['fold'],k]['count_trace'],baseline_arithmetic=dict(target_mean=m['target_mean'],terms=dict(zip(m['names'],terms.tolist()))),
            correction_model=fits[k[0],r['fold']],annual_MLB_paths=annual))
    assert all(key(r) in covered|{tuple(w['identity']) for w in walks} for r in preds if r['applied'] and r['quality_rate'] is not None)
    paths=[Path(__file__),PUBLIC/'player-walkthrough.json.gz',PUBLIC/'supplement-selection.json.gz',OUT/'features.json.gz',OUT/'predictions.parquet',rawpath,nativepath,offpath]
    write(PUBLIC/'player-walkthrough-supplement.json.gz',dict(selections=manifest,walks=walks,distinct_player_origins=len(people),positions=len(walks),
         all_changed_measured_forecasts_walked=True,model_refits=0,player_walkthrough_status='pending_main_review',hashes={str(p):sha256_file(p) for p in paths}))
    for s in manifest:
        w=next(w for w in walks if w['identity']==s['identity']);r=w['forecast']
        print(json.dumps(dict(name=s['name'],origin=r['origin_year'],grade=[r[a] for a in ('baseline','candidate','quality_rate')],
            terms=r['correction_terms'],sources=[dict(level=t['level'],channel=t['channel'],count=t['count'],exposure=t['exposure'],weight=t['posterior']['weight']) for t in w['count_trace']],
            annual=[a['annual_rate'] for a in w['annual_MLB_paths']])),flush=True)


if __name__=='__main__':main()
