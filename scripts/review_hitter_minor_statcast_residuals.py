"""Retain official feeds for source count differences and split-venue games."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import requests
import polars as pl
from universal_baseball.storage import sha256_file
import materialize_hitter_minor_statcast_source as source

ROOT,OUT=source.ROOT,source.OUT
RAW=OUT/'official-review';CONTRACT=source.capture.CONTRACT


def feed(year,pk):
    RAW.mkdir(parents=True,exist_ok=True);p=RAW/f'feed-{year}-{pk}.json.gz';receipt=p.with_suffix('')
    if receipt.exists():
        r=json.loads(receipt.read_text(encoding='utf8'))
        assert r['script_sha256']==sha256_file(Path(__file__)) and r['compressed_sha256']==sha256_file(p)
        data=gzip.decompress(p.read_bytes());assert hashlib.sha256(data).hexdigest()==r['response_sha256']
        return json.loads(data),r
    assert not p.exists()
    response=requests.get(f'https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live',timeout=(20,60));response.raise_for_status()
    data=response.json();assert data['gamePk']==pk and int(data['gameData']['game']['season'])==year
    assert data['gameData']['game']['type']=='R'
    with gzip.GzipFile(filename=str(p),mode='wb',mtime=0) as z:z.write(response.content)
    r=dict(season=year,game_pk=pk,url=response.url,captured_at=datetime.now(timezone.utc),
        response_sha256=hashlib.sha256(response.content).hexdigest(),compressed_sha256=sha256_file(p),
        script_sha256=sha256_file(Path(__file__)),contract_sha256=sha256_file(CONTRACT),model_fits=0)
    source.capture.write(receipt,r)
    return data,r


def main():
    residual=json.loads((OUT/'contact-residual-review.json').read_text(encoding='utf8'))['cases']
    context=json.loads((OUT/'schedule-context-review.json').read_text(encoding='utf8'))['seasons']
    keys={(r['season'],r['game_pk']) for r in residual}
    keys.update((c['season'],r['game_pk']) for c in context for r in c['split_venue_games'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        got=list(pool.map(lambda x:(x,feed(*x)),sorted(keys)))
    feeds={k:v[0] for k,v in got};receipts=[v[1] for k,v in got]
    sources={y:pl.concat([pl.read_parquet(p) for p in (source.SOURCE/'seasons').glob(f'{y}*.parquet')]) for y in range(2021,2025)}
    cases=[]
    for r in residual:
        y,pk,pid=r['season'],r['game_pk'],r['player_id'];data=feeds[(y,pk)]
        bats=[t['players'][f'ID{pid}'].get('stats',{}).get('batting',{}) for t in data['liveData']['boxscore']['teams'].values() if f'ID{pid}' in t['players']]
        assert len(bats)==1
        batting=bats[0]
        expected=sum(int(batting.get(k,0)) for k in ['atBats','sacFlies','sacBunts'])-int(batting.get('strikeOuts',0))
        raw=sources[y].filter((pl.col('game_pk')==str(pk))&(pl.col('batter')==str(pid)))
        observations=[]
        for play in data['liveData']['plays']['allPlays']:
            if play.get('matchup',{}).get('batter',{}).get('id')!=pid:continue
            idx=play['atBatIndex']+1;s=raw.filter(pl.col('at_bat_number')==str(idx))
            events=play.get('playEvents',[])
            observations.append(dict(at_bat_number=idx,official_event=play['result'].get('eventType'),
                official_description=play['result'].get('description'),source_rows=s.to_dicts(),
                inplay_pitch_events=[e for e in events if e.get('details',{}).get('isInPlay')],
                hit_data_events=[e for e in events if e.get('hitData')]))
        cases.append(dict(**r,official_feed_batting=batting,official_feed_contact_boundary=expected,
            backbone_boundary_matches_current_feed=expected==r['expected_contact_count'],plays=observations))
    split=[]
    for c in context:
        for pk in sorted({g['game_pk'] for g in c['split_venue_games']}):
            data=feeds[(c['season'],pk)];segments=sorted([g for g in c['split_venue_games'] if g['game_pk']==pk],key=lambda g:g['segment_start'])
            threshold=segments[-1]['segment_start'];overrides=[]
            for play in data['liveData']['plays']['allPlays']:
                when=play.get('about',{}).get('endTime')
                if when is None:raise ValueError('Missing split-game terminal timestamp')
                # Parsed timestamps, not lexical order or a game-level final venue.
                t=datetime.fromisoformat(when.replace('Z','+00:00'))
                eligible=[s for s in segments if datetime.fromisoformat(s['segment_start'].replace('Z','+00:00'))<=t]
                assert eligible,'No completed schedule segment precedes terminal play'
                segment=eligible[-1]
                overrides.append(dict(game_pk=pk,at_bat_number=play['atBatIndex']+1,player_id=play['matchup']['batter']['id'],
                    venue_id=segment['venue_id'],venue_name=segment['venue_name'],terminal_timestamp=when,
                    segment_start=segment['segment_start']))
            split.append(dict(season=c['season'],game_pk=pk,segments=segments,play_venue_overrides=overrides,
                resumption_threshold=threshold,feed_datetime=data['gameData'].get('datetime')))
    source.write('official-contact-and-venue-review.json',dict(cases=cases,split_venue_reviews=split,receipts=receipts,
        source_report_sha256=sha256_file(OUT/'source-report.json'),script_sha256=sha256_file(Path(__file__)),
        all_classifications_reviewed=False,source_approved=False,models_fitted=0))
    print('Retained official feeds:',len(receipts),'player-game residuals:',len(cases),'split games:',len(split))
    for c in cases:
        no=[p for p in c['plays'] if not p['source_rows'] and p['official_event'] not in ['strikeout','walk','hit_by_pitch','intent_walk']]
        print(c['season'],c['game_pk'],c['player_id'],'boundary match',c['backbone_boundary_matches_current_feed'],
            [(p['official_event'],p['official_description'],len(p['inplay_pitch_events'])) for p in no])


if __name__=='__main__':main()
