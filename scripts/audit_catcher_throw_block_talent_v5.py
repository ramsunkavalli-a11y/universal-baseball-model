"""Count genuine chronological catcher talent windows before prediction scoring."""
from collections import defaultdict
import json
import math
from pathlib import Path

import polars as pl

from build_defense_native_range_v3 import identity
from source_catcher_throw_block_v5 import ROOT,OUT
from review_catcher_throw_block_source_v5 import FIXED,PUBLIC
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections,save
from universal_baseball.catcher_framing_baseline import recover_unknown_age
from universal_baseball.storage import sha256_file

SNAP=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated/opportunity-history-sources-v2/tables/hitter_snapshots.parquet')


def profile(r):
    age=r['age'];n=r['history_opportunities'];cut=(10,50) if r['component']=='throwing' else (500,3000)
    return ('unknown' if age is None else '<=24' if age<=24 else '25-29' if age<=29 else '30+',
            'tiny' if n<cut[0] else 'medium' if n<cut[1] else 'large')


def main():
    protected=protections();review=json.loads((OUT/'extension-review.json').read_text(encoding='utf8'));verify(review['hashes'])
    assert review['player_walkthrough_status']=='complete'
    annual=pl.read_parquet(OUT/'extension-annual.parquet').to_dicts()
    native={(r['season'],r['player_id']):r['native_outs'] for r in pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').filter(pl.col('position')==2).to_dicts()}
    histories=defaultdict(list)
    for r in annual:histories[r['component'],r['player_id']].append(r)
    bios,ages,agepaths=identity();snapshots=defaultdict(list)
    for r in pl.read_parquet(SNAP,columns=['snapshot_year','player_id','age_years']).to_dicts():snapshots[r['player_id']].append(r)
    rows=[]
    for (kind,pid),history in sorted(histories.items()):
        start=2016 if kind=='throwing' else 2018
        for y in range(start,2025):
            if y==2020:continue
            seen=[s for s in history if y-2<=s['season']<=y]
            if not seen:continue
            past=[s for s in seen if s['measurement_valid']]
            n=sum(s['opportunities']*2.**(s['season']-y) for s in past)
            runs=sum(s['runs']*2.**(s['season']-y) for s in past)
            dob=bios.get(pid);age=y-dob.year-((7,1)<(dob.month,dob.day)) if dob else ages.get((y,pid))
            age_basis='birthdate_july1' if dob else 'dated_panel'
            if age is None or not math.isfinite(age):
                a=recover_unknown_age(y,snapshots[pid]);age=a['age'];age_basis=a['age_basis']
            future=[s for s in history if y<s['season']<=min(y+3,2025) and s['measurement_valid']]
            missing=sum(native.get((year,pid),0) for year in range(y+1,min(y+3,2025)+1) if not any(s['season']==year for s in future))
            fn=sum(s['opportunities'] for s in future);fr=sum(s['runs'] for s in future)
            valid=y+3<=2025 and len(future)>=2 and fn>=(100 if kind=='throwing' else 3000) and missing==0
            unit=100 if kind=='throwing' else 1000
            rows.append(dict(component=kind,origin_year=y,player_id=pid,player_name=seen[-1]['player_name'],age=age,age_basis=age_basis,
                history_opportunities=n,history_runs=runs,history_seasons=len(past),quarantined_history_seasons=len(seen)-len(past),
                history_left_truncated=y-2<start,window_end=y+3,future_opportunities=fn,future_runs=fr,future_seasons=len(future),
                missing_native_outs=missing,quality_rate=unit*fr/fn if valid else None,
                quality_status='measured' if valid else 'window_incomplete' if y+3>2025 else 'unknown'))
    cohorts=[];cells=[];walks=[]
    def describe(r):
        k,pid,y=r['component'],r['player_id'],r['origin_year']
        return dict(origin=r,weighted_sources=[{**s,'weight':2.**(s['season']-y)} for s in histories[k,pid] if y-2<=s['season']<=y],
                future_sources=[s for s in histories[k,pid] if y<s['season']<=r['window_end']],model_fit=False)
    for kind in ('throwing','blocking'):
        rr=[r for r in rows if r['component']==kind]
        for y in sorted({r['origin_year'] for r in rr}):
            cohort=[r for r in rr if r['origin_year']==y]
            cohorts.append(dict(component=kind,origin=y,people=len(cohort),measured=sum(r['quality_rate'] is not None for r in cohort),
                            unknown_age=sum(r['age'] is None for r in cohort),quarantined_history=sum(r['quarantined_history_seasons']>0 for r in cohort)))
            for fold in range(5):
                tr=[r for r in rr if r['window_end']<=y and r['quality_rate'] is not None and r['player_id']%5!=fold]
                te=[r for r in cohort if r['player_id']%5==fold];p=defaultdict(set)
                assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
                for r in tr:p[profile(r)].add(r['player_id'])
                cells.append(dict(component=kind,origin=y,fold=fold,training_people=len({r['player_id'] for r in tr}),training_rows=len(tr),
                        training_origins=sorted({r['origin_year'] for r in tr}),train_keys=[[r['origin_year'],r['player_id']] for r in tr],
                        test_keys=[[r['origin_year'],r['player_id']] for r in te],joint_profile_people=[len(p[profile(r)]) for r in te]))
        primary=[r for r in rr if r['origin_year']==2022]
        selected=set(FIXED)|{r['player_id'] for r in sorted(primary,key=lambda r:(r['history_opportunities'],r['player_id']))[:2]}
        for pid in sorted(selected):
            r=next((s for s in primary if s['player_id']==pid),None)
            if not r:continue
            peers=sorted([p for p in primary if p['player_id']!=pid],key=lambda p:(abs((p['age'] or 27)-(r['age'] or 27)),abs(p['history_opportunities']-r['history_opportunities']),p['player_id']))[:3]
            walks.append(dict(primary=describe(r),peers=[describe(p) for p in peers],selection='fixed source cases/two smallest samples; age/exposure/ID peers'))
    table=OUT/'talent-labels.parquet';assert not table.exists();pl.DataFrame(rows,infer_schema_length=None).write_parquet(table)
    walk=OUT/'talent-source-player-walkthrough.json';assert not walk.exists();save(walk,dict(player_walkthrough_status='complete',cases=walks))
    paths=[OUT/'extension-review.json',OUT/'extension-annual.parquet',table,walk,SNAP,*agepaths,
        ROOT/'docs/catcher-throw-block-v5-support-contract.md',ROOT/'src/universal_baseball/catcher_framing_baseline.py',Path(__file__)]
    report=OUT/'talent-support-review.json';assert not report.exists()
    save(report,dict(before_scoring=True,model_fit=False,cohorts=cohorts,cells=cells,source_cases=len(walks),player_walkthrough_status='complete',
        no_2026_outcomes=True,protections=protected,hashes={str(p):sha256_file(p) for p in paths}))
    for p in (report,walk):(PUBLIC/p.name).write_bytes(p.read_bytes())
    print(json.dumps(dict(cohorts=cohorts,primary_training_people=[{k:c[k] for k in ('component','fold','training_people','training_origins')} for c in cells if c['origin']==2022],cases=len(walks)),indent=2))


if __name__=='__main__':main()
