"""No-fit, outcome-blind membership diagnosis for recent MLB hitters."""
import json
from pathlib import Path
import shutil
import polars as pl
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/hitter-returner-coverage'
EVIDENCE = ROOT / 'reports/model-evidence/hitter-returner-coverage'
YEARS = [2016, 2017, 2018, 2021, 2022, 2023, 2024]
OLD = Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')
PATHS = {
    'stints': ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet',
    'panel': ROOT/'reports/generated/practical-hitter-numeric-repair-v53/features.parquet',
    'roster': ROOT/'reports/generated/hitter-arrival-source-repair-v1/year-end-rosters.parquet',
    'support': ROOT/'model_artifacts/post-arrival-support-v17/panel.parquet',
    'predictions': ROOT/'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet',
    'modern_snapshots': OLD/'opportunity-history-sources-v2/tables/hitter_snapshots.parquet',
    'contract': ROOT/'docs/hitter-returner-coverage-contract.md',
    'constructor': ROOT/'scripts/prepare_practical_hitter_v31.py',
    'script': Path(__file__),
}
FIXED = [('Michael Conforto',624424,2022), ('Miguel Sano',593934,2023),
         ('Yoenis Cespedes',493316,2018), ('David Wright',431151,2017),
         ('Troy Tulowitzki',453064,2018), ('Khris Davis',501981,2022),
         ('Brandon Belt',474832,2024)]


def candidates(stints, year):
    past = stints.filter((pl.col('sport_id')==1) &
                        pl.col('season').is_between(year-2,year) &
                        (pl.col('plate_appearances')>0))
    # Latest played MLB season, then largest stint and deterministic tie.
    last = past.sort(['player_id','season','plate_appearances','team_id'],
                     descending=[False,True,True,False]).unique('player_id',keep='first')
    return last.filter(pl.col('position')!='1').sort('player_id')


def main():
    assert not (OUT/'audit.json').exists(), 'Preserve completed source audit'
    s=pl.read_parquet(PATHS['stints']); f=pl.read_parquet(PATHS['panel'])
    r=pl.read_parquet(PATHS['roster']); b=pl.read_parquet(PATHS['support'])
    q=pl.read_parquet(PATHS['predictions'])
    assert s['season'].max()==2025 and f['origin_year'].max()==2024
    assert q.height==30506 and q['row_id'].n_unique()==30506
    assert f.filter(pl.col('origin_year').is_in(YEARS)).select('row_id').sort('row_id').equals(q.select('row_id').sort('row_id'))
    snapshots=[]
    for y in YEARS:
        if y<2020:
            path=ROOT/f'model_artifacts/advanced-rookie-repair-v3/{y}/hitter_snapshots.parquet'
            PATHS['snapshot_'+str(y)]=path
            snapshots.append(pl.read_parquet(path).select(pl.col('snapshot_year').alias('origin_year'),'player_id'))
    snapshots.append(pl.scan_parquet(PATHS['modern_snapshots']).filter(pl.col('snapshot_year').is_in(YEARS)).select(pl.col('snapshot_year').alias('origin_year'),'player_id').collect())
    snaps=pl.concat(snapshots).unique()
    records=[]; summaries=[]; invariance=[]
    for y in YEARS:
        eligible=candidates(s,y)
        assert eligible.select('player_id').equals(candidates(s.filter(pl.col('season')<=y),y).select('player_id'))
        altered=s.with_columns(pl.when(pl.col('season')>y).then(999999).otherwise(pl.col('plate_appearances')).alias('plate_appearances'))
        assert eligible.select('player_id').equals(candidates(altered,y).select('player_id'))
        invariance.append(dict(origin_year=y,future_removed_and_mutated_membership_unchanged=True))
        current=set(f.filter(pl.col('origin_year')==y)['player_id'])
        snapshot=set(snaps.filter(pl.col('origin_year')==y)['player_id'])
        support=set(b.filter((pl.col('origin_year')==y)&pl.col('window_complete'))['player_id'])
        roster=set(r.filter(pl.col('season')==y)['player_id'])
        future=s.filter((pl.col('season')==y+1)&(pl.col('sport_id')==1)).group_by('player_id').agg(pl.col('plate_appearances').sum())
        outcomes=dict(future.iter_rows())
        for v in eligible.iter_rows(named=True):
            pid=v['player_id']
            hist=s.filter((pl.col('player_id')==pid)&(pl.col('sport_id')==1)&pl.col('season').is_between(y-2,y)).group_by('season').agg(pl.col('plate_appearances','home_runs','strike_outs','unintentional_walks').sum()).sort('season').to_dicts()
            item=dict(player_id=pid,player_name=v['player_name'],origin_year=y,last_mlb_season=v['season'],last_source_position=v['position'],
                in_current_panel=pid in current,in_snapshot=pid in snapshot,in_support=pid in support,in_stored_roster=pid in roster,
                own_history=hist,diagnostic_next_pa=int(outcomes.get(pid,0)))
            assert item['in_current_panel']==(item['in_snapshot'] or item['in_support']), 'Membership constructor does not replay'
            records.append(item)
        group=[v for v in records if v['origin_year']==y]; missing=[v for v in group if not v['in_current_panel']]
        summaries.append(dict(origin_year=y,review_candidates=len(group),omitted_candidates=len(missing),omitted_nonarrivals=sum(v['diagnostic_next_pa']==0 for v in missing),
            omitted_arrivals=sum(v['diagnostic_next_pa']>0 for v in missing),omitted_next_pa=sum(v['diagnostic_next_pa'] for v in missing),
            omitted_on_stored_roster=sum(v['in_stored_roster'] for v in missing)))
    cases=[]
    for name,pid,y in FIXED:
        g=[v for v in records if (v['player_id'],v['origin_year'])==(pid,y)]
        cases.append(dict(selection='fixed_before_audit',requested_name=name,player_id=pid,origin_year=y,qualifies_review_rule=bool(g),record=g[0] if g else None,
            panel_rows=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)).select('row_id','origin_year','player_name','elapsed','pa_0','on_40man').to_dicts(),
            support_rows=b.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)).select('origin_year','elapsed','window_complete').to_dicts(),
            roster_rows=r.filter((pl.col('player_id')==pid)&(pl.col('season')==y)).to_dicts()))
    missing=[v for v in records if not v['in_current_panel']]
    for label,record in [('largest_omitted_future_workload',sorted(missing,key=lambda v:(-v['diagnostic_next_pa'],v['origin_year'],v['player_id']))[0]),
                         ('ordinary_omitted_nonarrival',sorted([v for v in missing if not v['diagnostic_next_pa']],key=lambda v:(v['origin_year'],v['player_id']))[0])]:
        cases.append(dict(selection=label,record=record))
    # Additive factual receipt for the preceding value audit, not a new prediction.
    confortocheck=dict(player_id=624424,missing_origin_year=2022,
        panel_history=f.filter(pl.col('player_id')==624424).select('origin_year','player_name','elapsed','pa_0','on_40man').sort('origin_year').to_dicts(),
        roster_rows=r.filter((pl.col('player_id')==624424)&(pl.col('season')==2022)).to_dicts(),
        exact_transaction_cause_verified=False)
    assert not any(v['origin_year']==2022 for v in confortocheck['panel_history']) and not confortocheck['roster_rows']
    OUT.mkdir(parents=True,exist_ok=True); EVIDENCE.mkdir(parents=True,exist_ok=True)
    for name,obj in [('rows.json',records),('cases.json',cases),('conforto-source-check.json',confortocheck)]:
        path=OUT/name; assert not path.exists()
        path.write_text(json.dumps(obj,ensure_ascii=False,allow_nan=False,default=str,indent=2)+'\n',encoding='utf8')
    report=dict(source_hashes={str(p):sha256_file(p) for p in PATHS.values()},summary=summaries,invariance=invariance,
        source_diagnosis='Current membership is snapshot union window-complete post-arrival support; roster presence is a feature, not a membership union.',
        all_current_rows_retained=True,new_fits=0,forecasts_changed=False,protected_2026_opened=False,player_walkthrough_status='pending',
        inclusion_rule_approved=False,retirement_and_source_vintage_unresolved=True)
    (OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    for path in OUT.iterdir():
        target=EVIDENCE/path.name; assert not target.exists(); shutil.copyfile(path,target)
    print(json.dumps(summaries,indent=2))


if __name__=='__main__': main()
