"""Audit cached pre-2011 populations and repair only 2006/07 sport-15 history."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.affiliated_skill_source import project_affiliated_skill_splits
from universal_baseball.opportunity_history_source import (
    build_opportunity_snapshots, project_affiliated_season_stats_payload,
)
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OLD = Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')
OUT = ROOT / 'reports/generated/hitter-older-origin-source'
REPAIR = ROOT / 'model_artifacts/hitter-older-origin-source'
KEY = ['season', 'player_id', 'sport_id', 'team_id']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False,
                               default=str) + '\n', encoding='utf8')


def resolve(path):
    return OLD.parent.parent / path.replace('\\', '/')


def checked_receipt(receipt, path_key='path', hash_key='file_sha256'):
    path = resolve(receipt[path_key])
    assert sha256_file(path) == receipt[hash_key], path
    return path


def capture(year):
    assert year in [2006, 2007]
    folder = REPAIR / 'raw' / str(year)
    folder.mkdir(parents=True, exist_ok=True)
    evidence = []

    def get(name, route, params):
        path = folder / name
        if not path.exists():
            response = requests.get('https://statsapi.mlb.com/api/v1/' + route,
                                    params=params, timeout=45)
            response.raise_for_status()
            path.write_bytes(gzip.compress(json.dumps(response.json(), sort_keys=True)
                                           .encode('utf8'), mtime=0))
        evidence.append(dict(path=str(path), sha256=sha256_file(path), route=route,
                             parameters=params))
        return json.loads(gzip.decompress(path.read_bytes()))

    teams = get('teams.json.gz', 'teams', dict(sportId=15, season=year))
    team_ids = {int(t['id']) for t in teams['teams']}
    assert team_ids, 'Missing historical sport-15 teams'
    groups, basics = {}, []
    for group in ['hitting', 'pitching']:
        frames = []
        for offset in range(0, 25000, 5000):
            payload = get(f'{group}-{offset}.json.gz', 'stats', dict(
                stats='season', group=group, playerPool='ALL', season=year,
                sportIds='15', gameType='R', limit=5000, offset=offset))
            splits = payload['stats'][0]['splits']
            assert all(int(s['season']) == year and int(s['sport']['id']) == 15 for s in splits)
            frames.append(project_affiliated_skill_splits(splits, season=year, stat_group=group))
            basics.append(project_affiliated_season_stats_payload(payload, season=year, stat_group=group))
            if len(splits) < 5000:
                break
        else:
            raise ValueError('Sport-15 pagination safety bound reached')
        groups[group] = pl.concat(frames)
        assert groups[group].unique(KEY).height == groups[group].height
        assert set(groups[group].filter(pl.col('plate_appearances' if group == 'hitting' else 'batters_faced') > 0)['team_id']) == team_ids
        groups[group].write_parquet(REPAIR / f'{year}-{group}.parquet')
    basic = pl.concat(basics)
    assert basic.unique(['stat_group', *KEY]).height == basic.height
    basic.write_parquet(REPAIR / f'{year}-basic.parquet')
    pa = groups['hitting']['plate_appearances'].sum()
    bf = groups['pitching']['batters_faced'].sum()
    result = dict(season=year, teams=len(team_ids), pa=pa, bf=bf, pa_minus_bf=pa-bf,
                  captures=evidence, protected_outcomes_used=False,
                  outputs={str(p): sha256_file(p) for p in REPAIR.glob(f'{year}-*.parquet')})
    write(REPAIR / f'{year}-receipt.json', result)
    print(f'{year}: restored {pa} A-minus PA, {len(team_ids)} teams; PA-BF {pa-bf}', flush=True)
    return result


def raw_inventory(name, years):
    root = OLD / name
    report = read(root / 'report.json')
    skill_path = checked_receipt(report['storage']['hitting'])
    skills = pl.read_parquet(skill_path).filter(pl.col('season').is_in(years))
    rows, projected, hashes, pagination = [], [], {str(root/'report.json'):sha256_file(root/'report.json'), str(skill_path):sha256_file(skill_path)}, []
    for year in years:
        pages = sorted([c for c in report['captures'] if c['season'] == year and c['stat_group'] == 'hitting'], key=lambda c: c['offset'])
        assert pages and pages[0]['offset'] == 0
        assert pages[-1]['returned_rows'] < pages[-1]['requested_limit']
        for page in pages:
            path = resolve(page['path'])
            raw = gzip.decompress(path.read_bytes())
            import hashlib
            assert hashlib.sha256(raw).hexdigest() == page['response_sha256'], path
            payload = json.loads(raw)
            splits = payload['stats'][0]['splits']
            assert len(splits) == page['returned_rows']
            projected.append(project_affiliated_skill_splits(splits, season=year, stat_group='hitting'))
            hashes[str(path)] = sha256_file(path)
            for s in splits:
                assert int(s['season']) == year
                rows.append(dict(season=year, player_id=int(s['player']['id']), sport_id=int(s['sport']['id']),
                    team_id=int(s['team']['id']), league_id=int(s['league']['id']),
                    position=str(s.get('position', {}).get('code') or 'UNKNOWN'),
                    metadata_pa=int(s['stat']['plateAppearances']), num_teams=int(s.get('numTeams', 1))))
        assert [c['offset'] for c in pages] == [i*pages[0]['requested_limit'] for i in range(len(pages))]
        pagination.append(dict(season=year, pages=len(pages), last_page_rows=pages[-1]['returned_rows']))
    projected = pl.concat(projected).select(skills.columns).sort(KEY)
    assert projected.equals(skills.sort(KEY)), 'Raw and cached component reconstruction differ'
    metadata = pl.DataFrame(rows)
    assert metadata.unique(KEY).height == metadata.height
    assert skills.unique(KEY).height == skills.height
    stints = skills.join(metadata, on=KEY, validate='1:1')
    assert stints['plate_appearances'].equals(stints['metadata_pa'])
    return stints, hashes, pagination


def audit():
    assert not (OUT/'report.json').exists(), 'Preserve completed audit'
    previous = read(ROOT/'reports/generated/hitter-shared-development/final-report.json')
    assert previous['player_walkthrough_status'] == 'complete'
    early, hashes, pages = raw_inventory('affiliated-skill-source-2003-2007', list(range(2003, 2008)))
    later, hashes2, pages2 = raw_inventory('affiliated-skill-source-2008-2017', [2008, 2009, 2010])
    hashes.update(hashes2)
    current_path = ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet'
    current = pl.read_parquet(current_path).filter(pl.col('season').is_between(2008, 2010))
    measures = [c for c in early.columns if c in ['plate_appearances', 'at_bats','hits','doubles','triples','home_runs','base_on_balls','intentional_walks','hit_by_pitch','strike_outs','sac_bunts','sac_flies']]
    a = later.group_by('season','player_id','sport_id').agg(pl.col(measures).sum())
    b = current.filter(pl.col('sport_id')!=15).group_by('season','player_id','sport_id').agg(pl.col(measures).sum())
    assert a.sort('season','player_id','sport_id').equals(b.sort('season','player_id','sport_id')), 'Overlapping current/old person-sport totals differ'
    hashes[str(current_path)] = sha256_file(current_path)
    coverage = pl.concat([early, later]).group_by('season','sport_id','league_id').agg(
        pl.len().alias('rows'), pl.col('player_id').n_unique().alias('people'), pl.col('team_id').n_unique().alias('representative_teams'),
        pl.col('plate_appearances').sum().alias('pa'), (pl.col('num_teams')>1).sum().alias('aggregate_multiteam_rows')).sort('season','sport_id','league_id')
    snapshots, population_rows = [], []
    for year in [2008, 2009, 2010]:
        old_root = OLD/'opportunity-history-sources-pre2020'
        old_report = read(old_root/'report.json')
        record = next(s for s in old_report['season_reports'] if s['season']==year)
        roster_path = checked_receipt(record['storage']['roster'])
        old_snapshot_path = checked_receipt(record['storage']['hitters'])
        basic_path = ROOT/f'model_artifacts/advanced-rookie-repair-v3/{year}/affiliated_season_stats.parquet'
        roster, basic = pl.read_parquet(roster_path), pl.read_parquet(basic_path)
        new, _ = build_opportunity_snapshots(roster, basic)
        saved = pl.read_parquet(ROOT/f'model_artifacts/advanced-rookie-repair-v3/{year}/hitter_snapshots.parquet')
        assert new.equals(saved), 'Current snapshot rule replay differs'
        old = pl.read_parquet(old_snapshot_path)
        assert old.join(new, on=['snapshot_year','player_id'],how='anti').is_empty()
        added = new.join(old.select('snapshot_year','player_id'),on=['snapshot_year','player_id'],how='anti')
        population_rows.append(dict(origin=year, original_rows=len(old), rebuilt_rows=len(new), added_rows=len(added),
            removed_rows=0, added_by_level=added.group_by('as_of_level_group').len().to_dicts(),
            age_unknown=new['age_years'].null_count(), inactive=new.filter(pl.col('as_of_level_group')=='INACTIVE').height))
        snapshots.append(new)
        for path in [old_root/'report.json', roster_path, old_snapshot_path, basic_path]: hashes[str(path)] = sha256_file(path)
    population = pl.concat(snapshots).rename({'snapshot_year':'origin_year','age_years':'age','as_of_level_group':'snapshot_level'})
    # Raw outcomes provide participation labels; no future-return cohort selection.
    inventory = OLD/'career-mlb-outcome-inventory-2004-2009'
    cert = read(inventory/'report.json')
    assert cert['complete_seasons'] == list(range(2004,2010)) and not cert['protected_2026_accessed']
    target_old_path = inventory/'tables/mlb_hitting_components_2004_2009.parquet'
    target_new_path = OLD/'career-mlb-outcome-inventory-2009-2025/tables/mlb_hitting_components_2009_2025.parquet'
    outcomes_old, outcomes_new = pl.read_parquet(target_old_path), pl.read_parquet(target_new_path)
    common = [c for c in outcomes_old.columns if c in outcomes_new.columns]
    assert outcomes_old.filter(pl.col('season')==2009).select(common).sort('player_id').equals(outcomes_new.filter(pl.col('season')==2009).select(common).sort('player_id'))
    outcomes = pl.concat([outcomes_old.filter(pl.col('season')<2009).select(common), outcomes_new.select(common)])
    labels = outcomes.filter(pl.col('season').is_between(2009,2011)).select(
        (pl.col('season')-1).alias('origin_year'),'player_id', pl.col('batting_plate_appearances').alias('next_pa'))
    population = population.join(labels,on=['origin_year','player_id'],how='left',validate='1:1').with_columns(pl.col('next_pa').fill_null(0))
    debuts = pl.concat([pl.read_parquet(inventory/'tables/people-debut-dates.parquet'),pl.read_parquet(OLD/'career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet')]).unique()
    assert debuts.unique('player_id').height == debuts.height, 'Conflicting debut dates'
    population = population.join(debuts,on='player_id',how='left',validate='m:1').with_columns(
        pl.when(pl.col('mlb_debut_date').is_null()).then(pl.lit('unknown_or_no_recorded_debut'))
        .when(pl.col('mlb_debut_date').dt.year()<=pl.col('origin_year')).then(pl.lit('prior_debut'))
        .otherwise(pl.lit('future_recorded_debut')).alias('debut_evidence'))
    for path in [inventory/'report.json', target_old_path, target_new_path, inventory/'tables/people-debut-dates.parquet', OLD/'career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet']:
        hashes[str(path)] = sha256_file(path)
    for year in [2006,2007]:
        receipt = read(REPAIR/f'{year}-receipt.json')
        for path, digest in receipt['outputs'].items(): assert sha256_file(Path(path))==digest
        for capture_record in receipt['captures']: assert sha256_file(Path(capture_record['path'])) == capture_record['sha256']
        hashes[str(REPAIR/f'{year}-receipt.json')] = sha256_file(REPAIR/f'{year}-receipt.json')
    # A supplemental table; original histories and evaluations remain untouched.
    history = pl.concat([early.filter(pl.col('season')>=2006).drop('num_teams'), current.select([c for c in early.columns if c!='num_teams'])],how='vertical_relaxed')
    for year in [2006,2007]:
        path = REPAIR/f'{year}-hitting.parquet'
        supplemental = pl.read_parquet(path)
        metadata_rows=[]
        for capture_record in read(REPAIR/f'{year}-receipt.json')['captures']:
            if capture_record['parameters'].get('group')!='hitting': continue
            payload=json.loads(gzip.decompress(Path(capture_record['path']).read_bytes()))
            metadata_rows.extend(dict(season=year,player_id=int(s['player']['id']),sport_id=15,team_id=int(s['team']['id']),
                league_id=int(s['league']['id']),position=str(s.get('position',{}).get('code') or 'UNKNOWN'),metadata_pa=int(s['stat']['plateAppearances'])) for s in payload['stats'][0]['splits'])
        assert not history.filter(pl.col('season')==year).filter(pl.col('sport_id')==15).height
        supplemental = supplemental.join(pl.DataFrame(metadata_rows),on=KEY,validate='1:1')
        history = pl.concat([history,supplemental.select(history.columns)],how='vertical_relaxed')
    history=history.sort(KEY)
    assert history.unique(KEY).height==history.height
    mlb_overlap=outcomes.filter(pl.col('season').is_between(2006,2010)).select('season','player_id',pl.col('batting_plate_appearances').alias('target_pa'))
    joined=history.filter(pl.col('sport_id')==1).select('season','player_id','plate_appearances').join(mlb_overlap,on=['season','player_id'],how='full',coalesce=True,validate='1:1')
    assert joined.filter(pl.col('plate_appearances').fill_null(0)!=pl.col('target_pa').fill_null(0)).is_empty()
    OUT.mkdir(parents=True,exist_ok=True)
    for name,frame in [('coverage',coverage),('population',population),('history',history)]: frame.write_parquet(OUT/f'{name}.parquet')
    report=dict(no_new_fits=True, source_populations=population_rows, potential_added_origin_rows=len(population),
        active_next_year_labels=population.filter(pl.col('next_pa')>0).height,
        zero_next_year_labels=population.filter(pl.col('next_pa')==0).height,
        by_origin=population.group_by('origin_year').agg(pl.len().alias('rows'),(pl.col('next_pa')>0).sum().alias('active'),pl.col('next_pa').sum()).sort('origin_year').to_dicts(),
        by_debut_evidence=population.group_by('debut_evidence').agg(pl.len().alias('rows'),(pl.col('next_pa')>0).sum().alias('active')).to_dicts(),
        cached_coverage=coverage.to_dicts(), restored_shortseason=[read(REPAIR/f'{y}-receipt.json') for y in [2006,2007]],
        raw_components_reproduced=True, current_2008_2010_non_shortseason_totals_reproduced=True,
        current_snapshot_rule_replayed=True, positive_mlb_pa_reconciled=True, target_2009_overlap_exact=True,
        limits=['2003-2005 lower-level coverage is not certified by bulk-row presence',
                'Bulk rookie rows can aggregate multiple clubs or leagues under one representative identity',
                'Historical October roster listing is not certified year-end ownership or availability',
                'Missing debut rows remain unknown, not certified never-debut',
                'Compatible rankings, status, draft and generated level features still require reconciliation',
                'No exit augmentation beyond dated roster and season-use population has been certified'],
        player_walkthrough_status='pending', protected_outcomes_used=False,current_forecasts_changed=False)
    for path in [Path(__file__),ROOT/'docs/hitter-older-origin-source-contract.md',ROOT/'src/universal_baseball/opportunity_history_source.py',ROOT/'src/universal_baseball/affiliated_skill_source.py',OUT/'coverage.parquet',OUT/'population.parquet',OUT/'history.parquet']:
        hashes[str(path)]=sha256_file(path)
    report['input_and_output_hashes']=hashes
    write(OUT/'report.json',report)
    print(json.dumps({k:report[k] for k in ['potential_added_origin_rows','active_next_year_labels','zero_next_year_labels','by_origin']},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['capture','audit'])
    args=parser.parse_args()
    if args.action=='capture':
        with ThreadPoolExecutor(max_workers=2) as pool: list(pool.map(capture,[2006,2007]))
    else: audit()
