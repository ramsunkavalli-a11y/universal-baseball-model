"""Independent allocation check and completion, without approving forecasts."""
import json
import subprocess
import sys
import numpy as np
import polars as pl
from pathlib import Path
from audit_overseas_opportunity_inventory import ROOT, OUT, REP, GEN, read, verify, save
from universal_baseball.storage import sha256_file


def main():
    if (OUT/'final-review.json').exists(): raise ValueError('Preserve completed diagnosis')
    verify(read(OUT/'source-seal.json')['hashes']); verify(read(OUT/'execution-recovery.json')['hashes'])
    d=read(OUT/'inventory.json'); q=pl.read_parquet(REP/'predictions.parquet')
    ids=pl.read_parquet(GEN/'foreign-count-calibration/predictions.parquet').filter(pl.col('source_present')).select('row_id','route_used')
    q=q.join(ids,on='row_id',how='inner',validate='1:1')
    cats={w['row_id']:w['employment_category'] for w in d['walks']}
    f=pl.read_parquet(REP/'features-0.parquet',columns=['row_id','status_major_link','status_minor_agreement','status_employment_unknown']).filter(pl.col('row_id').is_in(q['row_id'].to_list()))
    f=f.with_columns(pl.when(pl.col('status_major_link')>0).then(pl.lit('major_link')).when(pl.col('status_minor_agreement')>0).then(pl.lit('minor_agreement')).when(pl.col('status_employment_unknown')>0).then(pl.lit('unknown')).otherwise(pl.lit('other')).alias('category'))
    q=q.join(f.select('row_id','category'),on='row_id',validate='1:1'); checks=0
    for report in d['groups']:
        name=report['scope']
        g=q.filter(pl.col('source_addition')) if name=='additions' else q.filter(~pl.col('source_addition'))
        if name.startswith('fresh_original'): g=g.filter(pl.col('route_used'))
        if name.startswith('fresh_original_'): g=g.filter(pl.col('category')==name[len('fresh_original_'):])
        if len(g)!=report['rows'] or g['next_pa'].sum()!=report['actual_PA']: raise ValueError('Scope/target mismatch')
        for arm,s in report['arms'].items():
            if arm=='current' and name=='additions':
                if s!={'missing_current_forecasts':True}: raise ValueError('Invented current prediction')
                continue
            n=np.array(g[arm+'_pa']); p=np.array(g[arm+'_p']); actual=np.array(g['next_pa']); y=np.array(g['origin_year'])
            a=actual>0; metrics=dict(expected_PA=float(n.sum()),expected_participants=float(p.sum()),PA_allocated_to_eventual_participants=float(n[a].sum()),PA_allocated_to_nonarrivals=float(n[~a].sum()),
                PA_RMSE=float(np.sqrt(np.mean([np.mean((n[y==v]-actual[y==v])**2) for v in np.unique(y)]))),Brier=float(np.mean([np.mean((p[y==v]-a[y==v])**2) for v in np.unique(y)])))
            for k,v in metrics.items():
                if not np.isclose(v,s[k],atol=1e-10,rtol=0): raise ValueError('Independent allocation mismatch')
                checks+=1
    focal=read(GEN/'foreign-count-calibration/player-walks.json')['cases']
    doc=ROOT/'docs/hitter-overseas-opportunity-inventory-result.md'; prose=doc.read_text(encoding='utf8')
    if len(focal)!=18 or d['unique_walk_rows']!=59 or d['saved_head_replays']!=118 or 'Read-only diagnosis complete' not in prose: raise ValueError('Incomplete walkthrough')
    reviewed={w['row_id'] for w in d['walks']}
    for c in focal:
        for t in [c['trace'],*[x['trace'] for x in c['peers']]]:
            if t['forecast']['row_id'] not in reviewed: raise ValueError('Dropped retained peer')
    tests=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider','tests/test_overseas_opportunity_inventory.py','tests/test_hitter_evidence_representation.py'],cwd=ROOT,capture_output=True,text=True)
    if tests.returncode: raise ValueError(tests.stdout+tests.stderr)
    freezes=[]
    for script in ['verify_hitter_selected_2026_freeze.py','verify_hitter_full_2026_freeze.py']:
        r=subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,capture_output=True,text=True)
        if r.returncode: raise ValueError(r.stdout+r.stderr)
        freezes.append(dict(script=script,output=json.loads(r.stdout),qualifier='Package verifier describes original pre-result state; completed 2026 evaluation is unchanged.'))
    paths=[doc,Path(__file__),ROOT/'tests/test_overseas_opportunity_inventory.py',OUT/'inventory.json',OUT/'source-seal.json',OUT/'execution-recovery.json']
    receipt=dict(status='diagnosis_complete',player_walkthrough_status='complete',focal_origins=18,unique_traces=59,saved_head_replays=118,
        independent_allocation_checks=checks,tests=tests.stdout,new_fits=0,new_forecasts=0,predictive_gain_claimed=False,deployment_approved=False,
        frozen_2026_forecasts_changed=False,freeze_checks=freezes,
        next_boundary='Audit saved public entrant coverage and dated overseas contract/role intent before another fit.',
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths})
    save('final-review.json',receipt)
    public=ROOT/'reports/model-evidence/overseas-opportunity-inventory'
    if public.exists(): raise ValueError('Preserve public receipt')
    public.mkdir();(public/'report.json').write_text(json.dumps(dict(**receipt,groups=d['groups']),indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(dict(status=receipt['status'],head_replays=118,allocation_checks=checks,tests=tests.stdout,forecasts_unchanged=True)),flush=True)


if __name__=='__main__': main()
