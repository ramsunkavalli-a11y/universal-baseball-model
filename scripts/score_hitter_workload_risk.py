"""Replays, proper risk scores and actual player evidence for locked test."""
from pathlib import Path
import json
import joblib
import numpy as np
import polars as pl
from scipy.stats import betabinom, binom
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_workload_risk import mixture_pmf, distribution_terms, fit_concentration
from universal_baseball.storage import sha256_file
from universal_baseball.histogram_prediction_trace import trace
from evaluate_hitter_readiness_v49 import logit_trace
from fit_practical_hitter_v31 import weights
import fit_hitter_workload_risk as fit

ROOT,OUT=fit.ROOT,fit.OUT
FIXED=[(701762,2024),(694671,2023),(624413,2018),(592450,2016),(592450,2024),(680574,2024),(474832,2023),(677551,2023)]


def equal_year(g,col):return float(g.group_by('target_year').agg(pl.col(col).mean())[col].mean())


def paired(g,reference,metric):
    d=(g['risk_'+metric]-g[reference+'_'+metric]).to_numpy()
    years=g['target_year'].to_numpy();players=g['player_id'].to_numpy()
    uy,yi=np.unique(years,return_inverse=True);up,pi=np.unique(players,return_inverse=True)
    den=np.zeros((len(up),len(uy)));num=den.copy()
    np.add.at(den,(pi,yi),1);np.add.at(num,(pi,yi),d)
    rng=np.random.default_rng(77);draws=[]
    for _ in range(1000):
        w=np.bincount(rng.integers(0,len(up),len(up)),minlength=len(up));a=w@den
        if (a>0).all():draws.append(float(np.mean((w@num)/a)))
    assert len(draws)>950
    return dict(reference=reference,metric=metric,estimate=float(np.mean(num.sum(axis=0)/den.sum(axis=0))),
        lower=float(np.quantile(draws,.025)),upper=float(np.quantile(draws,.975)),replicates=len(draws),
        interpretation='Nominal player-clustered development interval, equal represented target years')


def main():
    assert not (OUT/'scores.json').exists(),'Preserve the fixed scoring result'
    pre=fit.read(OUT/'preflight.json');report=fit.read(OUT/'fit-report.json')
    for paths in [pre['input_hashes'],fit.read(OUT/'fit-seal.json')]:
        for p,h in paths.items():assert sha256_file(Path(p))==h,p
    assert sha256_file(OUT/'predictions.parquet')==report['output_sha256']
    f=pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet')
    q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    anchor=pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v68/scored-predictions.parquet').sort('row_id')
    assert q.select(anchor.columns).equals(anchor)
    replayed=set();concentrations=[]
    with threadpool_limits(limits=2):
        for note in report['cells']:
            for h in note['nested_heads']:
                assert sha256_file(Path(h['model_path']))==h['model_sha256']
                assert sha256_file(Path(h['prediction_path']))==h['prediction_sha256']
                if h['model_path'] in replayed:continue
                m=joblib.load(h['model_path']);val=f.filter(pl.col('row_id').is_in(h['validation_row_ids'])).sort('row_id')
                saved=pl.read_parquet(h['prediction_path']).sort('row_id')
                assert val['row_id'].equals(saved['row_id'])
                assert np.allclose(m.predict(val.select(pre['features']).to_numpy()),saved['raw_conditional_pa'],atol=1e-10,rtol=0)
                replayed.add(h['model_path'])
            c=pl.read_parquet(note['calibration_path']);assert sha256_file(Path(note['calibration_path']))==note['calibration_sha256']
            fresh=fit_concentration(c['next_pa'].to_numpy(),c['conditional_pa'].to_numpy(),weights(c))
            assert fresh==note['concentration'];concentrations.append(dict(year=note['year'],fold=note['fold'],**fresh))
            g=q.filter((pl.col('origin_year')==note['year'])&(pl.col('outer_fold')==note['fold']))
            for arm,k in [('risk',fresh['concentration']),('binomial',None)]:
                pmf=mixture_pmf(g['preseason_p'].to_numpy(),g['preseason_conditional_pa'].to_numpy(),k)
                terms=distribution_terms(pmf,g['next_pa'].to_numpy())
                for key,v in terms.items():assert np.allclose(v,g[arm+'_'+key],atol=1e-10,rtol=0),key
    forest=pl.read_parquet(ROOT/'reports/generated/practical-hitter-joint-forest-v43/predictions.parquet').sort('row_id')
    assert q['row_id'].equals(forest['row_id']) and q['next_pa'].equals(forest['next_pa'])
    q=q.with_columns(*[forest['joint_pa_q'+str(j)].alias('forest_q'+str(j)) for j in [10,50,90]],
        forest['joint_p_400'].alias('forest_p400'),forest['joint_p_active'].alias('forest_pactive'))
    actual=q['next_pa'].to_numpy();quant=q.select('forest_q10','forest_q50','forest_q90').to_numpy();r=actual[:,None]-quant
    q=q.with_columns(pl.Series('forest_pinball',np.maximum(r*np.array([.1,.5,.9]),r*(np.array([.1,.5,.9])-1)).mean(axis=1)),
        pl.Series('forest_interval_score',quant[:,2]-quant[:,0]+10*np.maximum(quant[:,0]-actual,0)+10*np.maximum(actual-quant[:,2],0)),
        pl.Series('forest_coverage',(actual>=quant[:,0])&(actual<=quant[:,2])),pl.Series('forest_width',quant[:,2]-quant[:,0]))
    for arm in ['risk','binomial','forest']:
        p=q[arm+'_p400'].to_numpy();a=(actual>=400).astype(float);clipped=np.clip(p,1e-12,1-1e-12)
        q=q.with_columns(pl.Series(arm+'_brier400',(p-a)**2),pl.Series(arm+'_logloss400',-a*np.log(clipped)-(1-a)*np.log1p(-clipped)))
    profiles=pl.read_parquet(OUT/'profile-support.parquet').filter(pl.col('scope')=='outer').select('row_id','profile_people')
    q=q.join(profiles,on='row_id',validate='1:1')
    public=(pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null()
    assert q.filter(public).height==2627
    scopes=[('all',q),('public',q.filter(public)),('current_MLB',q.filter(pl.col('pa_0')>0)),
        ('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('absent_prior_debut',q.filter((pl.col('prior_debut')==1)&(pl.col('pa_0')==0))),
        ('thin_new_draftee',q.filter((pl.col('draft_known')==1)&(pl.col('draft_year')==pl.col('origin_year'))&
            (pl.col('minor_pa_0')+pl.col('minor_pa_1')+pl.col('minor_pa_2')+pl.col('pa_0')+pl.col('pa_1')+pl.col('pa_2')<150))),
        ('active_outcomes_diagnostic',q.filter(pl.col('next_pa')>0)),
        ('no_active_profile',q.filter(pl.col('profile_people')==0)),('supported20_diagnostic',q.filter(pl.col('profile_people')>=20))]
    scopes.extend(('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique()))
    scopes.extend(('probability_'+str(k),q.filter((pl.col('preseason_p')>=k/10)&(pl.col('preseason_p')<(k+1)/10))) for k in range(10))
    summaries=[];intervals=[]
    with threadpool_limits(limits=2):
        for name,g in scopes:
            if not len(g):continue
            arms={arm:{metric:equal_year(g,arm+'_'+metric) for metric in ['pinball','interval_score','coverage','width','brier400','logloss400']+(['crps'] if arm!='forest' else [])} for arm in ['risk','binomial','forest']}
            summaries.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),scores=arms,
                expected_pa=float(g['preseason_pa'].sum()),actual_pa=int(g['next_pa'].sum()),
                expected_value=float(g['preseason_value'].sum()),actual_value=float(g['next_value'].sum()),
                expected_appearances=float(g['preseason_p'].sum()),actual_appearances=int((g['next_pa']>0).sum()),
                expected400={arm:float(g[arm+'_p400'].sum()) for arm in arms},actual400=int((g['next_pa']>=400).sum())))
            if name in ['all','public','current_MLB','upper_never_debut','lower_never_debut','absent_prior_debut']:
                intervals.extend(dict(scope=name,**paired(g,arm,'pinball')) for arm in ['binomial','forest'])
    fit.write('scores.json',summaries);fit.write('intervals.json',intervals);fit.write('concentrations.json',concentrations)
    q.write_parquet(OUT/'scored-predictions.parquet')
    chosen={}
    def choose(g,why):
        assert len(g);chosen.setdefault(g['row_id'][0],[]).append(why)
    for pid,y in FIXED:choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed before fit')
    for arm in ['binomial','forest']:
        a=q.with_columns((pl.col(arm+'_pinball')-pl.col('risk_pinball')).alias('gain'))
        choose(a.sort('gain',descending=True),'largest pinball gain versus '+arm)
        choose(a.sort('gain'),'largest pinball harm versus '+arm)
    a=q.with_columns((pl.col('preseason_pa')-pl.col('next_pa')).alias('error'))
    choose(a.sort('error',descending=True),'major false high mean');choose(a.sort('error'),'major false low mean')
    choose(a.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()),'ordinary active mean')
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet');cases=[];head_replays=0
    current=ROOT/'reports/generated/hitter-preseason-readiness-v68'
    with threadpool_limits(limits=2):
        for rid,selection in chosen.items():
            r=q.filter(pl.col('row_id')==rid).row(0,named=True);te=f.filter(pl.col('row_id')==rid);y,k=r['origin_year'],r['outer_fold']
            note=fit.read(OUT/f'fit-{y}-{k}.json');p,c=r['preseason_p'],r['preseason_conditional_pa'];kap=note['concentration']['concentration']
            pmf=mixture_pmf(np.array([p]),np.array([c]),kap)[0]
            # Independent scalar inverse-CDF checks, not the grid argmax implementation.
            independent=[]
            for alpha in [.1,.5,.9]:
                if alpha<=1-p:answer=0
                elif c in [1,800]:answer=int(c)
                else:
                    t=(alpha-(1-p))/p;mu=(c-1)/799;answer=int(1+betabinom.ppf(t,799,mu*kap,(1-mu)*kap))
                independent.append(answer)
            assert independent==[r['risk_q10'],r['risk_q50'],r['risk_q90']]
            saved={}
            for h in fit.read(current/f'fit-{y}-{k}.json')['heads']:
                assert sha256_file(Path(h['path']))==h['sha256'];m=joblib.load(h['path']);x=te.select(pre['features']).to_numpy()
                if h['head']=='participation':
                    assert np.isclose(m.predict_proba(x)[0,1],r['preseason_raw_p'],atol=1e-10)
                    saved[h['head']]=logit_trace(m,x[0],pre['features'])
                else:
                    assert np.isclose(m.predict(x)[0],r['preseason_raw_conditional_pa'],atol=1e-10)
                    saved[h['head']]=trace(m,x[0],pre['features'])
                head_replays+=1
            peers=q.filter((pl.col('origin_year')==y)&(pl.col('prior_debut')==r['prior_debut'])&
                (pl.col('stage')==r['stage'])&(pl.col('player_id')!=r['player_id'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+
                 ((pl.col('pa_0')-r['pa_0'])/250)**2+2*(pl.col('new_scout_rank_score_0')-r['new_scout_rank_score_0'])**2+
                 (pl.col('source_position')!=r['source_position']).cast(pl.Float64)).alias('distance')).sort('distance','player_id').head(4)
            case=dict(origin=r,selection=selection,information_date=fit.read(current/f'fit-{y}-{k}.json')['information_date'],
                source_history=counts.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                actual_inputs=te.select(pre['features']).row(0,named=True),saved_point_paths=saved,
                dispersion_fit=note['concentration'],calibration_path=note['calibration_path'],calibration_sha256=note['calibration_sha256'],
                positive_law=dict(n=799,beta_a=(c-1)/799*kap,beta_b=(1-(c-1)/799)*kap),
                probability_mass=pmf.tolist(),independent_quantiles=independent,
                positive_variance=(c-1)/799*(1-(c-1)/799)*799*(799+kap)/(1+kap),
                profile_support=profiles.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.select('player_id','player_name','age','source_position','minor_pa_0','pa_0','new_scout_rank_score_0',
                    'preseason_p','preseason_conditional_pa','preseason_pa','risk_q10','risk_q50','risk_q90','next_pa','distance').to_dicts(),
                peer_limit='Origin-known age, broad stage, listed position, workload and rank; not matched injury, rights or full batting performance')
            cases.append(case)
    fit.write('cases.json',cases)
    fit.write('verification.json',dict(nested_heads_replayed=len(replayed),nested_contexts=95,concentrations_replayed=35,
        all_current_columns_exact=True,all_distribution_cells_replayed=35,case_point_heads_replayed=head_replays,
        independent_case_quantiles=len(cases)*3,cases=len(cases),player_walkthrough_status='pending',
        protected_outcomes_used=False,frozen_forecast_changed=False,distribution_is_workload_only=True,
        source_hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'preflight.json',OUT/'fit-seal.json',OUT/'fit-report.json',
            OUT/'predictions.parquet',OUT/'scored-predictions.parquet',OUT/'scores.json',OUT/'intervals.json',OUT/'cases.json']}))
    for s in summaries[:10]:print(s['scope'],{a:tuple(round(v[m],4) for m in ['pinball','coverage','brier400']) for a,v in s['scores'].items()},flush=True)
    for c in cases:
        r=c['origin'];print(r['player_name'],r['origin_year'],'PA',round(r['preseason_pa'],2),'range',c['independent_quantiles'],'actual',r['next_pa'],flush=True)
    print('Results provisional: actual player interpretation required before disposition.',flush=True)


if __name__=='__main__':main()
