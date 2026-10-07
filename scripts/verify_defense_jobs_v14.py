"""Independent group sums, saved dual replay, fixed-value and metric arithmetic."""

from collections import defaultdict
import json

import numpy as np
import polars as pl

from run_defense_jobs_v14 import OUT, OLD, VALUE, ARMS, ROLES, read, write, check, verify


def close(a,b):assert np.allclose(a,b,rtol=0,atol=1e-7,equal_nan=True),(a,b)


def main():
    check();note=read(OUT/'fit-report.json');verify(note['hashes'])
    assert not (OUT/'independent-verification.json').exists()
    f=pl.read_parquet(OUT/'features.parquet');rows={r['row_id']:r for r in f.to_dicts()}
    q=pl.read_parquet(OUT/'predictions.parquet');pred=q.to_dicts()
    channels=pl.read_parquet(OUT/'channel-predictions.parquet')
    oldchannels={(r['row_id'],r['channel']):r for r in pl.read_parquet(VALUE/'channel-predictions.parquet').to_dicts()}
    tables_count=0;group_checks=[]
    for entry in note['models']:
        model=read(__import__('pathlib').Path(entry['path']))
        for kind,ids,groups in [('joint',model['training_row_ids'],model['tables']),
                               ('reference',model['reference_training_row_ids'],model['reference_tables'])]:
            tr=[rows[i] for i in ids]
            assert all(r['target_year']<=model['origin'] and r['outer_fold']!=model['fold'] for r in tr)
            for c in groups:
                key=c['key'];selected=[]
                for r in tr:
                    if kind=='joint':
                        role,fam,status=str(r['job_primary_role']),r['job_family'],r['job_status']
                        if key[0].startswith('role') and role!=key[1]:continue
                        if key[0].startswith('family') and fam!=key[1]:continue
                        if key[0].endswith('_status') and status!=key[2]:continue
                    else:
                        if key[0].startswith('role') and str(r['repertoire_primary_role'])!=key[1]:continue
                        if key[0].startswith('family') and r['repertoire_family']!=key[1]:continue
                        if key[0].endswith('_stage') and r['stage']!=key[2]:continue
                    selected.append(r)
                assert c['people']==len({r['player_id'] for r in selected}) and c['rows']==len(selected)
                if kind=='joint':
                    num=np.sum([r['actual_job_vector'] for r in selected],axis=0) if selected else np.zeros(9)
                    close(num,c['numerators']);close(num.sum(),c['denominator_job_time'])
                    if num.sum():close(num/num.sum(),c['shares'])
                    assert all(r['target_year']>=2022 for r in selected)
                else:
                    den=sum(r['next_pa'] for r in selected)
                    outs=sum(sum(r[f'actual_{p}'] for p in ROLES[:-1]) for r in selected)
                    dh=sum(r['actual_10'] for r in selected)
                    close([den,outs,dh],[c['denominator_PA'],c['numerator_outs'],c['numerator_DH_starts']])
                tables_count+=1
        group_checks.append(dict(origin=model['origin'],fold=model['fold'],player_disjoint=True,
                                 same_policy_training_targets=sorted({rows[i]['target_year'] for i in model['training_row_ids']})))
    budgets=[]
    for budget in note['budgets']:
        year=budget['origin'];selected=sorted([r for r in pred if r['origin_year']==year],key=lambda r:r['row_id'])
        seed=np.array([[r[f'joint_{p}']*(r['origin_dh_outs'] if p==10 else 1.) for p in ROLES] for r in selected])
        actual=np.array([[r[f'candidate_{p}']*(r['origin_dh_outs'] if p==10 else 1.) for p in ROLES] for r in selected])
        seed*=budget['global_mass_factor'];mass=seed.sum(axis=1)
        weights=seed*np.exp(-np.array(budget['multipliers']))
        den=weights.sum(axis=1)
        replay=np.divide(mass[:,None]*weights,den[:,None],out=np.zeros_like(weights),where=den[:,None]>0)
        close(replay,actual);close(actual.sum(axis=1),mass)
        caps=np.array(budget['caps']);col=actual.sum(axis=0)
        assert (col<=caps+.02).all() and (actual[seed==0]==0).all()
        close(caps,np.array(budget['full_capacity'])-budget['outside_reserve']-budget['unknown_per_position'])
        close(budget['unknown_role_reserve'],sum(r['job_unknown_mass'] for r in selected))
        close(col,budget['allocated_column_totals'])
        for r in selected:
            if not r['job_catching_evidence']:assert r['candidate_2']==r['joint_2']==0
            if r['job_unknown']:assert all(r[f'candidate_{p}']==0 for p in ROLES)
        budgets.append(dict(origin=year,rows=len(selected),max_cap_excess=float(max(0.,max(col-caps))),
                            structural_zeros_preserved=True,row_margins_replayed=True))
    byid=defaultdict(list)
    for c in channels.to_dicts():
        old=oldchannels[c['row_id'],c['channel']]
        for key in ('history_quality','rate_unit','quality_evidence_observed','actual_runs','actual_official_exposure'):
            assert c[key]==old[key],(key,c['row_id'])
        byid[c['row_id']].append(c)
    rate={2:12.5,3:-12.5,4:2.5,5:2.5,6:7.5,7:-7.5,8:2.5,9:-7.5}
    for r in pred:
        conv=read(OLD/f"model-{r['origin_year']}-{r['outer_fold']}.json")['native_conversions']
        for arm in ARMS:
            total=0.;frame=0.
            for c in byid[r['row_id']]:
                name=c['channel']
                if name.startswith('range_'):n=r[f'{arm}_{name[-1]}']
                else:
                    outs=r[f'{arm}_2'] if name in ('framing','throwing','blocking') else r[f'{arm}_3'] if name=='receiving' else sum(r[f'{arm}_{p}'] for p in (7,8,9))
                    n=outs*conv[name]['rate']
                value=n*c['history_quality']/c['rate_unit']
                close(value,c[arm+'_runs']);total+=value
                if name=='framing':frame=value
            pos=sum(r[f'{arm}_{p}']*v/4374 for p,v in rate.items())-r[f'{arm}_10']*17.5/162
            close([total,pos,r['batting_forecast']+(total+pos)/10],
                  [r[arm+'_defense'],r[arm+'_position_runs'],r[arm+'_expanded']])
            close(r[arm+'_no_framing'],r[arm+'_expanded']-frame/10)
        actualpos=sum(r[f'actual_{p}']*v/4374 for p,v in rate.items())-r['actual_10']*17.5/162
        close(actualpos,r['actual_position_runs'])
    metrics=read(OUT/'report.json')['metrics'];metric_checks=0
    for target,scopes in metrics.items():
        for scope,entry in scopes.items():
            selected=[r for r in pred if r['actual_'+target] is not None and
                      (scope!='actual_defenders' or r['actual_fielding_outs']>0) and
                      (scope!='known_quality' or r['known_quality_channels']>0)]
            for m in entry['per_origin']:
                rs=[r for r in selected if r['origin_year']==m['origin']]
                x=np.array([r[m['arm']] for r in rs]);t=np.array([r['actual_'+target] for r in rs]);e=x-t
                close([np.sqrt(np.mean(e*e)),np.mean(abs(e)),e.mean(),x.sum(),t.sum()],
                      [m['rmse'],m['mae'],m['bias'],m['predicted_total'],m['actual_total']]);metric_checks+=1
    write('independent-verification.json',dict(status='passed',forecasts=len(pred),channel_rows=len(channels),
        group_tables_recomputed=tables_count,chronological_folds=group_checks,allocation_budgets=budgets,
        fixed_quality_and_native_arithmetic_rows=len(channels),metric_rows_recomputed=metric_checks,
        no_2026_outcomes=True,no_deployment=True,walkthrough_required=True))
    print(json.dumps(dict(status='independent_replay_passed',forecasts=len(pred),tables=tables_count,metrics=metric_checks)))


if __name__=='__main__':main()
