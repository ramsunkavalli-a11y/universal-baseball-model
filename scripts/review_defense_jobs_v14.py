"""Trace fixed stress cases, gains/harms and origin-selected peers after scoring."""

from collections import defaultdict
import json

import numpy as np
import polars as pl

from run_defense_jobs_v14 import OUT, SOURCE, VALUE, OLD, DH, ARMS, ROLES, read, write, check, hashes

FIXED=[('Shohei Ohtani',2022),('Shohei Ohtani',2023),('Shohei Ohtani',2024),
       ('Kyle Schwarber',2023),('Yordan Alvarez',2024),('Bobby Witt Jr.',2024),
       ('Bryce Eldridge',2024),('Patrick Bailey',2024),('Cal Raleigh',2024),
       ('Ceddanne Rafaela',2024),('Jackson Chourio',2023),('Franmil Reyes',2022)]


def main():
    check();assert not (OUT/'player-walkthrough.json').exists()
    assert read(OUT/'independent-verification.json')['status']=='passed'
    rows=pl.read_parquet(OUT/'predictions.parquet').to_dicts();lookup={(r['player_id'],r['origin_year']):r for r in rows}
    selected=defaultdict(list);missing=[]
    for name,y in FIXED:
        matches=[r for r in rows if r['player_name']==name and r['origin_year']==y]
        if not matches:missing.append(dict(name=name,origin=y));continue
        assert len(matches)==1
        selected[matches[0]['player_id'],y].append('fixed_stress_case')
    measured=[r for r in rows if r['actual_expanded'] is not None]
    gain=lambda r:(r['reference_expanded']-r['actual_expanded'])**2-(r['candidate_expanded']-r['actual_expanded'])**2
    error=lambda r:r['candidate_expanded']-r['actual_expanded']
    d=[r for r in measured if r['actual_fielding_outs']>0]
    dg=lambda r:(r['reference_defense']-r['actual_defense'])**2-(r['candidate_defense']-r['actual_defense'])**2
    for r,why in [(max(measured,key=gain),'largest_expanded_gain'),(min(measured,key=gain),'largest_expanded_harm'),
                  (max(measured,key=error),'largest_false_high'),(min(measured,key=error),'largest_false_low'),
                  (max(d,key=dg),'largest_defense_gain'),(min(d,key=dg),'largest_defense_harm'),
                  (min(d,key=lambda r:abs(error(r))),'ordinary_defender')]:
        selected[r['player_id'],r['origin_year']].append(why)
    source=pl.read_parquet(SOURCE/'source.parquet');profiles=pl.read_parquet(OUT/'profile-support.parquet')
    qc=pl.read_parquet(VALUE/'channel-predictions.parquet');dh=pl.read_parquet(DH/'reviewed-DH-starts.parquet')
    evidence=[];lines=['# Position forecast player review','',
        'All comparisons keep hitting, expected PA and defensive skill fixed. Job constraints do not prove talent or predict injuries.','']
    def record(r):
        pid,y=r['player_id'],r['origin_year']
        hist=source.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y+1))
        fields=['season','level_group','normalized_level','position_abbreviation','fielding_outs','games_started','games_played','level_subtype_certified','team_usage_certified']
        annual=hist.group_by(['season','level_group','normalized_level','position_abbreviation','level_subtype_certified','team_usage_certified']).agg(
            pl.col('fielding_outs','games_started','games_played').sum()).sort('season','normalized_level','position_abbreviation')
        corrections=dh.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y+1)).to_dicts()
        c=qc.filter(pl.col('row_id')==r['row_id']).select('channel','history_quality','rate_unit','quality_evidence_observed',
             'quality_status','history_opportunities','actual_runs','actual_official_exposure','actual_native_opportunities').to_dicts()
        model=read(OUT/f"model-{y}-{r['outer_fold']}.json")
        prior=next((c for c in model['tables'] if json.dumps(c['key'])==r['job_prior_key']),None)
        ref=next(c for c in model['reference_tables'] if json.dumps(c['key'])==r['reference_prior_key'])
        arms={a:dict(position_outs=[r[f'{a}_{p}'] for p in ROLES[:-1]],DH_starts=r[f'{a}_10'],
            position_runs=r[a+'_position_runs'],defense_runs=r[a+'_defense'],expanded_value=r[a+'_expanded'],no_framing=r[a+'_no_framing']) for a in ARMS}
        quality_unknown=sum(not c['quality_evidence_observed'] for c in c)
        judgments=[]
        if r['job_primary_role']==10:judgments.append('DH is explicitly represented; old minor/MLB field appearances do not define the whole current role.')
        if r['job_unknown']:judgments.append('Role remains unknown; no invented assignment or defensive value is awarded.')
        if quality_unknown:judgments.append(f'{quality_unknown} quality channels lack own observed evidence; numeric neutral fallback is not measured average ability.')
        if r['actual_expanded'] is None:judgments.append('Partial native target: whole expanded error is unknown; observed position/channel errors remain usable.')
        if r['next_pa']==0:judgments.append('No MLB contribution next year is an opportunity outcome, not proof of bad defensive talent.')
        if prior and prior['key'][0] in ('family','all','family_status'):judgments.append('Uses broad role fallback; not a demonstrated player-specific position-development forecast.')
        if r['job_weight']>.8:judgments.append('Strong own MLB role evidence dominates the joint seed; inspect whether the league cap nevertheless moves too much time.')
        if r['actual_expanded'] is not None:
            e0=arms['reference']['expanded_value']-r['actual_expanded'];e1=arms['candidate']['expanded_value']-r['actual_expanded']
            pd=abs(arms['candidate']['position_runs']-r['actual_position_runs'])-abs(arms['reference']['position_runs']-r['actual_position_runs'])
            dd=None if r['actual_defense'] is None else abs(arms['candidate']['defense_runs']-r['actual_defense'])-abs(arms['reference']['defense_runs']-r['actual_defense'])
            if abs(e1)<abs(e0) and (pd>0 or (dd is not None and dd>0)):judgments.append('Expanded error improves partly through component error cancellation; this is not a clean defense improvement.')
            if abs(e1)>abs(e0):judgments.append('Candidate increases expanded-value error for this player; retain the harm in the disposition.')
        return dict(player_id=pid,name=r['player_name'],row_id=r['row_id'],origin=y,target=y+1,fold=r['outer_fold'],
            source_position=r['source_position'],stage=r['stage'],age=r['age'],source_history=annual.to_dicts(),DH_source_corrections=corrections,
            origin_PA=[r[f'pa_{lag}'] for lag in range(3)],expected_PA=r['preseason_pa'],actual_PA=r['next_pa'],
            own_job_shares=r['job_own_shares'],learned_allowed_shares=r['job_learned_shares'],seed_shares=r['job_prediction_shares'],
            own_weight=r['job_weight'],evidence_kind=r['job_evidence_kind'],minor_fallback_season=r['job_minor_season'],
            role_prior=prior,reference_prior=ref,profile=profiles.filter(pl.col('row_id')==r['row_id']).to_dicts()[0],
            row_job_time=r['job_total'],unknown_job_time=r['job_unknown_mass'],origin_DH_job_conversion=r['origin_dh_outs'],
            capacity_multipliers=r['candidate_column_multipliers'],global_job_factor=r['candidate_global_job_factor'],
            batting_fixed=r['batting_forecast'],skill_channels=c,arms=arms,
            actual=dict(position_outs=[r[f'actual_{p}'] for p in ROLES[:-1]],DH_starts=r['actual_10'],raw_DH_starts=r['raw_actual_DH'],
                        position_runs=r['actual_position_runs'],defense_runs=r['actual_defense'],expanded_value=r['actual_expanded']),
            baseball_judgments=judgments)
    for key,reasons in selected.items():
        r=lookup[key]
        pool=[p for p in rows if p['origin_year']==r['origin_year'] and p['player_id']!=r['player_id'] and
              p['stage']==r['stage'] and p['job_primary_role']==r['job_primary_role']]
        def distance(p):
            age=abs(p['age']-r['age'])/5 if p['age'] is not None and r['age'] is not None else 5
            return (age+abs(p['pa_0']-r['pa_0'])/600+
                    np.abs(np.array(p['job_own_shares'])-r['job_own_shares']).sum(),p['player_id'])
        peers=sorted(pool,key=distance)[:3]
        records=[record(p) for p in [r,*peers]]
        evidence.append(dict(player_id=r['player_id'],origin=r['origin_year'],selection=reasons,
            peer_rule='Same origin/stage/primary nine-role; smallest age/5 + current PA/600 + L1 own-role-share distance; ID tiebreak; no target use.',
            peer_shortfall=3-len(peers),records=records))
        lines+=['## '+r['player_name']+' '+str(r['origin_year']),'', 'Selection: '+', '.join(reasons)+'.','',
                '| Player | Expected PA | Actual PA | Own weight | Reference DH | Candidate DH | Actual DH | Reference position runs | Candidate position runs | Actual position runs | Reference defense | Candidate defense | Actual defense |',
                '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
        for w in records:
            a=w['arms'];t=w['actual'];num=lambda x:'unknown' if x is None else f'{x:.3f}'
            lines.append('| '+w['name']+' | '+' | '.join(num(v) for v in [w['expected_PA'],w['actual_PA'],w['own_weight'],
                a['reference']['DH_starts'],a['candidate']['DH_starts'],t['DH_starts'],a['reference']['position_runs'],a['candidate']['position_runs'],
                t['position_runs'],a['reference']['defense_runs'],a['candidate']['defense_runs'],t['defense_runs']])+' |')
        w=records[0]
        lines+=['',f"Origin history: {json.dumps([s for s in w['source_history'] if s['season']<=w['origin']])}",'',
            f"Own nine-role shares {w['own_job_shares']}; reliability {w['own_weight']:.6f}; learned allowed shares {w['learned_allowed_shares']}. "
            f"Prior {w['role_prior']['key'] if w['role_prior'] else None}; detailed matching people {w['profile']['detailed_training_people']}. "
            f"Row job exposure {w['row_job_time']:.3f}; capacity multipliers {w['capacity_multipliers']}.",'',
            f"Fixed batting plus replacement {w['batting_fixed']:.6f}. Expanded reference {w['arms']['reference']['expanded_value']:.6f}, "
            f"joint {w['arms']['joint']['expanded_value']:.6f}, candidate {w['arms']['candidate']['expanded_value']:.6f}; "
            f"actual {w['actual']['expanded_value']}. Source corrections {w['DH_source_corrections']}.",'',
            ' '.join(w['baseball_judgments']),'']
    write('player-walkthrough.json',dict(status='complete',cases=evidence,missing_fixed_cases=missing,
        players_walked=sum(len(c['records']) for c in evidence),no_future_information_in_peer_selection=True,
        qualification='Future outcomes select error diagnostics, not independent confirmation. Each source history explicitly labels target season.',
        no_2026_outcomes=True,no_deployment=True))
    for dest in (OUT,__import__('run_defense_jobs_v14').PUBLIC):
        path=dest/'player-walkthrough.md';assert not path.exists();path.write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(dict(status='walkthrough_complete',cases=len(evidence),players=sum(len(c['records']) for c in evidence),missing=missing)))


if __name__=='__main__':main()
