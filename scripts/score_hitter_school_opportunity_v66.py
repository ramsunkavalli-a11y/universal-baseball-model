"""Replay matched heads and prepare complete source-to-forecast review evidence."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
from score_practical_hitter_v31 import paired
from score_hitter_readiness_v49 import probability_score
from evaluate_hitter_readiness_v49 import logit_trace
import evaluate_hitter_school_opportunity_v66 as e


def main():
    pre=e.read(e.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(e.OUT/'features.parquet');old=pl.read_parquet(e.base.OUT/'features.parquet')
    q=pl.read_parquet(e.OUT/'predictions.parquet').sort('row_id');baseline=pl.read_parquet(e.VALUE/'scored-predictions.parquet').sort('row_id')
    assert len(q)==30506 and q.select(baseline.columns).equals(baseline)
    assert q['school_rate'].equals(q['baseline_rate'])
    replayed=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            prior_inputs=old.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            f=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            note=e.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json")
            for h in note['heads']:
                for arm,path,hashval,frame in [('school',h['path'],h['sha256'],te),('baseline',h['baseline_path'],h['baseline_sha256'],prior_inputs)]:
                    assert sha256_file(Path(path))==hashval
                    m=joblib.load(path);x=frame.select(pre['pa_features']).to_numpy()
                    raw=m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                    col=('school_raw_p' if h['head']=='participation' else 'school_raw_conditional_pa') if arm=='school' else ('repaired_raw_p' if h['head']=='participation' else 'repaired_raw_conditional_pa')
                    assert np.allclose(raw,f[col],rtol=0,atol=1e-10);replayed+=1
            assert np.allclose(f['school_p']*f['school_conditional_pa'],f['school_pa'],rtol=0,atol=1e-10)
            assert np.allclose(f['school_pa']*(f['baseline_rate']/600+f['origin_replacement_rate']),f['school_value'],rtol=0,atol=1e-10)
            assert f.filter(pl.col('hard_unavailable')|pl.col('reported_retired'))['school_pa'].sum()==0
    # Use actual input metadata, preserving old forecasts and corrected target units.
    extra=source.select('row_id','school_background','school_source_name','school_background_basis','school_background_evidence_year',
        pl.col('draft_college').alias('new_draft_college'),pl.col('draft_hs').alias('new_draft_hs'),pl.col('draft_jc').alias('new_draft_jc'),
        ((pl.col('draft_class_unknown')==1)&(pl.col('school_background_known')==1)).alias('recovered_school'))
    q=q.join(extra,on='row_id',validate='1:1')
    pub=q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert len(pub)==2627
    scopes=[('all',q),('public_broad',pub),('never_debut',q.filter(pl.col('prior_debut')==0)),
        ('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('current_MLB',q.filter(pl.col('pa_0')>0)),('recovered_school',q.filter(pl.col('recovered_school'))),
        ('first_year_top_picks',q.filter((pl.col('draft_known')==1)&(pl.col('draft_year')==pl.col('origin_year'))&(pl.col('pick_number')<=15)))]
    scopes += [('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in sorted(q['origin_year'].unique())]
    scopes += [('stage_'+s,q.filter(pl.col('stage')==s)) for s in sorted(q['stage'].unique())]
    results=[];intervals=[]
    with threadpool_limits(limits=2):
        for name,g in scopes:
            if not len(g):continue
            results.append(dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
                scores={a:score(g,a) for a in ['baseline','school']+(['steamer'] if name=='public_broad' else [])},
                probability={a:probability_score(g,a) for a in ['baseline','school']}))
            if name in ['all','public_broad','never_debut','upper_never_debut','recovered_school']:
                intervals.extend(dict(scope=name,**paired(g,'school','baseline',metric)) for metric in ['pa','value'])
    e.write('scores.json',results);e.write('intervals.json',intervals);q.write_parquet(e.OUT/'scored-predictions.parquet')
    selected={}
    def choose(rows,reason):
        assert len(rows);rid=rows['row_id'][0];selected.setdefault(rid,[]).append(reason)
    for pid,y in e.FIXED:choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed prefit diagnostic')
    a=q.with_columns(((pl.col('baseline_value')-pl.col('next_value'))**2-(pl.col('school_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('school_value')-pl.col('next_value')).alias('error'))
    for why,g in [('largest delivered gain',a.sort('gain',descending=True)),('largest delivered harm',a.sort('gain')),
                  ('major false high',a.sort('error',descending=True)),('major false low',a.sort('error')),
                  ('ordinary active',a.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:choose(g,why)
    history=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet');profiles=pl.read_parquet(e.OUT/'profile-support.parquet')
    cached=e.read(e.SCHOOL/'source-cases.json');records={r['row_id']:r for r in cached['cases']};cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=q.filter(pl.col('row_id')==rid).row(0,named=True);te=source.filter(pl.col('row_id')==rid);prior_input=old.filter(pl.col('row_id')==rid)
            note=e.read(e.OUT/f"fit-{o['origin_year']}-{o['outer_fold']}.json");heads={};probes={}
            for h in note['heads']:
                head=h['head'];heads[head]={}
                for arm,path,frame in [('school',h['path'],te),('baseline',h['baseline_path'],prior_input)]:
                    m=joblib.load(path);x=frame.select(pre['pa_features']).to_numpy()[0]
                    heads[head][arm]=logit_trace(m,x,pre['pa_features']) if head=='participation' else trace(m,x,pre['pa_features'])
                m=joblib.load(h['path']);x=prior_input.select(pre['pa_features']).to_numpy()
                probes[head]=float(m.predict_proba(x)[0,1] if head=='participation' else m.predict(x)[0])
            old_flags={k:prior_input[k][0] for k in e.REPLACEMENTS};new_flags={k:te[k][0] for k in e.REPLACEMENTS}
            # Preserve actual fitted source metadata rather than old descriptive values.
            actual={n:te[n][0] for n in pre['pa_features']}
            actual.update({n:te[n][0] for n in ['draft_year','pick_number','draft_school_class','school_source_name','school_background','school_background_basis','school_background_evidence_year']})
            peers=q.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut'])&(pl.col('player_id')!=o['player_id'])).with_columns(
                (((pl.col('age')-o['age'])/3)**2+((pl.col('minor_pa_0')-o['minor_pa_0'])/250)**2+4*(pl.col('draft_rank')-o['draft_rank'])**2).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=o,selection=reasons,old_flags=old_flags,new_flags=new_flags,actual_inputs=actual,
                source_history=history.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).sort('season','bucket').to_dicts(),
                actual_history=history.filter((pl.col('player_id')==o['player_id'])&(pl.col('season')==o['target_year'])&(pl.col('bucket')=='MLB')).to_dicts(),
                training_profiles=profiles.filter(pl.col('row_id')==rid).to_dicts(),saved_traces=heads,
                candidate_fit_with_old_flags=probes,probe_interpretation='Fixed-fit input reversion, not a causal effect or another validated forecast. Own flags may be unchanged while training flags change.',
                peers=peers.select('player_id','player_name','age','minor_pa_0','draft_rank','baseline_p','school_p','baseline_conditional_pa','school_conditional_pa','baseline_pa','school_pa','baseline_value','school_value','next_pa','next_value','school_background').to_dicts(),
                earlier_source_review=records.get(rid)))
    e.write('cases.json',cases)
    e.write('verification.json',dict(replayed_heads=replayed,expected_candidate_heads=70,expected_baseline_heads=70,
        unchanged_hitting=True,unchanged_evaluation_and_old_forecasts=True,PA_product_verified=True,corrected_common_value_verified=True,
        player_walkthrough_status='pending',cases=len(cases),protected_outcomes_used=False,frozen_forecast_changed=False,
        conditional_PA_clips=int(((q['school_raw_conditional_pa']<1)|(q['school_raw_conditional_pa']>800)).sum())))
    for r in results[:8]:print(r['scope'],{a:(round(s['pa_rmse'],3),round(s['pa_mae'],3),round(s['value_rmse'],6),round(s['pa_total'])) for a,s in r['scores'].items()},flush=True)
    print('Actual saved-fit case evidence prepared; review required before disposition.',flush=True)


if __name__=='__main__':main()
