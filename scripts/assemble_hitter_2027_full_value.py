"""Development additive WAR accounting; neither a release nor contract value."""
from collections import defaultdict
from dataclasses import replace
from datetime import date
from pathlib import Path
import gzip,json,math
import numpy as np
import polars as pl
from universal_baseball.hitter_release_ledger import ComponentEstimate,annual_ledger,batting_rate_from_legacy
from universal_baseball.defense_value import POSITION_RUNS
from universal_baseball.player_value_runs_per_win import calculate_v1_runs_per_win
from universal_baseball.storage import sha256_file
from capture_hitter_2027_origin_counts import ROOT,write_once

OUT=ROOT/'reports/generated/hitter-2027-base'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'


def main():
    assert not (PUBLIC/'full-value-assembly.json').exists()
    paths=[]
    def read(p):paths.append(p);return pl.read_parquet(p)
    forecast=read(ROOT/'reports/generated/hitter-2027-batting-refresh/forecast.parquet')
    roles={r['player_id']:r for r in read(OUT/'role-opportunities-reviewed.parquet').to_dicts()}
    running={r['player_id']:r for r in read(OUT/'running-rates.parquet').to_dicts()}
    defense=defaultdict(list)
    for r in read(OUT/'defensive-contributions.parquet').to_dicts():defense[r['player_id']].append(r)
    actual=read(OUT/'values.parquet').filter(pl.col('season')==2026)
    assert len(actual)==662 and actual['mlb_pa'].sum()==183849
    environment=calculate_v1_runs_per_win(21769,129239/3,reference_season=2026)
    rpw=environment.runs_per_win;replacement=570*rpw/183849
    asof=date(2026,10,9);sourcecut=date(2026,10,9)
    estimates={};raw={};names={}
    def item(c,context,rate,n,unit,kind,evidence,estimator,source):
        return ComponentEstimate(c,context,float(rate),float(n),float(unit),kind,evidence,estimator,source,sourcecut)
    for q in forecast.to_dicts():
        pid=q['player_id'];pa=q['expected_pa'];role=roles[pid];run=running[pid];ee=[];names[pid]=q['player_name']
        ee.append(item('batting','all',batting_rate_from_legacy(q['hitting_wins_per_600']),pa,600,'MLB_PA',
            'individual_history' if q['career_mlb_observed_pa']>0 else 'translated_profile',q['talent_route'],'2027-batting-refresh'))
        for c,col in [('stealing','steal_runs_per_600'),('advancement','advancement_runs_per_600')]:
            ee.append(item(c,'all',run[col],pa,600,'MLB_PA','comparable_players' if run[col]==0 else 'individual_history',
                'B2_k5_k45' if c=='stealing' else 'A2_k25','running-rates'))
        for r in defense[pid]:
            ee.append(item(r['component'],r['context'],r['runs_per_unit'],r['projected_opportunities'],r['rate_unit'],r['opportunity_kind'],
                {'individual':'individual_history','translated_profile':'translated_profile','comparable':'comparable_players'}[r['evidence_tier']],r['estimator_id'],'defensive-contributions'))
        for p,rate in POSITION_RUNS.items():
            ee.append(item('position',str(p),rate,role[f'outs_{p}'],4374,'defensive_outs','accounting_reference','position_schedule','role-opportunities-reviewed'))
        ee.append(item('position','DH',-17.5,role['DH_starts'],162,'DH_starts','accounting_reference','position_schedule','role-opportunities-reviewed'))
        for c,n,unit,kind,recipe in [('gidp',pa,600,'MLB_PA','explicit_neutral_GIDP_residual'),
                ('double_play',sum(role[f'outs_{p}'] for p in [3,4,5,6]),1500,'infield_outs','v23_neutral_DP_selected'),
                ('abs_challenge',role['native_framing'],1000,'received_pitches','one_season_unvalidated_challenge_prior')]:
            ee.append(item(c,'all',0,n,unit,kind,'comparable_players',recipe,'2027-full-value-contract'))
        ee.append(item('arm','non_OF',0,sum(role[f'outs_{p}'] for p in [2,3,4,5,6]),1500,'non_OF_outs','comparable_players','non_OF_arm_unmeasured_prior','2027-full-value-contract'))
        ee.append(item('park','all',0,pa,600,'MLB_PA','accounting_reference','no_additional_correction_observed_context_not_certified_neutral','2027-full-value-contract'))
        ee.append(item('replacement','all',replacement,pa,1,'MLB_PA','accounting_reference','570_full_season_reference','2026-official-environment'))
        ee.append(item('league','all',0,pa,1,'MLB_PA','accounting_reference','fixed_2026_MLB_members_2027_projected_reference','pending_reference_assembly'))
        estimates[pid]=ee
        raw[pid]=annual_ledger(player_id=pid,season=2027,as_of=asof,estimates=ee,runs_per_win=rpw,
            fielding_reference='position_relative',batting_reference='observed_context',deployment_status='development')
    reference=[]
    for r in actual.to_dicts():
        pid=r['player_id'];ee=estimates.get(pid,[])
        pa=next((e.opportunities for e in ee if e.component=='batting'),0.)
        amount=math.fsum(e.projected_runs(as_of=asof) for e in ee if e.component not in ['park','replacement','league'])
        reference.append(dict(player_id=pid,name=names.get(pid),observed_origin_pa=r['mlb_pa'],projected_reference_PA=pa,
            projected_raw_above_average_runs=amount,outside_forecast=pid not in estimates))
    denominator=math.fsum(r['projected_reference_PA'] for r in reference)
    center=-math.fsum(r['projected_raw_above_average_runs'] for r in reference)/denominator
    assert abs(math.fsum(r['projected_raw_above_average_runs']+center*r['projected_reference_PA'] for r in reference))<1e-8
    ledgers=[];annual=[]
    for q in forecast.to_dicts():
        pid=q['player_id'];ee=[replace(e,runs_per_unit=center,source_id='fixed_2026_MLB_members_2027_projected_reference') if e.component=='league' else e for e in estimates[pid]]
        ledger=annual_ledger(player_id=pid,season=2027,as_of=asof,estimates=ee,runs_per_win=rpw,
            fielding_reference='position_relative',batting_reference='observed_context',deployment_status='development')
        ledger.update(player_name=q['player_name'],role_complete=not roles[pid]['evidence']['unknown'],
            park_context_qualified=True,ABS_scenario='2026_challenge_rules_continue',
            full_ABS_same_reference_war=ledger['war']-ledger['component_war']['framing'])
        ledgers.append(ledger)
        annual.append(dict(player_id=pid,player_name=q['player_name'],season=2027,stage=q['stage'],expected_pa=q['expected_pa'],
            hitting_wins_per_600=q['hitting_wins_per_600'],participation_probability=q['participation_probability'],
            **{c+'_runs':v for c,v in ledger['component_runs'].items()},**{c+'_war':v for c,v in ledger['component_war'].items()},
            total_war=ledger['war'],runs_per_win=rpw,role_complete=ledger['role_complete'],park_context_qualified=True,
            full_ABS_same_reference_war=ledger['full_ABS_same_reference_war'],release_status='development_not_released'))
    by={r['player_id']:r for r in ledgers}
    cases=json.loads(gzip.decompress((PUBLIC/'base-input-player-walks.json.gz').read_bytes()))['cases']
    ids={w['player_id'] for c in cases for w in [c['primary'],*c['peers']]}
    ids.update(r['player_id'] for r in sorted(annual,key=lambda r:r['total_war'])[:3]+sorted(annual,key=lambda r:r['total_war'])[-3:])
    walks=[]
    for pid in sorted(ids):
        r=by[pid];assert np.isclose(sum(r['component_war'].values()),r['war'])
        for d in r['details']:assert np.isclose(d['runs'],d['rate']*d['exposure']/d['unit'])
        walks.append(dict(ledger=r,role=roles[pid],running=running[pid]))
    assert all(r['component_runs']['range']==0 and r['component_runs']['framing']==0 for r in ledgers if sum(roles[r['player_id']][f'outs_{p}'] for p in range(2,10))==0)
    out=OUT/'full-value-development.parquet';assert not out.exists();pl.DataFrame(annual).write_parquet(out)
    detail=OUT/'full-value-ledger.json.gz';assert not detail.exists();detail.write_bytes(gzip.compress(json.dumps(ledgers,allow_nan=False).encode(),mtime=0))
    walk=PUBLIC/'full-value-player-walks.json.gz';assert not walk.exists();walk.write_bytes(gzip.compress(json.dumps(walks,allow_nan=False,default=str).encode(),mtime=0))
    paths.extend([Path(__file__),ROOT/'docs/hitter-2027-full-value-assembly.md'])
    write_once(PUBLIC/'full-value-assembly.json',dict(reference=reference,reference_projected_PA=denominator,
        centering_runs_per_PA=center,runs_per_win=rpw,replacement_runs_per_PA=replacement,
        total_war=sum(r['total_war'] for r in annual),component_totals={c:sum(r[c+'_runs'] for r in annual) for c in ledgers[0]['component_runs']},
        players=len(annual),role_incomplete=sum(not r['role_complete'] for r in annual),
        player_calculations_replayed=True,player_interpretation='pending_written_review',released=False,
        restrictions=['Batting retains observed-context qualification','Historical full-WAR/public comparison pending','Control and costs not yet joined'],
        output_hashes={str(p):sha256_file(p) for p in [out,detail,walk]},input_hashes={str(p):sha256_file(p) for p in paths}))
    for pid in [804944,805811,808393,592450,665487,660271,672275,596019]:
        print(names[pid],round(by[pid]['war'],3),{c:round(v,3) for c,v in by[pid]['component_war'].items() if v},flush=True)
    print('League',sum(r['total_war'] for r in annual),'centering runs/600',center*600,flush=True)


if __name__=='__main__':main()
