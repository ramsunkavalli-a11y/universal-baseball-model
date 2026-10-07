"""Certify bounded dated assignment evidence; no model or accuracy verdict."""
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse
import json

import polars as pl

from capture_defense_role_v15 import ROOT, OUT, PUBLIC, SOURCE, WALK, capture, check_seal, read, receipt
from universal_baseball.defense_role_logs import parse_logs, apply_dual_dh, position_totals
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections

LEVEL_SPORT = {'MLB':1, 'AAA':11, 'AA':12, 'Aplus':13, 'A':14, 'Aminus':15,
               'DSL':16, 'COMPLEX':16, 'ROOKIE_COMBINED':16, 'ADVANCED_ROOKIE':16}
DH = ROOT/'reports/generated/defense-budget-v13'


def validate_capture(path):
    assert sha256_file(path) == read(path.with_suffix('.capture.json'))['sha256'], path
    return read(path)


def annual(pid, year, sport):
    frame = pl.read_parquet(SOURCE).filter((pl.col('player_id') == pid) & (pl.col('season') == year))
    return [r for r in frame.to_dicts() if LEVEL_SPORT[r['normalized_level']] == sport]


def certify_raw(rows, original):
    expected = defaultdict(lambda: dict(fielding_outs=0,raw_starts=0,appearances=0))
    for r in original:
        key = (LEVEL_SPORT[r['normalized_level']], r['league_id'], int(r['position_code']))
        expected[key]['fielding_outs'] += r['fielding_outs']
        expected[key]['raw_starts'] += r['games_started']
        expected[key]['appearances'] += r['games_played']
    actual = position_totals(rows)
    comparisons = []
    for key in sorted(set(expected) | set(actual)):
        before = expected.get(key,dict(fielding_outs=0,raw_starts=0,appearances=0))
        after = actual.get(key,dict(fielding_outs=0,raw_starts=0,appearances=0))
        fields = ['fielding_outs','raw_starts','appearances']
        comparisons.append(dict(sport_id=key[0],league_id=key[1],position_code=key[2],
            annual={f:before[f] for f in fields},gamelog={f:after[f] for f in fields},
            exact_match=all(before[f] == after[f] for f in fields)))
    return comparisons


def corrections(pid, year):
    review = read(DH/'source-review.json')
    selected = []
    for c in review['corrections']:
        if c['player_id'] == pid and c['season'] == year:
            for r in c['game_evidence']:
                selected.append(dict(r,source_id=str(DH/'captures'/f"box-{r['game_id']}.json")))
    return selected


def probes():
    protections(); check_seal()
    assert not (OUT/'probe-review.json').exists()
    cases = [('probe-Schwarber-2023',656941,2023,1),('probe-Ohtani-2023',660271,2023,1),
             ('probe-Buxton-2024',621439,2024,1),('probe-Eldridge-2024-singular-11',805811,2024,11)]
    records=[]
    for name,pid,y,sport in cases:
        path=OUT/'captures'/(name+'.json')
        rows=parse_logs(validate_capture(path),player_id=pid,season=y,sport_id=sport,source_id=str(path))
        comparisons=certify_raw(rows,annual(pid,y,sport))
        assert rows and all(r['exact_match'] for r in comparisons), name
        fixed=apply_dual_dh(rows,corrections(pid,y)) if sport==1 else rows
        records.append(dict(name=name,player_id=pid,season=y,sport_id=sport,rows=len(rows),
            annual_comparison=comparisons,certified_DH_additions=sum(r['certified_dual_DH_addition'] for r in fixed)))
    path=OUT/'captures/probe-date-range-2023.json'; data=validate_capture(path)
    group=data['stats'][0]
    failed=dict(endpoint=read(path.with_suffix('.capture.json'))['endpoint'],
        reported_total_splits=group.get('totalSplits'),returned_splits=len(group['splits']),
        source_disposition='Unusable: no returned splits; no late-season denominator can be certified.')
    assert failed['returned_splits']==0
    # The plural parameter is demonstrably not an all-level source.
    p=OUT/'captures/probe-Eldridge-2024-all-sports.json'
    assert validate_capture(p)['stats']==[]
    p=OUT/'captures/probe-Buxton-2024-all-sports.json'
    assert {r['sport']['id'] for g in validate_capture(p)['stats'] for r in g['splits']}=={1}
    receipt('probe-review.json',dict(gamelog_source_integrity='pass',
        all_sports_scope_verified=False,explicit_single_sport_scope_verified=True,
        cases=records,date_range_failure=failed,
        plural_sport_failure='Ignored plural sport filter: Eldridge empty; Buxton MLB only despite AAA usage.',
        expansion_route='One explicit sportId request for each annual-source sport; preserve missing scopes.',
        no_fits=True,no_accuracy_claim=True,no_deployment=True,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),ROOT/'src/universal_baseball/defense_role_logs.py',
            ROOT/'tests/test_defense_role_logs.py',SOURCE,DH/'source-review.json',DH/'reviewed-DH-starts.parquet']}))
    print('Four game-log cases exactly match annual sources; dated DH correction verified. '
          'Plural scope and empty date range rejected.',flush=True)
    protections()


def source_check_seal():
    check_seal()
    for path,expected in read(OUT/'source-seal.json')['hashes'].items():
        assert sha256_file(Path(path))==expected,path


def expand():
    protections(); check_seal()
    probe=read(OUT/'probe-review.json')
    assert probe['explicit_single_sport_scope_verified']
    for path,expected in probe['hashes'].items():assert sha256_file(Path(path))==expected,path
    if not (OUT/'source-seal.json').exists():
        receipt('source-seal.json',dict(before_expansion=True,no_fits=True,hashes={str(p):sha256_file(p) for p in
            [Path(__file__),ROOT/'src/universal_baseball/defense_role_logs.py',ROOT/'tests/test_defense_role_logs.py',
             OUT/'probe-review.json',ROOT/'docs/defense-role-v15-scope-amendment.md',WALK,SOURCE]}))
    source_check_seal()
    cases={(r['player_id'],r['origin']):r['name'] for c in read(WALK)['cases'] for r in c['records']}
    cases.update({(621439,2023):'Byron Buxton prior DH year',(805811,2023):'Bryce Eldridge prior RF year'})
    diagnosis=read(ROOT/'reports/generated/defense-jobs-v14/source-profile-diagnosis.json')
    for name,y in [('Jonah Bride',2021),('Jonathan Aranda',2021),('Eric Wagaman',2023)]:
        match=[r for r in diagnosis['Eldridge_prior_contributors'] if r['player_name']==name and r['origin_year']==y]
        assert len(match)==1,(name,y)
        cases[(match[0]['player_id'],y)]=name+' prior contributor'
    frame=pl.read_parquet(SOURCE);requests=[];missing=[]
    for (pid,y),name in sorted(cases.items()):
        original=frame.filter((pl.col('player_id')==pid)&(pl.col('season')==y)).to_dicts()
        sports=sorted({LEVEL_SPORT[r['normalized_level']] for r in original})
        if not sports:missing.append(dict(player_id=pid,season=y,name=name,status='Unknown annual scope'))
        for sport in sports:
            requests.append(dict(player_id=pid,season=y,name=name,sport_id=sport,
                capture_name=f'log-{y}-{pid}-sport-{sport}',
                endpoint=f'people/{pid}/stats?stats=gameLog&group=fielding&season={y}&gameType=R&sportId={sport}',
                annual_source_leagues=sorted({r['league_id'] for r in original if LEVEL_SPORT[r['normalized_level']]==sport})))
    manifest=dict(cases=[dict(player_id=pid,season=y,name=name) for (pid,y),name in sorted(cases.items())],
        requests=requests,unknown_cases=missing,selection='All fixed v14 focal and outcome-blind peers, deduplicated, '
        'plus two prior-year role contrasts and three saved multi-position prior contributors.',
        max_season=2024,no_fits=True)
    if (OUT/'explicit-scope-manifest.json').exists():assert read(OUT/'explicit-scope-manifest.json')==manifest
    else:receipt('explicit-scope-manifest.json',manifest)
    def one(r):
        capture(r['endpoint'],r['capture_name'])
        print(f"Captured {r['season']} {r['name']} sport {r['sport_id']}",flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(one,requests))
    protections()


def audit():
    protections(); source_check_seal()
    assert not (OUT/'source-review.json').exists()
    manifest=read(OUT/'explicit-scope-manifest.json');rows=[];checks=[];unknown=[];corrected=[]
    for request in manifest['requests']:
        pid,y,sport=request['player_id'],request['season'],request['sport_id']
        path=OUT/'captures'/(request['capture_name']+'.json')
        raw=parse_logs(validate_capture(path),player_id=pid,season=y,sport_id=sport,source_id=str(path))
        comparisons=certify_raw(raw,annual(pid,y,sport))
        passed=bool(raw) and all(r['exact_match'] for r in comparisons)
        checks.append(dict(**request,rows=len(raw),status='pass' if passed else 'unknown_or_mismatch',
                           annual_comparison=comparisons))
        if not passed:
            unknown.append(dict(**request,reason='Source scope empty or differs from annual inventory. No zero imputation.'))
            continue
        fixed=apply_dual_dh(raw,corrections(pid,y)) if sport==1 else raw
        fixed_DH=sum(r['reviewed_starts'] for r in fixed if r['position_code']==10)
        if sport==1:
            d=pl.read_parquet(DH/'reviewed-DH-starts.parquet').filter((pl.col('player_id')==pid)&(pl.col('season')==y))
            expected=int(d['reviewed_DH_starts'].sum())
            assert fixed_DH==expected,(pid,y,fixed_DH,expected)
        corrected.extend(r for r in fixed if r['certified_dual_DH_addition'])
        rows.extend(fixed)
    assert rows
    pl.DataFrame(rows,infer_schema_length=None).write_parquet(OUT/'verified-role-games.parquet')
    periods=pl.DataFrame(rows,infer_schema_length=None).group_by(
        'player_id','season','sport_id','league_id','period','position_code','position').agg(
        pl.col('fielding_outs').sum(),pl.col('appearances').sum(),pl.col('raw_starts').sum(),
        pl.col('reviewed_starts').sum(),pl.col('certified_dual_DH_addition').sum(),
        pl.col('game_id').n_unique().alias('position_games'),pl.col('date').min().alias('first_date'),
        pl.col('date').max().alias('last_date')).sort('player_id','season','sport_id','league_id','period','position_code')
    periods.write_parquet(OUT/'verified-role-periods.parquet')
    for field in ('fielding_outs','raw_starts','reviewed_starts','appearances'):
        assert periods[field].sum()==sum(r[field] for r in rows)
    receipt('source-review.json',dict(source_integrity='pass_for_verified_scopes',
        cases=len(manifest['cases']),requested_scopes=len(checks),verified_scopes=sum(r['status']=='pass' for r in checks),
        rows=len(rows),period_rows=periods.height,unknown_scopes=unknown,unknown_cases=manifest['unknown_cases'],
        checks=checks,dated_DH_additions=corrected,source_only=True,no_fits=True,no_accuracy_claim=True,
        player_walkthrough_status='pending',no_forecast_or_explorer_changes=True,no_2026_outcomes=True,
        hashes={str(p):sha256_file(p) for p in [OUT/'source-seal.json',OUT/'explicit-scope-manifest.json',
            OUT/'verified-role-games.parquet',OUT/'verified-role-periods.parquet']}))
    print(f'{len(checks)} scopes checked; {len(unknown)} uncertain; {len(rows)} verified position-game rows; '
          f'{len(corrected)} dated DH additions. No fit or accuracy claim.',flush=True)
    protections()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['probes','expand','audit'])
    globals()[parser.parse_args().mode]()
