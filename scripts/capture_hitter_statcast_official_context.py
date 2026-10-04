"""Capture bounded historical official metadata and localize contact residuals."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import polars as pl
import requests
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/hitter-statcast-official-context'
CONTRACT=ROOT/'docs/hitter-statcast-official-context-contract.md'
AUDIT=ROOT/'reports/generated/hitter-statcast-historical-capture-audit/report.json'
SOURCE=ROOT/'reports/generated/hitter-statcast-historical-capture'


def read(p):return json.loads(p.read_text(encoding='utf8'))


def write(p,v):p.write_text(json.dumps(v,indent=2,default=str,allow_nan=False)+'\n',encoding='utf8',newline='\n')


def capture(name,url,params=None):
    expected=requests.Request('GET',url,params=params).prepare().url
    path=OUT/f'{name}.json'; receipt=OUT/f'{name}.receipt.json'
    if receipt.exists():
        r=read(receipt); assert r['requested_url']==expected
        assert r['response_sha256']==sha256_file(path)
        assert r['contract_sha256']==sha256_file(CONTRACT) and r['collector_sha256']==sha256_file(Path(__file__))
        return read(path)
    assert not path.exists(),'Partial unreceipted capture needs explicit inspection'
    for attempt in range(3):
        try:
            response=requests.get(url,params=params,timeout=(20,60)); response.raise_for_status(); data=response.json();break
        except requests.RequestException:
            if attempt==2:raise
            time.sleep(2*(attempt+1))
    path.write_bytes(response.content)
    write(receipt,dict(requested_url=expected,returned_url=response.url,response_sha256=hashlib.sha256(response.content).hexdigest(),
        response_bytes=len(response.content),captured_at=datetime.now(timezone.utc),
        contract_sha256=sha256_file(CONTRACT),collector_sha256=sha256_file(Path(__file__)),model_fits=0,protected_outcomes_used=False))
    print(f'{name}: captured official historical source.',flush=True)
    return data


def metadata(year):
    assert year in range(2015,2023)
    schedule=capture(f'schedule-{year}','https://statsapi.mlb.com/api/v1/schedule',dict(sportId=1,season=year,gameType='R',hydrate='venue'))
    teams=capture(f'teams-{year}','https://statsapi.mlb.com/api/v1/teams',dict(sportId=1,season=year))
    games=[g for day in schedule['dates'] for g in day['games']]
    assert all(int(g['season'])==year and g['gameType']=='R' for g in games)
    assert len({g['gamePk'] for g in games})==len(games)
    assert len([t for t in teams['teams'] if t.get('league',{}).get('id') in [103,104]])==30


def gamelog(case):
    year,pid=case['season'],case['player_id']; assert year in range(2015,2023)
    data=capture(f'gamelog-{year}-{pid}',f'https://statsapi.mlb.com/api/v1/people/{pid}/stats',
        dict(stats='gameLog',group='hitting',season=year,sportId=1,gameType='R'))
    splits=[s for group in data['stats'] for s in group.get('splits',[])]
    assert all(str(s['date']).startswith(str(year)+'-') for s in splits)
    # Players appearing for both clubs in one game can have distinct official splits.
    records=[]
    for s in splits:
        stat=s['stat']
        records.append(dict(game_pk=s['game']['gamePk'],player_id=pid,
            expected_contacts=stat.get('atBats',0)-stat.get('strikeOuts',0)+stat.get('sacFlies',0)+stat.get('sacBunts',0),
            AB=stat.get('atBats',0),K=stat.get('strikeOuts',0),SF=stat.get('sacFlies',0),SH=stat.get('sacBunts',0),
            PA=stat.get('plateAppearances',0),hits=stat.get('hits',0),HR=stat.get('homeRuns',0),
            doubles=stat.get('doubles',0),triples=stat.get('triples',0)))
    official=pl.DataFrame(records).group_by('game_pk','player_id').agg(pl.exclude('game_pk','player_id').sum())
    raw=pl.concat([pl.read_parquet(SOURCE/f'{year}-{m:02}.parquet').filter(pl.col('batter')==str(pid)) for m in range(3,11)])
    source=raw.filter(pl.col('events')!='catcher_interf').group_by(pl.col('game_pk').cast(pl.Int64).alias('game_pk')).agg(
        pl.len().alias('source_contacts'),pl.col('events').implode().alias('source_events'))
    source=source.with_columns(pl.lit(pid).alias('player_id'))
    joined=official.join(source,on=['game_pk','player_id'],how='full',coalesce=True).with_columns(
        pl.col('expected_contacts','source_contacts').fill_null(0))
    joined=joined.with_columns((pl.col('source_contacts')-pl.col('expected_contacts')).alias('residual'))
    errors=joined.filter(pl.col('residual')!=0)
    errors.write_parquet(OUT/f'game-residuals-{year}-{pid}.parquet')
    write(OUT/f'game-residuals-{year}-{pid}.json',dict(season=year,player_id=pid,player_name=case['player_name'],
        previous_season_residual=case['contact_denominator_residual'],
        gamelog_season_contacts=int(joined['expected_contacts'].sum()),
        prior_official_contacts=case['official_contact_denominator'],
        gamelog_matches_prior=int(joined['expected_contacts'].sum())==case['official_contact_denominator'],
        residual_games=errors.to_dicts(),game_log_totals=official.select(pl.exclude('game_pk','player_id').sum()).to_dicts()[0]))
    return [(year,int(pk)) for pk in errors['game_pk'].to_list()]


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=read(AUDIT)
    for p,h in source['source_hashes'].items():assert sha256_file(Path(p))==h
    cases=[dict(season=y['season'],**r) for y in source['years'] for r in y['contact_denominator_residuals']]
    assert len(cases)==20
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(metadata,range(2015,2023)))
        games=sorted(set(pair for result in pool.map(gamelog,cases) for pair in result))
        assert len(games)<=40,'Unexpected source diagnosis expansion'
        def feed(pair):
            year,pk=pair
            known={g['gamePk'] for d in read(OUT/f'schedule-{year}.json')['dates'] for g in d['games']}
            assert pk in known
            data=capture(f'feed-{year}-{pk}',f'https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live')
            assert data['gamePk']==pk and str(data['gameData']['datetime']['officialDate']).startswith(str(year))
        list(pool.map(feed,games))
    write(OUT/'capture-report.json',dict(source_only=True,new_model_fits=0,protected_outcomes_used=False,review_status='pending',
        seasons=list(range(2015,2023)),gamelog_cases=20,discrepant_games=games,
        input_hashes={str(p):sha256_file(p) for p in [CONTRACT,Path(__file__),AUDIT]},
        output_hashes={str(p):sha256_file(p) for p in sorted(OUT.glob('*')) if p.is_file()}))


if __name__=='__main__':main()
