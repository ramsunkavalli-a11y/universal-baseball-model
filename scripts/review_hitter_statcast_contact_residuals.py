"""Align fixed historical contact discrepancies with official terminal plays."""
from pathlib import Path
import polars as pl
import capture_hitter_statcast_official_context as capture


def main():
    destination=capture.OUT/'contact-residual-play-review.json'
    assert not destination.exists(),'Preserve source review'
    report=capture.read(capture.OUT/'capture-report.json')
    for p,h in report['output_hashes'].items():
        assert capture.sha256_file(Path(p))==h
    reviews=[]
    for path in sorted(capture.OUT.glob('game-residuals-*.json')):
        case=capture.read(path); year=case['season']; pid=case['player_id']
        raw=pl.concat([pl.read_parquet(capture.SOURCE/f'{year}-{m:02}.parquet')
            .filter(pl.col('batter')==str(pid)) for m in range(3,11)])
        games=[]
        for game in case['residual_games']:
            pk=game['game_pk']; feed=capture.read(capture.OUT/f'feed-{year}-{pk}.json')
            source=raw.filter(pl.col('game_pk')==str(pk)).to_dicts()
            lookup={int(s['at_bat_number'])-1:s for s in source}
            plays=[]
            for play in feed['liveData']['plays']['allPlays']:
                if play['matchup']['batter']['id']!=pid: continue
                index=play['atBatIndex']; result=play['result']
                plays.append(dict(at_bat_index=index,official_event=result['eventType'],
                    official_description=result['description'],source=lookup.get(index),
                    inplay_pitch_events=[dict(index=e.get('index'),pitch_number=e.get('pitchNumber'),
                        details=e.get('details'),hit_data=e.get('hitData')) for e in play['playEvents']
                        if e.get('details',{}).get('isInPlay')]))
            games.append(dict(game_comparison=game,official_player_plays=plays))
            print(year,case['player_name'],pk,'residual',game['residual'],
                'events',[(v['official_event'],None if v['source'] is None else v['source']['events']) for v in plays],flush=True)
        reviews.append(dict(season=year,player_id=pid,player_name=case['player_name'],
            gamelog_matches_prior=case['gamelog_matches_prior'],games=games))
    capture.write(destination,dict(source_only=True,new_model_fits=0,classification_status='pending',cases=reviews,
        collector_sha256=capture.sha256_file(Path(__file__)),capture_report_sha256=capture.sha256_file(capture.OUT/'capture-report.json')))


if __name__=='__main__':main()
