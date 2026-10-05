"""Check complete human walks and independent scores; append, never overwrite."""
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
import polars as pl

from run_foreign_count_calibration import ROOT, OUT, read, save, verify
from universal_baseball.storage import sha256_file


def scope(q,name):
    orig=q.filter(~pl.col('source_addition'))
    if name=='original_all': return orig
    if name=='additions': return q.filter(pl.col('source_addition'))
    if name=='original_foreign_sources': return orig.filter(pl.col('source_present'))
    if name=='original_route_eligible': return orig.filter(pl.col('route_eligible'))
    if name=='original_fresh_newcomers': return orig.filter(pl.col('route_eligible')&(pl.col('prior_debut')==0))
    if name=='original_fresh_returners': return orig.filter(pl.col('route_eligible')&(pl.col('prior_debut')>0))
    if name=='original_route_nonarrivals': return orig.filter(pl.col('route_eligible')&(pl.col('next_pa')==0))
    if name in ['original_upper_never','original_lower_never']:
        return orig.filter((pl.col('prior_debut')==0)&(pl.col('stage')==('Upper minors' if 'upper' in name else 'Lower minors')))
    if name.startswith('origin_') and name.endswith('_route'):
        return orig.filter(pl.col('route_eligible')&(pl.col('origin_year')==int(name.split('_')[1])))
    raise ValueError('Unknown locked score population')


def close(a,b):
    if a is None or b is None:
        if a is not b: raise ValueError('Missing-score disagreement')
    elif not np.isclose(a,b,atol=1e-10,rtol=0):
        raise ValueError(f'Independent score disagreement: {a}, {b}')


def main():
    if (OUT/'final-review.json').exists(): raise ValueError('Preserve final review')
    pre=read(OUT/'preflight.json'); scores=read(OUT/'scores.json')
    verify(pre['source_hashes']); verify(scores['hashes']); verify(read(OUT/'fit-report.json')['hashes'])
    verify(read(OUT/'calculation-review.json')['hashes'])
    walks=read(OUT/'player-walks.json')['cases']
    docs=[ROOT/'docs/hitter-foreign-count-calibration-result.md',ROOT/'docs/hitter-foreign-count-calibration-player-review.md']
    prose=docs[1].read_text(encoding='utf8')
    if len(walks)!=18 or 'candidate not approved' not in prose:
        raise ValueError('Incomplete required human review')
    for w in walks:
        if str(w['trace']['forecast']['player_id']) not in prose or len(w['peers'])!=3:
            raise ValueError('Missing named walk or origin-selected peers')
    q=pl.read_parquet(OUT/'predictions.parquet'); checks=0; sensitivity=[]
    for s in scores['scopes']:
        g=scope(q,s['scope']); years=sorted(g['origin_year'].unique())
        for arm,expected in s['metrics'].items():
            yearly=[]; rates=[]
            for y in years:
                z=g.filter(pl.col('origin_year')==y); v=z[arm+'_value'].to_numpy()-z['actual_relative_value'].to_numpy()
                yearly.append((np.mean(v*v),np.mean(abs(v)),np.mean(v)))
                active=z.filter(pl.col('next_pa')>0)
                if len(active):
                    pa=active['next_pa'].to_numpy(); d=(active[arm+'_rate']-active['actual_relative_rate']).to_numpy()
                    rates.append(float(np.sum(pa*d*d)/sum(pa)))
            derived=dict(rows=len(g),people=g['player_id'].n_unique(),active_rows=g.filter(pl.col('next_pa')>0).height,
                predicted_PA=g['fixed_pa'].sum(),actual_PA=g['next_pa'].sum(),expected_contribution=g[arm+'_value'].sum(),actual_contribution=g['actual_relative_value'].sum(),
                value_rmse=float(np.sqrt(np.mean([v[0] for v in yearly]))),value_mae=float(np.mean([v[1] for v in yearly])),value_bias=float(np.mean([v[2] for v in yearly])),
                rate_rmse=float(np.sqrt(np.mean(rates))) if rates else None)
            for k,v in derived.items(): close(v,expected[k]); checks+=1
        active=g.filter((pl.col('next_pa')>0)&pl.col('component_supported'))
        for arm in ['borrowed','count']:
            want=s['categorical'][arm]
            if not len(active):
                if want['rows']!=0: raise ValueError('Missing categorical rows')
                continue
            yearly=[]
            for y in sorted(active['origin_year'].unique()):
                z=active.filter(pl.col('origin_year')==y)
                p=np.array(z[arm+'_probability'].to_list()); c=np.array(z['actual_events'].to_list()); n=c.sum()
                ll=-float(np.sum(c*np.log(p))/n); brier=0.
                for j in range(8):
                    one=np.zeros(8); one[j]=1
                    brier+=float(np.sum(c[:,j]*np.sum((p-one)**2,axis=1))/n)
                yearly.append((ll,brier))
            close(np.mean([v[0] for v in yearly]),want['logloss']); close(np.mean([v[1] for v in yearly]),want['one_hot_brier']); checks+=2
        if s['scope'] in ['original_route_eligible','additions']:
            active=g.filter(pl.col('next_pa')>0); n=active['next_pa'].to_numpy()
            sensitivity.append(dict(scope=s['scope'],post_score_descriptive_only=True,pooled_actual_PA_RMSE={a:float(np.sqrt(n@((active[a+'_rate']-active['actual_relative_rate']).to_numpy()**2)/sum(n))) for a in ['baseline','borrowed','candidate']}))
    tests=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider','tests/test_foreign_count_calibration.py','tests/test_foreign_count_review.py'],cwd=ROOT,capture_output=True,text=True)
    if tests.returncode: raise ValueError(tests.stdout+tests.stderr)
    freezes=[]
    for script in ['verify_hitter_selected_2026_freeze.py','verify_hitter_full_2026_freeze.py']:
        r=subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,capture_output=True,text=True)
        if r.returncode: raise ValueError(r.stdout+r.stderr)
        freezes.append(dict(script=script,returncode=r.returncode,output=json.loads(r.stdout),
            qualifier='Verifier describes original pre-result package, not current completion status of the separate 2026 evaluation.'))
    paths=[*docs,Path(__file__),ROOT/'tests/test_foreign_count_review.py',OUT/'calculation-review.json',OUT/'player-walks.json',OUT/'scores.json']
    receipt=dict(player_walkthrough_status='complete',cases=18,origin_selected_peer_traces=54,
        calibration_cells_verified=35,independent_metric_checks=checks,tests=tests.stdout,
        predictive_gain_established=False,baseball_reasonability_pass=False,
        disposition='retain_as_research_do_not_deploy',deployment_approved=False,
        no_new_fits_or_scores_after_review=True,target_year_maximum=2025,
        frozen_2026_forecasts_changed=False,freeze_checks=freezes,sensitivity=sensitivity,
        one_person_bootstrap_not_population_evidence=True,
        next_boundary='Inventory existing historical overseas opportunity/source candidates before any new fit.',
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths})
    save('final-review.json',receipt)
    public=ROOT/'reports/model-evidence/foreign-count-calibration'
    if public.exists(): raise ValueError('Preserve public receipt')
    public.mkdir()
    (public/'report.json').write_text(json.dumps(dict(**receipt,scopes=scores['scopes'],matched_public=scores['matched_public'],
        original_forecasts=30506,separate_additions=13,route_eligible=126,original_active_route_players=5,added_active_route_players=6),indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(dict(disposition=receipt['disposition'],player_walkthrough_status='complete',cases=18,independent_metric_checks=checks,tests=tests.stdout,freezes_unchanged=True)),flush=True)


if __name__=='__main__': main()
