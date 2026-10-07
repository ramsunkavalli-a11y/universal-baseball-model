"""Correct context and expose the tested transparent recipe without a new fit."""
from collections import defaultdict
from pathlib import Path

import polars as pl

from audit_catcher_framing_talent_v4 import ROOT,SOURCE,OUT,PUBLIC,read,write
from universal_baseball.catcher_framing_baseline import history,recover_unknown_age
from universal_baseball.storage import sha256_file
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections


def main():
    protected=protections();final=read(OUT/'final-review.json');verify(final['hashes'])
    assert final['player_walkthrough_status']=='complete' and final['protections']==protected
    source_review=read(OUT/'support-review.json');verify(source_review['hashes'])
    original=pl.read_parquet(OUT/'labels.parquet').to_dicts()
    snapshot_path=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated/opportunity-history-sources-v2/tables/hitter_snapshots.parquet')
    snapshots=defaultdict(list)
    for r in pl.read_parquet(snapshot_path,columns=['snapshot_year','player_id','age_years']).iter_rows(named=True):
        if r['snapshot_year']<=2025:
            snapshots[r['player_id']].append(r)
    corrected=[];repairs=[]
    for r in original:
        new={**r}
        if r['age'] is None:
            recovery=recover_unknown_age(r['origin_year'],snapshots[r['player_id']])
            if recovery['age'] is not None:
                new['age']=recovery['age'];new['age_basis']=recovery['age_basis']
                repairs.append(dict(origin=r['origin_year'],player_id=r['player_id'],name=r['player_name'],original_age=None,**recovery))
        corrected.append(new)
    target=OUT/'corrected-age-context.parquet';assert not target.exists()
    pl.DataFrame(corrected,infer_schema_length=None).write_parquet(target)
    assert all({k:v for k,v in a.items() if k not in ('age','age_basis')}=={k:v for k,v in b.items() if k not in ('age','age_basis')} for a,b in zip(original,corrected))
    rogers=next(r for r in corrected if r['origin_year']==2022 and r['player_id']==668670)
    assert rogers['age']==27 and rogers['history_rate']==next(r['history_rate'] for r in original if r['origin_year']==2022 and r['player_id']==668670)
    native=defaultdict(list)
    for r in pl.read_parquet(SOURCE/'framing-annual.parquet').to_dicts():
        native[r['player_id']].append(r)
    # Verify the reusable recipe matches every sealed old history calculation.
    for r in original:
        h=history(native[r['player_id']],r['origin_year'])
        assert all(abs(h[k]-r[k])<1e-10 for k in ('history_pitches','history_runs','history_rate','reliability','history_seasons'))
    current=[]
    for pid,annual in sorted(native.items()):
        h=history(annual,2025)
        if not h['quality_evidence_observed']:
            continue
        latest=max([s for s in annual if s['season']<=2025],key=lambda s:s['season'])
        age=recover_unknown_age(2025,snapshots[pid])
        current.append(dict(player_id=pid,player_name=latest['player_name'],origin_year=2025,
                    age=age['age'],age_basis=age['age_basis'],**h,
                    framing_quality_per_1000=h['history_rate'],
                    research_only=True,future_pitch_exposure_forecast=False,
                    awarded_framing_value_forecast=False))
    path=OUT/'current-2025-history-baseline.parquet';assert not path.exists()
    pl.DataFrame(current,infer_schema_length=None).write_parquet(path)
    selected=[r for r in current if r['player_id'] in (595978,592663,596142,672275,672386,663728)]
    selected+=sorted(current,key=lambda r:(r['history_pitches'],r['player_id']))[:2]
    walks=[]
    for r in selected:
        peers=sorted([p for p in current if p['player_id']!=r['player_id']],key=lambda p:(abs(p['history_pitches']-r['history_pitches']),p['player_id']))[:3]
        def describe(p):
            return dict(component=p,source=[{**s,'weight':2.**(s['season']-2025)} for s in native[p['player_id']] if 2023<=s['season']<=2025])
        walks.append(dict(primary=describe(r),peers=[describe(p) for p in peers]))
    write('baseline-source-player-walkthrough.json',dict(player_walkthrough_status='complete',source_only=True,cases=walks,
          selection='fixed catchers plus two smallest current weighted exposures; peers closest exposure without quality selection'))
    paths=[target,path,OUT/'baseline-source-player-walkthrough.json',snapshot_path,
           ROOT/'docs/catcher-framing-talent-v4-age-repair.md',ROOT/'src/universal_baseball/catcher_framing_baseline.py',Path(__file__)]
    report=dict(source_correction_applied=True,corrected_unknown_age_rows=len(repairs),repairs=repairs,
                ordinary_origin_unknown_age_before=sum(r['origin_year']==2022 and r['age'] is None for r in original),
                ordinary_origin_unknown_age_after=sum(r['origin_year']==2022 and r['age'] is None for r in corrected),
                preserved_labels_and_all_history_forecasts=True,old_calibration_unchanged_and_not_adopted=True,
                new_model_fit=False,current_component_players=len(current),baseline_recipe_replayed_origins=len(original),
                player_walkthrough_status='complete',protections=protected,
                no_2026_outcomes=True,deployment_approved=False,
                hashes={str(p):sha256_file(p) for p in paths})
    write('baseline-preparation-review.json',report)
    for name in ('baseline-preparation-review.json','baseline-source-player-walkthrough.json'):
        p=PUBLIC/name;assert not p.exists();p.write_bytes((OUT/name).read_bytes())
    print({k:v for k,v in report.items() if k not in ('hashes','protections','repairs')})
    for r in selected:
        print(r['player_name'],r['history_pitches'],r['framing_quality_per_1000'])


if __name__=='__main__':
    main()
