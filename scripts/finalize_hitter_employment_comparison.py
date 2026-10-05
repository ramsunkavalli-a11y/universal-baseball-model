"""Independently verify the limited contrast and qualify its discovered timing gap."""
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
import polars as pl
from run_hitter_employment_comparison import ROOT,GEN,OLD,OUT,FIX,read,save,verify
from universal_baseball.storage import sha256_file


def independent_score(g,arm):
    losses=[]
    for y in sorted(g['origin_year'].unique()):
        f=g.filter(pl.col('origin_year')==y);actual=f['next_pa'].to_numpy()
        pa=f[arm+'_pa'].to_numpy();value=f[arm+'_value'].to_numpy();p=f[arm+'_p'].to_numpy()
        yes=(actual>0).astype(float);lp=np.clip(p,1e-12,1-1e-12)
        losses.append([np.mean((pa-actual)**2),np.mean(abs(pa-actual)),np.mean(pa-actual),
            np.mean((value-f['actual_relative_value'].to_numpy())**2),
            np.mean(abs(value-f['actual_relative_value'].to_numpy())),np.mean(value-f['actual_relative_value'].to_numpy()),
            np.mean((p-yes)**2),np.mean(-yes*np.log(lp)-(1-yes)*np.log1p(-lp))])
    a=np.mean(losses,axis=0)
    return dict(zip(['pa_rmse','pa_mae','pa_bias','value_rmse','value_mae','value_bias','brier','logloss'],
        [float(np.sqrt(a[0])),float(a[1]),float(a[2]),float(np.sqrt(a[3])),*map(float,a[4:])],strict=True))


def main():
    if (OUT/'final-review.json').exists():raise ValueError('Completed review; preserve it')
    receipt=read(OUT/'review-receipt.json');verify(receipt['hashes'])
    pre=read(OUT/'preflight.json');verify(pre['hashes'])
    fit=read(OUT/'fit-report.json');q=pl.read_parquet(OUT/'predictions.parquet')
    old=pl.read_parquet(OLD/'predictions.parquet')
    assert q.select(old.columns).sort('row_id').equals(old.sort('row_id'))
    assert q['corrected_job_rate'].equals(q['old_job_rate'])
    assert q.height==30519 and not q['next_pa'].is_null().any() and q['target_year'].max()==2025
    for c in fit['cells']:
        assert len(c['heads'])==2
        assert sha256_file(ROOT/c['predictions_path'])==c['predictions_sha256']
        for h in c['heads']:assert sha256_file(ROOT/h['path'])==h['sha256']
    original=q.filter(~pl.col('source_addition'));scores=read(OUT/'scores.json');checks=0
    for name,g in [('original_all',original),('additions',q.filter(pl.col('source_addition'))),
                   ('affected_original',original.filter(pl.col('employment_input_changed'))),
                   ('unaffected_original',original.filter(~pl.col('employment_input_changed')))]:
        reported=next(s for s in scores['scopes'] if s['scope']==name)
        assert reported['rows']==g.height and reported['actual_PA']==g['next_pa'].sum()
        for arm in reported['scores']:
            for n,v in independent_score(g,arm).items():
                assert np.isclose(v,reported['scores'][arm][n],atol=1e-10,rtol=0),(name,arm,n)
                checks+=1
    cases=read(OUT/'player-walks.json')['cases'];assert len(cases)==113
    selected=read(OUT/'case-selection.json')['selected']
    assert set(selected)=={str(c['origin']['row_id']) for c in cases}
    for c in cases:
        r=c['origin'];a=c['old_model_inputs'];b=c['corrected_model_inputs']
        for arm in ['old_job','corrected_job']:
            t=c['head_mechanics'][arm+'_participation'];u=c['head_mechanics'][arm+'_conditional_pa']
            p=t['linked_probability'];cond=float(np.clip(u['raw_prediction'],1,800))
            if a['status_hard_unavailable'] or a['status_retired']:p=0
            assert np.isclose(p,r[arm+'_p'],atol=1e-10)
            assert np.isclose(p*cond,r[arm+'_pa'],atol=1e-8)
            checks+=2
        assert c['input_changes']=={n:[a[n],b[n]] for n in pre['job_features'] if a[n]!=b[n]}
    # The dependency gap is counted, not hidden by the successful flag test.
    source=pl.read_parquet(OLD/'features-0.parquet',columns=['origin_year','player_id','row_id'])
    keys={f'{r["origin_year"]}:{r["player_id"]}' for r in source.to_dicts()}
    deltas=read(FIX/'employment-deltas.json')['rows']
    timing=[r for r in deltas if r['candidate_key'] in keys and r['old_employment']['latest_date']!=r['employment']['latest_date']]
    assert len(timing)==10267
    tests=[]
    for command in [[sys.executable,'-m','pytest','-q','-p','no:cacheprovider','tests/test_employment_comparison.py'],
        [sys.executable,'scripts/verify_hitter_selected_2026_freeze.py'],
        [sys.executable,'scripts/verify_hitter_full_2026_freeze.py']]:
        r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        if r.returncode:raise ValueError(r.stdout+r.stderr)
        tests.append(dict(command=command[1:],exit_code=0,output=r.stdout))
    paths=[Path(__file__),ROOT/'docs/hitter-employment-comparison-result.md',
        ROOT/'docs/hitter-employment-comparison-player-review.md',OUT/'review-receipt.json',
        OUT/'scores.json',OUT/'intervals.json',OUT/'predictions.parquet',OUT/'case-selection.json',OUT/'player-walks.json']
    result=dict(status='review_complete_limited_flags_no_promotion',player_walkthrough_status='complete',
        machine_traces=113,manual_review='All compact comparisons and detailed consequential source/head cases in linked document',
        primary_PA_improvement_demonstrated=False,source_parser_correction_retained=True,
        complete_employment_correction_tested=False,unrepaired_latest_date_rows_in_source_panel=10267,
        next_action='Rebuild both date-derived employment inputs; finish the same matched contrast with no tuning',
        new_heads=70,baseline_replayed=70,corrected_replayed=70,independent_score_and_product_checks=checks,
        target_year_maximum=2025,completed_2026_evaluation_unchanged=True,deployment_approved=False,
        tests_and_freezes=tests,hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths})
    verify(receipt['hashes']);verify(pre['hashes'])
    save('final-review.json',result)
    public=ROOT/'reports/model-evidence/hitter-employment-comparison/report.json'
    if public.exists():raise ValueError('Preserve public receipt')
    public.parent.mkdir(parents=True,exist_ok=True)
    public.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['hashes','tests_and_freezes']}),flush=True)


if __name__=='__main__':main()
