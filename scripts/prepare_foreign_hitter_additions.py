"""Seal batting-input additions, reconstruct histories, and prepare source walks."""
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import polars as pl

from prepare_foreign_component_translation import ROOT,read,save,verify,DOMESTIC,INPUTS
from universal_baseball.foreign_hitter_admission import materialize,COUNTS
from universal_baseball.storage import sha256_file

OUT=ROOT/'reports/generated/foreign-hitter-additions'
POP=ROOT/'reports/generated/hitter-preseason-population-source'
FIXED=[('Shohei Ohtani',660271,2017),('Seiya Suzuki',673548,2021),('Masataka Yoshida',807799,2022),
    ('Jung Hoo Lee',808982,2023),('Brian Bogusevic',460131,2016),('Hiroyuki Nakajima',493141,2012),('Oscar Colás',693049,2021)]


def main():
    assert not OUT.exists(),'Inspect current execution before attempting recovery'
    foreign_review=read(INPUTS/'independent-review.json');verify(foreign_review['hashes'])
    status=ROOT/'reports/generated/hitter-status-evidence-v2/final-review.json'
    reviewed=read(status);verify(reviewed['source_hashes']);verify(reviewed['artifact_hashes'])
    assert reviewed['player_walkthrough_status']=='complete_for_source_only'
    paths=[Path(__file__),ROOT/'src/universal_baseball/foreign_hitter_admission.py',
        ROOT/'tests/test_foreign_hitter_admission.py',ROOT/'docs/hitter-foreign-additions-contract.md',
        POP/'population.parquet',POP/'reviewed-role-hints.parquet',INPUTS/'origin-inputs.json',DOMESTIC,status]
    hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths}
    population=pl.read_parquet(POP/'population.parquet').to_dicts();foreign=read(INPUTS/'origin-inputs.json')['rows']
    stints=pl.read_parquet(DOMESTIC).to_dicts();assert max(s['season'] for s in stints)==2025
    rows=materialize(foreign,population,stints)
    assert len(rows)==148 and len({r['candidate_key'] for r in rows})==148
    roles={(r['player_id'],r['origin_year']):r['reviewed_role_hint'] for r in pl.read_parquet(POP/'reviewed-role-hints.parquet').to_dicts()}
    for r in rows:assert r['dated_role_hint']==roles[r['player_id'],r['origin_year']]
    # Membership is sealed before any next-year outcome or case category is inspected.
    save(OUT/'membership-seal.json',dict(source_hashes=hashes,all_source_additions=148,
        qualified_keys=[r['candidate_key'] for r in rows if r['qualified_for_batting_input']],
        original_forecast_membership_unchanged=True,new_fits=0,source_rules_before_outcomes=True))
    save(OUT/'origin-inputs.json',dict(rows=rows))
    lookup={r['candidate_key']:r for r in rows};flookup={r['candidate_key']:r for r in foreign}
    reconstructed=0
    for r in rows:
        pid,y=r['player_id'],r['origin_year'];prior=[s for s in stints if s['player_id']==pid and s['season']<=y]
        assert sorted(prior,key=lambda s:(s['season'],s['sport_id'],s['team_id']))==r['actual_prior_domestic_stints']
        assert r['qualified_for_batting_input']==(r['dated_role_hint'] in {'hitter_hint','two_way_hint','two_way_or_conflicting_hints'})
        assert r['career_observed_mlb_pa']==sum(s['plate_appearances'] for s in prior if s['sport_id']==1)
        for piece in r['three_year_domestic_history']:
            part=[s for s in prior if s['season']==piece['season']]
            assert set(piece['levels'])=={s['bucket'] for s in part}
            for level,item in piece['levels'].items():
                group=[s for s in part if s['bucket']==level]
                assert item['counts']=={c:sum(s[c] for s in group) for c in COUNTS}
                assert item['reported_positions']==sorted({s['position'] for s in group}) and item['stint_rows']==len(group)
                reconstructed+=len(COUNTS)
        assert r['new_forecast'] is None and not r['current_employment_guaranteed']
    for y in sorted({r['origin_year'] for r in rows}):
        future_changed=[dict(s,plate_appearances=999999,hits=999999) if s['season']>y else s for s in stints]
        subset=[f for f in foreign if f['origin_year']==y]
        assert materialize(subset,population,future_changed)==[r for r in rows if r['origin_year']==y]
    # Peers are qualified hitter/mixed inputs, not the original unknown role pool.
    peers={}
    for _,pid,y in FIXED:
        key=f'{y}:{pid}';f=flookup[key];a=f['age_at_information_date'];candidates=[]
        for q in foreign:
            if q['origin_year']!=y or q['player_id']==pid or q['dated_role_hint'] not in {'hitter_hint','two_way_hint','two_way_or_conflicting_hints'}:continue
            if (b:=q['age_at_information_date']) is None or a is None:continue
            d=abs(a-b)/5+abs(np.log1p(f['recent_foreign_pa'])-np.log1p(q['recent_foreign_pa']))+abs(np.log1p(f['recent_observed_domestic_pa'])-np.log1p(q['recent_observed_domestic_pa']))
            candidates.append(dict(candidate_key=q['candidate_key'],player_id=q['player_id'],distance=float(d)))
        peers[key]=sorted(candidates,key=lambda q:(q['distance'],q['player_id']))[:3]
    ordinary=sorted([r for r in rows if r['dated_role_hint']=='pitcher_hint'],key=lambda r:(r['origin_year'],r['player_id']))[0]
    fixed=FIXED+[(ordinary['player_name'],ordinary['player_id'],ordinary['origin_year'])]
    save(OUT/'case-membership-seal.json',dict(fixed=fixed,origin_only_peers=peers,
        peer_rule='same origin, reviewed hitter/mixed role and known ages; nearest age/5 plus log foreign/domestic exposure; ID ties; not matched jobs or hitting talent',
        pitcher_control='lowest origin then ID among pitcher-only additions',no_future_outcome_selection=True))
    # Historical MLB outcomes are consulted only after these source/case seals.
    annual=pl.DataFrame(stints).filter(pl.col('sport_id')==1).group_by('player_id','season').agg(pl.col(COUNTS).sum())
    actual={(r['player_id'],r['season']):r for r in annual.to_dicts()}
    cases=[]
    for name,pid,y in fixed:
        key=f'{y}:{pid}';r=lookup[key]
        cases.append(dict(name=name,player_id=pid,origin_year=y,admission=r,foreign_input=flookup[key],
            actual_next_MLB_counts=actual.get((pid,y+1)),actual_next_MLB_PA=actual.get((pid,y+1),{}).get('plate_appearances',0),
            target_2020_excluded_from_normal_year_model=y==2019,old_forecast=None,new_forecast=None,
            peers=[dict(q,foreign_input=flookup[q['candidate_key']],actual_next_MLB_PA=actual.get((q['player_id'],y+1),{}).get('plate_appearances',0)) for q in peers.get(key,[])]))
    save(OUT/'reviewed-cases.json',dict(cases=cases,player_walkthrough_status='machine_traces_ready_manual_pending'))
    tests=subprocess.run([sys.executable,'-m','pytest','-p','no:cacheprovider','tests/test_foreign_hitter_admission.py','-q'],cwd=ROOT,capture_output=True,text=True)
    assert tests.returncode==0,tests.stdout+tests.stderr
    summary=dict(source_additions=148,qualified_batting_inputs=sum(r['qualified_for_batting_input'] for r in rows),
        dispositions=dict(Counter(r['disposition'] for r in rows)),qualified_with_real_recent_domestic_history=sum(r['qualified_for_batting_input'] and r['recent_observed_domestic_pa']>0 for r in rows),
        count_fields_reconstructed=reconstructed,future_mutation_origins_checked=len({r['origin_year'] for r in rows}),tests=tests.stdout,
        population_rows_unchanged=83300,original_forecasts_unchanged=30506,new_fits=0,goal_achieved=False,deployment_approved=False,
        player_walkthrough_status='pending',source_hashes=hashes,
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [OUT/'membership-seal.json',OUT/'origin-inputs.json',OUT/'case-membership-seal.json',OUT/'reviewed-cases.json']})
    save(OUT/'source-review.json',summary)
    print(json.dumps({k:summary[k] for k in ['source_additions','qualified_batting_inputs','dispositions','qualified_with_real_recent_domestic_history','count_fields_reconstructed','future_mutation_origins_checked','new_fits']}),flush=True)


if __name__=='__main__':main()
