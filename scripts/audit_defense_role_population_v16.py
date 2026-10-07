"""Full-population dated role source certification, not a fitted projection."""
from collections import defaultdict
from pathlib import Path
import json

import polars as pl

from capture_defense_role_population_v16 import ROOT, OUT, SOURCE, OLD, SPORTS, read, write, check, people_logs
from universal_baseball.defense_role_logs import apply_dual_dh, position_totals
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

DH=ROOT/'reports/generated/defense-budget-v13'
FIELDS=('fielding_outs','appearances','raw_starts','reviewed_starts','certified_dual_DH_addition')


def main():
    protections();check();assert not (OUT/'source-review.json').exists()
    seal=dict(before_source_projection=True,no_fits=True,hashes={str(p):sha256_file(p) for p in
        [Path(__file__),ROOT/'src/universal_baseball/defense_role_logs.py',OUT/'manifest.json',
         OUT/'capture-complete.json',DH/'source-review.json',DH/'reviewed-DH-starts.parquet']})
    if (OUT/'source-audit-seal.json').exists():assert read(OUT/'source-audit-seal.json')==seal
    else:write('source-audit-seal.json',seal)
    manifest=read(OUT/'manifest.json');complete=read(OUT/'capture-complete.json')
    assert complete['all_manifest_requests_completed'] and complete['requests']==745
    assert read(OUT/'population-capture-seal.json')['manifest_sha256']==sha256_file(OUT/'manifest.json')
    original=defaultdict(lambda:defaultdict(lambda:dict(fielding_outs=0,raw_starts=0,appearances=0)))
    for r in pl.read_parquet(SOURCE).filter(pl.col('season').is_between(2021,2024)).to_dicts():
        key=(r['player_id'],r['season'],SPORTS[r['normalized_level']]);pos=(r['league_id'],int(r['position_code']))
        v=original[key][pos]
        v['fielding_outs']+=r['fielding_outs'];v['raw_starts']+=r['games_started'];v['appearances']+=r['games_played']
    corrections=defaultdict(list)
    d=read(DH/'source-review.json')
    for c in d['corrections']:
        if c['season']<=2024:
            for r in c['game_evidence']:
                corrections[r['player_id'],r['season']].append(dict(r,
                    source_id=str(DH/'captures'/f"box-{r['game_id']}.json")))
    parts=[];scope_checks=[];seen=set();errors=[];normal=OUT/'normalized';normal.mkdir(exist_ok=True)
    for index,job in enumerate(manifest['requests']):
        path=OUT/'captures'/(job['capture_name']+'.json')
        assert sha256_file(path)==complete['hashes'][str(path)]
        meta=read(path.with_suffix('.capture.json'))
        assert meta['endpoint']==job['endpoint'] and meta['sha256']==sha256_file(path)
        try:
            batch=people_logs(read(path),job['player_ids'],job['origin'],job['sport_id'],str(path))
        except (AssertionError,KeyError,ValueError) as exc:
            errors.append(dict(capture_name=job['capture_name'],reason=str(exc),player_ids=job['player_ids']))
            batch={}
        normalized=[]
        for pid in job['player_ids']:
            key=(pid,job['origin'],job['sport_id']);assert key not in seen;seen.add(key)
            raw=batch.get(pid,[]);actual=position_totals(raw)
            expected=original[key];comparison=[]
            actual_by_position={(k[1],k[2]):v for k,v in actual.items()}
            for position in sorted(set(expected)|set(actual_by_position)):
                e=expected.get(position,dict(fielding_outs=0,raw_starts=0,appearances=0))
                a=actual_by_position.get(position,dict(fielding_outs=0,raw_starts=0,appearances=0))
                fields=['fielding_outs','raw_starts','appearances']
                comparison.append(dict(league_id=position[0],position_code=position[1],
                    annual={f:e[f] for f in fields},log={f:a[f] for f in fields},
                    exact_match=all(e[f]==a[f] for f in fields)))
            passed=bool(raw) and bool(comparison) and all(v['exact_match'] for v in comparison)
            scope_checks.append(dict(player_id=pid,origin=job['origin'],sport_id=job['sport_id'],
                position_game_rows=len(raw),status='verified' if passed else 'unknown_or_mismatch',
                source=str(path),comparisons=comparison))
            if not passed:continue
            fixed=apply_dual_dh(raw,corrections[pid,job['origin']]) if job['sport_id']==1 else raw
            normalized.extend(fixed)
        if normalized:
            dest=normal/(job['capture_name']+'.parquet');assert not dest.exists()
            pl.DataFrame(normalized,infer_schema_length=None).write_parquet(dest);parts.append(dest)
        if index%50==0:print(f'Certified batches {index+1}/745; unknown scopes so far '
                            f"{sum(s['status']!='verified' for s in scope_checks)}",flush=True)
    assert len(seen)==manifest['source_scopes']==23412
    # Some batches contain no corrections; cast the null-only column consistently.
    frames=[pl.scan_parquet(p).with_columns(pl.col('correction_source').cast(pl.String)) for p in parts]
    games=pl.concat(frames,how='vertical_relaxed').collect()
    assert games.select('player_id','game_id','position_code').unique().height==games.height
    games.sort('player_id','season','sport_id','date','game_id','position_code').write_parquet(OUT/'verified-role-games.parquet')
    periods=games.group_by('player_id','season','sport_id','league_id','period','position_code','position').agg(
        *[pl.col(field).sum() for field in FIELDS],pl.col('game_id').n_unique().alias('position_games'),
        pl.col('date').min().alias('first_date'),pl.col('date').max().alias('last_date')).sort(
        'player_id','season','sport_id','league_id','period','position_code')
    periods.write_parquet(OUT/'verified-role-periods.parquet')
    for field in FIELDS:assert games[field].sum()==periods[field].sum()
    verified={(r['player_id'],r['origin'],r['sport_id']) for r in scope_checks if r['status']=='verified'}
    by_pair=defaultdict(list)
    for r in periods.to_dicts():by_pair[r['player_id'],r['season']].append(r)
    features=[]
    for case in manifest['input_cases']:
        pid,y=case['player_id'],case['origin'];declared=case['declared_sports']
        valid=bool(declared) and all((pid,y,sport) in verified for sport in declared)
        record=dict(**case,current_source_status='verified_all_declared_scopes' if valid else
            'unknown_current_scope' if not declared else 'partial_or_mismatch',
            verified_sports=[sport for sport in declared if (pid,y,sport) in verified],
            current_role_periods=by_pair[pid,y],
            current_assignment_is_defensive_talent=False)
        # Nullable all-source features are explicit: do not turn a source hole into zeros.
        for scope in ('all','MLB','minor'):
            for period in ('full_year','before_August','August_onward'):
                selected=[r for r in by_pair[pid,y] if (scope=='all' or (r['sport_id']==1)==(scope=='MLB'))
                    and (period=='full_year' or r['period']==period)]
                usable=valid and (scope=='all' or (1 in declared if scope=='MLB' else any(s!=1 for s in declared)))
                for field in ('fielding_outs','reviewed_starts','appearances'):
                    record[f'{scope}_{period}_{field}']=[sum(r[field] for r in selected if r['position_code']==p)
                        for p in range(2,11)] if usable else None
        features.append(record)
    frame=pl.DataFrame(features,infer_schema_length=None)
    assert frame.height==16674 and frame['row_id'].n_unique()==16674
    frame.write_parquet(OUT/'current-role-source-features.parquet')
    unknown=[r for r in scope_checks if r['status']!='verified']
    save(OUT/'scope-comparisons.json',dict(scopes=scope_checks,batch_parser_errors=errors))
    results=dict(source_integrity='verified_scopes_only',source_scopes=23412,
        verified_scopes=len(verified),unknown_scopes=len(unknown),unknown_scope_details=unknown,
        feature_rows=16674,evaluation_rows=12432,unknown_current_source_cases=len(manifest['unknown_current_source']),
        current_source_status=frame.group_by('current_source_status').len().to_dicts(),
        position_game_rows=games.height,period_cells=periods.height,
        dated_DH_additions=int(games['certified_dual_DH_addition'].sum()),batch_parser_errors=errors,
        latest_features_are_source_descriptors=True,no_recency_weight_chosen=True,
        no_fits=True,no_accuracy_claim=True,player_walkthrough_status='pending',no_deployment=True,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'manifest.json',OUT/'capture-complete.json',
            OUT/'scope-comparisons.json',OUT/'verified-role-games.parquet',OUT/'verified-role-periods.parquet',
            OUT/'current-role-source-features.parquet',DH/'source-review.json',DH/'reviewed-DH-starts.parquet']})
    write('source-review.json',results);protections()
    print(f'{games.height} verified position-game rows; {len(unknown)} unknown scopes; '
          f'{frame.height} fixed feature rows retained. Source certification, not a forecast.',flush=True)


if __name__=='__main__':main()
