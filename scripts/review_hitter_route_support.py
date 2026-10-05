"""Attach actual counts and saved paths to the support diagnostic, without fits."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
from evaluate_hitter_readiness_v49 import logit_trace
from run_hitter_nonmedical_opportunity import ROOT, OUT as BASE, read, verify
from diagnose_hitter_route_support import OUT, save


def main():
    assert not (OUT/'full-player-walks.json').exists(), 'Preserve completed walks'
    initial=read(OUT/'execution-receipt.json'); verify(initial['hashes'])
    school=read(OUT/'school-support-amendment.json'); verify(school['hashes'])
    counts_path=ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    foreign_path=ROOT/'reports/generated/foreign-origin-inputs/origin-inputs.json'
    paths=[Path(__file__),ROOT/'src/universal_baseball/histogram_prediction_trace.py',
        ROOT/'scripts/evaluate_hitter_readiness_v49.py',counts_path,foreign_path,
        OUT/'execution-receipt.json',OUT/'school-support-amendment.json']
    hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths}
    save('walk-source-seal.json',dict(before_walk=True,new_fits=0,hashes=hashes))
    counts=pl.read_parquet(counts_path); assert counts['season'].max()==2024
    foreign={r['candidate_key']:r for r in read(foreign_path)['rows']}
    frames={k:pl.read_parquet(BASE/f'features-{k}.parquet') for k in range(5)}
    fit=read(BASE/'fit-report.json'); walks=read(OUT/'player-support-walks.json')['cases']
    out=[]
    with threadpool_limits(limits=2):
        for c in walks:
            k,y=c['fold'],c['origin_year'];r=frames[k].filter(pl.col('row_id')==c['row_id']).row(0,named=True)
            h=counts.filter((pl.col('player_id')==r['player_id']) & pl.col('season').is_between(y-2,y))
            cell=next(z for z in fit['cells'] if (z['origin'],z['fold'])==(y,k))
            mechanics={}
            for head in cell['heads']:
                assert sha256_file(ROOT/head['path'])==head['sha256']
                m=joblib.load(ROOT/head['path']);v=np.array([r[n] for n in head['features']])
                mechanics[head['head']]=logit_trace(m,v,head['features']) if head['head']=='participation' else trace(m,v,head['features'])
            assert np.isclose(mechanics['participation']['linked_probability'],c['forecast']['observation_raw_p'],atol=1e-10)
            assert np.isclose(mechanics['conditional_pa']['raw_prediction'],c['forecast']['observation_raw_conditional_pa'],atol=1e-8)
            source=foreign.get(f'{y}:{r["player_id"]}')
            if source: assert source['information_date']==r['ctx_information_date']
            out.append(dict(**c,actual_domestic_history=h.sort(['season','bucket']).to_dicts(),
                actual_foreign_history=source,head_mechanics=mechanics,
                qualified_school_support=[s for s in school['cases'] if s['row_id']==c['row_id']],
                input_meanings='No MLB sample is distinguished by quality_present_0/last_MLB_known; work uses the incumbent workload reference, not raw PA'))
    verify(hashes)
    save('full-player-walks.json',dict(cases=out,walkthrough_status='pending_manual_review',
        hashes=hashes,new_fits=0,original_forecasts_unchanged=True))
    print(__import__('json').dumps(dict(walks=len(out),actual_saved_path_replays=2*len(out),new_fits=0)),flush=True)


if __name__=='__main__': main()
