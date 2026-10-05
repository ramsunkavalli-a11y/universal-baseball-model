"""Verify matched scores and reviewed walks; preserve a negative milestone."""
from pathlib import Path
import subprocess
import sys
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
from run_hitter_shared_production import ROOT,GEN,OUT,OLD,read,save,verify


def main():
    public=ROOT/'reports/model-evidence/hitter-shared-production/report.json'
    assert not public.exists() and not (OUT/'final-review.json').exists()
    pre=read(OUT/'preflight.json');verify(pre['source_hashes'])
    source=read(OUT/'source-review.json');verify(source['hashes'])
    review=read(OUT/'review-receipt.json');verify(review['hashes'])
    qualified=read(OUT/'review-qualification.json');verify(qualified['hashes'])
    fit=read(OUT/'fit-report.json');q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    old=pl.read_parquet(OLD/'predictions.parquet').sort('row_id');assert q.select(old.columns).equals(old)
    assert q['target_year'].max()==2025
    original=q.filter(~pl.col('source_addition'));assert original.height==30506 and original['shared_pa'].equals(original['current_pa'])
    scores=read(OUT/'scores.json');checks=0
    for s in scores['scopes']:
        name=s['scope'];g=original
        if name.startswith('origin_'):g=g.filter(pl.col('origin_year')==int(name[7:]))
        elif name=='current_MLB':g=g.filter(pl.col('pa_0')>0)
        elif name=='upper_never_debut':g=g.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))
        elif name=='lower_never_debut':g=g.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))
        elif name=='no_arrival':g=g.filter(pl.col('next_pa')==0)
        elif name=='additions':g=q.filter(pl.col('source_addition'))
        elif name=='foreign':
            ids=pl.read_parquet(OUT/'features-0.parquet').filter(pl.col('evidence_foreign_source_present')>0)['row_id'].to_list();g=g.filter(pl.col('row_id').is_in(ids))
        elif name=='public':
            a=pl.read_parquet(GEN/'hitter-minor-statcast-precision/scored-predictions.parquet').filter(
                (pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())['row_id'].to_list();g=g.filter(pl.col('row_id').is_in(a))
        assert g.height==s['rows'] and g['player_id'].n_unique()==s['players']
        assert int(g['next_pa'].sum())==s['actual_PA'] and np.isclose(g['actual_relative_value'].sum(),s['actual_value'])
        for arm,r in s['scores'].items():
            mse=[];mae=[];bias=[];rate=[]
            for y in sorted(g['origin_year'].unique()):
                z=g.filter(pl.col('origin_year')==y);e=(z[arm+'_value']-z['actual_relative_value']).to_numpy()
                mse.append(np.mean(e**2));mae.append(np.mean(abs(e)));bias.append(np.mean(e))
                a=z.filter(pl.col('next_pa')>0)
                if a.height:rate.append(np.average((a[arm+'_rate']-a['actual_relative_rate']).to_numpy()**2,weights=a['next_pa'].to_numpy()))
            assert np.isclose(np.sqrt(np.mean(mse)),r['value_rmse'],atol=1e-12)
            assert np.isclose(np.mean(mae),r['value_mae'],atol=1e-12) and np.isclose(np.mean(bias),r['value_bias'],atol=1e-12)
            assert np.isclose(g[arm+'_value'].sum(),r['expected_value'],atol=1e-8)
            assert np.isclose(g[arm+'_pa'].sum(),r['expected_PA'],atol=1e-8)
            if rate:assert np.isclose(np.sqrt(np.mean(rate)),r['rate_rmse'],atol=1e-12)
            else:assert r['rate_rmse'] is None
            checks+=6
    walks=read(OUT/'player-walks.json')['cases'];assert len(walks)==10 and review['heads_replayed']==105
    for c in walks:
        o=c['forecast'];assert all(r['season']<=o['origin_year'] for r in c['raw_history'])
        t=c['linear_trace'];assert np.isclose(t['intercept']+sum(e['effect'] for e in t['feature_effects']),o['shared_rate'],atol=1e-10)
        assert np.isclose(o['shared_pa']*(o['shared_rate']/600+o['origin_replacement_rate']),o['shared_value'],atol=1e-10)
        assert not o['next_pa'] or np.isfinite(o['actual_relative_rate'])
    docs=[ROOT/'docs/hitter-shared-production-result.md',ROOT/'docs/hitter-shared-production-player-review.md']
    assert all(p.exists() for p in docs)
    subprocess.run([sys.executable,'-m','pytest','tests/test_hitter_shared_production.py','tests/test_hitter_evidence_representation.py','-q','-p','no:cacheprovider'],cwd=ROOT,check=True)
    for script in ['verify_hitter_selected_2026_freeze.py','verify_hitter_full_2026_freeze.py']:
        subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,check=True)
    paths=[Path(__file__),OUT/'preflight.json',OUT/'source-review.json',OUT/'fit-seal.json',OUT/'fit-report.json',
        OUT/'review-receipt.json',OUT/'review-qualification.json',OUT/'predictions.parquet',OUT/'scores.json',OUT/'player-walks.json',*docs]
    result=dict(status='completed_historical_comparison_not_adopted',player_walkthrough_status='complete',
        source_integrity_pass=True,profile_support_qualified=True,predictive_improvement=False,
        reasonability_qualified=True,deployment_approved=False,broad_goal_achieved=False,protected_outcomes_used=False,
        frozen_forecasts_changed=False,heads_fitted=105,heads_replayed=105,original_rows=30506,addition_rows=13,
        matched_scores_verified=checks,player_cases=10,primary=scores['scopes'][0],intervals=scores['intervals'],
        review_triggers=scores['review_triggers'],public_comparison=scores['public'],
        event_direction_interpretation=qualified['interpretation'],next_question=qualified['proposed_next_question'],
        hashes={str(p):sha256_file(p) for p in paths})
    save('final-review.json',result)
    public.parent.mkdir(parents=True,exist_ok=True)
    public.write_text(__import__('json').dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
    print(f'Completed negative comparison: {checks} score checks, ten reviewed players, unchanged freezes; no adoption.')


if __name__=='__main__':main()
