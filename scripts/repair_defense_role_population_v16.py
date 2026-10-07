"""Additive team/date/component certification of the sealed role population."""
from collections import defaultdict
from pathlib import Path
import gzip
import hashlib
import json

import polars as pl

from capture_defense_role_population_v16 import ROOT, OUT, PUBLIC, SOURCE, SPORTS, read, check
from universal_baseball.defense_role_logs import position_totals, apply_dual_dh
from universal_baseball.defense_role_scope import schedule_context, parse_people_isolated, certify_measurements
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

DEST=OUT/'scope-repair'
AMEND=ROOT/'docs/defense-role-v16-scope-amendment.md'
DH=ROOT/'reports/generated/defense-budget-v13'
FIELDS=('fielding_outs','reviewed_starts','appearances')


def write(name,value):
    DEST.mkdir(parents=True,exist_ok=True)
    (PUBLIC/'scope-repair').mkdir(parents=True,exist_ok=True)
    save(DEST/name,value)
    save(PUBLIC/'scope-repair'/name,value)


def schedules():
    results, hashes = {}, {}
    injury=ROOT/'reports/generated/hitter-injury-history-v2/source'
    report=read(injury/'report.json');hashes[str(injury/'report.json')]=sha256_file(injury/'report.json')
    official={r['season']:r for r in report['source_records'] if r['kind']=='schedule'}
    for year in range(2021,2025):
        for sport in (1,11,12,13,14,16):
            if sport==1:
                p=ROOT/official[year]['path']
                assert sha256_file(p)==official[year]['sha256']
                payload=read(p);hashes[str(p)]=sha256_file(p)
            else:
                p=ROOT/'reports/generated/hitter-minor-statcast-capture/official-context'/f'schedule-{year}-{sport}.json.gz'
                meta=read(p.with_suffix(''))
                assert meta['season']==year and meta['sport_id']==sport
                assert meta['compressed_sha256']==sha256_file(p)
                raw=gzip.decompress(p.read_bytes())
                assert hashlib.sha256(raw).hexdigest()==meta['response_sha256']
                payload=json.loads(raw)
                hashes[str(p)]=sha256_file(p);hashes[str(p.with_suffix(''))]=sha256_file(p.with_suffix(''))
            results[year,sport]=schedule_context(payload,season=year,sport_id=sport)
    return results,hashes


def comparisons(expected,rows):
    totals=position_totals(rows)
    actual={(key[1],key[2]):value for key,value in totals.items()}
    zero=dict(fielding_outs=0,raw_starts=0,appearances=0)
    fields=tuple(zero)
    return [dict(league_id=p[0],position_code=p[1],
        annual={f:expected.get(p,zero)[f] for f in fields},
        log={f:actual.get(p,zero)[f] for f in fields}) for p in sorted(set(expected)|set(actual))]


def main():
    protections();check();assert not (DEST/'source-review.json').exists()
    for path,digest in read(OUT/'source-review.json')['hashes'].items():assert sha256_file(Path(path))==digest
    context,source_hashes=schedules()
    manifest=read(OUT/'manifest.json');complete=read(OUT/'capture-complete.json')
    inputs=[Path(__file__),AMEND,ROOT/'src/universal_baseball/defense_role_scope.py',
        OUT/'source-review.json',OUT/'manifest.json',OUT/'capture-complete.json',DH/'source-review.json']
    write('seal.json',dict(before_source_repair=True,no_fits=True,
        input_hashes={**source_hashes,**{str(p):sha256_file(p) for p in inputs}}))
    original=defaultdict(lambda:defaultdict(lambda:dict(fielding_outs=0,raw_starts=0,appearances=0)))
    for r in pl.read_parquet(SOURCE).filter(pl.col('season').is_between(2021,2024)).to_dicts():
        v=original[r['player_id'],r['season'],SPORTS[r['normalized_level']]][r['league_id'],int(r['position_code'])]
        v['fielding_outs']+=r['fielding_outs'];v['raw_starts']+=r['games_started'];v['appearances']+=r['games_played']
    corrections=defaultdict(list)
    for c in read(DH/'source-review.json')['corrections']:
        if c['season']<=2024:
            for r in c['game_evidence']:
                corrections[r['player_id'],r['season']].append(dict(r,
                    source_id=str(DH/'captures'/f"box-{r['game_id']}.json")))
    all_rows=[];scopes=[];seen=set();errors=[]
    for index,job in enumerate(manifest['requests']):
        p=OUT/'captures'/(job['capture_name']+'.json')
        assert sha256_file(p)==complete['hashes'][str(p)]
        meta=read(p.with_suffix('.capture.json'));assert meta['endpoint']==job['endpoint'] and meta['sha256']==sha256_file(p)
        batch,bad=parse_people_isolated(read(p),player_ids=job['player_ids'],season=job['origin'],
            sport_id=job['sport_id'],source_id=str(p),context=context[job['origin'],job['sport_id']])
        errors.extend(dict(player_id=pid,origin=job['origin'],sport_id=job['sport_id'],
                           source=str(p),reason=reason) for pid,reason in bad.items())
        for pid in job['player_ids']:
            key=(pid,job['origin'],job['sport_id']);assert key not in seen;seen.add(key)
            raw=batch.get(pid,[]);comparison=comparisons(original[key],raw)
            fixed=apply_dual_dh(raw,corrections[pid,job['origin']]) if raw and job['sport_id']==1 else raw
            cert=certify_measurements(comparison,fixed)
            teams=defaultdict(set)
            for r in fixed:teams[r['game_id'],r['position_code']].add(r['team_id'])
            scopes.append(dict(player_id=pid,origin=job['origin'],sport_id=job['sport_id'],source=str(p),
                position_game_rows=len(fixed),measurements=cert,comparisons=comparison,
                team_grain_resumption_records=[r for r in fixed if len(teams[r['game_id'],r['position_code']])>1]))
            all_rows.extend(fixed)
        if index%100==0:print(f'Repaired source batches {index+1}/745',flush=True)
    assert len(seen)==23412
    games=pl.DataFrame(all_rows,infer_schema_length=None).sort('player_id','season','sport_id','date','game_id','team_id','position_code')
    assert games.unique(['player_id','game_id','team_id','position_code']).height==games.height
    assert games['certified_dual_DH_addition'].sum()==51
    games.write_parquet(DEST/'normalized-role-games.parquet')
    periods=games.group_by('player_id','season','sport_id','league_id','period','position_code','position').agg(
        *[pl.col(f).sum() for f in (*FIELDS,'raw_starts','certified_dual_DH_addition')],
        pl.len().alias('team_position_game_rows'),pl.col('date').min().alias('first_original_date'),
        pl.col('date').max().alias('last_original_date')).sort('player_id','season','sport_id','league_id','period','position_code')
    periods.write_parquet(DEST/'normalized-role-periods.parquet')
    for field in FIELDS:assert games[field].sum()==periods[field].sum()
    per_pair=defaultdict(list)
    for r in periods.to_dicts():per_pair[r['player_id'],r['season']].append(r)
    certs={(s['player_id'],s['origin'],s['sport_id']):s['measurements'] for s in scopes}
    features=[]
    for case in manifest['input_cases']:
        pid,y=case['player_id'],case['origin'];declared=case['declared_sports'];records=per_pair[pid,y]
        row=dict(**case,current_role_periods=records,current_assignment_is_defensive_talent=False)
        for scope in ('all','MLB','minor'):
            sports=[s for s in declared if scope=='all' or (s==1)==(scope=='MLB')]
            for period in ('full_year','before_August','August_onward'):
                selected=[r for r in records if r['sport_id'] in sports and (period=='full_year' or r['period']==period)]
                for field in FIELDS:
                    flag='full_year' if period=='full_year' else 'periods'
                    usable=bool(sports) and all(certs[pid,y,s][field][flag] for s in sports)
                    name=f'{scope}_{period}_{field}'
                    row[name]=[sum(r[field] for r in selected if r['position_code']==p) for p in range(2,11)] if usable else None
                    row[name+'_known']=usable
        row['current_source_status']='unknown_current_scope' if not declared else (
            'certified_full_year_outs_and_starts' if row['all_full_year_fielding_outs_known'] and row['all_full_year_reviewed_starts_known']
            else 'partial_measurement_coverage')
        features.append(row)
    frame=pl.DataFrame(features,infer_schema_length=None)
    assert frame.height==16674 and frame['row_id'].n_unique()==16674
    frame.write_parquet(DEST/'current-role-source-features.parquet')
    # Large audit detail stays local; publish compact coverage and exception receipts.
    save(DEST/'scope-comparisons.json',dict(scopes=scopes,isolated_parser_errors=errors))
    mismatches=[s for s in scopes if not all(c['full_year'] for c in s['measurements'].values())]
    date_unknown=[s for s in scopes if any(c['full_year'] and not c['periods'] for c in s['measurements'].values())]
    coverage={f:dict(full_year=sum(s['measurements'][f]['full_year'] for s in scopes),
                    periods=sum(s['measurements'][f]['periods'] for s in scopes)) for f in FIELDS}
    save(DEST/'date-uncertainty-scopes.json',dict(scopes=date_unknown))
    outputs=[DEST/n for n in ('normalized-role-games.parquet','normalized-role-periods.parquet',
        'current-role-source-features.parquet','scope-comparisons.json','date-uncertainty-scopes.json')]
    write('source-review.json',dict(feature_rows=frame.height,source_scopes=len(scopes),
        normalized_position_team_game_rows=games.height,period_cells=periods.height,dated_DH_additions=51,
        scope_measurement_coverage=coverage,isolated_parser_errors=errors,residual_mismatches=mismatches,
        resumed_two_team_scopes=[s for s in scopes if s['team_grain_resumption_records']],
        date_sensitive_uncertain_scopes=len(date_unknown),date_status=games.group_by('date_status').len().to_dicts(),
        feature_status=frame.group_by('current_source_status').len().to_dicts(),
        feature_coverage={c:int(frame[c].sum()) for c in frame.columns if c.endswith('_known')},
        no_fits=True,no_accuracy_claim=True,no_deployment=True,player_walkthrough_status='pending',
        original_audit_preserved=True,input_hashes=read(DEST/'seal.json')['input_hashes'],
        output_hashes={str(p):sha256_file(p) for p in outputs}))
    protections();print(json.dumps(dict(coverage=coverage,unknown_dates=len(date_unknown),
        parser_errors=len(errors),residual_mismatches=len(mismatches))),flush=True)


if __name__=='__main__':main()
