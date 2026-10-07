"""Source through DH forecast walkthrough with outcome-blind origin peers."""

from pathlib import Path
import json
import math
import polars as pl
from universal_baseball.defense_value import position_value
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-budget-v13'
PUBLIC=ROOT/'reports/model-evidence/defense-budget-v13'
FIXED=[(660271,2022),(660271,2023),(660271,2024),(656941,2023),
       (670541,2024),(677951,2024),(805811,2024)]


def read(p): return json.loads(p.read_text(encoding='utf8'))


def main():
    protections(); d=read(OUT/'source-review.json'); v=read(OUT/'independent-verification.json')
    assert v['source_integrity']=='pass' and v['forecast_DH_replays']==12432
    for p,h in {**d['hashes'],**d['output_hashes'],**v['hashes']}.items(): assert sha256_file(Path(p))==h,p
    q=pl.read_parquet(ROOT/'reports/generated/defense-transition-v10/predictions.parquet')
    f=pl.read_parquet(ROOT/'reports/generated/defense-repertoire-v9/features.parquet')
    source=pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet')
    fr={r['row_id']:r for r in f.iter_rows(named=True)}; qr={r['row_id']:r for r in q.iter_rows(named=True)}
    parts={r['row_id']:r for c in d['cells'] for r in c['players']}
    add={(r['season'],r['player_id']):r['certified_dual_starts'] for r in d['corrections']}
    cells={(c['origin'],c['fold']):c for c in d['cells']}
    def walk(rid):
        r=qr[rid]; feat=fr[rid]; part=parts[rid]; y=r['origin_year'];pid=r['player_id']
        hist=source.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y))
        current=hist.filter((pl.col('season')==y)&pl.col('is_mlb'))
        assert current.filter(pl.col('position_code')=='10')['games_started'].sum()==part['raw_current_DH_starts']
        current_outs={str(p):current.filter(pl.col('position_code')==str(p))['fielding_outs'].sum() for p in range(2,10)}
        assert all(current_outs[str(p)]==r[f'carry_{p}'] for p in range(2,10))
        yearly=[]
        for (year,level),g in hist.group_by(['season','normalized_level']):
            yearly.append(dict(season=year,level=level,source_rows=g.height,
                positions=g.group_by('position_code').agg(pl.col('fielding_outs').sum(),pl.col('games_started').sum()).sort('position_code').to_dicts()))
        table=next(t for t in cells[y,r['outer_fold']]['tables'] if t['key']==part['selected_prior'])
        origin_original=part['raw_current_DH_starts']; origin_added=part['certified_current_dual_DH_starts']
        target_added=add.get((y+1,pid),0)
        return dict(player_id=pid,player_name=r['player_name'],origin=y,target_year=y+1,fold=r['outer_fold'],
            stage=r['stage'],age=r['age'],primary_role=feat['repertoire_primary_role'],
            source_history=sorted(yearly,key=lambda x:(x['season'],x['level'])),
            current_MLB_PA=r['pa_0'],origin_raw_DH_starts=origin_original,
            origin_certified_dual_starts=origin_added,origin_reviewed_DH_starts=origin_original+origin_added,
            current_defensive_outs=current_outs,repertoire_fallback=feat['repertoire_fallback_kind'],
            repertoire_shares=feat['repertoire_shares'],current_sample_weight=part['weight'],
            prior=table,expected_PA=r['preseason_pa'],actual_PA=r['next_pa'],
            saved_own_DH=part['own_history_forecast_DH'],saved_prior_DH=part['prior_forecast_DH'],
            saved_forecast_DH=part['forecast_DH'],source_only_own_DH_delta=part['own_source_only_DH_change'],
            source_only_forecast_position_run_delta=-17.5*part['own_source_only_DH_change']/162.,
            actual_raw_DH=part['raw_actual_DH'],actual_reviewed_DH=part['reviewed_actual_DH'],
            actual_position_source_delta=-17.5*target_added/162.,
            saved_forecast_fielding_outs={str(p):r[f'repair_{p}'] for p in range(2,10)},
            actual_fielding_outs={str(p):r[f'actual_{p}'] for p in range(2,10)},
            saved_forecast_position_runs=position_value(r,'repair'),
            original_actual_position_runs=position_value(r,'actual'),
            reviewed_actual_position_runs=position_value(r,'actual')-17.5*target_added/162.,
            unknown_repertoire=feat['repertoire_unknown'],unknown_role_outs=r['repair_unallocated_outs'],
            unchanged_inputs=['batting','expected_PA','defensive_quality','fielding_outs','native_opportunities'],
            qualification='No fitted correction or accuracy verdict. The source-only change holds the saved pooled prior fixed.')
    selected=[]
    for pid,y in FIXED:
        r=next(r for r in qr.values() if r['player_id']==pid and r['origin_year']==y)
        feat=fr[r['row_id']]
        eligible=[x for x in qr.values() if x['origin_year']==y and x['player_id']!=pid and
                  x['stage']==r['stage'] and fr[x['row_id']]['repertoire_primary_role']==feat['repertoire_primary_role']]
        def distance(x):
            da=abs(x['age']-r['age']) if x['age'] is not None and r['age'] is not None else 100.
            return da+abs(math.log1p(x['pa_0'])-math.log1p(r['pa_0'])),x['player_id']
        peers=sorted(eligible,key=distance)[:3]
        selected.append(dict(selection='Fixed source/role cases named in the source contract',
            primary=walk(r['row_id']),eligible_origin_role_stage_peers=len(eligible),
            peer_rule='Same origin, stage and primary role; age difference plus absolute log1p current-MLB-PA distance; ID tie break. No target information.',
            peers=[walk(p['row_id']) for p in peers]))
    controls=[]
    for c in d['corrections']:
        if c['certified_dual_starts']==0:
            controls.append(dict(player_id=c['player_id'],player_name=c['player_name'],season=c['season'],
                pitching_starts=c['pitching_starts'],raw_DH_starts=c['raw_starts'],DH_appearances=c['dh_appearances'],
                reviewed_DH_starts=c['reviewed_starts'],game_evidence=c['game_evidence'],
                reason='No original batting-order slot in any pitching start; DH appearance is not a DH start.'))
    result=dict(player_walkthrough_status='complete',focal_cases=len(selected),peer_walks=sum(len(c['peers']) for c in selected),
        cases=selected,negative_controls=controls,new_fits=0,forecast_or_explorer_changed=False,protected_outcomes_used=False,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'source-review.json',OUT/'independent-verification.json']})
    for dest in (OUT,PUBLIC): save(dest/'player-walkthrough.json',result)
    summary=dict(inventory=d['inventory'],corrections=[{k:v for k,v in c.items() if k!='game_evidence'} for c in d['corrections']],
        population=d['population'],cells=[{k:v for k,v in c.items() if k not in ('players','tables')}|
              {'all_players_prior':next(t for t in c['tables'] if t['key']==['all'])} for c in d['cells']],
        full_audit_path=str((OUT/'source-review.json').resolve()),full_audit_sha256=sha256_file(OUT/'source-review.json'),
        independent_verification=v,player_walkthrough_status='complete',new_fits=0,no_accuracy_claim=True)
    for dest in (OUT,PUBLIC): save(dest/'source-summary.json',summary)
    protections();print('Seven focal and 21 outcome-blind peer walks complete; two negative controls retained.',flush=True)
    for c in selected:
        a=c['primary']
        print(json.dumps({k:a[k] for k in ['player_name','origin','current_MLB_PA','expected_PA','actual_PA',
            'origin_raw_DH_starts','origin_reviewed_DH_starts','saved_own_DH','saved_prior_DH','saved_forecast_DH',
            'source_only_own_DH_delta','actual_raw_DH','actual_reviewed_DH','saved_forecast_position_runs',
            'reviewed_actual_position_runs','current_defensive_outs','saved_forecast_fielding_outs','actual_fielding_outs']}),flush=True)


if __name__=='__main__': main()
