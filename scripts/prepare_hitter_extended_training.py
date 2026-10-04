"""Reconstruct compatible earlier inputs and seal all matched preflights."""
from pathlib import Path
import gzip
import json

import numpy as np
import polars as pl

from universal_baseball.forecast_validation import preflight
from universal_baseball.historical_prospect_rank import features as rank_features
from universal_baseball.hitter_value_panel import build_neutral_mlb_value_targets
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.practical_hitter_v30 import EVENTS
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import materialize as pooled_features
from prepare_hitter_games_v38 import features as game_features

ROOT = Path(__file__).resolve().parents[1]
OLD = Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')
OUT = ROOT/'reports/generated/hitter-extended-training'
EARLY = ROOT/'reports/generated/hitter-older-origin-source'
CURRENT = ROOT/'reports/generated/hitter-preseason-readiness-v68'
BUCKETS = ['MLB','AAA','AA','Aplus','A','Aminus','DSL','RK120','RK121','RK124','RK128','RK134','RKother','MEX']
POS = [str(i) for i in range(1,11)]+['Y','UNKNOWN']
FLAGS = ['roster_coverage_known','debut_elapsed_unknown']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def write(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                   allow_nan=False, default=str)+'\n', encoding='utf8')


def verify(hashes):
    for path, digest in hashes.items():
        assert sha256_file(Path(path)) == digest, path


def bucket(row):
    if row['league_id'] == 125:
        return 'MEX'
    if row['sport_id'] == 1:
        return 'MLB'
    if row['league_id'] == 130:
        return 'DSL'
    if row['sport_id'] in [11,12,13,14,15]:
        return {11:'AAA',12:'AA',13:'Aplus',14:'A',15:'Aminus'}[row['sport_id']]
    if row['league_id'] in [120,121,124,128,134]:
        return 'RK'+str(row['league_id'])
    return 'RKother'


def earlier_games(history):
    """Read only 2006/07 raw games; overlapping later games already reconciled."""
    report = read(OLD/'affiliated-skill-source-2003-2007/report.json')
    rows, hashes = [], {}
    pages = [p for p in report['captures'] if p['season'] in [2006,2007]
             and p['stat_group'] == 'hitting']
    paths = [OLD.parent.parent/p['path'].replace('\\','/') for p in pages]
    for year in [2006,2007]:
        receipt = read(ROOT/f'model_artifacts/hitter-older-origin-source/{year}-receipt.json')
        paths += [Path(p['path']) for p in receipt['captures']
                  if p['parameters'].get('group') == 'hitting']
    for path in paths:
        hashes[str(path)] = sha256_file(path)
        payload = json.loads(gzip.decompress(path.read_bytes()))
        for block in payload['stats']:
            for s in block['splits']:
                y = int(s['season'])
                assert y in [2006,2007]
                g = s['stat'].get('gamesPlayed')
                assert isinstance(g, int) and g >= 0, 'Unknown games are not zero'
                rows.append(dict(season=y, player_id=int(s['player']['id']),
                    sport_id=int(s['sport']['id']), team_id=int(s['team']['id']),
                    source_pa=int(s['stat']['plateAppearances']), games_played=g))
    raw = pl.DataFrame(rows)
    keys = ['season','player_id','sport_id','team_id']
    assert raw.unique(keys).height == raw.height
    joined = history.filter(pl.col('season') < 2008).join(raw, on=keys, validate='1:1')
    assert len(joined) == len(history.filter(pl.col('season') < 2008))
    assert joined['source_pa'].equals(joined['plate_appearances'])
    assert joined.filter((pl.col('plate_appearances') > 0)&(pl.col('games_played') == 0)).is_empty()
    counts = joined.group_by('season','player_id','bucket').agg(
        pl.col('plate_appearances','games_played').sum())
    path = ROOT/'reports/generated/practical-hitter-v38/game-counts.parquet'
    later = pl.read_parquet(path).filter(pl.col('season') <= 2010)
    combined = pl.concat([counts, later], how='vertical_relaxed').sort('season','player_id','bucket')
    expected = history.group_by('season','player_id','bucket').agg(pl.col('plate_appearances').sum())
    assert combined.select(expected.columns).sort('season','player_id','bucket').equals(
        expected.sort('season','player_id','bucket'))
    hashes[str(path)] = sha256_file(path)
    return combined, hashes


def debut_inputs(year, date, observed_mlb):
    dated = date is not None and date.year <= year
    prior = dated or observed_mlb
    return (year-date.year if dated else -1), int(prior), int(prior and not dated)


def materialize(population, history, counts, targets, old_mlb, roster):
    # MLB batting above average does not depend on the replacement/schedule term.
    early_value = build_neutral_mlb_value_targets(old_mlb.filter(pl.col('season').is_between(2006,2009)))
    annual_pa = old_mlb.group_by('season').agg(pl.col('batting_plate_appearances').sum()).to_dicts()
    totals = {s['season']:s['batting_plate_appearances'] for s in annual_pa}
    env = {s['season']:(s['schedule_fraction'], 570*s['schedule_fraction']/s['league_pa'])
           for s in targets.unique('season').iter_rows(named=True)}
    values = {(s['season'],s['player_id']):s for s in targets.iter_rows(named=True)}
    for s in early_value.filter(pl.col('season') < 2009).iter_rows(named=True):
        values[s['season'],s['player_id']] = s
    for year in [2006,2007,2008]:
        env[year] = (1.,570/totals[year])
    check = early_value.filter(pl.col('season') == 2009).join(
        targets.filter(pl.col('season') == 2009).select('player_id','component_war'),
        on='player_id', validate='1:1', suffix='_calendar')
    fraction, replacement = env[2009]
    assert len(check) == len(early_value.filter(pl.col('season') == 2009))
    assert np.allclose(check['component_war']-570/totals[2009]*check['mlb_pa'],
        check['component_war_calendar']-replacement*check['mlb_pa'], atol=1e-12, rtol=0)
    lut = {(s['season'],s['player_id'],s['bucket']):s for s in counts.iter_rows(named=True)}
    assert len(lut) == len(counts)
    primary = history.filter(pl.col('plate_appearances') > 0).sort(
        ['season','player_id','plate_appearances','team_id'], descending=[False,False,True,False]
    ).unique(['season','player_id'], keep='first').sort('season')
    histories = {}
    for s in primary.iter_rows(named=True):
        histories.setdefault(s['player_id'],[]).append(s)
    listings = {(s['season'],s['player_id']):s['team_id'] for s in roster.iter_rows(named=True)}
    earliest_observed = old_mlb.filter(pl.col('batting_plate_appearances') > 0).group_by('player_id').agg(
        pl.col('season').min()).to_dicts()
    first = {s['player_id']:s['season'] for s in earliest_observed}
    rows = []
    for i,s in enumerate(population.sort('origin_year','player_id').iter_rows(named=True)):
        y,pid = s['origin_year'],s['player_id']
        past = [v for v in histories.get(pid,[]) if v['season'] <= y]
        last = past[-1] if past else None
        unknown = s['resolved_age'] is None
        age = 27. if unknown else s['resolved_age']
        elapsed, prior, elapsed_unknown = debut_inputs(y,s['mlb_debut_date'],first.get(pid,9999) <= y)
        row = dict(row_id=1000000+i, origin_year=y, target_year=y+1, horizon=1,
            player_id=pid, outer_fold=player_fold(pid), age=float(age), age_unknown=int(unknown),
            age_centered=(age-27)/5, age_squared=((age-27)/5)**2,
            elapsed=elapsed, elapsed_scaled=max(-1,elapsed)/10, prior_debut=prior,
            debut_elapsed_unknown=elapsed_unknown, window_complete=True,
            player_name=last['player_name'] if last else s['captured_name'],
            team_id=listings.get((y,pid), last['team_id'] if last else None),
            on_40man=int((y,pid) in listings) if y >= 2009 else -1,
            roster_coverage_known=int(y >= 2009), reorganized=0,
            last_stat_gap=min(5,y-last['season']) if last else 5,
            source_position=last['position'] if last else 'UNKNOWN',
            snapshot_level=s['snapshot_level'])
        for p in POS:
            row['position_'+p] = int(row['source_position'] == p)
        regular,absence = 0,0
        for lag in range(3):
            year = y-lag
            row['milb_canceled_'+str(lag)] = 0
            allpa,mpa = 0,0
            for b in BUCKETS:
                c = lut.get((year,pid,b))
                pa = c['plate_appearances'] if c else 0
                allpa += pa
                key = f'{b}_{lag}_'
                row[key+'pa'] = float(pa)
                row[key+'present'] = int(pa > 0)
                for e,(num,den,prior_rate) in EVENTS.items():
                    row[key+e] = ((c[num] if c else 0)+100*prior_rate)/((c[den] if c else 0)+100)
                if b == 'MLB':
                    mpa = pa
            row[f'pa_{lag}'] = mpa
            row[f'work_{lag}'] = mpa/env[year][0]
            row[f'minor_pa_{lag}'] = allpa-mpa
            target = values.get((year,pid))
            value = target['component_war'] if target else 0
            row[f'quality_{lag}'] = 600*(value-env[year][1]*mpa)/(mpa+1200)
            row[f'quality_present_{lag}'] = int(mpa > 0)
            regular += row[f'work_{lag}'] >= 400
            absence += mpa == 0
        row.update(regular_window=int(regular),regular_window_scaled=regular/3,absence_window_scaled=absence/3)
        row['current_state'] = 0 if row['pa_0'] == 0 else 1 if row['pa_0'] < 200 else 2 if row['pa_0'] < 400 else 3
        row['stage'] = 'Current MLB' if row['pa_0'] > 0 else 'Upper minors' if row['AAA_0_pa']+row['AA_0_pa'] > 0 else 'Lower minors' if row['minor_pa_0'] > 0 else 'Inactive / unknown'
        row['origin_replacement_rate'] = env[y][1]/env[y][0]
        row['career_mlb_observed_pa'] = sum(v['plate_appearances'] for v in past if v['sport_id'] == 1 and v['season'] >= 2008)
        row['career_mlb_left_truncated'] = int(s['mlb_debut_date'] is not None and s['mlb_debut_date'].year < 2008)
        nxt = values.get((y+1,pid))
        pa,value = (nxt['mlb_pa'],nxt['component_war']) if nxt else (0,0.)
        assert pa == s['next_pa']
        row.update(next_pa=pa,next_value=value,next_state=0 if pa==0 else 1 if pa<200 else 2 if pa<400 else 3,
            next_batting_rate=600*(value-env[y+1][1]*pa)/pa if pa else 0.,
            next_active=int(pa > 0), hard_unavailable=False, needs_availability_scenario=False)
        rows.append(row)
    return pl.DataFrame(rows), dict(overlap_batting_formula_exact=True,
        early_quality_seasons=[2006,2007,2008], early_workload_schedule='nominal full season',
        early_elapsed_unknown=sum(r['debut_elapsed_unknown'] for r in rows))


def profile(f):
    dominant = []
    for s in f.select([f'{b}_0_pa' for b in BUCKETS]).iter_rows(named=True):
        b = max(BUCKETS,key=lambda b:s[f'{b}_0_pa'])
        dominant.append(b if s[f'{b}_0_pa'] > 0 else 'INACTIVE')
    return f.with_columns(pl.Series('dominant_level',dominant),
        pl.when(pl.col('age_unknown')==1).then(pl.lit('unknown'))
          .when(pl.col('age')<=17).then(pl.lit('17under')).when(pl.col('age')<=20).then(pl.lit('18to20'))
          .when(pl.col('age')<=23).then(pl.lit('21to23')).otherwise(pl.lit('24plus')).alias('age_band'),
        pl.when(pl.col('scout_listed_0')<0).then(-1).when(pl.col('scout_listed_0')==0).then(0)
          .when(pl.col('scout_rank_score_0')>=.81).then(1).otherwise(2).alias('rank_band'),
        (pl.sum_horizontal([pl.col(f'{b}_{k}_pa') for b in BUCKETS for k in range(3)])<150).alias('thin_pro'),
        ((pl.col('draft_known')==1)&(pl.col('draft_year')==pl.col('origin_year'))).alias('new_draftee'))


def main():
    assert not (OUT/'preflight.json').exists(), 'Preserve sealed comparison'
    reviewed = read(EARLY/'final-report.json')
    assert reviewed['player_walkthrough_status'] == 'complete'
    verify(reviewed['hashes'])
    f = pl.read_parquet(CURRENT/'features.parquet').sort('row_id')
    assert len(f) == 63282
    original_cols = f.columns
    # Current histories already passed the dated debut source review.
    f = f.with_columns(pl.lit(1).alias(FLAGS[0]),pl.lit(0).alias(FLAGS[1]))
    history = pl.read_parquet(EARLY/'history.parquet')
    history = history.with_columns(pl.Series('bucket',[bucket(s) for s in history.iter_rows(named=True)]),
        (pl.col('hits')-pl.col('home_runs')-pl.col('doubles')-pl.col('triples')).alias('singles'),
        (pl.col('base_on_balls')-pl.col('intentional_walks')).alias('unintentional_walks'),
        (pl.col('hits')-pl.col('home_runs')).alias('babip_hits'),
        (pl.col('at_bats')-pl.col('strike_outs')-pl.col('home_runs')+pl.col('sac_flies')).alias('babip_opportunities'))
    countcols = list(dict.fromkeys(['plate_appearances',*[v[0] for v in EVENTS.values()],*[v[1] for v in EVENTS.values()]]))
    counts = history.group_by('season','player_id','bucket').agg(pl.col(countcols).sum()).sort('season','player_id','bucket')
    current_counts = pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet').filter(pl.col('season')<=2010)
    assert counts.filter(pl.col('season')>=2008).select(current_counts.columns).sort('season','player_id','bucket').equals(current_counts.sort('season','player_id','bucket'))
    games, game_hashes = earlier_games(history)
    population = pl.read_parquet(EARLY/'population-with-ages.parquet')
    targets = pl.read_parquet(ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet')
    old_mlb_path = OLD/'career-mlb-outcome-inventory-2004-2009/tables/mlb_hitting_components_2004_2009.parquet'
    old_mlb = pl.read_parquet(old_mlb_path)
    roster_path = ROOT/'reports/generated/hitter-arrival-source-repair-v1/year-end-rosters.parquet'
    old, note = materialize(population,history,counts,targets,old_mlb,pl.read_parquet(roster_path))
    draft_path = OLD/'draft-history/draft-history.parquet'
    draft = pl.read_parquet(draft_path).filter(pl.col('draft_year')<=2024)
    old = pooled_features(old,counts,draft)
    old, _ = game_features(old,games)
    ranks_path = ROOT/'reports/generated/hitter-preseason-readiness-v67/ranks.parquet'
    ranks = pl.read_parquet(ranks_path)
    lookup = {(r['season'],r['player_id']):r['rank'] for r in ranks.iter_rows(named=True)}
    capacity = {r['season']:r['list_capacity'] for r in ranks.iter_rows(named=True)}
    scout = [n for n in f.columns if n.startswith('scout_')]
    overlay = pl.DataFrame([dict(row_id=r['row_id'],**rank_features(r['player_id'],r['origin_year']+1,lookup,capacity))
        for r in old.iter_rows(named=True)],schema={'row_id':pl.Int64,**{n:pl.Float64 for n in scout}}).with_columns(pl.col(scout).fill_null(-1.))
    old = old.join(overlay,on='row_id',validate='1:1')
    # Keep only actual model and review inputs, rather than fabricate unused legacy fields.
    p = read(CURRENT/'preflight.json')
    rate = read(ROOT/'reports/generated/practical-hitter-numeric-repair-v53/preflight.json')['rate_features']+FLAGS
    pa = p['pa_features']+FLAGS
    extra = ['row_id','origin_year','target_year','horizon','player_id','outer_fold','age','age_unknown','elapsed',
        'prior_debut','window_complete','player_name','team_id','source_position','snapshot_level','stage',
        'regular_window','current_state','next_pa','next_value','next_batting_rate','next_active',
        'pa_0','minor_pa_0','origin_replacement_rate','draft_year','pick_number',
        *[f'{b}_0_pa' for b in BUCKETS]]
    columns = list(dict.fromkeys([*extra,*rate,*pa]))
    assert f.select(original_cols).equals(pl.read_parquet(CURRENT/'features.parquet').sort('row_id'))
    source = pl.concat([f.select(columns),old.select(columns)],how='vertical_relaxed').sort('row_id')
    assert len(source)==76639 and source.unique(['origin_year','player_id']).height==len(source)
    assert np.isfinite(source.select(list(dict.fromkeys(rate+pa))).to_numpy()).all()
    OUT.mkdir(parents=True,exist_ok=True)
    source.write_parquet(OUT/'features.parquet')
    history.write_parquet(OUT/'dated-earlier-history.parquet')
    counts.write_parquet(OUT/'earlier-counts.parquet')
    games.write_parquet(OUT/'earlier-games.parquet')
    supports,profiles,cells = [],[],[]
    for c in p['cells']:
        te = source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
        checks, memberships = {},{}
        for arm in ['restricted','extended']:
            tr = source.filter(pl.col('row_id').is_in(c['training_row_ids']))
            if arm == 'extended':
                added = source.filter((pl.col('origin_year')<=2010)&(pl.col('target_year')<=c['year'])&(pl.col('outer_fold')!=c['fold']))
                tr = pl.concat([tr,added],how='vertical_relaxed')
            tr = tr.sort('row_id')
            memberships[arm] = tr['row_id'].to_list()
            for head,sub,names in [('participation',tr,pa),('conditional_pa',tr.filter(pl.col('next_pa')>0),pa),('rate',tr.filter(pl.col('next_pa')>0),rate)]:
                sup,check = preflight(sub,te,cutoff=c['year'],fold=c['fold'],features=names,expected_keys=te.select('row_id','horizon').iter_rows())
                checks[arm+'_'+head] = check
                supports.append(sup.with_columns(pl.lit(arm).alias('arm'),pl.lit(head).alias('head')))
                for kind,keys in [('broad',['prior_debut','dominant_level','age_band']),('refined',['prior_debut','dominant_level','age_band','rank_band','thin_pro','new_draftee'])]:
                    a,b = profile(sub),profile(te)
                    n = a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                    profiles.append(b.select('row_id',*keys).join(n,on=keys,how='left',validate='m:1').with_columns(
                        pl.col('profile_people').fill_null(0),pl.lit(arm).alias('arm'),pl.lit(head).alias('head'),pl.lit(kind).alias('kind')))
        cells.append(dict(year=c['year'],fold=c['fold'],test_row_ids=c['test_row_ids'],training_row_ids=memberships,checks=checks))
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    pl.concat(profiles,how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet')
    paths = [Path(__file__),ROOT/'docs/hitter-extended-training-contract.md',ROOT/'scripts/fit_hitter_extended_training.py',
        ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'scripts/prepare_practical_hitter_v33.py',ROOT/'scripts/prepare_hitter_games_v38.py',
        ROOT/'src/universal_baseball/hitter_value_panel.py',ROOT/'src/universal_baseball/forecast_validation.py',
        ROOT/'src/universal_baseball/historical_prospect_rank.py',EARLY/'final-report.json',EARLY/'history.parquet',EARLY/'population-with-ages.parquet',
        CURRENT/'features.parquet',CURRENT/'preflight.json',CURRENT/'scored-predictions.parquet',old_mlb_path,roster_path,draft_path,ranks_path,
        ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet',
        ROOT/'reports/generated/hitter-talent-bridge-v74/predictions.parquet',
        OUT/'features.parquet',OUT/'dated-earlier-history.parquet',OUT/'earlier-counts.parquet',OUT/'earlier-games.parquet',OUT/'support.parquet',OUT/'profile-support.parquet']
    hashes = {str(path):sha256_file(path) for path in paths}
    hashes.update(game_hashes)
    write('preflight.json',dict(before_fitting=True,cells=cells,pa_features=pa,rate_features=rate,settings=p['settings'],ridge_alpha=100,
        original_source_rows=63282,added_rows=13357,evaluation_rows=30506,checks_before_fits=210,
        current_inputs_exact=True,source_recipe_note=note,input_hashes=hashes,
        unavailable_2008_roster_rows=old.filter(pl.col('roster_coverage_known')==0).height,
        unknown_early_rank_rows=old.filter(pl.col('scout_listed_0')<0).height,
        player_walkthrough_status='pending',protected_outcomes_used=False))
    print('All 210 matched arm/head checks sealed; source',len(source),'; rate/PA inputs',len(rate),len(pa),';',note,flush=True)


if __name__ == '__main__':
    main()
