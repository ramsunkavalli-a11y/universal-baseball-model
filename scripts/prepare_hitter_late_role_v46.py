"""Capture and verify two nonoverlapping historical MLB usage windows."""
from datetime import date,timedelta,datetime,timezone
from pathlib import Path
import json
import requests
import polars as pl
from universal_baseball.storage import sha256_file
from universal_baseball.mlb_usage_window import project_mlb_usage_date_range_payload
import evaluate_hitter_poisson_v45 as e

ROOT=e.ROOT;OUT=ROOT/'reports/generated/practical-hitter-late-role-v46'
YEARS=range(2010,2025)
FIXED=[(701762,2024),(683011,2022),(592450,2016),(592450,2024),(667670,2022),(405395,2021),(621020,2016),(621311,2016),(665487,2022)]


def write(n,o):
    p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,indent=2,default=str,allow_nan=False),encoding='utf8')


def strict_frame(payload,y):
    b=payload['stats'][0]
    assert b['type']['displayName']=='byDateRange' and b['group']['displayName']=='hitting'
    ids=[]
    for s in b['splits']:
        assert s['season']==str(y) and s['sport']['id']==1
        assert 'plateAppearances' in s['stat'] and 'gamesPlayed' in s['stat']
        ids.append(s['player']['id'])
    assert len(set(ids))==len(ids),'Aggregate and team splits or duplicated player'
    f=project_mlb_usage_date_range_payload(payload,group='hitting')
    assert (f['workload']==f['workload'].floor()).all()
    return f.rename({'workload':'pa'}).drop('starts')


def capture():
    assert e.r.read(e.OUT/'report.json')['player_walkthrough_status']=='complete'
    session=requests.Session();manifest=[];rows=[];notes=[]
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet').filter(pl.col('bucket')=='MLB')
    games=pl.read_parquet(e.BASE/'game-counts.parquet').filter(pl.col('bucket')=='MLB')
    for y in YEARS:
        schedule=OUT/f'captures/{y}-schedule.json';schedule_meta=OUT/f'captures/{y}-schedule-request.json'
        schedule_request=requests.Request('GET','https://statsapi.mlb.com/api/v1/schedule',params=dict(sportId=1,season=y,gameType='R',fields='dates,date,games,gamePk,gameType,officialDate,status,abstractGameState,codedGameState,detailedState,teams,away,home,team,id')).prepare()
        if not schedule.exists():
            response=session.send(schedule_request,timeout=60);response.raise_for_status();schedule.parent.mkdir(parents=True,exist_ok=True);schedule.write_bytes(response.content)
            write(schedule_meta.relative_to(OUT),dict(url=schedule_request.url,captured_utc=datetime.now(timezone.utc).isoformat(),sha256=sha256_file(schedule)))
        schedule_metadata=e.r.read(schedule_meta);assert schedule_metadata['url']==schedule_request.url and schedule_metadata['sha256']==sha256_file(schedule)
        p=e.r.read(schedule);known={};ignored=0
        for d in p['dates']:
            for g in d['games']:
                assert g['gameType']=='R'
                if g['status']['codedGameState'] not in ['F','O']:
                    ignored+=1;continue
                assert g['status']['abstractGameState']=='Final'
                value=(date.fromisoformat(g['officialDate']),g['teams']['home']['team']['id'],g['teams']['away']['team']['id'])
                assert g['gamePk'] not in known or known[g['gamePk']]==value
                known[g['gamePk']]=value
        final=max(v[0] for v in known.values());assert final.year==y and final<=date(y,12,31)
        late_start=final-timedelta(days=29);early_end=late_start-timedelta(days=1);early_start=early_end-timedelta(days=29)
        intervals=[('annual',date(y,1,1),date(y,12,31)),('preceding',early_start,early_end),('late',late_start,final)]
        frames={};windows={}
        for label,start,end in intervals:
            dest=OUT/f'captures/{y}-{label}.json';meta=OUT/f'captures/{y}-{label}-request.json'
            params=dict(stats='byDateRange',group='hitting',sportIds=1,startDate=start.strftime('%m/%d/%Y'),endDate=end.strftime('%m/%d/%Y'),playerPool='ALL',gameType='R',limit=5000)
            request=requests.Request('GET','https://statsapi.mlb.com/api/v1/stats',params=params).prepare()
            if not dest.exists():
                response=session.send(request,timeout=60);response.raise_for_status();payload=response.json();strict_frame(payload,y)
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(response.content)
                write(meta.relative_to(OUT),dict(url=request.url,captured_utc=datetime.now(timezone.utc).isoformat(),sha256=sha256_file(dest)))
            metadata=e.r.read(meta);assert metadata['url']==request.url and metadata['sha256']==sha256_file(dest)
            frames[label]=strict_frame(e.r.read(dest),y)
            teams={t for v in known.values() for t in v[1:]};assert len(teams)==30
            average_games=sum(start<=v[0]<=end for v in known.values())*2/len(teams)
            assert average_games>0
            windows[label]=dict(start=start,end=end,average_team_games=average_games)
            manifest.append(dict(season=y,window=label,**metadata,path=str(dest),rows=len(frames[label]),**windows[label]))
        annual=frames['annual'];ref=counts.filter(pl.col('season')==y).select('player_id',pl.col('plate_appearances').alias('reference_pa'))
        check=annual.join(ref,on='player_id',how='full',coalesce=True).with_columns(pl.col('pa','reference_pa').fill_null(0))
        bad=check.filter(pl.col('pa')!=pl.col('reference_pa'))
        if len(bad):
            write(f'blocked-{y}-pa-reconciliation.json',bad.to_dicts());raise ValueError(f'Full-year MLB PA mismatch {y}: {len(bad)} rows; no fits')
        frame=annual.rename({'pa':'annual_pa','games':'annual_games'})
        for label in ['preceding','late']:
            frame=frame.join(frames[label].rename({'pa':label+'_pa','games':label+'_games'}),on='player_id',how='full',coalesce=True)
        frame=frame.with_columns(pl.exclude('player_id').fill_null(0))
        assert (frame['late_pa']+frame['preceding_pa']<=frame['annual_pa']).all()
        assert (frame['late_games']+frame['preceding_games']<=frame['annual_games']).all()
        g=games.filter(pl.col('season')==y).select('player_id',pl.col('games_played').alias('team_summed_games'))
        dif=frame.join(g,on='player_id',how='left').filter(pl.col('annual_games')!=pl.col('team_summed_games'))
        notes.append(dict(season=y,annual_players=len(annual),annual_pa=int(annual['pa'].sum()),reference_pa=int(ref['reference_pa'].sum()),game_aggregation_differences=dif.to_dicts(),schedule_path=str(schedule),schedule_sha256=sha256_file(schedule),schedule_url=schedule_request.url,excluded_nonplayed_schedule_entries=ignored,unique_completed_games=len(known)))
        frame=frame.with_columns(pl.lit(y).alias('season'),pl.lit(windows['late']['average_team_games']).alias('late_team_games'),pl.lit(windows['preceding']['average_team_games']).alias('preceding_team_games'))
        rows.append(frame);print(f'Checked source {y}: {len(annual)} players, full PA exact, final {final}',flush=True)
    OUT.mkdir(parents=True,exist_ok=True);pl.concat(rows).sort('season','player_id').write_parquet(OUT/'windows.parquet')
    write('source-manifest.json',dict(sources=manifest,years=list(YEARS),checks=notes,player_walkthrough_status='pending',protected_outcomes_used=False))


def features():
    manifest=e.r.read(OUT/'source-manifest.json');source=pl.read_parquet(e.BASE/'features.parquet');windows=pl.read_parquet(OUT/'windows.parquet');names=[];f=source
    for lag in [0,1]:
        prefix=f'late_usage_{lag}_';names.extend(prefix+k for k in ['available','late_pa','preceding_pa','late_pace','preceding_pace'])
        w=windows.with_columns((pl.col('season')+lag).alias('origin_year')).rename({c:prefix+c for c in windows.columns if c not in ['season','player_id']}).drop('season')
        f=f.join(w,on=['origin_year','player_id'],how='left',validate='m:1')
        # Completeness is certified by YEAR, not by whether this player appears.
        f=f.with_columns(pl.col('origin_year').sub(lag).is_in(manifest['years']).cast(pl.Float64).alias(prefix+'available'))
        for k in ['late_pa','preceding_pa','late_games','preceding_games']:f=f.with_columns(pl.col(prefix+k).fill_null(0))
        f=f.with_columns(((pl.col(prefix+'late_pa')+20)/(pl.col(prefix+'late_games')+5)).alias(prefix+'late_role'),((pl.col(prefix+'preceding_pa')+20)/(pl.col(prefix+'preceding_games')+5)).alias(prefix+'preceding_role'))
        denominator={m['season']:m['average_team_games'] for m in manifest['sources'] if m['window']=='late'}
        prior={m['season']:m['average_team_games'] for m in manifest['sources'] if m['window']=='preceding'}
        f=f.with_columns((pl.col(prefix+'late_pa')/pl.col('origin_year').sub(lag).replace_strict(denominator,return_dtype=pl.Float64)).alias(prefix+'late_pace'),(pl.col(prefix+'preceding_pa')/pl.col('origin_year').sub(lag).replace_strict(prior,return_dtype=pl.Float64)).alias(prefix+'preceding_pace'))
    assert f.select(source.columns).equals(source) and len(names)==10 and f.select(names).null_count().sum_horizontal().sum()==0
    f.select(source.columns+names).write_parquet(OUT/'features.parquet');write('features.json',dict(added=names,source_sha256=sha256_file(e.BASE/'features.parquet'),windows_sha256=sha256_file(OUT/'windows.parquet'),rows=len(f)))
    cases=[]
    for pid,y in FIXED:
        o=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)).to_dicts();assert len(o)==1
        cases.append(dict(origin=o[0],windows=windows.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-1,y)).to_dicts(),added_inputs={n:o[0][n] for n in names}))
    write('source-cases.json',cases);print('10 exact PA-only source-joined inputs ready; nine source reviews pending, no models fitted.',flush=True)


if __name__=='__main__':
    import sys
    if sys.argv[1]=='capture':capture()
    elif sys.argv[1]=='features':features()
    else:raise ValueError('Choose capture or features')
