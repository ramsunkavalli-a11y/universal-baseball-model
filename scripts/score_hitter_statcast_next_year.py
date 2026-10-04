"""Matched scores and mandatory player traces; no final disposition here."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from universal_baseball.histogram_prediction_trace import trace
from prepare_practical_hitter_v33 import safe_matrix
import prepare_hitter_statcast_next_year as prep


def losses(g,arm,kind):
    if kind=='rate':
        g=g.filter(pl.col('next_pa')>0); actual=g['actual_future_relative_rate'].to_numpy(); pred=g[arm+'_rate'].to_numpy()
        weight=g['next_pa'].to_numpy().astype(float)
    else:
        actual=g['next_value'].to_numpy(); pred=g[arm+'_value'].to_numpy();weight=np.ones(len(g))
    years=g['origin_year'].to_numpy(); denominator=np.zeros(len(g))
    for y in np.unique(years):denominator[years==y]=weight[years==y].sum()
    weight=weight/denominator;weight/=weight.sum();err=pred-actual
    return dict(mse=float(np.sum(weight*err**2)),rmse=float(np.sqrt(np.sum(weight*err**2))),
        mae=float(np.sum(weight*np.abs(err))),bias=float(np.sum(weight*err)),rows=len(g),people=g['player_id'].n_unique())


def interval(g,candidate,control,kind):
    if kind=='rate':
        g=g.filter(pl.col('next_pa')>0); actual=g['actual_future_relative_rate'].to_numpy()
        w=g['next_pa'].to_numpy().astype(float); suffix='_rate'
    else:actual=g['next_value'].to_numpy();w=np.ones(len(g));suffix='_value'
    diff=(g[candidate+suffix].to_numpy()-actual)**2-(g[control+suffix].to_numpy()-actual)**2
    people,pindex=np.unique(g['player_id'].to_numpy(),return_inverse=True)
    years,yindex=np.unique(g['origin_year'].to_numpy(),return_inverse=True)
    num=np.zeros((len(people),len(years)));den=np.zeros_like(num)
    np.add.at(num,(pindex,yindex),w*diff);np.add.at(den,(pindex,yindex),w)
    rng=np.random.default_rng(724); samples=[]
    for _ in range(2000):
        idx=rng.integers(0,len(people),len(people)); n=num[idx].sum(axis=0);d=den[idx].sum(axis=0)
        assert (d>0).all();samples.append(float(np.mean(n/d)))
    return dict(candidate=candidate,control=control,kind=kind,delta_mse=float(np.mean(num.sum(axis=0)/den.sum(axis=0))),
        nominal_95_percent=np.quantile(samples,[.025,.975]).tolist(),resamples=2000,player_clustered=True,multiplicity_adjusted=False)


def main():
    out=prep.OUT; assert not (out/'scores.json').exists(),'Preserve completed scores'
    pre=prep.read(out/'preflight.json'); fit=prep.read(out/'fit-report.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    assert sha256_file(out/'predictions.parquet')==fit['predictions_sha256']
    f=pl.read_parquet(out/'features.parquet'); current=pl.read_parquet(pre['current_anchor']).sort('row_id')
    q=pl.read_parquet(out/'predictions.parquet').sort('row_id')
    assert q.select(current.columns).equals(current)
    q=q.join(f.select('row_id',pl.col('next_batting_rate').alias('actual_future_relative_rate')),on='row_id',validate='1:1')
    replayed=0
    with threadpool_limits(limits=2):
        for cell in fit['cells']:
            ids=next(c['test_row_ids'] for c in pre['cells'] if (c['year'],c['fold'])==(cell['year'],cell['fold']))
            test=f.filter(pl.col('row_id').is_in(ids)).sort('row_id'); got=q.filter(pl.col('row_id').is_in(ids)).sort('row_id')
            for h in cell['heads']:
                assert sha256_file(Path(h['path']))==h['sha256']; model=joblib.load(h['path'])
                raw=model.predict(safe_matrix(test,h['features']))
                assert np.allclose(raw,got[h['arm']+'_raw_rate'],atol=1e-12,rtol=0);replayed+=1
    public=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert len(public)==2627
    groups=[('all',q),('tracked',q.filter(pl.col('sc_tracked'))),('untracked',q.filter(~pl.col('sc_tracked'))),
        ('current_MLB',q.filter(pl.col('pa_0')>0)),('tracked_with_recent_minors',q.filter(pl.col('sc_tracked')&(pl.col('minor_pa_0')>0))),
        ('never_debut',q.filter(pl.col('prior_debut')==0)),('public_broad',public),
        ('tracked_under50',q.filter(pl.col('sc_own_ev_n').is_between(1,49))),('tracked_50to199',q.filter(pl.col('sc_own_ev_n').is_between(50,199))),
        ('tracked_200plus',q.filter(pl.col('sc_own_ev_n')>=200)),('early_origins',q.filter(pl.col('origin_year')<=2018)),
        ('modern_origins',q.filter(pl.col('origin_year')>=2021))]
    groups += [(f'origin_{y}',q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    groups += [(f'tracked_origin_{y}',q.filter((pl.col('origin_year')==y)&pl.col('sc_tracked'))) for y in sorted(q['origin_year'].unique())]
    arms=['preseason',*pre['arms']]; scores=[]
    for name,g in groups:
        if not len(g):continue
        scores.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),actual_value=float(g['next_value'].sum()),
            actual_pa=int(g['next_pa'].sum()),predicted_pa=float(g['preseason_pa'].sum()),
            contribution={arm:dict(**losses(g,arm,'value'),predicted_total=float(g[arm+'_value'].sum())) for arm in arms+(['steamer'] if name=='public_broad' else [])},
            participant_rate={arm:losses(g,arm,'rate') for arm in arms} if g.filter(pl.col('next_pa')>0).height else None))
    intervals=[]
    with threadpool_limits(limits=2):
        for candidate in ['ridge_measurements','hist_measurements']:
            for control in ['preseason',candidate.replace('measurements','coverage')]:
                intervals.append(interval(q.filter(pl.col('sc_tracked')),candidate,control,'rate'))
                intervals.append(interval(q,candidate,control,'value'))
    selected={}
    def select(g,why):
        assert len(g);rid=g['row_id'][0];selected.setdefault(rid,[]).append(why)
    fixed=prep.read(prep.source.OUT/'final-cases.json')
    fixed_lut={c['origin']['row_id']:c for c in fixed['cases']}
    for rid in fixed_lut:select(q.filter(pl.col('row_id')==rid),'fixed before fit')
    for arm in ['ridge_measurements','hist_measurements']:
        errors=q.with_columns(((pl.col('preseason_value')-pl.col('next_value'))**2-(pl.col(arm+'_value')-pl.col('next_value'))**2).alias('gain'),
            (pl.col(arm+'_value')-pl.col('next_value')).alias('error'))
        for frame,reason in [(errors.sort('gain','row_id',descending=[True,False]),'largest gain'),
            (errors.sort('gain','row_id'),'largest harm'),(errors.sort('error','row_id',descending=[True,False]),'false high'),
            (errors.sort('error','row_id'),'false low'),
            (errors.filter(pl.col('next_pa').is_between(200,600)).with_columns(pl.col('error').abs().alias('absolute_error')).sort('absolute_error','row_id'),'ordinary active')]:
            select(frame,arm+' '+reason)
    dated=pl.read_parquet(prep.ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    annual=pl.read_parquet(prep.source.OUT/'annual-launch-features.parquet'); profile=pl.read_parquet(out/'tracked-profile-support.parquet'); cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            row=q.filter(pl.col('row_id')==rid).row(0,named=True); test=f.filter(pl.col('row_id')==rid)
            cell=next(c for c in fit['cells'] if (c['year'],c['fold'])==(row['origin_year'],row['outer_fold']))
            traces={}
            for h in cell['heads']:
                model=joblib.load(h['path']); x=safe_matrix(test,h['features'])[0]
                if h['arm'].startswith('ridge'):
                    terms=x*model.coef_; raw=float(model.intercept_+terms.sum())
                    traces[h['arm']]=dict(intercept=float(model.intercept_),sum_terms=float(terms.sum()),raw_rate=raw,
                        all_terms=[dict(feature=n,input=float(v),coefficient=float(c),signed_term=float(t)) for n,v,c,t in zip(h['features'],x,model.coef_,terms)],
                        tracked_values_sum=float(sum(t for n,t in zip(h['features'],terms) if n in pre['measurement_features'])),
                        coverage_sum=float(sum(t for n,t in zip(h['features'],terms) if n in pre['control_features'])))
                else:traces[h['arm']]=trace(model,x,h['features'])
                assert np.isclose(float(model.predict(x.reshape(1,-1))[0]),row[h['arm']+'_raw_rate'],atol=1e-10)
            if rid in fixed_lut:
                peers=q.filter(pl.col('row_id').is_in([p['row_id'] for p in fixed_lut[rid]['peers']]))
            else:
                peers=q.filter((pl.col('origin_year')==row['origin_year'])&(pl.col('stage')==row['stage'])&(pl.col('prior_debut')==row['prior_debut'])&(pl.col('player_id')!=row['player_id'])).with_columns(
                    (((pl.col('age')-row['age'])/3)**2+((pl.col('pa_0')-row['pa_0'])/250)**2+
                     ((pl.col('minor_pa_0')-row['minor_pa_0'])/250)**2+((pl.col('quality_0')-row['quality_0'])/2)**2).alias('peer_distance')).sort('peer_distance','player_id').head(4)
            cases.append(dict(origin=row,selection=reasons,actual_inputs=test.select(pre['arms']['ridge_measurements']).to_dicts()[0],
                source_history=dated.filter((pl.col('player_id')==row['player_id'])&pl.col('season').is_between(row['origin_year']-2,row['origin_year'])).to_dicts(),
                launch_history=annual.filter((pl.col('player_id')==row['player_id'])&pl.col('season').is_between(row['origin_year']-2,row['origin_year'])).to_dicts(),
                saved_traces=traces,untracked_fallback=not row['sc_tracked'],training_profile=profile.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.to_dicts(),fixed_source_case=(fixed_lut.get(rid))))
    prep.write('scores.json',dict(scopes=scores,intervals=intervals,player_walkthrough_status='pending',
        no_final_disposition=True,score_runner_sha256=sha256_file(Path(__file__)),replayed_heads=replayed))
    prep.write('cases.json',dict(cases=cases,peer_rule='Retained fixed manifest; added cases same origin/stage/debut, nearest age/MLB PA/minor PA/origin quality; no future outcomes in distance.',
        player_walkthrough_status='pending',predictions_changed_only_for_tracked=True))
    q.write_parquet(out/'scored-predictions.parquet')
    for score in scores[:3]:print(score['scope'],{a:round(s['rmse'],6) for a,s in score['contribution'].items()},flush=True)
    print('Scores provisional; required player walkthrough pending.',len(cases),'selected cases;',replayed,'saved heads replayed.')


if __name__=='__main__':main()
