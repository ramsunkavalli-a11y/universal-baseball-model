"""Independent V17 feature units, saved logits, margins, native value and scores."""
from collections import Counter, defaultdict
import json

import numpy as np
import polars as pl

from run_defense_assignments_v17 import OUT, OLD, ARMS, ROLES, read, write, check, verify


def close(a,b):
    assert np.allclose(a,b,atol=1e-7,rtol=0,equal_nan=True),(a,b)


def main():
    pre=check(); note=read(OUT/'fit-report.json'); verify(note['hashes'])
    assert not (OUT/'independent-verification.json').exists()
    f=pl.read_parquet(OUT/'features.parquet'); features={r['row_id']:r for r in f.to_dicts()}
    lineage=pl.read_parquet(OUT/'feature-lineage.parquet').to_dicts()
    # Replay counts and missing flags without calling the feature constructor.
    for l in lineage:
        r=features[l['row_id']]; dh=r['origin_dh_outs']; year=r['origin_year']
        assert all(h['season']<year and h['player_id']==r['player_id'] for h in l['older_history'])
        for sport,record in l['current_by_sport'].items():
            counts=np.zeros(9)
            for p in l['source_current_row']['current_role_periods']:
                assert p['season']==year and p['player_id']==r['player_id']
                if str(p['sport_id'])!=sport or p['position_code']==1:
                    continue
                j=ROLES.index(p['position_code'])
                if p['position_code']==10 and record['DH_known']:
                    counts[j]+=p['reviewed_starts']
                elif p['position_code']!=10 and record['field_known']:
                    counts[j]+=p['fielding_outs']/dh
            close(counts,record['counts'])
            close(np.log1p(counts)/np.log(163),[r[f'current_s{sport}_r{p}'] for p in ROLES])
            assert r[f'current_s{sport}_field_known']==record['field_known']
            assert r[f'current_s{sport}_DH_known']==record['DH_known']
        current=np.sum([p['counts'] for p in l['current_by_sport'].values()],axis=0)
        close(current,l['current_counts'])
        assert r['assignment_current_role']==(ROLES[int(current.argmax())] if current.sum() else 0)
        for scope in ('MLB','minor'):
            hist=[h for h in l['older_history'] if h['is_mlb']==(scope=='MLB')]
            total=np.zeros(9)
            for h in hist:
                total+=np.array([h[f'outs_{p}']/dh for p in ROLES[:-1]]+[h['starts_10']])
            close((total>0).astype(float),[r[f'{scope}_older_seen_r{p}'] for p in ROLES])
            assert r[f'{scope}_older_history_known']==bool(hist)
            for lag in (1,2):
                past=[h for h in hist if h['season']==year-lag]; counts=np.zeros(9)
                for h in past:
                    counts+=np.array([h[f'outs_{p}']/dh for p in ROLES[:-1]]+[h['starts_10']])
                close(np.log1p(counts)/np.log(163),[r[f'{scope}_lag{lag}_r{p}'] for p in ROLES])
                assert r[f'{scope}_lag{lag}_known']==bool(past)
            for label,key in [('late','August_onward_minimum'),('unplaced','unresolved_period_exposure')]:
                counts=np.zeros(9); b=l['certified_period_bounds']
                if b[scope+'_fielding_outs'] is not None:
                    counts[:8]=np.array(b[scope+'_fielding_outs'][key][:8])/dh
                if b[scope+'_reviewed_starts'] is not None:
                    counts[8]=b[scope+'_reviewed_starts'][key][8]
                close(np.log1p(counts)/np.log(163),[r[f'{scope}_{label}_r{p}'] for p in ROLES])
        assert r['age_unknown']==(r['age'] is None)
        close(r['age_centered'],(r['age']-27)/10 if r['age'] is not None else 0)
    pred=pl.read_parquet(OUT/'predictions.parquet').to_dicts()
    lookup={r['row_id']:r for r in pred}
    old={r['row_id']:r for r in pl.read_parquet(OLD/'predictions.parquet').to_dicts()}
    supports={r['row_id']:r for r in pl.read_parquet(OUT/'profile-support.parquet').to_dicts()}
    models=[]
    for entry in note['models']:
        from pathlib import Path
        assert __import__('universal_baseball.storage',fromlist=['sha256_file']).sha256_file(Path(entry['path']))==entry['sha256']
        m=read(Path(entry['path'])); tr=[features[i] for i in m['training_row_ids']]
        test=[lookup[i] for i in m['test_row_ids']]
        assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in test)
        assert all(r['target_year']<=m['origin'] and r['target_year']>=2022 and r['outer_fold']!=m['fold'] for r in tr)
        b=np.array(m['coefficients']); names=m['features']
        x=np.column_stack([np.ones(len(tr)),[[r[n] for n in names] for r in tr]])
        target=np.array([r['actual_job_vector'] for r in tr]); target/=target.sum(axis=1,keepdims=True)
        count=Counter(r['player_id'] for r in tr); w=np.array([1/count[r['player_id']] for r in tr])
        z=x@b; z-=z.max(axis=1,keepdims=True); p=np.exp(z); p/=p.sum(axis=1,keepdims=True)
        loss=-np.sum(w[:,None]*target*np.log(p))+.5*np.sum(b[1:]**2)
        grad=x.T@((p-target)*w[:,None]); grad[1:]+=b[1:]
        close(loss,m['objective']); close(abs(grad).max(),m['max_gradient']); close(w.sum(),m['training_people'])
        tx=np.column_stack([np.ones(len(test)),[[r[n] for n in names] for r in test]])
        z=tx@b; z-=z.max(axis=1,keepdims=True); learned=np.exp(z); learned/=learned.sum(axis=1,keepdims=True)
        for r,p in zip(test,learned):
            close(p,r['assignment_learned_shares'])
            s=supports[r['row_id']]
            matching={t['player_id'] for t in tr if t['stage']==r['stage'] and t['assignment_current_role']==r['assignment_current_role']}
            assert len(matching)==s['stage_role_people'] and (len(matching)==0)==r['assignment_unseen_fallback']
            allowed=np.array(r['assignment_fallback'] if not matching else p)
            if not r['job_catching_evidence']:
                allowed[0]=0
            allowed=np.zeros(9) if r['job_unknown'] else allowed/allowed.sum()
            close(allowed,r['assignment_allowed_shares'])
            for j,pos in enumerate(ROLES):
                close(r[f'seed_{pos}']*(r['origin_dh_outs'] if pos==10 else 1),r['job_total']*allowed[j])
        models.append(dict(origin=m['origin'],fold=m['fold'],rows=len(tr),people=len(count),
            weight_sum=float(w.sum()),max_gradient=float(abs(grad).max()),held_people_disjoint=True))
    margins=[]
    for budget in note['budgets']:
        rows=sorted([r for r in pred if r['origin_year']==budget['origin']],key=lambda r:r['row_id'])
        s=np.array([[r[f'seed_{p}']*(r['origin_dh_outs'] if p==10 else 1) for p in ROLES] for r in rows])*budget['global_mass_factor']
        mass=s.sum(axis=1); weights=s*np.exp(-np.array(budget['multipliers']))
        replay=np.divide(mass[:,None]*weights,weights.sum(axis=1,keepdims=True),out=np.zeros_like(s),where=weights.sum(axis=1,keepdims=True)>0)
        actual=np.array([[r[f'candidate_{p}']*(r['origin_dh_outs'] if p==10 else 1) for p in ROLES] for r in rows])
        close(replay,actual); close(mass,actual.sum(axis=1))
        assert (actual.sum(axis=0)<=np.array(budget['caps'])+.02).all()
        assert (actual[s==0]==0).all()
        for r in rows:
            baseline=np.array([old[r['row_id']][f'candidate_{p}']*(r['origin_dh_outs'] if p==10 else 1) for p in ROLES])
            close(baseline.sum(),sum(r[f'candidate_{p}']*(r['origin_dh_outs'] if p==10 else 1) for p in ROLES))
        margins.append(dict(origin=budget['origin'],rows=len(rows),fixed_old_row_masses=True,
            cap_excess=float(max(0.,max(actual.sum(axis=0)-budget['caps'])))))
    channel_rows=pl.read_parquet(OUT/'channel-predictions.parquet').to_dicts()
    oldchannels={(r['row_id'],r['channel']):r for r in pl.read_parquet(OLD/'channel-predictions.parquet').to_dicts()}
    byid=defaultdict(list)
    for c in channel_rows:
        o=oldchannels[c['row_id'],c['channel']]
        for key in ('history_quality','rate_unit','quality_evidence_observed','actual_runs','actual_official_exposure'):
            assert c[key]==o[key],(c['row_id'],key)
        close(c['baseline_runs'],o['candidate_runs']); close(c['reference_runs'],o['reference_runs'])
        byid[c['row_id']].append(c)
    rate={2:12.5,3:-12.5,4:2.5,5:2.5,6:7.5,7:-7.5,8:2.5,9:-7.5}
    conversions={}
    for r in pred:
        o=old[r['row_id']]
        for key in ('preseason_pa','batting_forecast','job_total','job_unknown_mass','actual_defense','actual_expanded','actual_position_runs'):
            assert r[key]==o[key]
        key=(r['origin_year'],r['outer_fold'])
        if key not in conversions:
            conversions[key]=read(OLD/f'model-{key[0]}-{key[1]}.json')['native_conversions']
        conv=conversions[key]
        for arm in ARMS:
            total=0.; framing=0.
            for c in byid[r['row_id']]:
                name=c['channel']
                if name.startswith('range_'):
                    exposure=r[f'{arm}_{name[-1]}']
                else:
                    outs=r[f'{arm}_2'] if name in ('framing','throwing','blocking') else r[f'{arm}_3'] if name=='receiving' else sum(r[f'{arm}_{p}'] for p in (7,8,9))
                    exposure=outs*conv[name]['rate']
                runs=exposure*c['history_quality']/c['rate_unit']
                close(runs,c[arm+'_runs']); total+=runs
                if name=='framing':
                    framing=runs
            pos=sum(r[f'{arm}_{p}']*v/4374 for p,v in rate.items())-r[f'{arm}_10']*17.5/162
            close([total,pos,r['batting_forecast']+(pos+total)/10],
                [r[arm+'_defense'],r[arm+'_position_runs'],r[arm+'_expanded']])
            close(r[arm+'_no_framing'],r[arm+'_expanded']-framing/10)
    count=0
    for target,scopes in read(OUT/'report.json')['metrics'].items():
        for scope,entry in scopes.items():
            for m in entry['per_origin']:
                rs=[r for r in pred if r['origin_year']==m['origin'] and r['actual_'+target] is not None and
                    (scope!='actual_defenders' or r['actual_fielding_outs']>0) and
                    (scope!='known_quality' or r['known_quality_channels']>0)]
                p=np.array([r[m['arm']] for r in rs]); t=np.array([r['actual_'+target] for r in rs]); e=p-t
                close([np.sqrt(np.mean(e*e)),np.mean(abs(e)),e.mean(),p.sum(),t.sum()],
                    [m['rmse'],m['mae'],m['bias'],m['predicted_total'],m['actual_total']]); count+=1
    write('independent-verification.json',dict(status='passed',feature_rows=len(lineage),forecasts=len(pred),
        channel_rows=len(channel_rows),models=models,budgets=margins,metric_rows=count,
        no_2026_outcomes=True,no_deployment=True,player_walkthrough_status='pending'))
    print(json.dumps(dict(status='independent_arithmetic_passed',features=len(lineage),forecasts=len(pred),metrics=count)),flush=True)


if __name__=='__main__':
    main()
