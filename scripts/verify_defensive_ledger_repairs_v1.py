"""Independent file/denominator verification, not a new defensive model."""
from collections import Counter
import json
from pathlib import Path
import polars as pl
from universal_baseball.storage import sha256_file
from universal_baseball.defensive_event_repair import official_events, reconcile_box


def read(p):return json.loads(p.read_text(encoding='utf-8'))


def main():
    timeline=Path('model_artifacts/defensive-timeline-v1-2026-09-25')
    frozen=read(timeline/'validation-freeze.json')
    for name,digest in frozen['code_hashes'].items():assert sha256_file(Path(name))==digest
    assert sha256_file(timeline/'development-report.json')==frozen['development_report_sha256']
    assert sha256_file(timeline/'selection.json')==frozen['selection_sha256']
    dev=read(timeline/'development-report.json');val=read(timeline/'validation-report.json')
    assert len(dev['games'])==len(val['games'])==128
    assert not {g['game_pk'] for g in dev['games']}&{g['game_pk'] for g in val['games']}
    assert dev['game_status']=={'reconstructed':128}
    assert val['game_status']=={'reconstructed':127,'reconstruction_failed':1}
    for report in (dev,val):
        for name,obj in report['artifacts'].items():
            assert sha256_file(Path(name))==obj['sha256']
            assert pl.read_parquet(name).height==obj['rows']
        assert not any(report[n] for n in ['player_discrepancies','credit_discrepancies',
            'matchup_discrepancies','terminal_discrepancies','box_discrepancies'])
    pc=pl.read_parquet('reports/generated/defensive-timeline-v1/validation/player-checks.parquet')
    assert pc.filter(pl.col('official')!=pl.col('ledger')).is_empty()
    positive=pc.group_by('metric').agg(pl.len().alias('checks'),
        (pl.col('official')>0).sum().alias('nonzero_checks'),pl.col('official').sum().alias('event_total')).sort('metric')
    # Retain the failing game's event mass rather than hiding it behind 127/128.
    fail=[g for g in val['games'] if g['status']!='reconstructed'];assert len(fail)==1
    cap=[c for c in read(timeline/'captures.json')['records'] if c['game_pk']==fail[0]['game_pk']][0]
    assert sha256_file(Path(cap['path']))==cap['sha256']
    payload=read(Path(cap['path']));events,_=official_events(payload,cap['game_pk'],fail[0]['season'])
    assert all(c['status']=='matched' for c in reconcile_box(payload,events))
    gb=Path('model_artifacts/ground-ball-ledger-v2-2026-09-26');lock=read(gb/'freeze.json');report=read(gb/'report.json')
    assert report['freeze_sha256']==sha256_file(gb/'freeze.json')
    for n,h in lock['code_hashes'].items():assert sha256_file(Path(n))==h
    raw_schema=[];totals=[];taxonomy=[];all_keys=[]
    for year in [2016,2017,2018,2019,2021,2022,2023,2024]:
        raw=[]
        for n,h in lock['source_hashes'].items():
            if f'season={year}' not in n:continue
            assert sha256_file(Path(n))==h
            raw.append(pl.read_parquet(n,columns=['game_pk','at_bat_index','bb_type']))
        source=pl.concat(raw,how='diagonal_relaxed')
        keys=source.filter(pl.col('bb_type')=='ground_ball').select('game_pk','at_bat_index').unique()
        p=Path(f'reports/generated/ground-ball-ledger-v2/{year}.parquet')
        artifact=report['artifacts'][str(p)];assert sha256_file(p)==artifact['sha256']
        d=pl.read_parquet(p);actual=d.select('game_pk','at_bat_index')
        assert actual.height==actual.unique().height==keys.height==artifact['rows']
        assert keys.join(actual,on=['game_pk','at_bat_index'],how='anti').is_empty()
        assert d.select((pl.col('share_a')+pl.col('share_b')+pl.col('unassigned_share')==1).all()).item()
        assert not d['individual_range_certified'].any()
        assert d.filter(pl.col('has_source_conflict') & (pl.col('unassigned_share')!=1)).is_empty()
        for slot in ('a','b'):
            for pos in range(1,10):
                x=d.filter(pl.col('candidate_position_'+slot)==pos)
                assert x['candidate_fielder_'+slot].equals(x[f'fielder_{pos}'])
        totals.append({'season':year,'balls':d.height,'conflicts':d['has_source_conflict'].sum(),
            'unknown_candidate_identity':d['unknown_candidate_identity'].sum(),
            'unassigned_share':d['unassigned_share'].sum(),
            'unassigned_sensitivity_share':d['unassigned_sensitivity_share'].sum()})
        raw_schema.append(d.group_by('allocation_basis').len())
        # Bunt_grounder is a SEPARATE source category; scope must not imply those
        # archived records vanished or that the non-bunt range ledger covers them.
        taxonomy.extend(source.unique().group_by('bb_type').len().with_columns(pl.lit(year).alias('season')).to_dicts())
        all_keys.append(actual)
    keys=pl.concat(all_keys);assert keys.unique().height==keys.height==report['ground_ball_union_keys']
    q=pl.read_parquet('reports/generated/ground-ball-ledger-v2/source-checks.parquet')
    assert q.filter(pl.col('official_ground_ball')!=pl.col('archive_ground_ball_key')).is_empty()
    assert q.height==5742
    assert q.filter(pl.col('outcome_status')=='mismatch').is_empty()
    assert q.filter(pl.col('location_status')=='mismatch').height==1
    evidence={'verified':True,'timeline_validation_games':128,'timeline_reconstructed':127,
        'validation_positive_checks':positive.to_dicts(),'timeline_failed_game':fail[0],
        'failed_game_events_without_certified_battery':dict(Counter(e['family'] for e in events)),
        'battery_attributed_events':val['events'],'validation_all_events':val['events']+len(events),
        'ground_ball_totals':totals,'allocation':pl.concat(raw_schema).group_by('allocation_basis').agg(pl.col('len').sum()).sort('allocation_basis').to_dicts(),
        'source_trajectory_inventory_distinct_key_type':taxonomy,
        'scope':'All archived ground_ball keys, not all ground-contact types or all scheduled games',
        'new_fits':0,'production_changed':False,'protected_outcomes_used':False}
    path=gb/'verification.json';path.write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in evidence.items() if k not in ['ground_ball_totals','allocation','source_trajectory_inventory_distinct_key_type','validation_positive_checks']}))


if __name__=='__main__':main()
