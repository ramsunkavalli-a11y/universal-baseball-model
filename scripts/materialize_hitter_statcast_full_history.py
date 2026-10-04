"""Historical measurement source with explicit interference and played venues."""
import json
from datetime import datetime
from pathlib import Path
import polars as pl
from universal_baseball.hitter_statcast_measurement import project_measurements,annual_launch_features,interference_award
from universal_baseball.hitter_statcast_history import KEY
from universal_baseball.mlb_contact_history import RAW_COLUMNS
from universal_baseball.mlb_performance import assign_savant_actual_league
from universal_baseball.mlb_season_stats import MlbTeamLeague
from universal_baseball.storage import sha256_file
import recover_hitter_own_mlb_contact as old
import capture_hitter_statcast_official_context as context

ROOT=old.ROOT
OUT=ROOT/'reports/generated/hitter-statcast-full-history'
BOUNDARY=ROOT/'docs/hitter-statcast-measurement-boundary.md'


def checked_report(path):
    r=old.read(path)
    for group in ['source_hashes','output_hashes','input_hashes']:
        for p,h in r.get(group,{}).items():old.checked(Path(p),h)
    return r


def split_venues(year,schedule):
    conflicts=old.read(context.OUT/f'actual-schedule-review-{year}.json')['conflicts']
    rows=[]
    for c in conflicts:
        pk=c['game_pk']
        segments=[g for d in schedule['dates'] for g in d['games'] if g['gamePk']==pk
            and g['status']['detailedState'].split(':')[0] in {'Final','Completed Early'}]
        segments=sorted(segments,key=lambda g:g['gameDate'])
        assert len(segments)==2 and segments[0].get('resumeDate')==segments[1]['gameDate']
        feed=old.read(context.OUT/f'feed-{year}-{pk}.json')
        assert feed['gameData']['datetime']['resumeDateTime']==segments[1]['gameDate']
        threshold=datetime.fromisoformat(segments[1]['gameDate'].replace('Z','+00:00'))
        for play in feed['liveData']['plays']['allPlays']:
            terminal=datetime.fromisoformat(play['about']['endTime'].replace('Z','+00:00'))
            segment=segments[int(terminal>=threshold)]
            rows.append(dict(game_pk=pk,at_bat_number=play['atBatIndex']+1,venue_id=segment['venue']['id'],
                venue_name=segment['venue']['name'],terminal_timestamp=play['about']['endTime'],
                segment_start=segment['gameDate'],source='completed_schedule_plus_terminal_feed'))
    return rows


def classify_residuals():
    review=old.read(context.OUT/'contact-residual-play-review.json'); classifications=[]; noncontacts=[]; awards=[]
    for case in review['cases']:
        assert case['gamelog_matches_prior']
        for game in case['games']:
            comparison=game['game_comparison']; change=comparison['residual']; assert abs(change)==1
            if change<0:
                selected=[p for p in game['official_player_plays'] if p['official_event']=='field_out'
                    and p['source'] is None and not p['inplay_pitch_events']
                    and 'out on batter interference' in p['official_description'].lower()]
                label='official_AB_without_physical_contact'
            else:
                selected=[p for p in game['official_player_plays'] if p['official_event']=='field_error'
                    and p['source'] and 'reaches on an interference error' in p['official_description'].lower()]
                label='interference_award_without_official_AB'
            assert len(selected)==1,'Unexplained source discrepancy'
            record=dict(season=case['season'],player_id=case['player_id'],player_name=case['player_name'],
                game_pk=comparison['game_pk'],at_bat_number=selected[0]['at_bat_index']+1,
                residual=change,classification=label,official_description=selected[0]['official_description'])
            classifications.append(record)
            (noncontacts if change<0 else awards).append(record)
    assert len(classifications)==20 and len(noncontacts)==13 and len(awards)==7
    return classifications,noncontacts,awards


def main():
    assert not (OUT/'source-report.json').exists(),'Preserve completed source'
    OUT.mkdir(parents=True,exist_ok=True)
    audit_path=ROOT/'reports/generated/hitter-statcast-historical-capture-audit/report.json'
    audit=checked_report(audit_path)
    capture=checked_report(context.OUT/'capture-report.json')
    pilot=checked_report(old.OUT/'source-report.json')
    checked_report(ROOT/'reports/generated/hitter-statcast-history/source-report.json')
    fixed,noncontacts,awards=classify_residuals()
    old.write(OUT/'residual-classifications.json',dict(cases=fixed,all_explained=True,unchanged_raw_responses=True))
    dated=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet').filter(pl.col('bucket')=='MLB')
    hashes={str(p):sha256_file(p) for p in [BOUNDARY,Path(__file__),
        ROOT/'src/universal_baseball/hitter_statcast_measurement.py',ROOT/'src/universal_baseball/hitter_statcast_history.py',
        audit_path,context.OUT/'capture-report.json',context.OUT/'contact-residual-play-review.json',
        ROOT/'reports/generated/hitter-statcast-history/source-report.json',old.OUT/'cases.json',old.CURRENT/'features.parquet',old.CURRENT/'preflight.json']}
    annual=[]; years=[]; detail={}; overrides=[]
    for year in range(2015,2025):
        if year<2023:
            raw=pl.concat([pl.read_parquet(context.SOURCE/f'{year}-{m:02}.parquet') for m in range(3,11)])
            venues=pl.read_parquet(context.OUT/f'actual-venues-{year}.parquet')
            team=old.read(context.OUT/f'teams-{year}.json')
            override=split_venues(year,old.read(context.OUT/f'schedule-{year}.json'))
            overrides.extend(dict(season=year,**r) for r in override)
            official=dated.filter(pl.col('season')==year).group_by('player_id').agg(
                (pl.col('at_bats')-pl.col('strike_outs')+pl.col('sac_flies')+pl.col('sac_bunts')).sum().alias('official_contacts'))
            correction={r['player_id']:1 for r in noncontacts if r['season']==year}
            official=official.with_columns(pl.Series('noncontact_AB',[correction.get(p,0) for p in official['player_id']]))
            normal=raw.filter((pl.col('events')!='catcher_interf')&~interference_award()).group_by(
                pl.col('batter').cast(pl.Int64).alias('player_id')).agg(pl.len().alias('source_contacts'))
            reconciled=official.join(normal,on='player_id',how='full',coalesce=True).fill_null(0)
            assert reconciled.select((pl.col('official_contacts')-pl.col('noncontact_AB')==pl.col('source_contacts')).all()).item()
            assert len(raw.filter(interference_award()))==len([r for r in awards if r['season']==year])
        else:
            base=old.CACHE/f'mlb-{year}'
            legacy=old.read(base/f'reports/generated/current-talent-historical-mlb-game-evidence/{year}/report.json')
            team=old.read(base/legacy['source']['team_authority']['raw_path'])
            source=pl.read_parquet(old.OUT/f'events-{year}.parquet')
            venues=source.select('game_pk','venue_id','venue_name').unique()
            assert venues.unique('game_pk').height==len(venues)
            raw=pl.concat([pl.read_csv(base/c['raw_path'],columns=RAW_COLUMNS+['launch_speed','launch_angle'],
                schema_overrides={n:pl.String for n in RAW_COLUMNS+['launch_speed','launch_angle']},
                null_values=['null','NaN','nan','']) for c in legacy['source']['savant_captures']])
            raw=raw.filter(pl.col('game_type')=='R')
            # Pilot source includes nonterminal physical contacts. Measurement projection requires terminal records only.
            raw=raw.filter(pl.col('events').fill_null('').str.strip_chars().ne(''))
            override=[]
        q,excluded=project_measurements(raw,year)
        q=q.join(venues.select('game_pk','venue_id','venue_name'),on='game_pk',how='left',validate='m:1')
        if override:
            ov=pl.DataFrame(override).select('game_pk','at_bat_number',pl.col('venue_id').alias('override_venue'),
                pl.col('venue_name').alias('override_name'))
            q=q.join(ov,on=['game_pk','at_bat_number'],how='left',validate='1:1')
            split_keys={r['game_pk'] for r in override}
            assert q.filter(pl.col('game_pk').is_in(split_keys)&pl.col('override_venue').is_null()).is_empty()
            q=q.with_columns(pl.coalesce('override_venue','venue_id').alias('venue_id'),
                pl.coalesce('override_name','venue_name').alias('venue_name')).drop('override_venue','override_name')
        assert q['venue_id'].null_count()==0 and q['invalid_ev'].sum()==0 and q['invalid_la'].sum()==0
        # Season-specific batting-team league authority, using physical terminal keys.
        identity=raw.select(pl.col('game_year').cast(pl.Int64),pl.col('game_pk').cast(pl.Int64),
            (pl.col('at_bat_number').cast(pl.Int64)-1).alias('at_bat_index'),pl.col('pitch_number').cast(pl.Int64),
            pl.when(pl.col('inning_topbot')=='Top').then(pl.col('away_team')).otherwise(pl.col('home_team')).alias('batting_team'))
        identity=identity.with_columns(pl.col('batting_team').replace({'ATH':'OAK'}))
        teams=[MlbTeamLeague(team_id=t['id'],abbreviation=t['abbreviation'],league_id=t['league']['id'],
            league_name=t['league']['name']) for t in team['teams'] if t.get('league',{}).get('id') in [103,104]]
        league=assign_savant_actual_league(identity,teams).with_columns((pl.col('at_bat_index')+1).alias('at_bat_number'))
        q=q.join(league.select('game_pk','at_bat_number','pitch_number','league_id'),on=['game_pk','at_bat_number','pitch_number'],how='left',validate='1:1')
        assert q['league_id'].null_count()==0
        features=annual_launch_features(q); annual.append(features)
        q.write_parquet(OUT/f'launch-events-{year}.parquet'); excluded.write_parquet(OUT/f'excluded-{year}.parquet')
        years.append(dict(season=year,nonbunt_contacts=len(q),complete_pairs=int(q['complete_pair'].sum()),
            missing_pairs=int((~q['complete_pair']).sum()),people=q['player_id'].n_unique(),games=q['game_pk'].n_unique(),
            interference_awards=int(excluded.filter(pl.col('measurement_exclusion')=='interference_award').height),
            exact_corrected_normal_contact_reconciliation=(True if year<2023 else 'previous_accepted_pilot'),
            split_game_venue_contacts=q.filter(pl.col('game_pk').is_in([r['game_pk'] for r in override]))
                .group_by('game_pk','venue_id','venue_name').len().to_dicts()))
        print(year,len(q),int(q['complete_pair'].sum()),'complete pairs; context and count checks passed',flush=True)
        detail[year]=q
    annual=pl.concat(annual).sort('season','player_id'); annual.write_parquet(OUT/'annual-launch-features.parquet')
    f=pl.read_parquet(old.CURRENT/'features.parquet'); pre=old.read(old.CURRENT/'preflight.json')
    lookup={(r['season'],r['player_id']):r['measured_pair_contacts'] for r in annual.iter_rows(named=True)}
    coverage=f.select('row_id','origin_year','target_year','player_id','outer_fold','prior_debut','stage','age','next_pa').with_columns(
        pl.Series('own_mlb_launch_pairs',[sum(lookup.get((r['origin_year']-lag,r['player_id']),0) for lag in range(3)) for r in f.iter_rows(named=True)]),
        pl.Series('available_history_seasons',[sum(2015<=r['origin_year']-lag<=2024 for lag in range(3)) for r in f.iter_rows(named=True)]))
    coverage.write_parquet(OUT/'forecast-source-coverage.parquet'); cells=[]
    for c in pre['cells']:
        tr=coverage.filter(pl.col('row_id').is_in(c['training_row_ids'])); te=coverage.filter(pl.col('row_id').is_in(c['test_row_ids']))
        assert tr['target_year'].max()<=c['year'] and not tr['outer_fold'].eq(c['fold']).any()
        active=tr.filter((pl.col('next_pa')>0)&(pl.col('own_mlb_launch_pairs')>0))
        cells.append(dict(origin_year=c['year'],fold=c['fold'],active_training_rows=len(active),
            active_training_people=active['player_id'].n_unique(),tracked_test_people=te.filter(pl.col('own_mlb_launch_pairs')>0)['player_id'].n_unique(),
            training_origins=sorted(active['origin_year'].unique().to_list()),
            sample_support=active.with_columns(pl.when(pl.col('own_mlb_launch_pairs')<50).then(pl.lit('under50')).when(pl.col('own_mlb_launch_pairs')<200)
                .then(pl.lit('50to199')).otherwise(pl.lit('200plus')).alias('sample_band'))
                .group_by('sample_band').agg(pl.col('player_id').n_unique().alias('people')).to_dicts()))
    cases=old.read(old.OUT/'cases.json'); walks=[]
    for case in cases['cases']:
        o=case['origin']; year=o['origin_year']; pid=o['player_id']
        walks.append(dict(**case,full_launch_history=annual.filter((pl.col('player_id')==pid)&pl.col('season').is_between(year-2,year)).to_dicts(),
            full_venue_history=[dict(season=y,venues=q.filter(pl.col('player_id')==pid).group_by('venue_id','venue_name').len().to_dicts())
                for y,q in detail.items() if year-2<=y<=year],tracking_candidate_forecast=None,forecasts_changed=False))
    old.write(OUT/'cases.json',dict(source_only=True,cases=walks,selection_rules=cases['selection_rules'],peer_rule=cases['peer_rule']))
    old.write(OUT/'split-game-venue-overrides.json',dict(overrides=overrides,source_only=True))
    for p in context.OUT.glob('*'):
        if p.is_file():hashes[str(p)]=sha256_file(p)
    old.write(OUT/'source-report.json',dict(source_only=True,new_model_fits=0,forecasts_changed=False,protected_outcomes_used=False,
        source_walkthrough_status='pending_readable_review',source_approval=False,years=years,actual_fold_support=cells,
        complete_pairs_total=sum(r['complete_pairs'] for r in years),provider_imputation_flags_available=False,
        original_publication_vintage_known=False,raw_metrics_not_park_or_opponent_adjusted=True,source_hashes=hashes,
        output_hashes={str(p):sha256_file(p) for p in OUT.glob('*') if p.is_file()}))


if __name__=='__main__':main()
