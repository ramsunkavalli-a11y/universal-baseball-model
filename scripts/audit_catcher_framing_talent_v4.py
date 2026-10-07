"""Count mature native-pitch framing talent examples; no learner fit."""
from collections import defaultdict
import json
import math
from pathlib import Path

import polars as pl

from build_defense_native_range_v3 import identity
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file
from audit_defensive_talent_support import verify

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'reports/generated/catcher-native-opportunity-v3/modern'
OUT=ROOT/'reports/generated/catcher-framing-talent-v4'
PUBLIC=ROOT/'reports/model-evidence/catcher-framing-talent-v4'
FIXED=(595978,592663,518735,596142,672386,663728,672275)


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def write(name,value):
    p=OUT/name;assert not p.exists(),f'Preserve {p}'
    save(p,value)
    return p


def profile(r):
    age=r['age'];n=r['history_pitches']
    return ('unknown' if age is None else '<=24' if age<=24 else '25-29' if age<=29 else '30+',
            '<1000' if n<1000 else '1000-5999' if n<6000 else '6000+')


def main():
    protected=protections();source=read(SOURCE/'source-review.json');verify(source['hashes'])
    assert source['player_walkthrough_status']=='complete' and source['pre2018_framing_quarantined']
    assert read(SOURCE/'verification.json')['source_replay']=='pass'
    annual=pl.read_parquet(SOURCE/'framing-annual.parquet').to_dicts()
    assert all(2018<=r['season']<=2025 and r['pitches']>0 and r['framing_measurement_valid'] and r['exposure_valid'] for r in annual)
    native=pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').filter(pl.col('position')==2).to_dicts()
    exposure={(r['season'],r['player_id']):r['native_outs'] for r in native}
    bypid=defaultdict(list)
    for r in annual:
        bypid[r['player_id']].append(r)
    bios,ages,identity_paths=identity()
    rows=[]
    for year in range(2018,2025):
        if year==2020:
            continue
        for pid,history in sorted(bypid.items()):
            past=[s for s in history if year-2<=s['season']<=year]
            if not past:
                continue
            n=sum(s['pitches']*.5**(year-s['season']) for s in past)
            runs=sum(s['framing_runs']*.5**(year-s['season']) for s in past)
            dob=bios.get(pid)
            age=year-dob.year-((7,1)<(dob.month,dob.day)) if dob else ages.get((year,pid))
            if age is not None and (not math.isfinite(age) or not 15<=age<=55):
                age=None
            path=[s for s in history if year<s['season']<=min(year+3,2025)]
            missing=sum(exposure.get((y,pid),0) for y in range(year+1,min(year+3,2025)+1) if not any(s['season']==y for s in path))
            fn=sum(s['pitches'] for s in path);fr=sum(s['framing_runs'] for s in path)
            valid=year+3<=2025 and len(path)>=2 and fn>=6000 and missing==0
            rows.append(dict(origin_year=year,player_id=pid,player_name=past[-1]['player_name'],age=age,
                    age_basis='birthdate_july1' if dob else 'dated_panel' if age is not None else 'unknown',
                    history_pitches=n,history_runs=runs,history_rate=1000*runs/(6000+n),reliability=n/(6000+n),
                    history_seasons=len(past),history_left_truncated=year-2<2018,window_end=year+3,
                    window_has_2020=year<2020<=year+3,window_mature=year+3<=2025,
                    future_pitches=fn,future_runs=fr,future_seasons=len(path),missing_native_outs=missing,
                    quality_rate=1000*fr/fn if valid else None,
                    quality_status='measured' if valid else 'window_incomplete' if year+3>2025 else 'unknown'))
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'labels.parquet').exists()
    pl.DataFrame(rows,infer_schema_length=None).write_parquet(OUT/'labels.parquet')
    cohorts=[];cells=[]
    for year in sorted({r['origin_year'] for r in rows}):
        cohort=[r for r in rows if r['origin_year']==year]
        measured=[r for r in cohort if r['quality_rate'] is not None]
        cohorts.append(dict(origin=year,eligible_people=len(cohort),measured_people=len(measured),
                      left_truncated_people=sum(r['history_left_truncated'] for r in cohort),
                      missing_age_people=sum(r['age'] is None for r in cohort)))
        for fold in range(5):
            tr=[r for r in rows if r['window_end']<=year and r['quality_rate'] is not None and r['player_id']%5!=fold]
            te=[r for r in cohort if r['player_id']%5==fold]
            assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
            profiles=defaultdict(set)
            for r in tr:
                profiles[profile(r)].add(r['player_id'])
            cells.append(dict(origin=year,fold=fold,training_people=len({r['player_id'] for r in tr}),
                  training_rows=len(tr),training_origins=sorted({r['origin_year'] for r in tr}),
                  training_left_truncated_rows=sum(r['history_left_truncated'] for r in tr),
                  train_keys=[[r['origin_year'],r['player_id']] for r in tr],test_keys=[[r['origin_year'],r['player_id']] for r in te],
                  joint_profile_people=[len(profiles[profile(r)]) for r in te],
                  training_pitch_range=[min((r['history_pitches'] for r in tr),default=None),max((r['history_pitches'] for r in tr),default=None)]))
    primary=[r for r in rows if r['origin_year']==2022]
    selected=set(FIXED)|{r['player_id'] for r in sorted(primary,key=lambda r:(r['history_pitches'],r['player_id']))[:2]}
    walks=[];missing=[]
    def describe(r):
        y,pid=r['origin_year'],r['player_id']
        return dict(origin=r,weighted_sources=[{**s,'weight':.5**(y-s['season'])} for s in bypid[pid] if y-2<=s['season']<=y],
                    future_sources=[s for s in bypid[pid] if y<s['season']<=r['window_end']],
                    scope='native framing source/support; no fitted model')
    for pid in sorted(selected):
        r=next((s for s in primary if s['player_id']==pid),None)
        if r is None:
            missing.append(pid);continue
        peers=sorted([p for p in primary if p['player_id']!=pid],key=lambda p:(abs((p['age'] or 27)-(r['age'] or 27)),abs(p['history_pitches']-r['history_pitches']),p['player_id']))[:3]
        walks.append(dict(primary=describe(r),peers=[describe(p) for p in peers]))
    write('source-player-walkthrough.json',dict(player_walkthrough_status='complete',cases=walks,missing_fixed_cases=missing,
         selection='fixed identities and two smallest weighted origin pitch samples; peers by same origin/age/exposure/ID without future selection'))
    paths=[SOURCE/'framing-annual.parquet',SOURCE/'source-review.json',SOURCE/'verification.json',
           ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet',OUT/'labels.parquet',OUT/'source-player-walkthrough.json',
           ROOT/'docs/catcher-framing-talent-v4-support-contract.md',Path(__file__),*identity_paths]
    result=dict(before_fitting=True,model_fit=False,no_2026_outcomes=True,player_walkthrough_status='complete',
         cohorts=cohorts,cells=cells,all_origins=len(rows),source_cases=len(walks),protections=protected,
         hashes={str(p):sha256_file(p) for p in paths})
    write('support-review.json',result)
    PUBLIC.mkdir(parents=True,exist_ok=True)
    for name in ('support-review.json','source-player-walkthrough.json'):
        p=PUBLIC/name;assert not p.exists();p.write_bytes((OUT/name).read_bytes())
    print(json.dumps(dict(cohorts=cohorts,ordinary_origin_cells=[c for c in cells if c['origin']==2022],source_cases=len(walks),missing_fixed_cases=missing),indent=2))


if __name__=='__main__':
    main()
