"""Independent capture replay, official exposure and possible future support; no fit."""
from collections import defaultdict
from pathlib import Path
import gzip
import hashlib
import json
import math
import re

import numpy as np
import polars as pl
from universal_baseball.older_fielding_coverage import coverage, older_valid, exposure_valid
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import read, write
from run_hitter_finite_return_baseline import protections

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/defense-older-quality-v24'
PUBLIC = ROOT/'reports/model-evidence/defense-older-quality-v24'
OFFICIAL = ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet'
NATIVE = ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
MINOR = ROOT/'reports/generated/defense-minor-counts-v18'
POS = {'1B':3, '2B':4, '3B':5, 'SS':6, 'LF':7, 'CF':8, 'RF':9}
KEY = ['season','player_id','position']


def fielding_sources():
    official = defaultdict(int)
    for r in pl.read_parquet(OFFICIAL, columns=['season','player_id','position_code','fielding_outs','is_mlb']).iter_rows(named=True):
        if r['is_mlb'] and r['position_code'].isdigit():
            official[r['season'],r['player_id'],int(r['position_code'])] += r['fielding_outs']
    old = {(r['season'],r['player_id'],r['position']):r
           for r in pl.read_parquet(OUT/'older-conversion-ledger.parquet').iter_rows(named=True)}
    native = {(r['season'],r['player_id'],r['position']):r
              for r in pl.read_parquet(NATIVE).iter_rows(named=True)}
    for k, r in old.items():
        r['official_outs'] = official.get(k)
        r['older_exposure_valid'] = exposure_valid(r['fielding_outs'], r['official_outs'])
        r['older_conversion_valid'] = older_valid(r, r['official_outs'])
    return official, old, native


def capture_replay(old):
    report = read(PUBLIC/'capture-report.json.gz')
    for p, h in report['hashes'].items(): assert sha256_file(Path(p)) == h, p
    years = []
    for rec in report['years']:
        year = rec['season']; path = OUT/f'fielding-{year}.html.gz'
        receipt_path = OUT/f'fielding-{year}-receipt.json.gz'; receipt = read(receipt_path)
        assert sha256_file(path) == rec['compressed_sha256'] == receipt['compressed_sha256']
        assert sha256_file(receipt_path) == rec['receipt_sha256']
        body = gzip.decompress(path.read_bytes())
        assert hashlib.sha256(body).hexdigest() == receipt['raw_sha256']
        match = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', body.decode('utf8'), re.S)
        assert match
        page = json.loads(match[1])['props']['pageProps']
        tables = [q for q in page['dehydratedState']['queries'] if q['queryKey'][0] == 'leaders/major-league/data']
        assert len(tables) == 1
        query = tables[0]['queryKey'][1]; payload = tables[0]['state']['data']; rows = payload['data']
        assert query['season'] == query['season1'] == year and query['stats'] == 'fld' and str(query['qual']) == '0'
        assert int(page['qsContext']['season']) == int(page['qsContext']['season1']) == year
        assert int(receipt['requested']['season']) == int(receipt['requested']['season1']) == year
        assert len(rows) == payload['totalCount'] == rec['raw_rows']
        seen = set(); metrics = defaultdict(int)
        for raw in rows:
            assert raw['Season'] == raw['SeasonMin'] == raw['SeasonMax'] == year
            pos = POS.get(raw['Position'])
            if pos is None: continue
            k = year, int(raw['xMLBAMID']), pos
            assert k not in seen; seen.add(k); r = old[k]
            whole, _, remainder = str(raw['Inn']).partition('.')
            assert remainder in ('','0','1','2')
            outs = 3*int(whole) + int(remainder or 0)
            assert outs == r['fielding_outs']
            assert int(raw['playerid']) == r['fangraphs_id'] and raw['PlayerName'] == r['player_name']
            for field in ['RngR','ErrR','ARM','DPR','UZR','DRS','rPM','BIZ','Plays','OOZ']:
                assert raw.get(field) == r[field], (k,field)
                if r[field] is not None: metrics['known_'+field] += 1
            for field in ['BIZ','Plays','OOZ']:
                assert r[field] is None or (r[field] >= 0 and int(r[field]) == r[field])
            assert r['Plays'] is None or r['BIZ'] is None or r['Plays'] <= r['BIZ']
            converted = raw['RngR'] + raw['ErrR'] if raw.get('RngR') is not None and raw.get('ErrR') is not None and outs > 0 else None
            assert converted == r['older_conversion_runs']
            gap = 3*raw['TInn']-outs
            assert abs(gap) <= .02 and gap == r['decimal_innings_gap_outs']
            assert (abs(gap) < .001) == r['original_decimal_innings_check']
            assert r['UZR'] is None or abs(sum(raw.get(f) or 0 for f in ['RngR','ErrR','ARM','DPR'])-r['UZR']) <= .001
            metrics['positive_exposure'] += outs > 0
            metrics['certified_conversion'] += r['older_conversion_valid']
            metrics['official_exact'] += r['official_outs'] == outs
            metrics['missing_official'] += r['official_outs'] is None
            metrics['positive_missing_official'] += outs > 0 and r['official_outs'] is None
            metrics['exposure_failed'] += outs > 0 and not r['older_exposure_valid']
        assert seen == {k for k in old if k[0] == year}
        years.append(dict(season=year, raw_rows=len(rows), component_rows=len(seen), **dict(metrics)))
    return years


def overlap(old, native):
    rows = []
    for k, o in old.items():
        n = native.get(k)
        if 2016 <= k[0] <= 2021 and o['older_conversion_valid'] and n is not None and n['range_valid']:
            rows.append(dict(season=k[0],player_id=k[1],position=k[2],old_outs=o['fielding_outs'],
                native_outs=n['native_outs'],old_rate=1500*o['older_conversion_runs']/o['fielding_outs'],
                native_rate=1500*n['range_runs']/n['native_outs']))
    groups = []
    for pos in [None,*range(3,10)]:
        eligible = [r for r in rows if (pos is None or r['position'] == pos) and min(r['old_outs'],r['native_outs']) >= 1500]
        a = np.array([r['old_rate'] for r in eligible]); b = np.array([r['native_rate'] for r in eligible])
        groups.append(dict(position=pos, player_position_seasons=len(eligible),people=len({r['player_id'] for r in eligible}),
            older_mean=float(a.mean()),native_mean=float(b.mean()),correlation=float(np.corrcoef(a,b)[0,1]),
            older_minus_native_mean=float((a-b).mean()),median_absolute_difference=float(np.median(abs(a-b))),
            rms_difference=float(np.sqrt(np.mean((a-b)**2))),
            opposite_signs=int(((a*b)<0).sum()),claim='Contemporaneous measurement agreement, not accuracy or a fitted bridge'))
    return dict(all_certified_overlap_rows=len(rows),people=len({r['player_id'] for r in rows}),
        substantial_exposure_groups=groups,minimum_both_outs=1500,units='runs per 500 defensive innings',model_fits=0)


def coverage_rows(official, old, native):
    label = pl.read_parquet(MINOR/'labels.parquet').filter(pl.col('component') == 'range')
    records = []
    for r in label.iter_rows(named=True):
        y,pid,pos = r['origin_year'],r['player_id'],r['position']
        years = range(y+1,min(y+r['window'],2025)+1)
        o = {year: official.get((year,pid,pos),0) for year in years}
        older = {year: old[year,pid,pos] for year in years if (year,pid,pos) in old}
        n = {year: native[year,pid,pos] for year in years if (year,pid,pos) in native}
        v = coverage(y,r['window'],o,older,n)
        assert v['native_observed_outs'] == r['future_opportunities']
        assert v['native_measured_seasons'] == r['future_measured_seasons']
        assert v['native_missing_official_outs'] == r['unmeasured_official_outs']
        assert v['future_same_position_official_outs'] == r['future_official_position_outs']
        assert v['native_quality_available'] == (r['quality_status']=='measured')
        other = sum(official.get((year,pid,p),0) for year in years for p in range(2,10) if p != pos)
        assert other == r['future_other_position_outs']
        records.append(dict(origin_year=y,player_id=pid,position=pos,window=r['window'],window_end=r['window_end'],
            current_quality_status=r['quality_status'],future_other_position_outs=other,**v))
    return pl.DataFrame(records,infer_schema_length=None)


def support(frame):
    profiles = ['level','position','age_band','sample_band','early_rookie_qualification']
    rows = []
    for cutoff in [2021,2022]:
        for window in [3,5]:
            all_training = frame.filter((pl.col('window')==window)&(pl.col('window_end')<=cutoff)&~pl.col('prior_current_MLB_fielding'))
            for fold in range(5):
                tr = all_training.filter(pl.col('player_id')%5 != fold)
                current = tr.filter(pl.col('native_quality_available'))
                potential = tr.filter(pl.col('potential_coverage_available'))
                totals = dict(cutoff=cutoff,window=window,held_fold=fold,
                    eligible_people=tr['player_id'].n_unique(),native_people=current['player_id'].n_unique(),
                    potential_people=potential['player_id'].n_unique(),new_people=len(set(potential['player_id'])-set(current['player_id'])),
                    native_origin_positions=len(current),potential_origin_positions=len(potential),
                    latest_window_end=int(tr['window_end'].max()),
                    source_counts_complete_potential_people=potential.filter(pl.col('range_counts_complete'))['player_id'].n_unique())
                rows.append(dict(kind='overall',**totals))
                for fields in [['level'],['position'],['age_band'],profiles]:
                    broad = tr.group_by(fields).agg(pl.col('player_id').n_unique().alias('eligible_people'))
                    cur = current.group_by(fields).agg(pl.col('player_id').n_unique().alias('native_people'))
                    pot = potential.group_by(fields).agg(pl.col('player_id').n_unique().alias('potential_people'))
                    groups = broad.join(cur,on=fields,how='left').join(pot,on=fields,how='left').fill_null(0).sort(fields)
                    for r in groups.to_dicts():
                        rows.append(dict(kind='joint' if len(fields)>1 else fields[0],cutoff=cutoff,window=window,held_fold=fold,**r))
    return rows


def main():
    protections()
    assert not (PUBLIC/'audit-preflight.json.gz').exists(), 'Preserve completed or partial audit; do not restart'
    paths = [Path(__file__),ROOT/'src/universal_baseball/older_fielding_coverage.py',
        ROOT/'tests/test_older_fielding_coverage.py',ROOT/'docs/defense-older-quality-v24-contract.md',
        ROOT/'docs/defense-older-quality-v24-precision-amendment.md',PUBLIC/'capture-report.json.gz',
        OUT/'older-conversion-ledger.parquet',OFFICIAL,NATIVE,MINOR/'origins.parquet',MINOR/'labels.parquet',
        *sorted(OUT.glob('fielding-*-receipt.json.gz'))]
    write(PUBLIC/'audit-preflight.json.gz',dict(before_audit=True,model_fits=0,quality_labels_created=0,
        potential_support_not_validated_transfer=True,hashes={str(p):sha256_file(p) for p in paths}))
    official,old,native = fielding_sources()
    years = capture_replay(old)
    for k,r in native.items():
        assert r['official_outs'] == official.get(k,0), k
        valid = exposure_valid(r['native_outs'],r['official_outs']) and r['range_runs'] is not None
        assert valid == r['range_valid'], k
    qualified = pl.DataFrame([dict(season=k[0],player_id=k[1],position=k[2],fielding_outs=r['fielding_outs'],
        official_outs=r['official_outs'],older_exposure_valid=r['older_exposure_valid'],older_conversion_valid=r['older_conversion_valid'])
        for k,r in old.items()]).sort(KEY)
    qualified.write_parquet(OUT/'exposure-qualification.parquet')
    cov = coverage_rows(official,old,native); cov.write_parquet(OUT/'potential-coverage.parquet')
    origins = pl.read_parquet(MINOR/'origins.parquet')
    frame = cov.join(origins,on=['origin_year','player_id','position'],validate='m:1')
    totals=[]
    for window in [3,5]:
        q=frame.filter((pl.col('window')==window)&~pl.col('prior_current_MLB_fielding'))
        additional = (set(q.filter(pl.col('potential_coverage_available'))['player_id'])
                      - set(q.filter(pl.col('native_quality_available'))['player_id']))
        totals.append(dict(window=window,origin_positions=len(q),people=q['player_id'].n_unique(),
            current_measured_people=q.filter(pl.col('native_quality_available'))['player_id'].n_unique(),
            potential_measured_people=q.filter(pl.col('potential_coverage_available'))['player_id'].n_unique(),
            additional_origin_positions=q.filter(pl.col('potential_new_coverage')).height,
            additional_people=len(additional)))
    supported = support(frame); write(PUBLIC/'support.json.gz',dict(cells=supported,labels_created=0,
        person_fold='player_id modulo 5',potential_is_coverage_only=True))
    write(PUBLIC/'audit-report.json.gz',dict(source_years=years,older_component_rows=len(old),
        older_certified_conversion=sum(r['older_conversion_valid'] for r in old.values()),
        raw_source_bytes=sum(p.stat().st_size for p in OUT.glob('fielding-*.html.gz')),
        exact_source_replay=True,native_labels_replayed=len(cov),coverage_totals=totals,
        overlap=overlap(old,native),support_overall=[r for r in supported if r['kind']=='overall'],
        independent_coverage_replay_pending=True,player_walkthrough_status='pending',model_fits=0,
        quality_labels_created=0,forecasts_unchanged=True,
        hashes={str(p):sha256_file(p) for p in [PUBLIC/'audit-preflight.json.gz',PUBLIC/'support.json.gz',
            OUT/'exposure-qualification.parquet',OUT/'potential-coverage.parquet']}))
    print(json.dumps(dict(source_rows=len(old),coverage_windows=len(cov),coverage_totals=totals,
        support_overall=[r for r in supported if r['kind']=='overall']),indent=2),flush=True)
    protections()


if __name__ == '__main__': main()
