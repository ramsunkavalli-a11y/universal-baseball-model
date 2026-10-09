"""Join reviewed role, native skill and supported minor profile evidence."""
from collections import defaultdict,Counter
from pathlib import Path
import gzip,json
import numpy as np
import polars as pl
from universal_baseball.hitter_defense_rates_v1 import DefenseRates
from universal_baseball.defense_reference_history import origin_reference
from universal_baseball.minor_range_talent import design,ridge_predict
from universal_baseball import hitter_role_fallback_v1 as role_model
from universal_baseball.defense_repertoire import ROLES
from universal_baseball.defense_opportunity_bridge import native_from_outs
from universal_baseball.storage import sha256_file
from capture_hitter_2027_origin_counts import ROOT,write_once
from assemble_hitter_2027_defense_rates import NEW
from run_defense_jobs_v14 import inputs

OUT=ROOT/'reports/generated/hitter-2027-base'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'


def main():
    assert not (PUBLIC/'defensive-contribution-assembly.json').exists()
    paths=[]
    def read(p):paths.append(p);return pl.read_parquet(p)
    fore=read(ROOT/'reports/generated/hitter-2027-batting-refresh/forecast.parquet')
    players={r['player_id']:r for r in fore.to_dicts()}
    roles=read(OUT/'role-opportunities.parquet').to_dicts()
    bios={r['player_id']:r for r in read(ROOT/'reports/generated/hitter-2027-membership-source/bios.parquet').to_dicts()}
    annual=read(ROOT/'reports/generated/hitter-2027-position-source/annual-usage-reviewed.parquet')
    _,_,hist=inputs()
    for r in annual.to_dicts():hist[r['player_id']].append(r)
    production=json.loads((PUBLIC/'role-production-review.json').read_text())
    fixes=[];dh=129239/4858
    for r in roles:
        if not r['evidence']['unknown']:continue
        pid=r['player_id'];code=str(bios.get(pid,{}).get('position_code'))
        if code not in {str(p) for p in ROLES}:continue
        q=players[pid].copy();q.update(source_position=code,preseason_pa=q['expected_pa'])
        q.update(role_model.evidence(q,hist[pid],dh));assert not q['unknown']
        m=next(m for m in production['models'] if m['fold']==q['outer_fold'])
        tables={tuple(c['key']):c for c in m['tables']}
        p=role_model.predict(q,tables,dh);nat=native_from_outs(p['values'],m['native_conversions'])
        before=r.copy()
        r.update(source_position=code,**{f'outs_{pos}':v for pos,v in zip(ROLES[:-1],p['values'][:-1])},DH_starts=p['values'][-1],
                 **{f'native_{c}':v for c,v in nat.items()},calculation=p,
                 evidence={k:q[k] for k in ['role_shares','role','family','current_vector','fallback_vector','fallback_sources','reliability','unknown']},
                 capacity_warning=p['job_budget']>r['expected_capacity']+1e-8)
        fixes.append(dict(player_id=pid,name=r['player_name'],biography_position=code,previous=before,completed=r))
    role_by={r['player_id']:r for r in roles}
    source_paths=dict(native=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet',
        framing=ROOT/'reports/generated/catcher-native-opportunity-v3/modern/framing-annual.parquet',
        catcher=ROOT/'reports/generated/catcher-throw-block-v5/extension-annual.parquet',
        other=ROOT/'reports/generated/arm-receiving-v6/official-scope/annual.parquet')
    additions=dict(native=[NEW/'component-ledger.parquet'],framing=[NEW/'framing-annual.parquet'],
        catcher=[NEW/'catcher-opportunities.parquet'],other=[NEW/'arm-official-scope-annual.parquet',NEW/'receiving-native-annual.parquet'])
    data={k:read(p).to_dicts() for k,p in source_paths.items()}
    for k,pp in additions.items():
        for p in pp:data[k].extend(read(p).to_dicts())
    model=DefenseRates(origin=2026,native=data['native'],framing=data['framing'],catcher=data['catcher'],arm_receiving=data['other'])
    fitpath=ROOT/'reports/model-evidence/defense-minor-range-v19/fit-report.json.gz';paths.append(fitpath)
    fits=json.loads(gzip.decompress(fitpath.read_bytes()))['cells']
    cells={c['outer_fold']:c for c in fits if c['kind']=='outer' and c['cutoff']==2022}
    minor=defaultdict(list)
    for r in annual.filter(~pl.col('is_mlb')).to_dicts():minor[r['player_id']].append(r)
    profiles={};rates=[];decisions=Counter()
    for pid,q in players.items():
        rr=model.player(pid);c=cells[pid%5];fit=c['fits']['baseline-10']
        any_mlb=any(r['range_valid'] and r['native_outs']>0 for r in model.by['native'][pid])
        for r in rr:
            detail=None;reason='existing_MLB_skill_or_nonrange'
            if r['component']=='range' and not any_mlb:
                pos=int(r['context']);parts=[s for s in minor[pid] if s[f'outs_{pos}']>0]
                if parts:
                    bylevel=defaultdict(float)
                    for s in parts:bylevel[s['normalized_level']]+=s[f'outs_{pos}']
                    level=max(bylevel,key=lambda k:(bylevel[k],k))
                    sample=dict(age=None if q['age_unknown'] else q['age'],minor_outs=sum(bylevel.values()),position=pos,level=level)
                    x=design([sample],np.zeros((1,4)),c['age_median'],False)
                    outside=(x[0]<np.array(fit['training_min'])-1e-10)|(x[0]>np.array(fit['training_max'])+1e-10)
                    support=bool(c['fit_supported']) and not outside.any()
                    native=float(ridge_predict(fit,x)[0]);center=origin_reference(2026,pos,pid%5,model.references)
                    terms=(x[0]-np.array(fit['mean']))/np.array(fit['scale'])*np.array(fit['coefficients'])
                    assert np.isclose(native,fit['target_mean']+sum(terms))
                    detail=dict(input=sample,native_grade=native,position_reference=center,supported=bool(support),
                        unsupported_fields=[n for n,v in zip(fit['names'],outside) if v],training_people=c['training_people'],
                        coefficients=dict(zip(fit['names'],terms.tolist())),intercept=fit['target_mean'],source_rows=parts)
                    reason='supported_minor_profile' if support else 'out_of_support_position_prior'
                    if support:
                        r.update(runs_per_unit=native-center,evidence_tier='translated_profile',
                            estimator_id='minor_range_v19_selected_profile_qualified',general_minor_transfer_validated=False)
                else:reason='no_current_minor_position_measurement'
            decisions[reason]+=1
            if detail:profiles[pid,r['context']]=detail
            role=role_by[pid]
            n=role[f"outs_{r['context']}"] if r['component']=='range' else role['native_'+{'catcher_throwing':'throwing'}.get(r['component'],r['component'])]
            r.update(projected_opportunities=n,projected_runs=n*r['runs_per_unit']/r['rate_unit'],
                profile_decision=reason,role_unknown=role['evidence']['unknown'],role_capacity_warning=role['capacity_warning'],
                measured_individual_grade=r['individual_evidence_observed'])
            rates.append(r)
    assert len(rates)==4851*12
    base=json.loads(gzip.decompress((PUBLIC/'base-input-player-walks.json.gz').read_bytes()))['cases']
    ids={w['player_id'] for c in base for w in [c['primary'],*c['peers']]}
    profile_rates=[r for r in rates if r['evidence_tier']=='translated_profile']
    ids.update(r['player_id'] for r in sorted(profile_rates,key=lambda r:r['runs_per_unit'])[:3]+sorted(profile_rates,key=lambda r:r['runs_per_unit'])[-3:])
    ids.update(r['player_id'] for r in rates if r['role_capacity_warning'])
    by=defaultdict(list)
    for r in rates:by[r['player_id']].append(r)
    walks=[]
    for pid in sorted(ids):
        for r in by[pid]:assert np.isclose(r['projected_runs'],r['projected_opportunities']*r['runs_per_unit']/r['rate_unit'])
        walks.append(dict(player_id=pid,name=players[pid]['player_name'],role=role_by[pid],rates=by[pid],
            minor_profile_details={context:value for (p,context),value in profiles.items() if p==pid},
            current_source_histories={k:[s for s in vv if s['player_id']==pid and 2024<=s['season']<=2026] for k,vv in data.items()}))
    out=OUT/'defensive-contributions.parquet';assert not out.exists();pl.DataFrame(rates,infer_schema_length=None).write_parquet(out)
    rp=OUT/'role-opportunities-reviewed.parquet';assert not rp.exists();pl.DataFrame(roles,infer_schema_length=None).write_parquet(rp)
    walk=PUBLIC/'defensive-contribution-player-walks.json.gz';assert not walk.exists();walk.write_bytes(gzip.compress(json.dumps(dict(cases=walks,roster_completions=fixes),allow_nan=False,default=str).encode(),mtime=0))
    paths.extend([Path(__file__),ROOT/'docs/hitter-2027-minor-profile-result.md',ROOT/'docs/hitter-2027-role-production-review.md'])
    write_once(PUBLIC/'defensive-contribution-assembly.json',dict(players=4851,rows=len(rates),roster_fallbacks_completed=len(fixes),
        remaining_unknown_roles=sum(r['evidence']['unknown'] for r in roles),
        remaining_unknown_role_PA=sum(r['expected_pa'] for r in roles if r['evidence']['unknown']),
        profile_decisions=dict(decisions),profile_estimates=len(profile_rates),new_fit=False,
        player_calculations_replayed=True,player_interpretation='pending_written_review',full_WAR=False,
        omitted_from_this_table=['double_play','non_OF_arm','ABS_challenge','GIDP','position','league','replacement','batting','running'],
        output_hashes={str(p):sha256_file(p) for p in [out,rp,walk]},input_hashes={str(p):sha256_file(p) for p in paths}))
    for pid in [804944,805811,808393,592450,665487,660271,672275,596019]:
        print(players[pid]['player_name'],[(r['component'],r['context'],round(r['projected_runs'],3),r['evidence_tier']) for r in by[pid] if r['projected_opportunities']>0],flush=True)


if __name__=='__main__':main()
