"""Shared-context uncertainty and review gate, separate from the locked fits."""
from pathlib import Path
import json
import sys
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
import evaluate_hitter_team_record_v75 as experiment

OUT, ROOT = experiment.OUT, experiment.ROOT


def crossed(g, a, b, metric):
    error=((g[a+'_'+metric]-g['next_'+metric])**2-(g[b+'_'+metric]-g['next_'+metric])**2).to_numpy()
    _,people=np.unique(g['player_id'].to_numpy(),return_inverse=True)
    _,years=np.unique(g['target_year'].to_numpy(),return_inverse=True)
    keys=[(r['origin_year'],r['context_parent_id'] if r['org_record_known'] else -1)
          for r in g.iter_rows(named=True)]
    groups={k:i for i,k in enumerate(sorted(set(keys)))};teams=np.array([groups[k] for k in keys])
    npeople=people.max()+1;nteam=len(groups);nyear=years.max()+1
    rng=np.random.default_rng(75);draw=[]
    for _ in range(1000):
        p=np.bincount(rng.integers(0,npeople,npeople),minlength=npeople)
        t=np.bincount(rng.integers(0,nteam,nteam),minlength=nteam)
        w=p[people]*t[teams];den=np.bincount(years,weights=w,minlength=nyear)
        if (den==0).any():continue
        draw.append(float(np.mean(np.bincount(years,weights=w*error,minlength=nyear)/den)))
    return dict(candidate=a,benchmark=b,metric=metric+'_mse',
        difference=float(np.mean([error[years==y].mean() for y in range(nyear)])),
        lower=float(np.quantile(draw,.025)),upper=float(np.quantile(draw,.975)),draws=len(draw),
        resampling='Crossed player and organization-year cluster weights; equal target years; nominal development sensitivity only')


def audit():
    assert experiment.read(OUT/'verification.json')['player_walkthrough_status']=='pending'
    f=pl.read_parquet(OUT/'scored-predictions.parquet').filter(pl.col('prior_debut')==0)
    intervals=[]
    with threadpool_limits(limits=2):
        for label,g in [('never_debut',f),('known_never_debut',f.filter(pl.col('org_record_known')==1))]:
            for a,b in [('record','coverage'),('record','current')]:
                for metric in ['pa','value']:
                    intervals.append(dict(scope=label,**crossed(g,a,b,metric)))
    group_source=f.with_columns(pl.when(pl.col('org_record_known')==1).then(pl.col('context_parent_id')).otherwise(-1).alias('cluster_parent_id'))
    groups=group_source.group_by('origin_year','cluster_parent_id','org_record_known').agg(
        pl.len().alias('rows'),pl.col('player_id').n_unique().alias('people'),
        pl.col('next_pa').sum().alias('actual_pa'),pl.col('record_pa').sum().alias('record_pa'),
        pl.col('coverage_pa').sum().alias('coverage_pa'),pl.col('current_pa').sum().alias('current_pa'),
        (((pl.col('record_pa')-pl.col('next_pa'))**2)-((pl.col('coverage_pa')-pl.col('next_pa'))**2)).sum().alias('record_minus_coverage_pa_squared_error_sum'),
        (((pl.col('record_value')-pl.col('next_value'))**2)-((pl.col('coverage_value')-pl.col('next_value'))**2)).sum().alias('record_minus_coverage_value_squared_error_sum')).sort('origin_year','cluster_parent_id')
    experiment.write('crossed-intervals.json',intervals)
    experiment.write('organization-year-losses.json',groups.to_dicts())
    cases=experiment.read(OUT/'cases.json');summaries=[]
    for c in cases:
        r=c['origin'];probes={}
        for pct,heads in c['fixed_record_probes'].items():
            probes[pct]=dict(p=heads['participation'],conditional_pa=float(np.clip(heads['conditional_pa'],1,800)),
                             pa=heads['participation']*float(np.clip(heads['conditional_pa'],1,800)))
        summary=dict(row_id=r['row_id'],player_id=r['player_id'],player_name=r['player_name'],origin_year=r['origin_year'],
            selection=c['selection'],age=r['age'],stage=r['stage'],parent=r['context_parent'],
            record_known=r['org_record_known'],win_pct=r['org_record_centered']+.5 if r['org_record_known'] else None,
            source_history=c['source_history'],
            forecasts={a:{m:r[a+'_'+m] for m in ['p','conditional_pa','pa','value']} for a in ['current','coverage','record','record_all']},
            fixed_hitting_rate=r['baseline_rate'],actual_pa=r['next_pa'],actual_value=r['next_value'],probes=probes,
            training_support=[p for p in c['training_profiles'] if p['arm']=='record' and p['kind']=='refined'],
            record_path_effects={head:[z for z in c['saved_traces']['record'][head]['feature_effects'] if z['feature'].startswith('org_record_')]
                                 for head in ['participation','conditional_pa']},
            peer_names=[dict(player_id=p['player_id'],name=p['player_name'],rank=p['fresh_rank'],pa=p['next_pa']) for p in c['peers']])
        summaries.append(summary)
    experiment.write('review-case-summary.json',summaries)
    paths=[OUT/'preflight.json',OUT/'verification.json',OUT/'fits.json',OUT/'scores.json',OUT/'intervals.json',
           OUT/'scored-predictions.parquet',OUT/'cases.json',OUT/'review-case-summary.json',OUT/'crossed-intervals.json',
           OUT/'organization-year-losses.json',ROOT/'docs/hitter-team-record-v75-uncertainty-supplement.md',Path(__file__)]
    experiment.write('review-audit.json',dict(hashes={str(p):sha256_file(p) for p in paths},
        player_walkthrough_status='pending',shared_context_check_complete=True,protected_outcomes_used=False))
    for r in summaries:
        print(r['player_name'],r['origin_year'],'PA',*[round(r['forecasts'][a]['pa'],2) for a in ['current','coverage','record']],
              'actual',r['actual_pa'],'record',r['win_pct'],r['selection'],flush=True)


def finalize():
    audit=experiment.read(OUT/'review-audit.json');experiment.verify_hashes(audit['hashes'])
    notes=experiment.read(ROOT/'config/hitter_team_record_v75_review.json')
    cases=experiment.read(OUT/'review-case-summary.json')
    assert set(notes['players'])=={str(c['row_id']) for c in cases}
    assert all(len(v)>100 for v in notes['players'].values())
    completed=[dict(**c,baseball_review=notes['players'][str(c['row_id'])]) for c in cases]
    experiment.write('reviewed-cases.json',completed)
    paths=[OUT/'reviewed-cases.json',ROOT/'config/hitter_team_record_v75_review.json',
           ROOT/'docs/hitter-team-record-v75-result.md']
    experiment.write('report.json',dict(execution_integrity=True,new_heads_replayed=140,baseline_heads_replayed=70,
        evaluation_rows=30506,player_walkthrough_status='complete',reviewed_cases=len(completed),
        predictive_disposition=notes['disposition'],current_candidate_changed=False,full_goal_complete=False,
        profile_claim='Sparse active prospect intersections and partial rights coverage remain qualified',
        source_and_execution_hashes=audit['hashes'],review_hashes={str(p):sha256_file(p) for p in paths},
        protected_outcomes_used=False,frozen_forecast_changed=False,deployment_approved=False))
    print('Review complete; candidate unchanged.',flush=True)


if __name__=='__main__':
    {'audit':audit,'finalize':finalize}[sys.argv[1]]()
