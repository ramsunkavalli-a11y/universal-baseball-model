"""Seal the reviewed no-promotion decision and additional seed/interval replays."""

from collections import Counter
from pathlib import Path
import json

import numpy as np
import polars as pl

from run_defense_jobs_v14 import ROOT,OUT,PUBLIC,DH,read,write,check,hashes,verify
from run_hitter_finite_return_baseline import protections


def main():
    pre=check();assert not (OUT/'final-review.json').exists()
    note=read(OUT/'fit-report.json');verify(note['hashes'])
    walk=read(OUT/'player-walkthrough.json');diag=read(OUT/'source-profile-diagnosis.json')
    report=read(OUT/'report.json');tests=read(OUT/'test-review.json')
    assert walk['status']=='complete' and not walk['missing_fixed_cases'] and all(c['peer_shortfall']==0 for c in walk['cases'])
    assert read(OUT/'independent-verification.json')['status']=='passed' and tests['pytest_exit_code']==0
    q=pl.read_parquet(OUT/'predictions.parquet');rows=q.to_dicts();models={}
    dhdelta={(r['season'],r['player_id']):r['certified_dual_DH_starts'] for r in pl.read_parquet(DH/'reviewed-DH-starts.parquet').to_dicts()}
    for r in rows:
        key=r['origin_year'],r['outer_fold']
        if key not in models:models[key]=read(OUT/f'model-{key[0]}-{key[1]}.json')
        model=models[key]
        choices=[['role_status',str(r['job_primary_role']),r['job_status']],['role',str(r['job_primary_role'])],
                 ['family_status',r['job_family'],r['job_status']],['family',r['job_family']],['all']]
        table={tuple(c['key']):c for c in model['tables']}
        prior=next((table[tuple(k)] for k in choices if table[tuple(k)]['people']>=20 and
                    table[tuple(k)]['effective_people']>=10 and table[tuple(k)]['denominator_job_time']>0),None)
        learned=np.array(prior['shares'] if prior else r['job_own_shares'],float)
        if not r['job_catching_evidence']:learned[0]=0
        if learned.sum():learned/=learned.sum()
        own=np.array(r['job_own_shares']);seed=np.zeros(9) if r['job_unknown'] else r['job_weight']*own+(1-r['job_weight'])*learned
        if seed.sum():seed/=seed.sum()
        assert np.allclose(seed,r['job_prediction_shares'],atol=1e-12,rtol=0)
        jobtime=r['reference_potential_outs']+r['reference_10']*r['origin_dh_outs']
        predicted=np.array([r[f'joint_{p}'] for p in range(2,11)]);predicted[-1]*=r['origin_dh_outs']
        assert np.allclose(predicted,jobtime*seed,atol=1e-8,rtol=0)
        assert r['carry_10']==r['raw_carry_DH']+dhdelta.get((r['origin_year'],r['player_id']),0)
        assert r['actual_10']==r['raw_actual_DH']+dhdelta.get((r['target_year'],r['player_id']),0)
    intervals=[]
    for saved in report['intervals']:
        rs=[r for r in rows if r[saved['target']] is not None]
        people=sorted({r['player_id'] for r in rs});pi={pid:i for i,pid in enumerate(people)}
        loss=np.zeros((len(people),3,2));count=np.zeros((len(people),3))
        for r in rs:
            i,j=pi[r['player_id']],r['origin_year']-2022;assert count[i,j]==0;count[i,j]=1
            loss[i,j]=[(r[a]-r[saved['target']])**2 for a in (saved['left'],saved['right'])]
        rng=np.random.default_rng(712001);draws=[]
        for _ in range(2000):
            sampled=rng.integers(len(people),size=len(people));den=count[sampled].sum(axis=0)
            roots=np.sqrt(loss[sampled].sum(axis=0)/den[:,None]).mean(axis=0);draws.append(float(roots[0]-roots[1]))
        limits=np.quantile(draws,[.025,.975]);assert np.allclose(limits,saved['interval_95'],atol=1e-12,rtol=0)
        intervals.append(dict(target=saved['target'],people=len(people),draws=2000,interval_95=limits.tolist(),replayed=True))
    write('additional-verification.json',dict(joint_seed_forecasts_replayed=len(rows),corrected_DH_inputs_and_targets_replayed=len(rows),
        intervals=intervals,no_refits=True,no_replacement_forecasts=True))
    summary=dict(status=diag['status'],inferred_unobserved_position_rows=diag['inferred_unobserved_position_rows'],
        unobserved_counts_by_origin=dict(Counter(r['origin'] for r in diag['unobserved_allocations'])),
        qualification='Unobserved position borrowing is not always impossible; specific pure-DH/primary-label failures are reviewed separately.',
        explicit_defects=diag['explicit_defects'],Eldridge_prior=diag['Eldridge_prior'],
        Eldridge_prior_contributors=diag['Eldridge_prior_contributors'],
        full_local_diagnosis_path=str(OUT/'source-profile-diagnosis.json'),full_diagnosis_sha256=hashes([OUT/'source-profile-diagnosis.json'])[str(OUT/'source-profile-diagnosis.json')],
        source_provenance_records=sum(len(c['records']) for c in diag['source_provenance']))
    write('diagnosis-summary.json',summary)
    owned=[ROOT/'docs/defense-jobs-v14-contract.md',ROOT/'docs/defense-jobs-v14-result.md',
           ROOT/'src/universal_baseball/defense_jobs.py',ROOT/'tests/test_defense_jobs.py',
           *[ROOT/f'scripts/{n}' for n in ['run_defense_jobs_v14.py','verify_defense_jobs_v14.py','review_defense_jobs_v14.py',
                                           'diagnose_defense_jobs_v14.py','finalize_defense_jobs_v14.py']]]
    owned += [OUT/n for n in ['preflight.json','fit-report.json','report.json','independent-verification.json','additional-verification.json',
                              'player-walkthrough.json','player-walkthrough.md','source-profile-diagnosis.json','diagnosis-summary.json','test-review.json']]
    protections()
    write('final-review.json',dict(status='reviewed_repair_required_not_promoted',execution_integrity='passed',
        training_support='qualified_sparse_and_unseen_profiles',predictive_improvement=False,
        baseball_reasonability='failed_role_representation_and_temporary_assignment_checks',
        primary_value_RMSE_change=report['intervals'][0]['mean_origin_RMSE_difference'],
        primary_value_interval=report['intervals'][0]['interval_95'],
        disposition='Retain corrected source and capacity checks; do not promote individual allocation. Keep existing quality baselines.',
        player_walkthrough_status='complete',focal_cases=len(walk['cases']),walked_records=walk['players_walked'],
        open_work=['Current versus older/temporary role evidence','Full repertoire versus primary-label pooling',
                   'Dated upcoming role evidence','Sparse/minor defensive talent and longer-horizon value',
                   'Separate Lovich batting defect'],
        no_2026_outcomes_used=True,frozen_forecast_and_explorer_unchanged=True,full_defense_goal_complete=False,
        hashes=hashes(owned)))
    print(json.dumps(dict(status='reviewed_no_promotion',forecasts=len(rows),focal_cases=len(walk['cases']),goal_complete=False)))


if __name__=='__main__':main()
