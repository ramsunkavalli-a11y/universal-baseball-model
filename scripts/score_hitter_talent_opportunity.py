"""Independent replay, matched scoring and actual case traces; no disposition."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from universal_baseball.histogram_prediction_trace import trace
from evaluate_hitter_readiness_v49 import logit_trace
from prepare_practical_hitter_v33 import safe_matrix
import fit_hitter_talent_opportunity as fit

ROOT, OUT = fit.ROOT, fit.OUT
read, write, verify = fit.read, fit.write, fit.verify
FIXED = [(701762,2024),(694671,2023),(624413,2018),(592450,2016),(592450,2024),
         (665742,2021),(680574,2024),(474832,2023),(677551,2023)]


def equal_year(g, name):
    return float(g.group_by('target_year').agg(pl.col(name).mean())[name].mean())


def paired(g, reference, metric):
    delta = (g['talent_'+metric]-g[reference+'_'+metric]).to_numpy()
    _, yi = np.unique(g['target_year'].to_numpy(), return_inverse=True)
    people, pi = np.unique(g['player_id'].to_numpy(), return_inverse=True)
    den = np.zeros((len(people), yi.max()+1)); num = den.copy()
    np.add.at(den, (pi,yi), 1); np.add.at(num, (pi,yi), delta)
    rng = np.random.default_rng(79); draws = []
    for _ in range(1000):
        w = np.bincount(rng.integers(0,len(people),len(people)), minlength=len(people))
        d = w@den
        if (d > 0).all():
            draws.append(float(np.mean((w@num)/d)))
    assert len(draws) > 950
    return dict(reference=reference, metric=metric, difference=float(np.mean(num.sum(0)/den.sum(0))),
        lower=float(np.quantile(draws,.025)), upper=float(np.quantile(draws,.975)), replicates=len(draws),
        qualification='Nominal player-clustered development interval with equal represented target years')


def main():
    assert not (OUT/'scores.json').exists(), 'Preserve original scoring'
    pre = read(OUT/'preflight.json'); verify(pre['input_hashes']); verify(read(OUT/'fit-seal.json'))
    gen = read(OUT/'generation-report.json'); verify(gen['output_hashes'])
    report = read(OUT/'fit-report.json')
    assert sha256_file(OUT/'predictions.parquet') == report['output_sha256']
    f = pl.read_parquet(fit.setup.current.OUT/'features.parquet').sort('row_id')
    q = pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    anchor = pl.read_parquet(fit.setup.current.OUT/'scored-predictions.parquet').sort('row_id')
    assert q.select(anchor.columns).equals(anchor)
    rate_replays = 0; opportunity_replays = 0; baseline_replays = 0
    with threadpool_limits(limits=2):
        for g, note in zip(pre['graphs'], gen['notes'], strict=True):
            assert g['tag'] == note['tag']; verify(note['hashes'])
            val = f.filter(pl.col('row_id').is_in(g['validation_row_ids'])).sort('row_id')
            saved = pl.read_parquet(OUT/(g['tag']+'.parquet'))
            assert val['row_id'].equals(saved['row_id'])
            tr = f.filter(pl.col('row_id').is_in(g['training_row_ids']))
            assert not set(val['player_id']) & set(tr['player_id'])
            assert not tr.filter(pl.col('outer_fold').is_in(g['excluded_folds'])).height
            if g['estimated']:
                assert (tr['target_year'] <= g['cutoff']).all() and (tr['target_year'] != 2020).all()
                model = joblib.load(OUT/(g['tag']+'.joblib'))
                assert np.allclose(model.predict(safe_matrix(val,pre['rate_features'])),
                    saved['talent_mlb_rate'], atol=1e-10, rtol=0)
                rate_replays += 1
            else:
                assert (saved['talent_known'] == 0).all() and (saved['talent_mlb_rate'] == 0).all()
        for c, note in zip(pre['cells'], report['cells'], strict=True):
            assert (c['year'],c['fold']) == (note['year'],note['fold']); verify(note['hashes'])
            y,k = c['year'],c['fold']
            expanded = f.join(pl.read_parquet(OUT/f'generated-features-{k}.parquet'),on='row_id',how='inner',validate='1:1')
            te = expanded.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            saved = q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            for h in note['heads']:
                m = joblib.load(h['path']); x = te.select(h['features']).to_numpy()
                raw = m.predict_proba(x)[:,1] if h['head'] == 'participation' else m.predict(x)
                name = h['arm']+('_raw_p' if h['head']=='participation' else '_raw_conditional_pa')
                assert np.allclose(raw,saved[name],atol=1e-10,rtol=0)
                opportunity_replays += 1
            for h in read(fit.setup.current.OUT/f'fit-{y}-{k}.json')['heads']:
                verify({h['path']:h['sha256']}); m=joblib.load(h['path']); x=te.select(pre['pa_features']).to_numpy()
                raw=m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                name='preseason_raw_p' if h['head']=='participation' else 'preseason_raw_conditional_pa'
                assert np.allclose(raw,saved[name],atol=1e-10,rtol=0);baseline_replays += 1
            for arm in ['coverage','talent']:
                expected_p = saved[arm+'_raw_p'].to_numpy().copy()
                expected_p[saved['hard_unavailable'].to_numpy() | saved['reported_retired'].to_numpy()] = 0
                cond=np.clip(saved[arm+'_raw_conditional_pa'].to_numpy(),1,800)
                assert np.array_equal(expected_p,saved[arm+'_p'])
                assert np.array_equal(cond,saved[arm+'_conditional_pa'])
                assert np.array_equal(expected_p*cond,saved[arm+'_pa'])
                assert np.allclose(expected_p*cond*(saved['baseline_rate']/600+saved['origin_replacement_rate']),
                    saved[arm+'_value'],atol=1e-10,rtol=0)
    q=q.with_columns([pl.col('preseason_'+name).alias('current_'+name) for name in ['p','conditional_pa','pa','value']])
    for arm in ['current','coverage','talent']:
        p=q[arm+'_p'].to_numpy(); pp=np.clip(p,1e-12,1-1e-12);active=(q['next_pa']>0).to_numpy().astype(float)
        q=q.with_columns(((pl.col(arm+'_pa')-pl.col('next_pa'))**2).alias(arm+'_pa_mse'),
            (pl.col(arm+'_pa')-pl.col('next_pa')).abs().alias(arm+'_pa_mae'),
            ((pl.col(arm+'_value')-pl.col('next_value'))**2).alias(arm+'_value_mse'),
            pl.Series(arm+'_brier',(p-active)**2),
            pl.Series(arm+'_logloss',-active*np.log(pp)-(1-active)*np.log1p(-pp)))
    public=(pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null()
    assert q.filter(public).height==2627
    scopes=[('all',q),('public',q.filter(public)),('current_MLB',q.filter(pl.col('pa_0')>0)),
        ('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('absent_prior_debut',q.filter((pl.col('prior_debut')==1)&(pl.col('pa_0')==0))),
        ('thin_new_draftee',q.filter((pl.col('draft_known')==1)&(pl.col('draft_year')==pl.col('origin_year'))&
            (pl.col('minor_pa_0')+pl.col('minor_pa_1')+pl.col('minor_pa_2')+pl.col('pa_0')+pl.col('pa_1')+pl.col('pa_2')<150)))]
    scopes.extend(('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique()))
    scopes.extend(('hitting_band_'+str(i),q.filter((pl.col('talent_mlb_rate')>=lo)&(pl.col('talent_mlb_rate')<hi)))
        for i,(lo,hi) in enumerate([(-100,-1),(-1,0),(0,1),(1,100)]))
    scores=[];intervals=[]
    with threadpool_limits(limits=2):
        for name,g in scopes:
            assert len(g)
            arms={arm:dict(pa_rmse=np.sqrt(equal_year(g,arm+'_pa_mse')),pa_mae=equal_year(g,arm+'_pa_mae'),
                value_rmse=np.sqrt(equal_year(g,arm+'_value_mse')),brier=equal_year(g,arm+'_brier'),logloss=equal_year(g,arm+'_logloss'),
                expected_pa=float(g[arm+'_pa'].sum()),expected_value=float(g[arm+'_value'].sum()),expected_appearances=float(g[arm+'_p'].sum()))
                for arm in ['current','coverage','talent']}
            scores.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),scores=arms,
                actual_pa=int(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),actual_appearances=int((g['next_pa']>0).sum())))
            if not name.startswith(('origin_','hitting_band_')):
                intervals.extend(dict(scope=name,**paired(g,ref,metric)) for ref in ['current','coverage'] for metric in ['pa_mse','value_mse'])
    write('scores.json',scores);write('intervals.json',intervals);q.write_parquet(OUT/'scored-predictions.parquet')
    chosen={}
    def choose(g,why):
        assert len(g);chosen.setdefault(g['row_id'][0],[]).append(why)
    for pid,y in FIXED:
        choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed before fit')
    for ref in ['current','coverage']:
        g=q.with_columns((pl.col(ref+'_pa_mse')-pl.col('talent_pa_mse')).alias('gain'))
        choose(g.sort('gain',descending=True),'largest PA squared-error gain versus '+ref)
        choose(g.sort('gain'),'largest PA squared-error harm versus '+ref)
    g=q.with_columns((pl.col('talent_pa')-pl.col('next_pa')).alias('error'))
    choose(g.sort('error',descending=True),'major false high');choose(g.sort('error'),'major false low')
    choose(g.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()),'ordinary active forecast')
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet');cases=[]
    profile_support=pl.read_parquet(OUT/'profile-support.parquet')
    with threadpool_limits(limits=2):
        for rid,why in chosen.items():
            r=q.filter(pl.col('row_id')==rid).row(0,named=True);y,k=r['origin_year'],r['outer_fold']
            extra=pl.read_parquet(OUT/f'generated-features-{k}.parquet')
            te=f.filter(pl.col('row_id')==rid).join(extra,on='row_id',validate='1:1')
            c=next(c for c in pre['cells'] if c['year']==y and c['fold']==k)
            current_note=read(fit.setup.current.OUT/f'fit-{y}-{k}.json');new_note=read(OUT/f'fit-{y}-{k}.json')
            paths={}
            for arm,notes in [('current',current_note['heads']),('coverage',[h for h in new_note['heads'] if h['arm']=='coverage']),
                              ('talent',[h for h in new_note['heads'] if h['arm']=='talent'])]:
                paths[arm]={}
                for h in notes:
                    model=joblib.load(h['path']);names=pre['pa_features'] if arm=='current' else h['features'];x=te.select(names).to_numpy()[0]
                    paths[arm][h['head']]=logit_trace(model,x,names) if h['head']=='participation' else trace(model,x,names)
            tag=f'rate-{y}-{k}';rate_model=joblib.load(OUT/(tag+'.joblib'));rx=safe_matrix(te,pre['rate_features'])[0]
            coeff=rate_model.coef_*rx
            assert np.isclose(float(rate_model.intercept_+coeff.sum()),r['talent_mlb_rate'],atol=1e-10)
            peers=q.filter((pl.col('origin_year')==y)&(pl.col('prior_debut')==r['prior_debut'])&
                (pl.col('stage')==r['stage'])&(pl.col('player_id')!=r['player_id'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+
                 ((pl.col('pa_0')-r['pa_0'])/250)**2+2*(pl.col('new_scout_rank_score_0')-r['new_scout_rank_score_0'])**2+
                 ((pl.col('talent_mlb_rate')-r['talent_mlb_rate'])/2)**2+
                 (pl.col('source_position')!=r['source_position']).cast(pl.Float64)).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=r,selection=why,information_date=c['information_date'],
                source_history=counts.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                actual_inputs=te.select(*pre['pa_features'],'talent_known','talent_mlb_rate').row(0,named=True),
                generated_rate_fit=read(OUT/(tag+'.json')),generated_rate_intercept=float(rate_model.intercept_),
                generated_rate_terms=[dict(feature=n,scaled_input=float(x),coefficient=float(b),contribution=float(v))
                    for n,x,b,v in zip(pre['rate_features'],rx,rate_model.coef_,coeff,strict=True)],
                training_profiles=profile_support.filter((pl.col('row_id')==rid)&(pl.col('held_outer_fold')==k)).to_dicts(),
                saved_opportunity_paths=paths,peers=peers.select('player_id','player_name','age','source_position','minor_pa_0','pa_0',
                    'new_scout_rank_score_0','talent_mlb_rate','current_pa','coverage_pa','talent_pa','next_pa','distance').to_dicts(),
                peer_limit='Origin-known age, stage, position, workload, rank and generated hitting; not matched medical/legal status or full talent'))
    write('cases.json',cases)
    paths=[Path(__file__),OUT/'preflight.json',OUT/'fit-seal.json',OUT/'generation-report.json',OUT/'fit-report.json',
        OUT/'predictions.parquet',OUT/'scored-predictions.parquet',OUT/'scores.json',OUT/'intervals.json',OUT/'cases.json']
    write('verification.json',dict(rate_heads_replayed=rate_replays,opportunity_heads_replayed=opportunity_replays,
        baseline_heads_replayed=baseline_replays,all_current_columns_exact=True,case_count=len(cases),
        player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False,
        source_hashes={str(p):sha256_file(p) for p in paths}))
    for s in scores[:7]:
        print(s['scope'],{a:tuple(round(v[m],4) for m in ['pa_rmse','pa_mae','value_rmse','brier']) for a,v in s['scores'].items()},flush=True)
    for c in cases:
        r=c['origin'];print(r['player_name'],r['origin_year'],round(r['talent_mlb_rate'],3),
            *[round(r[a+'_pa'],2) for a in ['current','coverage','talent']],r['next_pa'],flush=True)
    print('Scored and replayed; actual player interpretation required before disposition.',flush=True)


if __name__ == '__main__':
    main()
