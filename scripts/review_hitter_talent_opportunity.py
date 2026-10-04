"""Supplementary source traces and a separate manual-review receipt; no refits."""
import json
import shutil
import sys
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.storage import sha256_file
from universal_baseball.histogram_prediction_trace import trace
from evaluate_hitter_readiness_v49 import logit_trace
from prepare_practical_hitter_v33 import safe_matrix
import fit_hitter_talent_opportunity as fit

ROOT, OUT = fit.ROOT, fit.OUT
EVIDENCE = ROOT / 'reports/model-evidence/hitter-talent-opportunity'


def supplementary():
    assert not (OUT/'supplementary-cases.json').exists(), 'Preserve the source trace'
    v = fit.read(OUT/'verification.json'); fit.verify(v['source_hashes'])
    pre = fit.read(OUT/'preflight.json')
    f = pl.read_parquet(fit.setup.current.OUT/'features.parquet')
    q = pl.read_parquet(OUT/'scored-predictions.parquet')
    counts = pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    support = pl.read_parquet(OUT/'profile-support.parquet')
    pena = q.filter((pl.col('player_id')==665161)&(pl.col('origin_year')==2021))
    assert len(pena)==1 and pena['player_name'][0]=='Jeremy Peña'
    lower = q.filter((pl.col('origin_year')==2024)&(pl.col('prior_debut')==0)&
        (pl.col('stage')=='Lower minors')&(pl.col('age')<20)).sort(
            ['talent_mlb_rate','player_id'], descending=[True,False]).head(1)
    chosen = [(pena['row_id'][0], 'Correct predeclared Peña identity'),
              (lower['row_id'][0], 'Highest projected hitting among origin-2024 lower-minors players under 20; outcome-blind')]
    cases = []
    with threadpool_limits(limits=2):
        for rid,why in chosen:
            r=q.filter(pl.col('row_id')==rid).row(0,named=True); y,k=r['origin_year'],r['outer_fold']
            te=f.filter(pl.col('row_id')==rid).join(pl.read_parquet(OUT/f'generated-features-{k}.parquet'),
                on='row_id',validate='1:1')
            c=next(c for c in pre['cells'] if c['year']==y and c['fold']==k)
            old=fit.read(fit.setup.current.OUT/f'fit-{y}-{k}.json')
            new=fit.read(OUT/f'fit-{y}-{k}.json'); paths={}
            for arm, heads in [('current',old['heads']),('coverage',[h for h in new['heads'] if h['arm']=='coverage']),
                               ('talent',[h for h in new['heads'] if h['arm']=='talent'])]:
                paths[arm]={}
                for h in heads:
                    fit.verify({h['path']:h['sha256']})
                    names=pre['pa_features'] if arm=='current' else h['features']; x=te.select(names).to_numpy()[0]
                    m=joblib.load(h['path'])
                    paths[arm][h['head']]=logit_trace(m,x,names) if h['head']=='participation' else trace(m,x,names)
                    prediction=paths[arm][h['head']]['linked_probability'] if h['head']=='participation' else paths[arm][h['head']]['raw_prediction']
                    original='preseason' if arm=='current' else arm
                    column=original+('_raw_p' if h['head']=='participation' else '_raw_conditional_pa')
                    assert np.isclose(prediction,r[column],atol=1e-10,rtol=0)
            tag=f'rate-{y}-{k}'; note=fit.read(OUT/(tag+'.json')); fit.verify(note['hashes'])
            m=joblib.load(OUT/(tag+'.joblib')); rx=safe_matrix(te,pre['rate_features'])[0]; terms=rx*m.coef_
            assert np.isclose(float(m.intercept_+terms.sum()),r['talent_mlb_rate'],atol=1e-10,rtol=0)
            peers=q.filter((pl.col('origin_year')==y)&(pl.col('prior_debut')==r['prior_debut'])&
                (pl.col('stage')==r['stage'])&(pl.col('player_id')!=r['player_id'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+
                 ((pl.col('pa_0')-r['pa_0'])/250)**2+2*(pl.col('new_scout_rank_score_0')-r['new_scout_rank_score_0'])**2+
                 ((pl.col('talent_mlb_rate')-r['talent_mlb_rate'])/2)**2+
                 (pl.col('source_position')!=r['source_position']).cast(pl.Float64)).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=r,selection=[why],information_date=c['information_date'],
                source_history=counts.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                actual_inputs=te.select(*pre['pa_features'],'talent_known','talent_mlb_rate').row(0,named=True),
                generated_rate_fit=note,generated_rate_intercept=float(m.intercept_),
                generated_rate_terms=[dict(feature=n,scaled_input=float(x),coefficient=float(b),contribution=float(v))
                    for n,x,b,v in zip(pre['rate_features'],rx,m.coef_,terms,strict=True)],
                training_profiles=support.filter((pl.col('row_id')==rid)&(pl.col('held_outer_fold')==k)).to_dicts(),
                saved_opportunity_paths=paths,peers=peers.select('player_id','player_name','age','source_position','minor_pa_0','pa_0',
                    'new_scout_rank_score_0','talent_mlb_rate','current_pa','coverage_pa','talent_pa','next_pa','distance').to_dicts(),
                peer_limit='Origin-known age, stage, position, workload, rank and generated hitting; not matched medical/legal status or full talent'))
    fit.write('supplementary-cases.json', cases)
    paths=[Path(__file__),ROOT/'docs/hitter-talent-opportunity-review-amendment.md',OUT/'verification.json',OUT/'supplementary-cases.json']
    fit.write('supplementary-verification.json',dict(no_fits=True,no_scores_changed=True,
        original_cases_retained=True,source_hashes={str(p):sha256_file(p) for p in paths}))
    print('Added correct Peña identity and outcome-blind lower-level case:',[(c['origin']['player_name'],c['origin']['row_id']) for c in cases])


def inspect():
    cases=fit.read(OUT/'cases.json')+fit.read(OUT/'supplementary-cases.json')
    for c in cases:
        r=c['origin']; stats=c['source_history']; paths=c['saved_opportunity_paths']
        selected={k:r.get(k) for k in ['row_id','player_name','player_id','origin_year','age','source_position','stage','minor_pa_0',
            'pa_0','new_scout_rank_score_0','draft_year','talent_mlb_rate','next_pa','next_value','reported_retired','hard_unavailable']}
        selected['outputs']={a:{n:round(r[a+'_'+n],5) for n in ['p','conditional_pa','pa','value']} for a in ['current','coverage','talent']}
        selected['stats']=stats
        selected['profiles']={s['scope']:s['profile_people'] for s in c['training_profiles']}
        selected['rate_intercept']=c['generated_rate_intercept']
        selected['rate_terms']=sorted(c['generated_rate_terms'],key=lambda t:abs(t['contribution']),reverse=True)[:5]
        selected['paths']={a:{h:{'reference':v['reference'],'largest_effects':v['feature_effects'][:4],
            'talent_effects':[e for e in v['feature_effects'] if e['feature'].startswith('talent_')]}
            for h,v in heads.items()} for a,heads in paths.items() if a!='coverage'}
        selected['peers']=[{k:p[k] for k in ['player_name','age','source_position','minor_pa_0','pa_0','talent_mlb_rate','talent_pa','next_pa']} for p in c['peers']]
        print(json.dumps(selected,ensure_ascii=False))


def finalize():
    v=fit.read(OUT/'verification.json'); fit.verify(v['source_hashes']); fit.verify(fit.read(OUT/'fit-seal.json'))
    s=fit.read(OUT/'supplementary-verification.json'); fit.verify(s['source_hashes'])
    cases=fit.read(OUT/'cases.json')+fit.read(OUT/'supplementary-cases.json')
    notes_path=ROOT/'config/hitter_talent_opportunity_review.json'; notes=fit.read(notes_path)
    ids={str(c['origin']['row_id']) for c in cases}
    assert len(ids)==len(cases) and set(notes['players'])==ids
    assert all(len(n)>200 for n in notes['players'].values())
    assert not notes['current_candidate_changed'] and not notes['deployment_approved'] and not notes['full_goal_complete']
    doc=ROOT/'docs/hitter-talent-opportunity-player-walkthrough.md'; text=doc.read_text(encoding='utf8')
    assert all(c['origin']['player_name'] in text and str(c['origin']['row_id']) in text for c in cases)
    assert any(c['origin']['player_id']==665161 and c['origin']['origin_year']==2021 for c in cases)
    assert v['all_current_columns_exact'] and v['rate_heads_replayed']==135 and v['opportunity_heads_replayed']==140 and v['baseline_heads_replayed']==70
    reviewed=[dict(row_id=c['origin']['row_id'],player_id=c['origin']['player_id'],player_name=c['origin']['player_name'],
        origin_year=c['origin']['origin_year'],selection=c['selection'],baseball_review=notes['players'][str(c['origin']['row_id'])]) for c in cases]
    fit.write('reviewed-cases.json',reviewed)
    paths=[notes_path,doc,ROOT/'docs/hitter-talent-opportunity-result.md',OUT/'reviewed-cases.json',
        OUT/'supplementary-cases.json',OUT/'supplementary-verification.json',Path(__file__)]
    final=dict(execution_integrity=True,evaluation_rows=30506,rate_heads_replayed=135,new_opportunity_heads_replayed=140,
        baseline_heads_replayed=70,player_walkthrough_status='complete',reviewed_cases=len(cases),walkthrough_path=str(doc),
        predictive_disposition=notes['disposition'],support_claim=notes['support_claim'],baseball_limits=notes['baseball_limits'],
        current_candidate_changed=False,full_goal_complete=False,deployment_approved=False,
        protected_outcomes_used=False,frozen_forecast_changed=False,all_current_forecasts_exact=True,
        source_and_execution_hashes=v['source_hashes'],review_hashes={str(p):sha256_file(p) for p in paths})
    fp=OUT/'final-report.json'
    if fp.exists():
        assert fit.read(fp)==final,'Do not overwrite a different completed review'
    else:
        fit.write('final-report.json',final)
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    for name in ['fit-seal.json','scores.json','intervals.json','verification.json','cases.json','supplementary-cases.json',
                 'supplementary-verification.json','reviewed-cases.json','final-report.json','legacy-source-reconciliation.json']:
        source,target=OUT/name,EVIDENCE/name
        if target.exists():
            assert sha256_file(source)==sha256_file(target)
        else:
            shutil.copyfile(source,target)
    print('All actual player reviews complete; separate completed receipt; original fits and scores preserved.')


if __name__=='__main__':
    {'supplementary':supplementary,'inspect':inspect,'finalize':finalize}[sys.argv[1]]()
