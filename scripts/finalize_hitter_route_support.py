"""Independently verify actual-fold support and record the completed manual review."""
from collections import defaultdict
from pathlib import Path
import json
import subprocess
import sys
import numpy as np
import polars as pl
from universal_baseball.hitter_route_support import tag, STRATA
from universal_baseball.storage import sha256_file
from run_hitter_nonmedical_opportunity import ROOT, OUT as BASE, read, verify
from diagnose_hitter_route_support import OUT, save, FIXED


def main():
    public=ROOT/'reports/model-evidence/hitter-route-support-diagnostic/report.json'
    assert not public.exists() and not (OUT/'final-review.json').exists(), 'Preserve completion'
    execution=read(OUT/'execution-receipt.json');verify(execution['hashes'])
    school=read(OUT/'school-support-amendment.json');verify(school['hashes'])
    walks=read(OUT/'full-player-walks.json');verify(walks['hashes'])
    assert execution['heads_replayed']==70 and execution['new_fits']==0
    assert {c['row_id'] for c in walks['cases']}==set(FIXED)
    overlay=pl.read_parquet(ROOT/'reports/generated/hitter-cached-school-source-v65/school-overlay.parquet')
    pre=read(BASE/'preflight.json'); support_checks=0
    for qualified,path in [(False,'support.parquet'),(True,'school-qualified-support.parquet')]:
        recorded=pl.read_parquet(OUT/path)
        for k in range(5):
            f=pl.read_parquet(BASE/f'features-{k}.parquet')
            if qualified:
                f=f.join(overlay,on='row_id',how='left',validate='1:1').with_columns(
                    pl.when(pl.col('school_background_known')==1).then(pl.col('school_background_college'))
                    .otherwise(pl.col('draft_college')).alias('draft_college'))
            f=tag(f)
            for c in [c for c in pre['cells'] if c['fold']==k]:
                tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']))
                te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
                assert tr['target_year'].max()<=c['year'] and 2020 not in tr['target_year']
                assert not set(tr['player_id']) & set(te['player_id'])
                for head,sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                    broad=defaultdict(set); exact=defaultdict(set)
                    for r in sub.select('player_id',*STRATA).iter_rows(named=True):
                        broad[r['audit_route']].add(r['player_id'])
                        exact[tuple(r[n] for n in STRATA)].add(r['player_id'])
                    lookup={r['row_id']:r for r in recorded.filter((pl.col('origin')==c['year'])
                        & (pl.col('fold')==k) & (pl.col('head')==head)).to_dicts()}
                    assert set(lookup)==set(te['row_id'])
                    for r in te.select('row_id',*STRATA).iter_rows(named=True):
                        assert lookup[r['row_id']]['route_people']==len(broad[r['audit_route']])
                        assert lookup[r['row_id']]['stratum_people']==len(exact[tuple(r[n] for n in STRATA)])
                        support_checks+=2
    q=pl.read_parquet(BASE/'predictions.parquet')
    context=tag(pl.read_parquet(BASE/'features-0.parquet')).select('row_id','audit_route')
    g=q.join(context,on='row_id',validate='1:1')
    summaries=read(OUT/'route-summaries.json')['rows'];score_checks=0
    for s in summaries:
        rows=g.filter(pl.col('audit_route')==s['route'])
        if s['scope']=='origin': rows=rows.filter(pl.col('origin_year')==s['origin'])
        assert rows.height==s['rows'] and rows['player_id'].n_unique()==s['people']
        assert np.isclose(rows['observation_pa'].sum(),s['expected_pa'],atol=1e-8)
        assert rows['next_pa'].sum()==s['actual_pa']
        year_scores=[]
        for y in sorted(rows['origin_year'].unique()):
            z=rows.filter(pl.col('origin_year')==y)
            year_scores.append([float(np.mean((z['observation_pa'].to_numpy()-z['next_pa'].to_numpy())**2)),
                float(np.mean((z['observation_p'].to_numpy()-(z['next_pa'].to_numpy()>0))**2))])
        assert np.isclose(np.sqrt(np.mean(np.array(year_scores)[:,0])),s['equal_origin_pa_rmse'],atol=1e-10)
        assert np.isclose(np.mean(np.array(year_scores)[:,1]),s['equal_origin_brier'],atol=1e-10)
        score_checks+=6
    product_checks=0
    for c in walks['cases']:
        r=c['forecast'];assert q.filter(pl.col('row_id')==c['row_id']).row(0,named=True)==r
        assert np.isclose(r['observation_p']*r['observation_conditional_pa'],r['observation_pa'],atol=1e-10)
        assert np.isclose(r['observation_pa']*(r['observation_rate']/600+r['origin_replacement_rate']),r['observation_value'],atol=1e-10)
        assert all(s['season']<=c['origin_year'] for s in c['actual_domestic_history'])
        product_checks+=2
    docs=[ROOT/'docs/hitter-route-support-diagnostic-result.md',ROOT/'docs/hitter-route-support-player-review.md']
    assert all(p.exists() for p in docs), 'Actual manual review required'
    tests=[]
    for cmd in [[sys.executable,'-m','pytest','-q','-p','no:cacheprovider','tests/test_hitter_route_support.py'],
        [sys.executable,'scripts/verify_hitter_selected_2026_freeze.py'],
        [sys.executable,'scripts/verify_hitter_full_2026_freeze.py']]:
        r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
        assert r.returncode==0,r.stdout+r.stderr
        tests.append(dict(command=cmd[1:],exit_code=0,output=r.stdout))
    verify(execution['hashes']);verify(school['hashes']);verify(walks['hashes'])
    paths=[Path(__file__),*docs,*OUT.iterdir()]
    receipt=dict(status='diagnostic_and_player_review_complete',new_fits=0,heads_replayed=70,
        saved_case_paths_replayed=26,player_cases=13,player_walkthrough_status='complete',
        independent_support_value_checks=support_checks,independent_score_checks=score_checks,
        player_product_checks=product_checks,tests_and_freezes=tests,
        school_qualification_is_not_predictor_substitution=True,original_forecasts_unchanged=True,
        completed_2026_evaluation_unchanged=True,deployment_approved=False,
        no_universal_return_or_prospect_boost=True,
        next_design='source_qualified_common_production_learning_with_existing_talent_routes_and_fixed_opportunity',
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths})
    save('final-review.json',receipt)
    public.parent.mkdir(parents=True,exist_ok=True)
    public.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['hashes','tests_and_freezes']}),flush=True)


if __name__=='__main__': main()
