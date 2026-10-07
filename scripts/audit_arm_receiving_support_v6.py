"""Complete later quality windows and exact held-player support before scoring."""
from collections import defaultdict
from pathlib import Path
import json
import math
import polars as pl
from build_defense_native_range_v3 import identity
from review_arm_receiving_pilot_v6 import FIXED
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file
from universal_baseball.catcher_framing_baseline import recover_unknown_age

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/arm-receiving-v6'
PUBLIC=ROOT/'reports/model-evidence/arm-receiving-v6'
SNAP=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated/opportunity-history-sources-v2/tables/hitter_snapshots.parquet')


def profile(r):
    a=r['age'];n=r['history_opportunities'];lo,hi=(50,300) if r['kind']=='arm' else (100,500)
    return ('unknown' if a is None else '<=24' if a<=24 else '25-29' if a<=29 else '30+',
            'tiny' if n<lo else 'medium' if n<hi else 'large')


def main():
    protections()
    assert not (OUT/'talent-support-review.json').exists()
    review=json.loads((OUT/'extension-review.json').read_text())
    assert review['support_audit_allowed'] and review['player_walkthrough_status']=='complete'
    for group in ('input_hashes','output_hashes'):
        for path,h in review[group].items():assert sha256_file(Path(path))==h,path
    annual=pl.read_parquet(OUT/'annual.parquet').to_dicts()
    histories=defaultdict(list)
    for r in annual:histories[r['kind'],r['player_id']].append(r)
    ledger_path=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    native=defaultdict(list)
    for r in pl.read_parquet(ledger_path).to_dicts():native[r['season'],r['player_id']].append(r)
    bios,ages,agepaths=identity();snapshots=defaultdict(list)
    for r in pl.read_parquet(SNAP,columns=['snapshot_year','player_id','age_years']).to_dicts():snapshots[r['player_id']].append(r)
    rows=[]
    for (kind,pid),history in sorted(histories.items()):
        start=2016 if kind=='arm' else 2021
        def valid(s):return bool(s['isolated_outfield_quality_valid'] if kind=='arm' else s['quality_valid'])
        for y in range(start,2025):
            if y==2020:continue
            seen=[s for s in history if y-2<=s['season']<=y]
            if not seen or (kind=='arm' and not any(s['of_outs']>0 for s in seen)):continue
            past=[s for s in seen if valid(s)]
            n=sum(s['opportunities']*2.**(s['season']-y) for s in past)
            runs=sum(s['runs']*2.**(s['season']-y) for s in past)
            dob=bios.get(pid);age=y-dob.year-((7,1)<(dob.month,dob.day)) if dob else ages.get((y,pid))
            basis='birthdate_july1' if dob else 'dated_panel'
            if age is None or not math.isfinite(age):
                result=recover_unknown_age(y,snapshots[pid]);age=result['age'];basis=result['age_basis']
            future=[s for s in history if y<s['season']<=min(y+3,2025)]
            measured=[s for s in future if valid(s)]
            gaps=[dict(season=s['season'],reason='invalid_or_mixed_positive_opportunity',opportunities=s['opportunities'])
                  for s in future if not valid(s)]
            for year in range(y+1,min(y+3,2025)+1):
                if any(s['season']==year for s in future):continue
                col='arm_runs' if kind=='arm' else 'fielding_runs_prevented_on_rec1b'
                relevant=[r for r in native.get((year,pid),[]) if (r['position'] in (7,8,9) if kind=='arm' else r['position']==3)]
                if any(r[col] is not None and abs(r[col])>1e-12 for r in relevant):
                    gaps.append(dict(season=year,reason='nonzero_native_credit_without_source',opportunities=None))
            fn=sum(s['opportunities'] for s in measured);fr=sum(s['runs'] for s in measured)
            good=y+3<=2025 and len(measured)>=2 and fn>=(600 if kind=='arm' else 1000) and not gaps
            rows.append(dict(kind=kind,origin_year=y,player_id=pid,player_name=seen[-1]['player_name'],age=age,age_basis=basis,
                history_opportunities=n,history_runs=runs,history_seasons=len(past),
                unknown_or_mixed_history_seasons=len(seen)-len(past),history_left_truncated=y-2<start,
                window_end=y+3,future_opportunities=fn,future_runs=fr,future_seasons=len(measured),
                coverage_gap_seasons=len(gaps),quality_rate=100*fr/fn if good else None,
                quality_status='measured' if good else 'window_incomplete' if y+3>2025 else 'unknown'))
    cohorts=[];cells=[];walks=[]
    def describe(r):
        k,pid,y=r['kind'],r['player_id'],r['origin_year']
        return dict(origin=r,origin_sources=[{**s,'weight':2.**(s['season']-y)} for s in histories[k,pid] if y-2<=s['season']<=y],
                    future_sources=[s for s in histories[k,pid] if y<s['season']<=r['window_end']],model_fit=False)
    for kind in ('arm','receiving'):
        rr=[r for r in rows if r['kind']==kind]
        for y in sorted({r['origin_year'] for r in rr}):
            cohort=[r for r in rr if r['origin_year']==y]
            cohorts.append(dict(kind=kind,origin=y,people=len(cohort),measured=sum(r['quality_rate'] is not None for r in cohort),
                unknown_age=sum(r['age'] is None for r in cohort),unknown_or_mixed_history=sum(r['unknown_or_mixed_history_seasons']>0 for r in cohort),
                future_scope_or_coverage_gaps=sum(r['coverage_gap_seasons']>0 for r in cohort)))
            for fold in range(5):
                tr=[r for r in rr if r['window_end']<=y and r['quality_rate'] is not None and r['player_id']%5!=fold]
                te=[r for r in cohort if r['player_id']%5==fold];profiles=defaultdict(set)
                assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
                for r in tr:profiles[profile(r)].add(r['player_id'])
                cells.append(dict(kind=kind,origin=y,fold=fold,training_people=len({r['player_id'] for r in tr}),
                    training_rows=len(tr),training_origins=sorted({r['origin_year'] for r in tr}),
                    train_keys=[[r['origin_year'],r['player_id']] for r in tr],test_keys=[[r['origin_year'],r['player_id']] for r in te],
                    joint_profile_people=[len(profiles[profile(r)]) for r in te],
                    measured_test_profile_people=[len(profiles[profile(r)]) for r in te if r['quality_rate'] is not None]))
        primary=[r for r in rr if r['origin_year']==2022]
        selected=set(FIXED[kind])|{r['player_id'] for r in sorted(primary,key=lambda r:(r['history_opportunities'],r['player_id']))[:2]}
        for pid in sorted(selected):
            focal=next((r for r in primary if r['player_id']==pid),None)
            if focal is None:continue
            peers=sorted((r for r in primary if r['player_id']!=pid),
                key=lambda r:(abs((r['age'] or 27)-(focal['age'] or 27)),abs(r['history_opportunities']-focal['history_opportunities']),r['player_id']))[:3]
            walks.append(dict(primary=describe(focal),peers=[describe(r) for r in peers],
                selection='Fixed source cases and two smallest histories; age/exposure/ID-selected peers.'))
    pl.DataFrame(rows,infer_schema_length=None).write_parquet(OUT/'talent-labels.parquet')
    walk=dict(cases=walks,player_walkthrough_status='complete',no_model_fit=True,no_2026_outcomes=True)
    save(OUT/'talent-source-player-walkthrough.json',walk)
    paths=[Path(__file__),OUT/'extension-review.json',OUT/'annual.parquet',OUT/'talent-labels.parquet',
        OUT/'talent-source-player-walkthrough.json',ledger_path,SNAP,*agepaths,
        ROOT/'docs/arm-receiving-v6-support-contract.md',ROOT/'src/universal_baseball/catcher_framing_baseline.py']
    report=dict(cohorts=cohorts,cells=cells,before_scoring=True,no_model_fit=True,no_2026_outcomes=True,
        player_walkthrough_status='complete',source_cases=len(walks),input_hashes={str(p):sha256_file(p) for p in paths})
    save(OUT/'talent-support-review.json',report)
    save(PUBLIC/'talent-support-review.json',report);save(PUBLIC/'talent-source-player-walkthrough.json',walk)
    print(json.dumps(dict(cohorts=cohorts,primary_training_people=[{k:c[k] for k in ('kind','fold','training_people','training_origins')} for c in cells if c['origin']==2022],cases=len(walks)),indent=2))


if __name__=='__main__':main()
