"""Outcome-complete archived GB accounting and same-feed source comparisons."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import polars as pl
from universal_baseball.storage import sha256_file
from universal_baseball.ground_ball_ledger import reconcile_ground_balls, add_benchmark, KEY
from universal_baseball.current_talent_contact_value_source import STRUCTURED_TERMINAL_GROUP

ROOT=Path('data/working/pbp-opportunity-foundation-v1')
OUT=Path('model_artifacts/ground-ball-ledger-v2-2026-09-26')
DETAIL=Path('reports/generated/ground-ball-ledger-v2')
YEARS=[2016,2017,2018,2019,2021,2022,2023,2024]
SAMPLES=[Path('model_artifacts')/name for name in
    ['defensive-event-source-repair-v1-2026-09-25','defensive-timeline-v1-2026-09-25']]


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def code_hashes():
    return {str(p):sha256_file(p) for p in [Path('docs/ground-ball-ledger-v2-contract.md'),
        Path(__file__).resolve().relative_to(Path.cwd()),Path('src/universal_baseball/ground_ball_ledger.py'),
        Path('src/universal_baseball/pbp_opportunity_events.py'),
        Path('src/universal_baseball/current_talent_contact_value_source.py'),Path('tests/test_ground_ball_ledger.py')]}


def freeze():
    if (OUT/'freeze.json').exists():raise ValueError('Already frozen')
    paths=sorted(ROOT.glob('season=*/level=*/terminal/*.parquet'))
    assert len(paths)==244
    assert all(int(str(p).split('season=')[1][:4]) in YEARS for p in paths)
    save(OUT/'freeze.json',{'time':datetime.now(timezone.utc).isoformat(),'code_hashes':code_hashes(),
        'source_hashes':{str(p):sha256_file(p) for p in paths},
        'sample_manifest_hashes':{str(p/name):sha256_file(p/name) for p in SAMPLES for name in ['selection.json','captures.json']},
        'new_fits':0,'protected_outcomes_used':False})


def build():
    lock=json.loads((OUT/'freeze.json').read_text());assert lock['code_hashes']==code_hashes()
    for p,h in lock['sample_manifest_hashes'].items():assert sha256_file(Path(p))==h
    artifacts={};summaries=[];sample_tables=[];all_source_rows=0
    selected={g['game_pk']:g for s in SAMPLES for g in json.loads((s/'selection.json').read_text())['games']}
    assert len(selected)==256
    DETAIL.mkdir(parents=True,exist_ok=True)
    for year in YEARS:
        frames=[]
        for p,h in lock['source_hashes'].items():
            if f'season={year}' not in p:continue
            assert sha256_file(Path(p))==h
            frames.append(pl.read_parquet(p))
        all_source_rows+=sum(f.height for f in frames)
        ledger=add_benchmark(reconcile_ground_balls(frames))
        assert ledger.select(KEY).unique().height==ledger.height
        assert ledger.select((pl.col('share_a')+pl.col('share_b')+pl.col('unassigned_share')==1).all()).item()
        assert not ledger['individual_range_certified'].any()
        path=DETAIL/f'{year}.parquet';ledger.write_parquet(path)
        artifacts[str(path)]={'rows':ledger.height,'sha256':sha256_file(path)}
        for fields in [['season','level','terminal_outcome_group'],['season','allocation_basis']]:
            summaries.append({'grouping':fields,'rows':ledger.group_by(fields).agg(
                pl.len().alias('balls'),pl.col('legacy_456_selected').sum().alias('legacy_456_selected'),
                pl.col('has_source_conflict').sum().alias('source_conflicts'),
                pl.col('any_bunt').sum().alias('bunts'),pl.col('unassigned_share').sum().alias('unassigned_mass'),
                pl.col('unknown_candidate_identity').sum().alias('unknown_candidate_identity'),
                pl.col('hit_location').is_in([7,8,9]).sum().alias('outfield_first_touch'),
            ).sort(fields).to_dicts()})
        sample_tables.append(ledger.filter(pl.col('game_pk').is_in(list(selected))))
        print(f'{year}: {ledger.height:,} balls retained',flush=True)
    sample=pl.concat(sample_tables,how='diagonal_relaxed')
    archive={(r['game_pk'],r['at_bat_index']):r for r in sample.to_dicts()}
    comparisons=[];official_keys=set();capture_issues=[];game_accounting=[]
    for s in SAMPLES:
        caps=json.loads((s/'captures.json').read_text())['records']
        for cap in caps:
            if 'error' in cap:
                capture_issues.append(cap);continue
            path=Path(cap['path']);assert sha256_file(path)==cap['sha256']
            payload=json.loads(path.read_text(encoding='utf-8'));game=cap['game_pk'];meta=selected[game]
            assert payload['gameData']['game']['pk']==game
            assert int(payload['gameData']['datetime']['officialDate'][:4])==meta['season']<2026
            assert payload['gameData']['game']['type']=='R'
            n=0
            for play in payload['liveData']['plays']['allPlays']:
                balls=[e for e in play.get('playEvents',[]) if e.get('details',{}).get('isInPlay')]
                key=(game,play['about']['atBatIndex'])
                official_gb=any(e.get('hitData',{}).get('trajectory')=='ground_ball' for e in balls)
                if not official_gb and key not in archive:continue
                if official_gb:official_keys.add(key);n+=1
                row=archive.get(key);hit=balls[0].get('hitData',{}) if len(balls)==1 else {}
                event=play.get('result',{}).get('eventType');group=STRUCTURED_TERMINAL_GROUP.get(event)
                aout=row.get('terminal_outcome_group') if row else None
                loc=hit.get('location');loc=int(loc) if str(loc).isdigit() else None
                comparisons.append({'game_pk':game,'at_bat_index':key[1],'season':meta['season'],'level':meta['level'],
                    'official_ground_ball':official_gb,'archive_ground_ball_key':row is not None,
                    'official_inplay_events':len(balls),'official_event':event,'official_outcome':group,
                    'archive_outcome':aout,'archive_conflict':row['has_source_conflict'] if row else None,
                    'archive_bunt':row['any_bunt'] if row else None,'official_location':loc,
                    'archive_location':row.get('hit_location') if row else None,
                    'outcome_status':'not_comparable' if row is None or len(balls)!=1 or group is None or aout is None
                        else 'match' if group==aout else 'mismatch',
                    'location_status':'not_comparable' if row is None or len(balls)!=1 or loc is None or row.get('hit_location') is None
                        else 'match' if row['hit_location']==loc else 'mismatch'})
            game_accounting.append({**meta,'official_GB':n,'archived_GB_keys':sum(k[0]==game for k in archive)})
    unmatched=set(archive)-{(r['game_pk'],r['at_bat_index']) for r in comparisons}
    for key in sorted(unmatched):
        comparisons.append({'game_pk':key[0],'at_bat_index':key[1],'official_ground_ball':False,
            'archive_ground_ball_key':True,'outcome_status':'PA_absent_official','location_status':'PA_absent_official'})
    compare=pl.DataFrame(comparisons,infer_schema_length=None)
    path=DETAIL/'source-checks.parquet';compare.write_parquet(path)
    artifacts[str(path)]={'rows':compare.height,'sha256':sha256_file(path)}
    counts={c:dict(Counter(r[c] for r in comparisons)) for c in ['outcome_status','location_status']}
    report={'freeze_sha256':sha256_file(OUT/'freeze.json'),'source_rows':all_source_rows,
        'ground_ball_union_keys':sum(v['rows'] for p,v in artifacts.items() if not p.endswith('source-checks.parquet')),
        'summaries':summaries,'artifacts':artifacts,'source_sample':{'games':game_accounting,'capture_issues':capture_issues,
            'official_GB':len(official_keys),'archive_GB_keys':len(archive),
            'official_GB_not_in_archive_GB':[list(k) for k in sorted(official_keys-set(archive))],
            'archive_GB_not_official_GB':[list(k) for k in sorted(set(archive)-official_keys)],
            'checks':counts,'disagreements':[r for r in comparisons if r['outcome_status']=='mismatch' or r['location_status']=='mismatch'],
            'by_level_year':compare.group_by('season','level','outcome_status','location_status').len().sort('season','level').to_dicts(),
            'outcome_confusion':compare.group_by('official_event','official_outcome','archive_outcome','outcome_status').len().sort('official_event').to_dicts()},
        'accounting_conservation':True,'individual_range_certified':False,'new_fits':0,
        'production_changed':False,'protected_outcomes_used':False}
    save(OUT/'report.json',report)
    print(json.dumps({'balls':report['ground_ball_union_keys'],'source_sample':counts,
        'official_GB_missing':len(official_keys-set(archive)),'archive_GB_extra':len(set(archive)-official_keys)}))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['freeze','build']);args=ap.parse_args()
    {'freeze':freeze,'build':build}[args.mode]()
