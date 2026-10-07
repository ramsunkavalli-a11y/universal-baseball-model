"""Compact readback of every saved source/mechanics/reality player trace."""
import argparse
import json
import numpy as np
from run_defense_assignments_v17 import OUT, ROLES, read


def rounded(v):
    return None if v is None else round(float(v),3)


def main(start,end):
    cases=read(OUT/'player-walkthrough.json')['cases']
    for i,case in enumerate(cases[start:end],start):
        print(json.dumps(dict(case=i,selection=case['selection'],peer_rule=case['peer_rule'])))
        for r in case['records']:
            l=r['source']; feature=r['feature_vector']; p=np.array(r['allowed_shares'])
            dominant=int(p.argmax()); competitor=int(np.argsort(-p)[1])
            terms=[]
            for t in r['role_logit_terms']:
                v=t['role_logit_terms']; d=v[dominant]-v[competitor]
                if d:
                    terms.append([t['feature'],rounded(t['input']),rounded(d)])
            recent=[]
            for h in l['older_history']:
                if h['season']>=r['origin']-2:
                    recent.append([h['season'],h['normalized_level'],
                        {str(p):h['outs_'+str(p)] for p in ROLES[:-1] if h['outs_'+str(p)]},h['starts_10']])
            arms={a:dict(outs=[rounded(v) for v in v['field_outs']],DH=rounded(v['DH_starts']),
                pos=rounded(v['position_runs']),defense=rounded(v['defense_runs']),value=rounded(v['expanded']))
                for a,v in r['arms'].items() if a in ('baseline','candidate')}
            actual=r['actual']
            skill=[[q['channel'],rounded(q['history_quality']),q['rate_unit'],rounded(q['actual_runs'])]
                for q in r['native_quality_fixed'] if q['quality_evidence_observed']]
            print(json.dumps(dict(name=r['name'],origin=r['origin'],age=r['age'],stage=r['stage'],
                expected_actual_PA=[rounded(r['expected_PA_fixed']),r['actual_PA']],
                current={s:[rounded(v) for v in c['counts']] for s,c in l['current_by_sport'].items()
                    if sum(c['counts'])},recent=recent,
                late={k:rounded(v) for k,v in feature.items() if '_late_r' in k and v},
                unplaced={k:rounded(v) for k,v in feature.items() if '_unplaced_r' in k and v},
                older_seen=[k for k,v in feature.items() if '_older_seen_' in k and v],
                support=[r['support']['joint_people'],r['support']['stage_role_people']],
                fallback=r['used_fallback'],logit_contrast=[ROLES[dominant],ROLES[competitor]],
                largest_logit_terms=sorted(terms,key=lambda t:-abs(t[2]))[:4],
                shares=[rounded(v) for v in r['allowed_shares']],arms=arms,
                actual=dict(outs=actual['field_outs'],DH=actual['DH_starts'],pos=rounded(actual['position_runs']),
                    defense=rounded(actual['defense_runs']),value=rounded(actual['expanded'])),
                measured_skill=skill,judgments=r['baseball_judgments'])))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('start',type=int);p.add_argument('end',type=int)
    args=p.parse_args();main(args.start,args.end)
