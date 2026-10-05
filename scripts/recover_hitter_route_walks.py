"""Recover the source-boundary assertion, preserving the first runner and seal."""
import joblib
import numpy as np
import polars as pl
from pathlib import Path
from threadpoolctl import threadpool_limits
from review_hitter_route_support import ROOT, BASE, OUT, read, verify, save, sha256_file, trace, logit_trace


def main():
    assert not (OUT/'full-player-walks.json').exists(), 'Preserve completed walks'
    first=read(OUT/'walk-source-seal.json'); verify(first['hashes'])
    verify(read(OUT/'execution-receipt.json')['hashes'])
    school=read(OUT/'school-support-amendment.json'); verify(school['hashes'])
    paths=[Path(__file__),ROOT/'docs/hitter-route-walk-execution-note.md',OUT/'walk-source-seal.json']
    hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths}
    save('walk-recovery-seal.json',dict(before_recovery=True,new_fits=0,hashes=hashes))
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    assert counts['season'].max()==2025
    counts=counts.filter(pl.col('season')<=2024)
    foreign={r['candidate_key']:r for r in read(ROOT/'reports/generated/foreign-origin-inputs/origin-inputs.json')['rows']}
    frames={k:pl.read_parquet(BASE/f'features-{k}.parquet') for k in range(5)}
    fit=read(BASE/'fit-report.json'); out=[]
    with threadpool_limits(limits=2):
        for c in read(OUT/'player-support-walks.json')['cases']:
            k,y=c['fold'],c['origin_year'];r=frames[k].filter(pl.col('row_id')==c['row_id']).row(0,named=True)
            history=counts.filter((pl.col('player_id')==r['player_id']) & pl.col('season').is_between(y-2,y))
            cell=next(z for z in fit['cells'] if (z['origin'],z['fold'])==(y,k)); mechanics={}
            for head in cell['heads']:
                assert sha256_file(ROOT/head['path'])==head['sha256']
                m=joblib.load(ROOT/head['path']);v=np.array([r[n] for n in head['features']])
                mechanics[head['head']]=logit_trace(m,v,head['features']) if head['head']=='participation' else trace(m,v,head['features'])
            assert np.isclose(mechanics['participation']['linked_probability'],c['forecast']['observation_raw_p'],atol=1e-10)
            assert np.isclose(mechanics['conditional_pa']['raw_prediction'],c['forecast']['observation_raw_conditional_pa'],atol=1e-8)
            source=foreign.get(f'{y}:{r["player_id"]}')
            if source: assert source['information_date']==r['ctx_information_date']
            out.append(dict(**c,actual_domestic_history=history.sort(['season','bucket']).to_dicts(),
                actual_foreign_history=source,head_mechanics=mechanics,
                qualified_school_support=[s for s in school['cases'] if s['row_id']==c['row_id']],
                input_meanings='No MLB sample is distinguished by quality_present_0/last_MLB_known; work uses the incumbent workload reference, not raw PA'))
    verify(first['hashes']);verify(hashes)
    save('full-player-walks.json',dict(cases=out,walkthrough_status='pending_manual_review',
        hashes=first['hashes']|hashes,new_fits=0,original_forecasts_unchanged=True))
    print(__import__('json').dumps(dict(walks=len(out),actual_saved_path_replays=2*len(out),new_fits=0)),flush=True)


if __name__=='__main__': main()
