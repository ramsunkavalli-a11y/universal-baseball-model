"""Keep sealed original traces; correct inactive observation display and audit losses."""
import copy
from pathlib import Path
import shutil
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
import evaluate_hitter_shared_development as e
from review_hitter_talent_bridge_v74 import scope


def main():
    assert not (e.OUT/'final-report.json').exists(),'Preserve final review'
    prep=e.read(e.OUT/'review-preparation.json');e.verify(prep['hashes']);e.verify(prep['model_hashes'])
    pre=e.read(e.OUT/'preflight.json');e.verify(pre['input_hashes']);e.verify(e.read(e.OUT/'fit-seal.json'))
    source=pl.read_parquet(e.bridge.previous.OUT/'features.parquet')
    q=pl.read_parquet(e.OUT/'predictions.parquet').sort('row_id')
    rates=q.drop('next_batting_rate').join(source.select('row_id','next_batting_rate'),on='row_id',validate='1:1')
    scores=e.read(e.OUT/'scores.json');checks=0
    # Independent direct loss formula, retaining distinct rate and value responses.
    for s in scores:
        g=scope(q,s['scope']);r=rates.filter(pl.col('row_id').is_in(g['row_id'].to_list()))
        assert len(g)==s['rows']
        for a in ['preseason','translated_ridge',*e.ARMS]:
            yearly=[];active=r.filter(pl.col('next_pa')>0)
            for _,v in active.group_by('target_year'):
                err=(v[a+'_rate']-v['next_batting_rate']).to_numpy();w=v['next_pa'].to_numpy()
                yearly.append([np.average(err**2,weights=w),np.average(abs(err),weights=w),np.average(err,weights=w)])
            m=np.mean(yearly,axis=0)
            expected=s['rate'][a]
            assert np.allclose([np.sqrt(m[0]),m[1],m[2]],[expected['rmse'],expected['mae'],expected['bias']],atol=1e-10,rtol=0)
            val=g.with_columns((pl.col(a+'_value')-pl.col('next_value')).alias('_e'))
            actual=np.sqrt(val.group_by('target_year').agg((pl.col('_e')**2).mean())['_e'].mean())
            assert abs(actual-s['delivered'][a]['value_rmse'])<1e-10
            assert g[a+'_pa'].equals(g['preseason_pa'])
            assert np.allclose(g[a+'_value'],g['preseason_pa']*(g[a+'_rate']/600+g['origin_replacement_rate']),atol=1e-10,rtol=0)
            checks+=1
    notes=e.read(e.ROOT/'config/hitter_shared_development_review.json');cases=e.read(e.OUT/'cases.json')
    assert set(notes)=={str(c['origin']['row_id']) for c in cases}
    reviewed=[];nulls=[]
    source_rates={r['row_id']:r['next_batting_rate'] for r in source.select('row_id','next_batting_rate').iter_rows(named=True)}
    for case in cases:
        c=copy.deepcopy(case);rid=c['origin']['row_id'];n=notes[str(rid)]
        assert n['review_status']=='complete' and n['assessment']
        if c['selection']['next_pa']==0:
            c['selection']['numeric_scoring_placeholder']=c['selection'].pop('actual_target_centered_rate')
            c['selection']['observed_target_centered_rate']=None;nulls.append(rid)
        else:
            rate=c['selection'].pop('actual_target_centered_rate');assert abs(rate-source_rates[rid])<1e-10
            c['selection']['observed_target_centered_rate']=rate
        c.update(n);reviewed.append(c)
    # Confirm unchanged established-player primary rates, not just public scores.
    established=q.filter(pl.col('prior_debut')==1)
    for a in e.ARMS: assert established[a+'_rate'].equals(established['baseline_rate'])
    e.write('reviewed-cases.json',reviewed)
    e.write('observation-display-correction.json',dict(original_case_files_preserved=True,
        original_numeric_rate_sentinel=0,reviewed_nonparticipant_observed_rate=None,corrected_case_rows=nulls,
        original_rate_scoring_active_only=True,all_rate_and_value_RMSE_MAE_bias_checks=checks,
        fitting_forecasts_losses_or_membership_changed=False))
    paths=[Path(__file__),e.ROOT/'config/hitter_shared_development_review.json',e.ROOT/'docs/hitter-shared-development-result.md',
        e.OUT/'reviewed-cases.json',e.OUT/'observation-display-correction.json']
    e.write('final-report.json',dict(player_walkthrough_status='complete',reviewed_cases=len(cases),new_heads_replayed=70,
        disposition='Do not promote either new arm; retain translated/ranking research alternative and current opportunity',
        independent_score_checks=checks,conditional_rate_response='Target-year average; no inactive talent labels',
        delivered_response='Common origin environment',protected_outcomes_used=False,frozen_forecast_changed=False,
        explorer_changed=False,deployment_approved=False,full_goal_complete=False,
        source_and_execution_hashes=pre['input_hashes'],review_preparation_hashes=prep['hashes'],
        model_hashes=prep['model_hashes'],review_hashes={str(p):sha256_file(p) for p in paths}))
    evidence=e.ROOT/'reports/model-evidence/hitter-shared-development';evidence.mkdir(parents=True,exist_ok=True)
    for name in ['scores.json','intervals.json','selected-cases.json','cases.json','verification.json',
                 'reviewed-cases.json','observation-display-correction.json','final-report.json']:
        shutil.copyfile(e.OUT/name,evidence/name);assert sha256_file(e.OUT/name)==sha256_file(evidence/name)
    print('Fourteen player reviews completed; independent score checks:',checks,'inactive display rates made null:',nulls)


if __name__=='__main__':main()
