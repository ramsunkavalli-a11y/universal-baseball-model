"""Fixed and outcome-selected diagnostics, source-to-logit-to-value peer walks."""
from collections import defaultdict
import json

import numpy as np
import polars as pl

from run_defense_assignments_v17 import ROOT, OUT, PUBLIC, VALUE, ARMS, ROLES, read, write, check


def main():
    check(); assert not (OUT/'player-walkthrough.json').exists()
    assert read(OUT/'independent-verification.json')['status']=='passed'
    f=pl.read_parquet(OUT/'predictions.parquet'); rows=f.to_dicts()
    lookup={(r['player_id'],r['origin_year']):r for r in rows}
    lineage={r['row_id']:r for r in pl.read_parquet(OUT/'feature-lineage.parquet').to_dicts()}
    supports={r['row_id']:r for r in pl.read_parquet(OUT/'profile-support.parquet').to_dicts()}
    qc=defaultdict(list)
    for c in pl.read_parquet(VALUE/'channel-predictions.parquet').to_dicts():
        qc[c['row_id']].append(c)
    prior=read(ROOT/'reports/generated/defense-role-v15/player-walkthrough.json')['cases']
    cases={}; reasons=defaultdict(list)
    for case in prior:
        focal=case['records'][0]; key=(focal['player_id'],focal['origin'])
        cases[key]=[(r['player_id'],r['origin']) for r in case['records']]
        reasons[key].append('fixed_previous_focal_and_three_peers')
    measured=[r for r in rows if r['actual_expanded'] is not None]
    defenders=[r for r in measured if r['actual_fielding_outs']>0]
    gain=lambda r:(r['baseline_expanded']-r['actual_expanded'])**2-(r['candidate_expanded']-r['actual_expanded'])**2
    dgain=lambda r:(r['baseline_defense']-r['actual_defense'])**2-(r['candidate_defense']-r['actual_defense'])**2
    error=lambda r:r['candidate_expanded']-r['actual_expanded']
    choices=[(max(measured,key=gain),'largest_expanded_gain'),(min(measured,key=gain),'largest_expanded_harm'),
        (max(measured,key=error),'largest_false_high'),(min(measured,key=error),'largest_false_low'),
        (max(defenders,key=dgain),'largest_native_defense_gain'),(min(defenders,key=dgain),'largest_native_defense_harm'),
        (min(defenders,key=lambda r:abs(error(r))),'ordinary_defender')]
    peer_rule='Same origin/stage/current observed dominant role, nearest age/5 + current PA/600 + current minor outs/4374; ID tiebreak; no future outcomes.'
    for r,why in choices:
        key=(r['player_id'],r['origin_year']); reasons[key].append(why)
        if key not in cases:
            pool=[p for p in rows if p['origin_year']==r['origin_year'] and p['player_id']!=r['player_id'] and
                  p['stage']==r['stage'] and p['assignment_current_role']==r['assignment_current_role']]
            def distance(p):
                age=abs(p['age']-r['age'])/5 if p['age'] is not None and r['age'] is not None else 5
                return (age+abs(p['pa_0']-r['pa_0'])/600+
                    abs(p['minor_current_defensive_outs']-r['minor_current_defensive_outs'])/4374,p['player_id'])
            cases[key]=[key,*[(p['player_id'],p['origin_year']) for p in sorted(pool,key=distance)[:3]]]
    models={}
    def record(r):
        key=(r['origin_year'],r['outer_fold'])
        if key not in models:
            models[key]=read(OUT/f'model-{key[0]}-{key[1]}.json')
        m=models[key]; names=m['features']; b=np.array(m['coefficients'])
        x=np.array([1.,*[r[n] for n in names]])
        terms=x[:,None]*b; logits=terms.sum(axis=0)
        p=np.exp(logits-logits.max()); p/=p.sum()
        assert np.allclose(p,r['assignment_learned_shares'],atol=1e-12,rtol=0)
        contributions=[dict(feature=n,input=float(v),role_logit_terms=t.tolist())
            for n,v,t in zip(['intercept',*names],x,terms)]
        arms={a:dict(field_outs=[r[f'{a}_{p}'] for p in ROLES[:-1]],DH_starts=r[f'{a}_10'],
            position_runs=r[a+'_position_runs'],defense_runs=r[a+'_defense'],expanded=r[a+'_expanded'],
            no_framing=r[a+'_no_framing']) for a in ARMS}
        judgments=[]
        s=supports[r['row_id']]
        if s['sparse_joint']:
            judgments.append(f"Only {s['joint_people']} distinct training people match the detailed role/age/sample/coverage profile.")
        if s['unseen_stage_role']:
            judgments.append('Unseen stage/current-role profile uses only own current/older/roster fallback, not learned allocation.')
        if r['job_unknown']:
            judgments.append('Unknown role mass remains reserved; no invented defensive assignment/value.')
        if not r['job_catching_evidence']:
            judgments.append('Existing origin-catching guard sets C share to zero; other role shares are not mechanically forbidden.')
        if r['next_pa']==0:
            judgments.append('No MLB play is zero delivered contribution, not zero defensive talent.')
        unknown=sum(not c['quality_evidence_observed'] for c in qc[r['row_id']])
        if unknown:
            judgments.append(f'{unknown} of twelve skill channels have no own measured quality; neutral fallback is not proof of average talent.')
        if r['actual_expanded'] is None:
            judgments.append('Partial native target remains unscored as a complete value label.')
        elif abs(error(r))<abs(r['baseline_expanded']-r['actual_expanded']):
            if any(abs(r['candidate_'+n]-r['actual_'+n])>abs(r['baseline_'+n]-r['actual_'+n]) for n in ('position_runs','defense')):
                judgments.append('Expanded value improves despite a worse component error; inspect cancellation, not a clean defense gain.')
        elif abs(error(r))>abs(r['baseline_expanded']-r['actual_expanded']):
            judgments.append('Candidate worsens expanded value for this case; the harm stays in the review.')
        l=lineage[r['row_id']]
        return dict(player_id=r['player_id'],name=r['player_name'],origin=r['origin_year'],target=r['target_year'],
            fold=r['outer_fold'],row_id=r['row_id'],age=r['age'],stage=r['stage'],source_position=r['source_position'],
            source=l,feature_vector={n:r[n] for n in names},role_logit_terms=contributions,
            support=s,learned_shares=r['assignment_learned_shares'],allowed_shares=r['assignment_allowed_shares'],
            fallback_kind=r['assignment_fallback_kind'],used_fallback=r['assignment_unseen_fallback'],
            expected_PA_fixed=r['preseason_pa'],actual_PA=r['next_pa'],batting_fixed=r['batting_forecast'],
            job_mass_fixed=r['job_total'],unknown_mass_fixed=r['job_unknown_mass'],
            cap_multipliers=r['candidate_column_multipliers'],global_job_factor=r['candidate_global_job_factor'],
            native_quality_fixed=qc[r['row_id']],arms=arms,
            actual=dict(field_outs=[r[f'actual_{p}'] for p in ROLES[:-1]],DH_starts=r['actual_10'],
                position_runs=r['actual_position_runs'],defense_runs=r['actual_defense'],expanded=r['actual_expanded']),
            baseball_judgments=judgments)
    evidence=[]; lines=['# Position assignment comparison player review','',
        'Current position use and older experience feed one role model. Playing time, batting and defensive quality are fixed.',
        'This is a 2023 to 2025 delivery comparison, not proof of minor league defensive talent or full WAR.',
        'Prepared arithmetic traces require the main review before disposition.','']
    for key,people in cases.items():
        records=[record(lookup[p]) for p in people]
        evidence.append(dict(selection=reasons[key],peer_rule='Preserved original peer identities' if 'fixed_previous_focal_and_three_peers' in reasons[key] else peer_rule,
            peer_shortfall=4-len(records),records=records))
        lines += ['## '+records[0]['name']+' '+str(key[1]),'', 'Selection: '+', '.join(reasons[key])+'.','']
        for w in records:
            a=w['arms']; t=w['actual']; l=w['source']; fmt=lambda v:'unknown' if v is None else f'{v:.4f}'
            lines += [w['name']+f" age {w['age']}, {w['stage']}; expected/actual PA {w['expected_PA_fixed']:.1f}/{w['actual_PA']:.1f}.",
                f"Current starts-equivalent by sport: {json.dumps(l['current_by_sport'])}",
                f"Pre-origin own exposure: {l['older_counts']}; fixed job mass {w['job_mass_fixed']:.3f}; unknown reserve {w['unknown_mass_fixed']:.3f}.",
                f"Support joint {w['support']['joint_people']}, stage/current-role {w['support']['stage_role_people']}; fallback used {w['used_fallback']}.",
                f"Learned shares {w['learned_shares']}; allowed shares {w['allowed_shares']}; cap multipliers {w['cap_multipliers']}."]
            for arm in ARMS:
                lines.append(f"{arm}: outs {a[arm]['field_outs']}, DH {a[arm]['DH_starts']:.3f}; position {a[arm]['position_runs']:.4f}, defense {a[arm]['defense_runs']:.4f} runs; expanded {a[arm]['expanded']:.6f}.")
            lines += [f"Actual: outs {t['field_outs']}, DH {t['DH_starts']}; position {fmt(t['position_runs'])}, defense {fmt(t['defense_runs'])} runs; expanded {fmt(t['expanded'])}.",
                ' '.join(w['baseball_judgments']),'']
    write('player-walkthrough.json',dict(player_walkthrough_status='pending_main_read',cases=evidence,
        focal_cases=len(evidence),records=sum(len(c['records']) for c in evidence),
        preserved_focal_cases=len(prior),peer_rule=peer_rule,no_future_information_in_peer_selection=True,
        no_2026_outcomes=True,no_deployment=True))
    for dest in (OUT,PUBLIC):
        path=dest/'player-walkthrough.md'; assert not path.exists()
        path.write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(dict(status='prepared_pending_main_read',cases=len(evidence),records=sum(len(c['records']) for c in evidence))),flush=True)


if __name__=='__main__':
    main()
