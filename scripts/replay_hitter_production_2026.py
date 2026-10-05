"""Independent input scaling/linear sums, saved heads and source-player walks."""
from pathlib import Path
from types import SimpleNamespace
import json
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.practical_hitter_v30 import EVENTS
from universal_baseball.storage import sha256_file
from prepare_hitter_production_2026 import ROOT,OUT,read,write


def independent_matrix(f,names):
    columns=[]
    for name in names:
        v=f[name].to_numpy().astype(float)
        if name=='career_mlb_observed_pa':v=v/6000
        elif name.endswith('_pa'):v=v/600
        elif name=='last_stat_gap':v=v/5
        elif name.startswith('pooled_') and name.rsplit('_',1)[-1] in EVENTS:
            v=(v-EVENTS[name.rsplit('_',1)[-1]][2])/.1
        columns.append(v)
    return np.column_stack(columns)


def main():
    assert not (OUT/'independent-review.json').exists(),'Preserve replay review'
    pre=read(OUT/'preflight.json');fit=read(OUT/'fit-report.json')
    assert sha256_file(OUT/'forecast.parquet')==fit['forecast_sha256']
    forecast=pl.read_parquet(OUT/'forecast.parquet');support=pl.read_parquet(OUT/'profile-support.parquet')
    base_path=ROOT/'reports/generated/hitter-base-inputs-2025-reviewed/completed-player-walks.json'
    cases=read(base_path)['cases'];ids={c['primary']['player_id'] for c in cases}
    ids|={p['player_id'] for c in cases for p in c['exposure_peers']}
    # Source-independent extreme forecasts are additional pre-result diagnostics,
    # not false-high/low outcome selection or a basis for tuning this season.
    ids|=set(forecast.sort('hitting_wins_per_600',descending=True).head(3)['player_id'])
    ids|=set(forecast.filter(pl.col('prior_debut')==0).sort('batting_contribution',descending=True).head(3)['player_id'])
    walks=[];head_replays=[]
    with threadpool_limits(limits=2):
        for cell in pre['cells']:
            fold=cell['fold'];note=read(OUT/f'fit-{fold}.json');q=pl.read_parquet(OUT/f'forecast-{fold}.parquet').sort('row_id')
            assert sha256_file(OUT/f'forecast-{fold}.parquet')==note['forecast_sha256']
            models={};matrices={}
            for h in note['heads']:
                head=h['head'];mp=Path(h['path']);assert sha256_file(mp)==h['sha256'];m=joblib.load(mp);models[head]=m
                x=independent_matrix(q,h['features']) if head.startswith('rate') else q.select(h['features']).to_numpy()
                matrices[head]=x
                if head.startswith('rate'):
                    replay=x@np.asarray(m.coef_)+float(m.intercept_)
                    assert np.allclose(replay,m.predict(x),atol=1e-10,rtol=0)
                else:replay=m.predict_proba(x)[:,1] if head=='participation' else m.predict(x)
                assert np.allclose(replay,q['raw_'+head].to_numpy(),atol=1e-10,rtol=0),head
                head_replays.append(dict(fold=fold,head=head,forecast_rows=len(q),saved_head_verified=True,
                    independent_linear_sum=head.startswith('rate')))
            rawp=q['raw_participation'].to_numpy();override=q['reported_retired'].to_numpy()|q['hard_unavailable'].to_numpy()
            p=np.where(override,0.,rawp);cond=np.minimum(800.,np.maximum(1.,q['raw_conditional_pa'].to_numpy()))
            pa=p*cond
            never=q['prior_debut'].to_numpy()==0;tracked=q['sc_tracked'].to_numpy()
            rate=np.where(never,q['raw_rate_prospect'].to_numpy(),np.where(tracked,q['raw_rate_tracking'].to_numpy(),q['raw_rate_numeric'].to_numpy()))
            value=pa*(rate/600+570/182926)
            for name,v in [('participation_probability',p),('conditional_pa',cond),('expected_pa',pa),('hitting_wins_per_600',rate),('batting_contribution',value)]:
                assert np.allclose(v,q[name].to_numpy(),atol=1e-10,rtol=0),name
            for i,r in enumerate(q.iter_rows(named=True)):
                if r['player_id'] not in ids:continue
                rate_head='rate_prospect' if r['prior_debut']==0 else 'rate_tracking' if r['sc_tracked'] else 'rate_numeric'
                m=models[rate_head];names=pre['features'][rate_head];x=matrices[rate_head][i];terms=x*np.asarray(m.coef_)
                assert np.isclose(float(m.intercept_)+terms.sum(),r['hitting_wins_per_600'],atol=1e-10,rtol=0)
                ordered=np.argsort(-abs(terms))
                rate_terms=[dict(feature=names[j],raw_input=r[names[j]],scaled_input=float(x[j]),coefficient=float(m.coef_[j]),
                    contribution=float(terms[j])) for j in ordered]
                cls=models['participation'];proxy=SimpleNamespace(_baseline_prediction=cls._baseline_prediction,_predictors=cls._predictors,predict=cls.decision_function)
                p_trace=trace(proxy,matrices['participation'][i],pre['features']['participation'])
                z=p_trace['raw_prediction'];link=float(1/(1+np.exp(-z)))
                assert np.isclose(link,r['raw_participation'],atol=1e-10,rtol=0)
                pa_trace=trace(models['conditional_pa'],matrices['conditional_pa'][i],pre['features']['conditional_pa'])
                actual_support=support.filter(pl.col('row_id')==r['row_id'])
                base=next((w for c in cases for w in [c['primary'],*c['exposure_peers']] if w['player_id']==r['player_id']),None)
                warnings=[]
                if r['age_unknown']:warnings.append('Age unknown: fixed age-27 fallback is a source flag, not an observed age.')
                if r['translated_missing']:warnings.append('No recent supported translation exposure; prior/missing inputs, not established MLB talent.')
                if (actual_support['training_people']<20).any():warnings.append('One or more actual-head joint profiles have fewer than 20 distinct training people.')
                if (actual_support['training_people']==0).any():warnings.append('At least one refined actual-head profile is unseen in training.')
                if r['stage']=='Inactive / unknown':warnings.append('Recent inactivity does not certify retirement or a future zero outcome.')
                walks.append(dict(player_id=r['player_id'],name=r['player_name'],fold=fold,stage=r['stage'],source_walk=base,
                    actual_inputs={n:r[n] for n in names},talent_route=r['talent_route'],
                    intermediates={c:r[c] for c in ['raw_participation','participation_override','participation_probability','raw_conditional_pa',
                        'conditional_pa','expected_pa','raw_rate_numeric','raw_rate_tracking','raw_rate_prospect','hitting_wins_per_600','batting_contribution']},
                    actual_training_support=actual_support.to_dicts(),participation_logodds_trace=p_trace,participation_link=link,
                    conditional_pa_trace=pa_trace,rate_intercept=float(m.intercept_),rate_terms=rate_terms,
                    source_and_support_warnings=warnings,
                    baseball_judgment='Exact source and fitted mechanics inspected; uncertainty remains conditional hitting/MLB opportunity and sparse-profile extrapolation. '
                        'No reputation-driven forecast override, guarantee of MLB arrival or claim of future accuracy.',
                    realized_2026='Protected: not accessed before freeze',review_status='construction_walk_complete_no_outcome_validation'))
    assert {w['player_id'] for w in walks}==ids
    write(OUT/'pre-freeze-player-walks.json',dict(selection='Ten fixed source cases, their origin-selected peers, three highest rate and three highest never-debut contribution forecasts.',
        walks=walks,source_only=True,protected_outcomes_used=False))
    group=forecast.group_by('stage','talent_route').agg(pl.len().alias('players'),pl.col('expected_pa','batting_contribution').sum(),
        pl.col('participation_probability','hitting_wins_per_600').mean()).sort('stage','talent_route').to_dicts()
    write(OUT/'independent-review.json',dict(head_replays=head_replays,all_forecasts_replayed=4030,independent_linear_heads=15,
        head_replays_complete=True,output_products_replayed=True,actual_model_walks=len(walks),player_walkthrough_status='complete_for_construction',
        profile_warnings_retained=True,cohort_totals=group,expected_pa_total=float(forecast['expected_pa'].sum()),
        batting_contribution_total=float(forecast['batting_contribution'].sum()),
        minimum_hitting_rate=float(forecast['hitting_wins_per_600'].min()),maximum_hitting_rate=float(forecast['hitting_wins_per_600'].max()),
        interpretation='A fixed domestic-history candidate with explicit unsupported/new-foreign coverage; construction verified, accuracy not yet validated.',
        predictive_validation=False,universal_coverage_claim_allowed=False,candidate_frozen=False,protected_outcomes_used=False,
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'preflight.json',OUT/'fit-report.json',OUT/'forecast.parquet',
            OUT/'profile-support.parquet',base_path,ROOT/'src/universal_baseball/histogram_prediction_trace.py']},
        output_hashes={str(OUT/'pre-freeze-player-walks.json'):sha256_file(OUT/'pre-freeze-player-walks.json')}))
    print(f'All 4030 forecasts and 25 heads replayed; {len(walks)} exact fitted player walks. 2026 remains closed.',flush=True)


if __name__=='__main__':main()
