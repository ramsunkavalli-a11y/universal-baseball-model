"""Assemble dated 2026-origin inputs; no forecast fitting or rights inference."""
from pathlib import Path
from datetime import date
import gzip
import json
import numpy as np
import polars as pl
from universal_baseball.hitter_origin_base_v1 import base_inputs
from universal_baseball.hitter_origin_inputs_v1 import pooled_inputs
from universal_baseball.hitter_origin_tracking_v1 import materialize_tracking
from universal_baseball.hitter_value_panel import build_neutral_mlb_value_targets
from universal_baseball.historical_prospect_rank import features as rank_features
from universal_baseball.storage import sha256_file
from prepare_hitter_games_v38 import features as game_features
from capture_hitter_2027_origin_counts import write_once

ROOT=Path(__file__).resolve().parents[1]
OLD=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')
OUT=ROOT/'reports/generated/hitter-2027-base'
MEM=ROOT/'reports/generated/hitter-2027-membership-source'
CURRENT=ROOT/'reports/generated/hitter-2027-origin-counts'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'


def main():
    assert not (PUBLIC/'base-assembly.json').exists(),'Preserve completed assembly'
    OUT.mkdir(parents=True,exist_ok=True)
    paths=[]
    def read(path):
        paths.append(path);return pl.read_parquet(path)
    oldst=read(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    newst=read(CURRENT/'team-season-inputs.parquet')
    stints=pl.concat([oldst,newst.select(oldst.columns)],how='vertical_relaxed')
    counts=pl.concat([read(ROOT/'reports/generated/practical-hitter-v31/counts.parquet'),read(CURRENT/'counts.parquet')],how='vertical_relaxed')
    assert counts.unique(['season','player_id','bucket']).height==len(counts)
    values=read(ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet')
    # Same fixed linear weights and 10 runs/win as the historical predictor;
    # only replacement scales to completed games. Not full WAR.
    required=['plate_appearances','hits','doubles','triples','home_runs','base_on_balls','intentional_walks','hit_by_pitch']
    batting=newst.filter(pl.col('sport_id')==1).group_by('season','player_id').agg(pl.col(required).sum())
    newvalues=build_neutral_mlb_value_targets(batting.rename({c:'batting_'+c for c in required}))
    schedule_path=ROOT/'reports/generated/hitter-final-2026-source/captures/regular-season-schedule-2026.json.gz'
    paths.append(schedule_path)
    schedule=json.loads(gzip.decompress(schedule_path.read_bytes()))
    gameids={g['gamePk'] for d in schedule['dates'] for g in d['games'] if g['gameType']=='R' and g['status']['codedGameState']=='F'}
    assert len(gameids)==2429
    leaguepa=int(batting['plate_appearances'].sum());assert leaguepa==183849
    fraction=len(gameids)/2430
    newvalues=newvalues.with_columns(pl.col('component_war').alias('legacy_component_war'),
        (pl.col('component_war')+570*(fraction-1)*pl.col('mlb_pa')/leaguepa).alias('component_war'),
        pl.lit(leaguepa).alias('league_pa'),pl.lit(len(gameids)).alias('completed_games'),pl.lit(30).alias('teams'),
        pl.lit(fraction).alias('schedule_fraction')).with_columns(
        (600*pl.col('component_war')/pl.col('mlb_pa')).alias('conditional_component_war_per_600'))
    assert np.isclose(newvalues['component_war'].sum(),570*fraction)
    values=pl.concat([values,newvalues.select(values.columns)],how='vertical_relaxed')
    bios=read(MEM/'bios.parquet');candidates=read(MEM/'roster-candidates.parquet')
    frozen=read(ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05/forecast.parquet')
    ids=sorted(set(newst.filter(pl.col('position')!='1')['player_id'])|set(frozen['player_id'])|
        set(candidates.filter(pl.col('position_code')!='1')['player_id']))
    assert set(ids)<=set(bios['player_id'])
    primary=newst.filter(pl.col('plate_appearances')>0).sort(['plate_appearances','team_id'],descending=[True,False]).unique('player_id')
    age=newst.filter(pl.col('plate_appearances')>0).group_by('player_id').agg(pl.col('reported_age').median().alias('age'))
    pop=pl.DataFrame({'player_id':ids}).join(age,on='player_id',how='left').join(
        primary.select('player_id',pl.col('level_group').alias('snapshot_level')),on='player_id',how='left').join(
        bios.select('player_id','birth_date'),on='player_id',how='left')
    # Preserve the existing reported-season-age convention when stats exist.
    pop=pop.with_columns(pl.coalesce('age',((pl.lit(date(2026,7,1))-pl.col('birth_date').str.to_date()).dt.total_days()/365.25)).alias('age'),
        pl.col('snapshot_level').fill_null('INACTIVE'),pl.lit(2026).alias('origin_year'),
        (pl.col('player_id')+2_000_000_000).alias('row_id')).drop('birth_date')
    debuts=read(ROOT/'reports/generated/hitter-arrival-source-repair-v1/debut-dates.parquet')
    current_debuts=bios.filter(pl.col('debut_date').is_not_null()).select('player_id',pl.col('debut_date').str.to_date().alias('mlb_debut_date'))
    old_dates=debuts.select('player_id','mlb_debut_date')
    comparison=old_dates.join(current_debuts,on='player_id',suffix='_current').filter(pl.col('mlb_debut_date')!=pl.col('mlb_debut_date_current'))
    assert comparison.is_empty(),'Conflicting debut dates need review'
    debuts=pl.concat([old_dates,current_debuts.join(old_dates.select('player_id'),on='player_id',how='anti')]).sort('player_id')
    roster=read(ROOT/'reports/generated/hitter-arrival-source-repair-v1/year-end-rosters.parquet').select('season','player_id','team_id')
    r25=read(ROOT/'reports/generated/hitter-rosters-2025-source/year-end-2025.parquet').select(roster.columns)
    r26=read(MEM/'forty-man.parquet').select(roster.columns)
    roster=pl.concat([roster,r25,r26],how='vertical_relaxed')
    base=base_inputs(pop,stints,counts,values,debuts,roster,source_cutoff=2026)
    base=base.join(bios.select('player_id',pl.col('player_name').alias('_bio_name')),on='player_id',validate='1:1').with_columns(
        pl.coalesce('player_name','_bio_name').alias('player_name')).drop('_bio_name')
    draft=read(OLD/'draft-history/draft-history.parquet').filter(pl.col('draft_year')<=2025)
    draft_fields=['player_id','draft_year','pick_number','school_class','drafted'];draft=draft.select(draft_fields)
    picks=[]
    for path in sorted((MEM/'captures').glob('people-*.json.gz')):
        paths.append(path)
        for person in json.loads(gzip.decompress(path.read_bytes()))['people']:
            for d in person.get('drafts',[]):
                if int(d.get('year',0))==2026 and d.get('isDrafted') and int(d.get('pickNumber',0))>0:
                    picks.append(dict(player_id=person['id'],draft_year=2026,pick_number=int(d['pickNumber']),
                        school_class=d.get('school',{}).get('schoolClass',''),drafted=True))
    if picks:draft=pl.concat([draft,pl.DataFrame(picks).select(draft_fields)],how='vertical_relaxed').unique()
    out=base.join(pooled_inputs(base,counts,draft,source_cutoff=2026),on='row_id',validate='1:1')
    games=read(ROOT/'reports/generated/practical-hitter-v38/game-counts.parquet')
    newgames=newst.group_by('season','player_id','bucket').agg(pl.col('plate_appearances','games_played').sum()).select(games.columns)
    games=pl.concat([games,newgames],how='vertical_relaxed')
    paired=counts.select('season','player_id','bucket','plate_appearances').join(games,on=['season','player_id','bucket'],how='full',coalesce=True,validate='1:1')
    assert paired['plate_appearances'].equals(paired['plate_appearances_right']) and paired['games_played'].null_count()==0
    out,_=game_features(out,games)
    ranks=pl.concat([read(ROOT/'reports/generated/hitter-preseason-readiness-v67/ranks.parquet'),
        read(ROOT/'reports/generated/hitter-preseason-2026-archive-probe/preseason-2026-ranks.parquet')])
    lookup={(r['season'],r['player_id']):r['rank'] for r in ranks.iter_rows(named=True)}
    capacities={r['season']:r['list_capacity'] for r in ranks.iter_rows(named=True)}
    assert max(capacities)==2026
    records=[dict(row_id=r['row_id'],**rank_features(r['player_id'],2027,lookup,capacities)) for r in out.iter_rows(named=True)]
    overlay=pl.DataFrame(records,schema_overrides={c:pl.Float64 for c in records[0] if c.startswith('scout_')})
    scout=[c for c in overlay.columns if c.startswith('scout_')]
    out=out.join(overlay.with_columns(pl.col(scout).fill_null(-1.)),on='row_id',validate='1:1')
    annual=read(ROOT/'reports/generated/hitter-tracking-2026-source/review/annual-launch-features-through-2026.parquet')
    out,_,_=materialize_tracking(out,annual,source_cutoff=2026)
    assert not any(c.startswith('next_') for c in out.columns)
    assert len(out)==len(ids) and out['player_id'].n_unique()==len(ids)
    outputs={}
    for name,frame in dict(membership=pop,base_inputs=base,assembled=out,counts=counts,stints=stints,values=values,draft=draft,games=games,debuts=debuts).items():
        path=OUT/f'{name}.parquet';assert not path.exists();frame.write_parquet(path);outputs[str(path)]=sha256_file(path)
    write_once(PUBLIC/'base-assembly.json',dict(as_of='2026-10-09',origin=2026,forecast_year=2027,population=len(out),
        fitted=False,source_player_walkthrough='pending',stages=out.group_by('stage').len().to_dicts(),
        draft2026_people=len(picks),source2026_pa=leaguepa,completed_games=len(gameids),
        missing2027_preseason_list=True,rank_handling='Unavailable current list is missing, not unranked; prior published lists retain their actual lag.',
        organization_rights_certified=False,availability_pending=True,
        input_hashes={str(p):sha256_file(p) for p in paths},output_hashes=outputs,runner_sha256=sha256_file(Path(__file__))))
    print(f'Assembled {len(out)} 2027 rows, {len(picks)} current draft records; no fitted forecasts yet.',flush=True)


if __name__=='__main__':main()
