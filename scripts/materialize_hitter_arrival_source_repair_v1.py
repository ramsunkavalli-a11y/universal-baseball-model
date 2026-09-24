"""Reconstruct dated source evidence; no model fitting or 2026 requests."""
import gzip
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path
import polars as pl
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.playing_time_roster_source import _get_json, STATS_API_BASE, project_team_40man_membership_payload
from universal_baseball.hitter_arrival_source_repair import census_rows, corrected_cohorts, attach_roster, attach_leagues, COHORTS
from universal_baseball.storage import sha256_file

OUT = Path('reports/generated/hitter-arrival-source-repair-v1')
SOURCE = Path('reports/generated/hitter-detail-arrival-v1')
OLD = Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')
YEARS = list(range(2009, 2020))+list(range(2021, 2025))


def capture(relative, endpoint, params):
    path = OUT/'captures'/relative
    if path.exists():
        with gzip.open(path, 'rt', encoding='utf-8') as f: obj = json.load(f)
        assert obj['endpoint'] == endpoint and obj['params'] == params
    else:
        payload, evidence = _get_json(STATS_API_BASE+endpoint, params=params)
        obj = dict(evidence, endpoint=endpoint, params=params, captured_at=datetime.now(timezone.utc).isoformat())
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, 'wt', encoding='utf-8') as f: json.dump(obj, f, sort_keys=True)
    return obj['payload']


def debuts(panel):
    assert (panel['origin_year']-panel['age']).min() > 1960
    def fetch(year):
        payload = capture(f'census/{year}.json.gz', '/sports/1/players',
                          {'season': year, 'fields': 'people,id,mlbDebutDate'})
        f = census_rows(payload, year)
        return f, {'season': year, 'players': f.height}
    with ThreadPoolExecutor(max_workers=6) as ex: results = list(ex.map(fetch, range(1960, 2026)))
    all_rows = pl.concat([r[0] for r in results])
    assert not all_rows.group_by('player_id').agg(pl.col('mlb_debut_date').n_unique().alias('n')).filter(pl.col('n')>1).height
    d = all_rows.unique('player_id').sort('player_id')
    comparisons = []
    for name in ('career-mlb-outcome-inventory-2004-2009', 'career-mlb-outcome-inventory-2009-2025'):
        old = pl.read_parquet(OLD/name/'tables/people-debut-dates.parquet').select('player_id', 'mlb_debut_date')
        check = old.join(d.rename({'mlb_debut_date':'census_date'}), on='player_id', how='left', validate='1:1')
        assert not check.filter(pl.col('census_date').is_null() | (pl.col('census_date')!=pl.col('mlb_debut_date'))).height
        comparisons.append({'source': name, 'matched': check.height})
    d.write_parquet(OUT/'debut-dates.parquet')
    return d, {'censuses': [r[1] for r in results], 'cross_checks': comparisons,
               'inferred_earliest_birth_year': float((panel['origin_year']-panel['age']).min())}


def rosters():
    jobs = []
    for year in YEARS:
        teams = capture(f'roster/{year}/teams.json.gz', '/teams', {'sportId':1, 'season':year})['teams']
        ids = sorted({int(t['id']) for t in teams})
        assert len(ids)==30
        jobs.extend((year,t) for t in ids)
    def fetch(job):
        year, team = job
        payload = capture(f'roster/{year}/{team}.json.gz', f'/teams/{team}/roster',
                          {'rosterType':'40Man', 'season':year, 'date':f'{year}-12-31'})
        f = project_team_40man_membership_payload(payload, team_id=team, season=year, as_of_date=date(year,12,31))
        if not 15 <= f.height <= 65:
            raise ValueError(f'Suspicious roster size {year} {team}: {f.height}')
        return f
    with ThreadPoolExecutor(max_workers=6) as ex: frames = list(ex.map(fetch, jobs))
    r = pl.concat(frames).sort('season','team_id','player_id')
    assert not r.group_by('season','player_id').len().filter(pl.col('len')!=1).height
    assert r.filter((pl.col('season')==2021)&pl.col('player_id').is_in([665161,677649])).height==2
    r.write_parquet(OUT/'year-end-rosters.parquet')
    return r


def league_context():
    blocks = [('affiliated-skill-source-2003-2007', [2007]),
              ('affiliated-skill-source-2008-2017', list(range(2008,2018))),
              ('affiliated-skill-source-2018-2022', list(range(2018,2023))),
              ('affiliated-skill-source', [2023,2024])]
    outputs, audit, hashes = [], [], {}
    keys = ['season','player_id','sport_id','team_id']
    for folder, years in blocks:
        root = OLD/folder
        path = root/'tables/affiliated_hitting_components.parquet'
        hashes[str(path)] = sha256_file(path)
        canonical = pl.read_parquet(path).filter(pl.col('season').is_in(years)).select(*keys,'plate_appearances')
        assert canonical.unique(keys).height==canonical.height
        for year in years:
            raw = []
            paths = sorted((root/'captures'/str(year)).glob('hitting-offset-*.json.gz'))
            assert paths, (folder, year)
            for path in paths:
                hashes[str(path)] = sha256_file(path)
                with gzip.open(path, 'rt', encoding='utf-8') as f: payload=json.load(f)
                for stat in payload.get('stats',[]):
                    for s in stat.get('splits',[]):
                        # Canonical source accepts calendar seasons only; split
                        # tournament labels are not silently coerced into a year.
                        if str(s.get('season'))!=str(year): continue
                        if not all(s.get(k,{}).get('id') for k in ('player','sport','team')): continue
                        raw.append({'season':year,'player_id':int(s['player']['id']),
                            'sport_id':int(s['sport']['id']),'team_id':int(s['team']['id']),
                            'league_id':s.get('league',{}).get('id'),
                            'raw_pa':int(s.get('stat',{}).get('plateAppearances',0))})
            rf = pl.DataFrame(raw).unique()
            assert rf.unique(keys).height==rf.height, f'Conflicting league stints {year}'
            q=canonical.filter(pl.col('season')==year).join(rf,on=keys,how='left',validate='1:1')
            assert not q.filter(pl.col('raw_pa').is_not_null()&(pl.col('raw_pa')!=pl.col('plate_appearances'))).height
            a=q.group_by('season','player_id').agg(pl.col('plate_appearances').sum().alias('total_pa'),
                pl.when(pl.col('league_id').is_not_null()).then(pl.col('plate_appearances')).otherwise(0).sum().alias('known_pa'),
                pl.when(pl.col('league_id')==125).then(pl.col('plate_appearances')).otherwise(0).sum().alias('mexican_pa'))
            # Unknown rows never count as known affiliated play. A partially
            # covered player's known Mexican share is accompanied by coverage.
            a=a.with_columns(pl.when(pl.col('known_pa')>0).then(pl.col('mexican_pa')/pl.col('known_pa')).otherwise(None).alias('mexican_pa_share'),
                pl.when(pl.col('total_pa')>0).then(pl.col('known_pa')/pl.col('total_pa')).otherwise(0.).alias('known_pa_share'))
            outputs.append(a)
            audit.append({'season':year,'stints':q.height,'unmatched_stints':q['raw_pa'].null_count(),
                          'unknown_league_stints':q['league_id'].null_count(),'mexican_players':a.filter(pl.col('mexican_pa')>0).height})
    annual=pl.concat(outputs).sort('season','player_id')
    annual.write_parquet(OUT/'league-context.parquet')
    return annual, audit, hashes


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    panel=pl.read_parquet(SOURCE/'input-panel.parquet')
    print('Historical debut census 1960-2025',flush=True)
    d, da=debuts(panel)
    print('December 31 rosters, every study origin',flush=True)
    r=rosters()
    print('Dated league context from captured stints',flush=True)
    a, la, hashes=league_context()
    c=attach_leagues(corrected_cohorts(panel,d),a)
    f=attach_roster(c,r)
    assert f.height==panel.height and f['player_id'].equals(panel['player_id'])
    for col in panel.columns:
        if col not in COHORTS+['on_40man']: assert panel[col].equals(f[col]),col
    # Previously observed MLB PA must agree with repaired debut status.
    for lag in range(3):
        assert not f.filter((pl.col(f'mlb_pa_lag{lag}')>0)&~pl.col('prior_debut')).height
    f.write_parquet(OUT/'repaired-panel.parquet')
    change=panel.select('origin_year','player_id','player_name','age','level','prospect','prior_debut','on_40man').rename(
        {c:'old_'+c for c in ('prospect','prior_debut','on_40man')}).join(
        f.select('origin_year','player_id',*COHORTS,'on_40man','league_mexican_pa_share_lag0','league_known_pa_share_lag0'),
        on=['origin_year','player_id'],how='left',validate='1:1')
    change.write_parquet(OUT/'source-changes.parquet')
    hashes.update({str(SOURCE/'input-panel.parquet'):sha256_file(SOURCE/'input-panel.parquet')})
    hashes.update({str(p):sha256_file(p) for p in sorted((OUT/'captures').rglob('*.json.gz'))})
    save(OUT/'source-audit.json',{'debut':da,'leagues':la,'source_hashes':hashes,
        'changes':change.group_by('origin_year').agg(pl.len().alias('rows'),
            (pl.col('old_prospect')!=pl.col('prospect')).sum().alias('cohort_changes'),
            ((pl.col('old_on_40man')==0)&(pl.col('on_40man')==1)).sum().alias('roster_added'),
            ((pl.col('old_on_40man')==1)&(pl.col('on_40man')==0)).sum().alias('roster_removed')).sort('origin_year').to_dicts(),
        'roster_counts':r.group_by('season').agg(pl.len().alias('members'),pl.col('team_id').n_unique().alias('teams')).sort('season').to_dicts(),
        'protected_outcomes_used':False,'production_forecasts_changed':False})
    print('Sources materialized and audited',flush=True)


if __name__=='__main__':main()
