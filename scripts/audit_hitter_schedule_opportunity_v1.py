"""Reconstruct dated minor team denominators from local official captures."""
import json
from pathlib import Path
import polars as pl
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_schedule_opportunity import completed_teams,schedule_features,FEATURES
from universal_baseball.storage import sha256_file

OUT=Path('reports/generated/hitter-era-schedule-v1')
OLD=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'prefit-manifest.json').exists(): raise ValueError('Already frozen')
    sources={}; rows=[]
    for year in [2015,2016,2017,2018,2019,2021,2022,2023,2024]:
        root=OLD/('historical-affiliated-game-context' if year<2020 else 'affiliated-game-context')/'captures'
        paths=sorted(root.glob(f'schedule-{year}-sport-*.json'))
        assert paths,year
        for path in paths:
            sport=int(path.stem.split('-')[-1]); sources[str(path)]=sha256_file(path)
            rows.extend(completed_teams(json.loads(path.read_text()),year,sport))
    teams=pl.DataFrame(rows)
    stats=[]
    for folder,years in [('affiliated-skill-source-2008-2017',range(2015,2018)),
                         ('affiliated-skill-source-2018-2022',[2018,2019,2021,2022]),
                         ('affiliated-skill-source',[2023,2024])]:
        path=OLD/folder/'tables/affiliated_hitting_components.parquet';sources[str(path)]=sha256_file(path)
        stats.append(pl.read_parquet(path,columns=['season','player_id','sport_id','team_id','plate_appearances'])
                     .filter(pl.col('season').is_in(list(years))))
    stats=pl.concat(stats,how='vertical_relaxed')
    features=schedule_features(stats,teams)
    minor=stats.filter((pl.col('sport_id')!=1)&(pl.col('plate_appearances')>0))
    joined=minor.join(teams,on=['season','sport_id','team_id'],how='left',validate='m:1')
    coverage=joined.group_by('season','sport_id').agg(pl.len().alias('stints'),
        pl.col('plate_appearances').sum().alias('pa'),
        pl.when(pl.col('team_games').is_null()).then(pl.col('plate_appearances')).otherwise(0).sum().alias('unmatched_pa'),
        pl.col('team_id').n_unique().alias('teams')).sort('season','sport_id')
    relevant=teams.join(minor.select('season','sport_id','team_id').unique(),on=['season','sport_id','team_id'],how='semi')
    lengths=relevant.group_by('season','sport_id').agg(pl.len().alias('teams'),
        pl.col('team_games').min().alias('minimum'),pl.col('team_games').median().alias('median'),
        pl.col('team_games').max().alias('maximum')).sort('season','sport_id')
    panel=pl.read_parquet('reports/generated/hitter-detail-arrival-v1/input-panel.parquet',
                         columns=['origin_year','player_id','prospect','pa_lag0'])
    p=panel.filter(pl.col('prospect')&pl.col('origin_year').is_in([2015,2016,2017,2018,2019,2021,2022,2023,2024]))
    p=p.join(features.rename({'season':'origin_year'}),on=['origin_year','player_id'],how='left',validate='1:1')
    annual=p.group_by('origin_year').agg(pl.len().alias('players'),
        pl.col(FEATURES[1]).is_not_null().sum().alias('fully_covered'),pl.col('pa_lag0').mean().alias('mean_pa'),
        pl.col(FEATURES[1]).mean().alias('mean_pa_per_game'),pl.col(FEATURES[2]).mean().alias('mean_schedule')).sort('origin_year')
    teams.write_parquet(OUT/'team-schedules.parquet');features.write_parquet(OUT/'schedule-features.parquet')
    save(OUT/'schedule-audit.json',{'sources':sources,'coverage':coverage.to_dicts(),
        'team_lengths':lengths.to_dicts(),'prospects':annual.to_dicts(),
        'unmatched_stints':joined.filter(pl.col('team_games').is_null()).to_dicts(),
        'feature_hash':sha256_file(OUT/'schedule-features.parquet'),
        'team_hash':sha256_file(OUT/'team-schedules.parquet'),
        'limitations':['No pre-2015 local schedule captures used','Full team schedule, not personal roster tenure',
                      'No inference that short PA means injury','Historical reconstruction; captures retrieved later'],
        'protected_outcomes_used':False})
    print(json.dumps({'prospects':annual.to_dicts(),'team_lengths':lengths.to_dicts(),
                       'unmatched_pa':int(coverage['unmatched_pa'].sum())},indent=2))


if __name__=='__main__':main()
