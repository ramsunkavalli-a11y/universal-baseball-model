"""Recover league-specific launch evidence and independent contact/coverage audit."""
import gzip
import json
from pathlib import Path
import polars as pl
from universal_baseball.hitter_statcast_measurement import project_measurements, interference_award
from universal_baseball.hitter_statcast_history import annual_launch_features
from universal_baseball.storage import sha256_file
import capture_hitter_minor_statcast as capture
import review_hitter_minor_statcast_pilot as pilot

ROOT=capture.ROOT;SOURCE=capture.OUT;OUT=ROOT/'reports/generated/hitter-minor-statcast-source'


def write(name,value):capture.write(OUT/name,value)


def parquet(frame,name):
    path=OUT/name
    if path.exists():
        previous=pl.read_parquet(path)
        assert frame.sort(frame.columns).equals(previous.sort(previous.columns)),f'Different partial source: {path}'
    else:frame.write_parquet(path)


def schedules(year):
    rows=[];hashes={}
    for sport in [11,12,13,14,16]:
        p=SOURCE/'official-context'/f'schedule-{year}-{sport}.json.gz'
        r=json.loads(p.with_suffix('').read_text(encoding='utf8'))
        assert r['compressed_sha256']==sha256_file(p)
        data=json.loads(gzip.decompress(p.read_bytes()));hashes[str(p)]=sha256_file(p)
        hashes[str(p.with_suffix(''))]=sha256_file(p.with_suffix(''))
        for day in data['dates']:
            for g in day['games']:
                state=g['status']['detailedState']
                if not (state.startswith('Final') or state.startswith('Completed Early')):continue
                away=g['teams']['away']['team'];home=g['teams']['home']['team']
                assert away['league']['id']==home['league']['id']
                rows.append(dict(season=year,game_pk=int(g['gamePk']),league_id=int(home['league']['id']),sport_id=sport,
                    venue_id=g['venue']['id'],venue_name=g['venue']['name'],official_date=g['officialDate'],
                    segment_start=g['gameDate'],resume_date=g.get('resumeDate'),detailed_state=state,
                    home_team_id=home['id'],away_team_id=away['id']))
    frame=pl.DataFrame(rows,infer_schema_length=None).unique()
    conflict=frame.group_by('game_pk').agg(pl.col('venue_id').n_unique().alias('venue_count')).filter(pl.col('venue_count')>1)
    assert frame.group_by('game_pk').agg(pl.col('league_id').n_unique()).filter(pl.col('league_id')>1).is_empty()
    unique=frame.filter(~pl.col('game_pk').is_in(conflict['game_pk'].to_list())).unique('game_pk')
    return frame,unique,conflict,hashes


def main():
    assert not (OUT/'source-report.json').exists(),'Preserve completed source'
    capture_report=json.loads((SOURCE/'season-capture.json').read_text(encoding='utf8'))
    pilot.checked_receipts(capture_report)
    assert capture_report['contract_sha256']==sha256_file(capture.CONTRACT)
    OUT.mkdir(parents=True,exist_ok=True)
    hashes={str(Path(__file__)):sha256_file(Path(__file__)),str(capture.CONTRACT):sha256_file(capture.CONTRACT),
        str(SOURCE/'season-capture.json'):sha256_file(SOURCE/'season-capture.json')}
    summaries=[];annuals=[];coverages=[];residuals=[];contexts=[]
    for year in range(2021,2025):
        env,h=pilot.environments(year);hashes.update(h)
        schedule,unique,conflict,h=schedules(year);hashes.update(h)
        files=[Path(p) for r in capture_report['receipts'] if int(r['start'][:4])==year for p in r['outputs'] if p.endswith('.parquet')]
        for r in capture_report['receipts']:
            if int(r['start'][:4])==year:hashes.update(r['outputs'])
        raw=pl.concat([pl.read_parquet(p) for p in files]);assert raw.unique(capture.KEY).height==len(raw)
        all_keys=raw.with_columns(pl.col('game_pk').cast(pl.Int64),pl.col('batter').cast(pl.Int64).alias('player_id'))
        joined=all_keys.join(env.select('game_pk','player_id','league_id','level_group'),on=['game_pk','player_id'],how='left',validate='m:1')
        unmatched=joined.filter(pl.col('league_id').is_null());parquet(unmatched,f'unmatched-{year}.parquet')
        terminal=raw.filter(pl.col('events').fill_null('').str.strip_chars().ne(''))
        launch,excluded=project_measurements(terminal,year)
        nonterminal=raw.filter(pl.col('events').fill_null('').str.strip_chars().eq('')).with_columns(pl.lit('not_terminal_inplay').alias('measurement_exclusion'))
        excluded=pl.concat([excluded,nonterminal],how='diagonal_relaxed')
        parquet(excluded,f'excluded-{year}.parquet')
        launch=launch.join(env.select('game_pk','player_id','league_id','level_group'),on=['game_pk','player_id'],how='left',validate='m:1')
        launch=launch.join(unique.select('game_pk','venue_id','venue_name','home_team_id','away_team_id'),on='game_pk',how='left',validate='m:1')
        parquet(launch,f'launch-events-{year}.parquet')
        source_games=all_keys['game_pk'].unique().to_list()
        absent_schedule=sorted(set(source_games)-set(schedule['game_pk'].to_list()))
        affected_conflicts=conflict.filter(pl.col('game_pk').is_in(source_games))
        contexts.append(dict(season=year,unmatched_schedule_game_pks=absent_schedule,
            split_venue_games=schedule.filter(pl.col('game_pk').is_in(affected_conflicts['game_pk'].to_list())).to_dicts()))
        normal=terminal.filter((pl.col('events')!='catcher_interf')&~interference_award()).with_columns(
            pl.col('game_pk').cast(pl.Int64),pl.col('batter').cast(pl.Int64).alias('player_id'))
        counts=normal.group_by('game_pk','player_id').agg(pl.len().alias('source_contacts'))
        official=env.filter(pl.col('game_pk').is_in(source_games))
        paired=official.join(counts,on=['game_pk','player_id'],how='full',coalesce=True,validate='1:1').with_columns(pl.col('source_contacts').fill_null(0))
        paired=paired.with_columns((pl.col('source_contacts')-pl.col('expected_contact_count')).alias('contact_residual'))
        bad=paired.filter(pl.col('contact_residual').fill_null(999)!=0);parquet(bad,f'contact-residuals-{year}.parquet')
        residuals.extend(bad.to_dicts())
        coverage=schedule.unique('game_pk').group_by('season','league_id','sport_id').agg(pl.len().alias('official_completed_games'))
        returned=joined.group_by('league_id').agg(pl.col('game_pk').n_unique().alias('returned_games'))
        measured=launch.group_by('league_id').agg(pl.len().alias('nonbunt_contacts'),pl.col('complete_pair').sum().alias('pairs'),
            pl.col('valid_ev').sum().alias('ev_contacts'),pl.col('valid_la').sum().alias('la_contacts'))
        coverage=coverage.join(returned,on='league_id',how='left').join(measured,on='league_id',how='left').fill_null(0).sort('league_id')
        coverages.append(coverage)
        yearly=[]
        for league in launch['league_id'].drop_nulls().unique().sort():
            q=launch.filter(pl.col('league_id')==league)
            a=annual_launch_features(q).with_columns(pl.lit(int(league)).alias('league_id'),pl.lit(q['level_group'][0]).alias('level_group'))
            yearly.append(a)
        yearly=pl.concat(yearly);parquet(yearly,f'annual-{year}.parquet');annuals.append(yearly)
        month=launch.group_by('season','league_id',pl.col('game_date').dt.month().alias('month')).agg(
            pl.len().alias('contacts'),pl.col('complete_pair').sum().alias('pairs'),pl.col('game_pk').n_unique().alias('games'))
        parquet(month.sort('league_id','month'),f'monthly-coverage-{year}.parquet')
        venues=launch.group_by('season','league_id','venue_id','venue_name').agg(pl.len().alias('contacts'),
            pl.col('complete_pair').sum().alias('pairs'),pl.col('game_pk').n_unique().alias('games'))
        parquet(venues,f'venue-coverage-{year}.parquet')
        summaries.append(dict(season=year,raw_rows=len(raw),terminal_rows=len(terminal),canonical_contacts=len(launch),
            complete_pairs=int(launch['complete_pair'].sum()),unmatched_identity_rows=len(unmatched),
            unexplained_player_game_contact_residuals=len(bad),unmatched_schedule_games=len(absent_schedule),
            source_split_venue_games=len(affected_conflicts),invalid_ev=int(launch['invalid_ev'].sum()),invalid_la=int(launch['invalid_la'].sum())))
        print(json.dumps(summaries[-1]),flush=True)
    parquet(pl.concat(annuals),'annual-launch-features.parquet')
    parquet(pl.concat(coverages),'league-coverage.parquet')
    write('contact-residual-review.json',dict(cases=residuals,approval=False))
    write('schedule-context-review.json',dict(seasons=contexts,approval=False))
    outputs={str(p):sha256_file(p) for p in OUT.iterdir() if p.is_file()}
    write('source-report.json',dict(seasons=summaries,input_hashes=hashes,output_hashes=outputs,model_fits=0,
        source_walkthrough_status='pending',source_approved=False,protected_outcomes_used=False))


if __name__=='__main__':main()
