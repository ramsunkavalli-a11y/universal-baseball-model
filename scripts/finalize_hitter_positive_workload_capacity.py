"""Independent score/product checks and a mandatory manual player review gate."""
import json
import shutil
import subprocess
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import test_hitter_positive_workload_capacity as run

ROOT=run.ROOT; OUT=run.OUT; EVIDENCE=run.EVIDENCE


def main():
    p=run.read(OUT/'preflight.json');run.verify(p['source_hashes']);run.verify(p['baseline_hashes'])
    amendment=run.read(OUT/'reporting-amendment.json')
    run.verify({amendment['scorer_path']:amendment['scorer_sha256']})
    assert amendment['original_runner_sha256']==sha256_file(Path(run.__file__)) and amendment['new_fits']==0
    v=run.read(OUT/'verification.json');run.verify(v['output_hashes'])
    heads=run.read(OUT/'fit-report.json')['heads']
    assert len(heads)==70 and len({(h['arm'],h['year'],h['fold']) for h in heads})==70
    for h in heads:run.verify({h['path']:h['sha256'],h['prediction_path']:h['prediction_sha256']})
    q=pl.read_parquet(OUT/'scored-predictions.parquet').sort('row_id')
    anchor=pl.read_parquet(run.current.OUT/'scored-predictions.parquet').sort('row_id')
    assert len(q)==30506 and q.select(anchor.columns).equals(anchor) and q['target_year'].max()==2025
    assert len(p['checks'])==70 and all(c['integrity_pass'] for c in p['checks'])
    assert v['new_heads_replayed']==70 and v['baseline_conditional_heads_replayed_before_fits']==35
    for arm in ['deep_hist','lightgbm']:
        raw=q[arm+'_raw_conditional_pa'].to_numpy();bounded=np.minimum(800,np.maximum(1,raw))
        pa=q['preseason_p'].to_numpy()*bounded
        value=pa*(q['preseason_rate'].to_numpy()/600+q['origin_replacement_rate'].to_numpy())
        for key,actual in [('conditional_pa',bounded),('pa',pa),('value',value)]:
            assert np.allclose(q[arm+'_'+key],actual,atol=1e-10,rtol=0)
    groups={'all':q,'public':run.location.public(q),
        'current_MLB':q.filter(pl.col('pa_0')>0),
        'absent_prior_debut':q.filter((pl.col('prior_debut')==1)&(pl.col('pa_0')==0)),
        'upper_never_debut':q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors')),
        'lower_never_debut':q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors')),
        'thin_new_draftee':q.filter((pl.col('draft_known')==1)&(pl.col('draft_year')==pl.col('origin_year'))&
            (pl.sum_horizontal('minor_pa_0','minor_pa_1','minor_pa_2','pa_0','pa_1','pa_2')<150))}
    assert len(groups['public'])==2627
    groups.update({f'origin_{y}':q.filter(pl.col('origin_year')==y) for y in q['origin_year'].unique()})
    groups.update({f'current_PA_{lo}_{hi}':q.filter(pl.col('pa_0').is_between(lo,hi)) for lo,hi in [(1,199),(200,399),(400,599),(600,10000)]})
    score_rows=run.read(OUT/'scores.json')
    assert set(groups)=={s['scope'] for s in score_rows}
    recomputed=0
    for s in score_rows:
        g=groups[s['scope']];assert len(g)==s['rows'] and g['next_pa'].sum()==s['actual_pa']
        for arm,scores in s['scores'].items():
            for metric in ['pa','value']:
                error=g[arm+'_'+metric].to_numpy()-g['next_'+metric].to_numpy()
                years=g['target_year'].to_numpy();parts=[error[years==y] for y in np.unique(years)]
                checks={'rmse':np.sqrt(np.mean([np.mean(z*z) for z in parts])),
                    'mae':np.mean([np.mean(abs(z)) for z in parts]),'bias':np.mean([np.mean(z) for z in parts]),
                    'total':float(g[arm+'_'+metric].sum())}
                for key,actual in checks.items():assert np.isclose(scores[metric+'_'+key],actual,atol=1e-9,rtol=0)
                recomputed+=1
    cases=run.read(OUT/'cases.json');review_path=ROOT/'config/hitter_positive_workload_capacity_review.json'
    review=run.read(review_path);assert set(review['players'])=={str(c['origin']['row_id']) for c in cases}
    doc=ROOT/'docs/hitter-positive-workload-capacity-result.md';content=doc.read_text(encoding='utf8')
    for c in cases:
        r=c['origin'];notes=review['players'][str(r['row_id'])]
        assert all(len(notes[k])>=80 for k in ['stats_and_inputs','mechanics','outcome_and_judgment','peer_context'])
        assert r['player_name'] in content and str(r['row_id']) in content
        assert len(c['actual_inputs'])==251 and len(c['saved_conditional_paths'])==3 and len(c['peers'])==4
        actual=q.filter(pl.col('row_id')==r['row_id']).row(0,named=True)
        for name,value in r.items():
            if name=='next_batting_rate' and not r['next_pa']:assert value is None
            else:assert actual[name]==value
        assert all(t['next_batting_rate'] is None for t in c['peers'] if not t['next_pa'])
    assert review['current_candidate_changed'] is False and review['full_goal_complete'] is False
    freeze=json.loads(subprocess.check_output([str(ROOT/'.venv/Scripts/python.exe'),'-X','utf8',
        str(ROOT/'scripts/verify_hitter_full_2026_freeze.py')],cwd=ROOT))
    assert freeze['status']=='verified' and freeze['protected_2026_opened'] is False
    paths=[OUT/n for n in ['preflight.json','fit-report.json','scores.json','intervals.json','cases.json','verification.json','reporting-amendment.json']]
    paths.extend([Path(__file__),review_path,doc])
    profile=pl.read_parquet(OUT/'profiles.parquet')
    profile_summary={kind:dict(rows=len(g),absent=int((g['profile_people']==0).sum()),sparse=int((g['profile_people']<20).sum()))
        for (kind,),g in profile.group_by('kind')}
    run.write('final-report.json',dict(execution_integrity=True,player_walkthrough_status='complete',reviewed_cases=len(cases),
        conditional_heads_fitted_and_replayed=70,baseline_heads_replayed_before_fits=35,score_components_independently_recomputed=recomputed,
        profile_support=profile_summary,disposition=review['disposition'],next_step=review['next_step'],
        current_candidate_changed=False,full_goal_complete=False,protected_outcomes_used=False,deployment_approved=False,
        frozen_verification=freeze,evidence_hashes={str(path):sha256_file(path) for path in paths},
        local_fit_hashes={h['path']:h['sha256'] for h in heads}))
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    for name in ['preflight.json','fit-report.json','scores.json','intervals.json','cases.json','verification.json','reporting-amendment.json','final-report.json']:
        assert not (EVIDENCE/name).exists();shutil.copyfile(OUT/name,EVIDENCE/name)
    print('Independent scores verified; all selected player walks complete; current and protected forecasts unchanged.',flush=True)


if __name__=='__main__':main()
