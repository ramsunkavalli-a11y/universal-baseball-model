"""Matched MLB endpoint scores and actual-input player explanations, still provisional."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_minor_precision import METRICS
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from score_hitter_statcast_next_year import losses, interval
from score_hitter_minor_statcast_next_year import linear_trace
from review_hitter_minor_statcast_next_year import repaired_rows, scope, distance, META
import prepare_hitter_minor_precision as prep


def main():
    out=prep.OUT;assert not (out/'scores.json').exists(),'Preserve completed scores'
    pre=prep.read(out/'preflight.json');fit=prep.read(out/'fit-report.json')
    prep.old.verify_hashes(pre['input_hashes']);assert sha256_file(out/'predictions.parquet')==fit['predictions_sha256']
    q=pl.read_parquet(out/'predictions.parquet').sort('row_id')
    anchor=pl.read_parquet(out/'anchor.parquet').sort('row_id');assert q.select(anchor.columns).equals(anchor)
    q,changed=repaired_rows(q,prep.read(prep.old.OUT/'preflight.json'))
    # Historical negative heads are contrasts only, never rerun here.
    q=q.with_columns(pl.col('minor_measurements_rate').alias('old_joint_rate'),pl.col('minor_measurements_value').alias('old_joint_value'))
    arms=['preseason','ridge_measurements','combined','old_joint',*pre['arms']]
    replays=0
    with threadpool_limits(limits=2):
        for k in range(5):
            f=pl.read_parquet(out/f'features-{k}.parquet')
            for c in [c for c in pre['cells'] if c['fold']==k]:
                tr,te,_=prep.routed(f,c);got=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                assert te['row_id'].equals(got['row_id']) and te['msc_eligible'].equals(got['msc_eligible'])
                cell=prep.read(out/f'fit-{c["year"]}-{k}.json')
                assert sha256_file(Path(cell['predictions_path']))==cell['predictions_sha256']
                for h in cell['heads']:
                    assert sha256_file(Path(h['path']))==h['sha256']
                    raw=joblib.load(h['path']).predict(safe_matrix(te,h['features']))
                    assert np.allclose(raw,got[h['arm']+'_raw_update'],atol=1e-12,rtol=0);replays+=1
    for arm in pre['arms']:
        fallback=q.filter(~pl.col('msc_eligible'))
        for kind in ['rate','value']:assert fallback[arm+'_'+kind].equals(fallback['combined_'+kind])
        assert np.allclose(q[arm+'_value'],q['preseason_pa']*(q[arm+'_rate']/600+q['origin_replacement_rate']),atol=1e-12,rtol=0)
    prior=prep.read(prep.old.OUT/'scores.json');scores=[]
    for s in prior['scopes']:
        g=scope(q,s['scope']);assert len(g)==s['rows']
        active=g.filter(pl.col('next_pa')>0)
        rates={arm:losses(g,arm,'rate') for arm in arms} if len(active) else None
        equal={arm:dict(rmse=float(np.sqrt(np.mean((active[arm+'_rate'].to_numpy()-active['actual_future_relative_rate'].to_numpy())**2))),
                       mae=float(np.mean(abs(active[arm+'_rate'].to_numpy()-active['actual_future_relative_rate'].to_numpy())))) for arm in arms} if len(active) else None
        scores.append(dict(scope=s['scope'],rows=len(g),people=g['player_id'].n_unique(),participant_rate=rates,equal_active_row_rate=equal,
            actual_value=float(g['next_value'].sum()),actual_pa=int(g['next_pa'].sum()),predicted_pa=float(g['preseason_pa'].sum()),
            contribution={arm:dict(**losses(g,arm,'value'),predicted_total=float(g[arm+'_value'].sum())) for arm in arms+(['steamer'] if s['scope']=='public' else [])}))
    intervals=[]
    for label in ['eligible','eligible_predebut','all']:
        for control in ['combined','precision_coverage']:
            for kind in ['rate','value']:
                if label=='all' and kind=='rate':continue
                intervals.append(dict(scope=label,**interval(scope(q,label),'precision_measurements',control,kind)))
    oldcases=prep.read(prep.old.OUT/'reviewed-cases.json')['cases'];selected={c['origin']['row_id']:['retained reviewed origin before fit'] for c in oldcases}
    err=scope(q,'eligible').with_columns(((pl.col('combined_value')-pl.col('next_value'))**2-(pl.col('precision_measurements_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('precision_measurements_value')-pl.col('next_value')).alias('error'))
    for g,why in [(err.sort('gain','row_id',descending=[True,False]),'largest gain'),(err.sort('gain','row_id'),'largest harm'),
        (err.sort('error','row_id',descending=[True,False]),'false high'),(err.sort('error','row_id'),'false low'),
        (err.filter(pl.col('next_pa').is_between(100,600)).with_columns(pl.col('error').abs().alias('abs_error')).sort('abs_error','row_id'),'ordinary active')]:
        selected.setdefault(g['row_id'][0],[]).append(why)
    dated=pl.read_parquet(prep.ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    annual=pl.read_parquet(out/'annual-contact-noise.parquet');cases=[]
    for k in range(5):
        f=pl.read_parquet(out/f'features-{k}.parquet');refs=prep.read(out/f'noise-reference-{k}.json')['references']
        for c in [c for c in pre['cells'] if c['fold']==k]:
            _,te,_=prep.routed(f,c)
            for rid in [rid for rid in selected if rid in c['test_row_ids']]:
                o=q.filter(pl.col('row_id')==rid).row(0,named=True);row=te.filter(pl.col('row_id')==rid)
                oldcase=next((z for z in oldcases if z['origin']['row_id']==rid),None);traces={}
                for h in prep.read(out/f'fit-{c["year"]}-{k}.json')['heads']:
                    traces[h['arm']]=linear_trace(joblib.load(h['path']),row,h['features'])
                    assert np.isclose(traces[h['arm']]['replayed_raw_rate'],o[h['arm']+'_raw_update'],atol=1e-10)
                mask=(row['prior_debut'][0]==0,row['prior_debut'][0]==1 and row['sc_tracked'][0],row['prior_debut'][0]==1 and not row['sc_tracked'][0])
                h=c['baseline_heads'][mask.index(True)]
                traces['combined_benchmark']=dict(path=h['path'],**linear_trace(joblib.load(h['path']),row,h['features']))
                assert np.isclose(traces['combined_benchmark']['replayed_raw_rate'],o['combined_rate'],atol=1e-10)
                pool=q.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('prior_debut')==o['prior_debut'])&(pl.col('player_id')!=o['player_id']))
                ps=pool.with_columns(distance(o).alias('peer_distance')).sort('peer_distance','player_id').head(4)
                peers=[]
                fields=['row_id','player_id','player_name','age',*META,'preseason_pa','next_pa','next_value','combined_rate',
                    'precision_coverage_rate','precision_measurements_rate','combined_value','precision_measurements_value','peer_distance']
                for p in ps.iter_rows(named=True):
                    peers.append(dict(**{n:p[n] for n in fields},actual_future_relative_rate=p['actual_future_relative_rate'] if p['next_pa'] else None,
                        dated_production=dated.filter((pl.col('player_id')==p['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).to_dicts()))
                own=annual.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year']))
                wanted={(r['season'],r['league_id']) for r in own.iter_rows(named=True)}
                if o['next_pa']==0:o['actual_future_relative_rate']=None
                cases.append(dict(origin=o,selection=selected[rid],prior_reviewed_case=oldcase,
                    source_history=dated.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).to_dicts(),
                    actual_history=dated.filter((pl.col('player_id')==o['player_id'])&(pl.col('season')==o['target_year'])).to_dicts(),
                    noise_history=own.to_dicts(),references=[r for r in refs if (r['season'],r['league_id']) in wanted],
                    actual_inputs=row.select(pre['arms']['precision_measurements']).to_dicts()[0],
                    information_shares=row.select([n for n in row.columns if n.startswith('msp_') and n.endswith('_share')]).to_dicts()[0],
                    saved_traces=traces,peers=peers,exact_fallback=not o['msc_eligible']))
    q.write_parquet(out/'scored-predictions.parquet')
    prep.write('scores.json',dict(scopes=scores,intervals=intervals,replayed_heads=replays,
        actual_metadata_difference_counts=changed,player_walkthrough_status='pending',score_runner_sha256=sha256_file(Path(__file__))))
    prep.write('cases.json',dict(cases=cases,player_walkthrough_status='pending',peer_rule='Same reviewed origin-only distance and actual feature metadata; no future outcomes.'))
    for s in scores[:4]:print(s['scope'],'rate',{a:round(v['rmse'],6) for a,v in (s['participant_rate'] or {}).items()},
        'value',{a:round(v['rmse'],6) for a,v in s['contribution'].items()},flush=True)
    print('Player review pending for',len(cases),'origins; no disposition yet.',flush=True)


if __name__=='__main__':main()
