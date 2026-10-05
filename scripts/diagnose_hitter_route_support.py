"""Replay existing forecasts and audit actual-fold origin-known route support."""
from pathlib import Path
import json
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_route_support import tag, counts, DISTANCE, STRATA
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from run_hitter_nonmedical_opportunity import ROOT, OUT as BASE, read, verify

OUT = ROOT / 'reports/generated/hitter-route-support-diagnostic'
FIXED = [47261, 51083, 51820, 57052, 44435, 35088, 63309, 63311,
         23934, 50571, 31364, 32754, 51153]
INSPECT = ['work_0','quality_0','quality_present_0','last_MLB_known','last_MLB_work',
    'last_MLB_quality','last_MLB_lag','last_first_team_known','last_first_team_work',
    'professional_work_0','professional_work_1','professional_work_2',
    'signed_first_team_work','returner_MLB_work','on_40man','status_major_link',
    'employment_evidence_age_years','scout_listed_0','scout_rank_score_0','draft_rank',
    'obs_status_finite_nonmedical','obs_status_unresolved_nonmedical']


def save(name, value):
    p=OUT/name
    assert not p.exists(), p
    p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')


def stats(g):
    w=weights(g); p=g['observation_p'].to_numpy(); y=g['next_pa'].to_numpy()
    return dict(rows=g.height,people=g['player_id'].n_unique(),
        expected_participants=float(p.sum()),actual_participants=int((y>0).sum()),
        expected_pa=float(g['observation_pa'].sum()),actual_pa=int(y.sum()),
        expected_contribution=float(g['observation_value'].sum()),
        actual_contribution=float(g['actual_relative_value'].sum()),
        equal_origin_pa_rmse=float(np.sqrt(np.average((g['observation_pa'].to_numpy()-y)**2,weights=w))),
        equal_origin_brier=float(np.average((p-(y>0))**2,weights=w)))


def main():
    assert not OUT.exists(), 'Preserve an existing diagnostic; inspect rather than restart'
    final=read(BASE/'final-review.json'); assert final['player_walkthrough_status']=='complete'
    verify(final['hashes']); pre=read(BASE/'preflight.json'); verify(pre['hashes'])
    fit=read(BASE/'fit-report.json'); q=pl.read_parquet(BASE/'predictions.parquet').sort('row_id')
    assert q.height==30519 and q['target_year'].max()==2025
    assert sha256_file(BASE/'predictions.parquet')==fit['predictions_sha256']
    paths=[Path(__file__), ROOT/'src/universal_baseball/hitter_route_support.py',
        ROOT/'tests/test_hitter_route_support.py',ROOT/'docs/hitter-route-support-diagnostic-contract.md',
        BASE/'final-review.json',BASE/'preflight.json',BASE/'fit-report.json',BASE/'predictions.parquet']
    paths += [BASE/f'features-{k}.parquet' for k in range(5)]
    paths += [ROOT/h['path'] for c in fit['cells'] for h in c['heads']]
    hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths}
    OUT.mkdir(); save('source-seal.json',dict(before_diagnostic=True,new_fits=0,hashes=hashes))
    frames={k:tag(pl.read_parquet(BASE/f'features-{k}.parquet')) for k in range(5)}
    context=frames[0]; routes=context.select('row_id',*STRATA)
    perturbed=tag(context.with_columns(pl.lit(777).alias('next_pa'),pl.lit(1).alias('next_active')))
    assert routes.equals(perturbed.select('row_id',*STRATA))
    support=[]; training=[]; cases=[]; usage=[]; replayed=0
    with threadpool_limits(limits=2):
        for c, fitted in zip(pre['cells'],fit['cells'],strict=True):
            y,k=c['year'],c['fold']; assert (y,k)==(fitted['origin'],fitted['fold'])
            f=frames[k]; tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            g=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert te['row_id'].equals(g['row_id'])
            assert tr['target_year'].max()<=y and tr['ctx_information_date'].max()<te['ctx_information_date'].min()
            assert not set(tr['player_id']) & set(te['player_id'])
            for head, sub in [('participation',tr),('conditional_pa',tr.filter(pl.col('next_pa')>0))]:
                s=counts(sub,te).with_columns(pl.lit(y).alias('origin'),pl.lit(k).alias('fold'),pl.lit(head).alias('head'))
                support.append(s)
                weighted=sub.with_columns(pl.Series('audit_fit_weight',weights(sub)))
                for (route,), z in weighted.group_by('audit_route'):
                    ww=z['audit_fit_weight'].to_numpy(); positive=z.filter(pl.col('next_pa')>0)
                    training.append(dict(origin=y,fold=k,head=head,route=route,rows=z.height,
                        people=z['player_id'].n_unique(),active_people=positive['player_id'].n_unique(),
                        empirical_prior_active_fraction=float(np.average(z['next_pa'].to_numpy()>0,weights=ww)),
                        empirical_prior_conditional_pa=float(np.average(positive['next_pa'].to_numpy(),weights=positive['audit_fit_weight'].to_numpy()))
                            if positive.height else None))
                h=next(h for h in fitted['heads'] if h['head']==head)
                assert sha256_file(ROOT/h['path'])==h['sha256']; m=joblib.load(ROOT/h['path'])
                x=te.select(h['features']).to_numpy()
                pred=m.predict_proba(x)[:,1] if head=='participation' else m.predict(x)
                n='observation_raw_p' if head=='participation' else 'observation_raw_conditional_pa'
                assert np.allclose(pred,g[n],atol=1e-10,rtol=0); replayed+=1
                use={n:0 for n in INSPECT}
                for trees in m._predictors:
                    for t in trees:
                        for node in t.nodes:
                            if not node['is_leaf']:
                                name=h['features'][int(node['feature_idx'])]
                                if name in use: use[name]+=1
                usage.append(dict(origin=y,fold=k,head=head,splits=use))
            for r in te.filter(pl.col('row_id').is_in(FIXED)).to_dicts():
                forecast=g.filter(pl.col('row_id')==r['row_id']).row(0,named=True)
                peers=tr.filter(pl.col('audit_route')==r['audit_route'])
                if peers.height:
                    matrix=peers.select(DISTANCE).to_numpy(); scale=tr.select(DISTANCE).to_numpy().std(axis=0)
                    scale=np.where(scale>0,scale,1.)
                    d=np.sum(((matrix-np.array([r[n] for n in DISTANCE]))/scale)**2,axis=1)
                    peers=peers.with_columns(pl.Series('distance',d)).sort(['distance','row_id'])
                    peers=peers.unique('player_id',keep='first',maintain_order=True).head(5)
                keep=['row_id','player_id','player_name','origin_year',*STRATA,*INSPECT,
                      'MLB_0_pa','AAA_0_pa','AA_0_pa','next_pa']
                cases.append(dict(row_id=r['row_id'],player_name=r['player_name'],origin_year=y,fold=k,
                    source_inputs={n:r[n] for n in dict.fromkeys(keep)},forecast=forecast,
                    actual_training_support=[s.filter(pl.col('row_id')==r['row_id']).row(0,named=True)
                                             for s in support[-2:]],
                    outcome_blind_training_peers=peers.select([*dict.fromkeys(keep),'distance']).to_dicts()
                        if peers.height else [],
                    interpretation='Training peers and frequencies are diagnostics, not replacement predictions'))
    assert replayed==70 and {c['row_id'] for c in cases}==set(FIXED)
    detail=pl.concat(support); detail.write_parquet(OUT/'support.parquet')
    g=q.join(routes,on='row_id',validate='1:1')
    assert g.select(q.columns).equals(q)
    assert np.allclose(g['observation_pa'],g['observation_p']*g['observation_conditional_pa'],atol=1e-10)
    summaries=[]
    for (route,), z in g.group_by('audit_route'):
        summaries.append(dict(scope='all',route=route,**stats(z)))
    for (year,route), z in g.group_by(['origin_year','audit_route']):
        summaries.append(dict(scope='origin',origin=int(year),route=route,**stats(z)))
    save('route-summaries.json',dict(rows=summaries))
    save('training-route-evidence.json',dict(rows=training))
    save('feature-use.json',dict(rows=usage))
    save('player-support-walks.json',dict(cases=cases))
    verify(hashes)
    save('execution-receipt.json',dict(new_fits=0,heads_replayed=replayed,evaluation_rows=q.height,
        fixed_walks=len(cases),target_year_maximum=2025,future_label_invariance=True,
        original_forecasts_unchanged=True,player_walkthrough_status='pending',deployment_approved=False,
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [*paths,*OUT.iterdir()]}))
    print(json.dumps(dict(new_fits=0,heads_replayed=replayed,walks=len(cases),rows=q.height)),flush=True)


if __name__=='__main__': main()
