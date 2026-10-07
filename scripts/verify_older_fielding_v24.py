"""Separate coverage arithmetic and distinct-person support replay; no learner."""
from collections import defaultdict
from pathlib import Path
import math

import polars as pl
from universal_baseball.storage import sha256_file
from verify_double_play_support_v22 import read, write
from run_hitter_finite_return_baseline import protections

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-older-quality-v24'
PUBLIC=ROOT/'reports/model-evidence/defense-older-quality-v24'


def main():
    protections()
    assert not (PUBLIC/'independent-review.json.gz').exists()
    for name in ['source-preflight','precision-preflight','capture-report','audit-preflight','audit-report']:
        for path,digest in read(PUBLIC/(name+'.json.gz'))['hashes'].items():
            assert sha256_file(Path(path))==digest,path
    official=defaultdict(int)
    for r in pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet').iter_rows(named=True):
        if r['is_mlb'] and r['position_code'].isdigit():
            official[r['season'],r['player_id'],int(r['position_code'])]+=r['fielding_outs']
    old={(r['season'],r['player_id'],r['position']):r
         for r in pl.read_parquet(OUT/'older-conversion-ledger.parquet').iter_rows(named=True)}
    valid={}
    for r in pl.read_parquet(OUT/'exposure-qualification.parquet').iter_rows(named=True):
        k=r['season'],r['player_id'],r['position']; raw=old[k]; expected=official.get(k)
        assert raw['fielding_outs']==r['fielding_outs'] and expected==r['official_outs']
        n=raw['fielding_outs']; o=expected
        good=o is not None and n>0 and o>0 and abs(n-o)<=5 and abs(n-o)<=.01*max(n,o)
        measured=good and raw['RngR'] is not None and raw['ErrR'] is not None
        assert r['older_exposure_valid']==good and r['older_conversion_valid']==measured
        valid[k]=measured
    native={(r['season'],r['player_id'],r['position']):r
            for r in pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').iter_rows(named=True)}
    origins={(r['origin_year'],r['player_id'],r['position']):r
             for r in pl.read_parquet(ROOT/'reports/generated/defense-minor-counts-v18/origins.parquet').iter_rows(named=True)}
    rows=pl.read_parquet(OUT/'potential-coverage.parquet').to_dicts()
    for r in rows:
        origin,pid,pos=r['origin_year'],r['player_id'],r['position']
        years=list(range(origin+1,min(origin+r['window'],2025)+1))
        ns=[native[y,pid,pos] for y in years if (y,pid,pos) in native and native[y,pid,pos]['range_valid']]
        os=[old[y,pid,pos] for y in years if y<2016 and valid.get((y,pid,pos),False)]
        native_years={n['season'] for n in ns}; old_years={o['season'] for o in os}
        assert native_years.isdisjoint(old_years)
        nouts=sum(n['native_outs'] for n in ns); oouts=sum(o['fielding_outs'] for o in os)
        missing=sum(official.get((y,pid,pos),0) for y in years if y not in native_years)
        remaining=sum(official.get((y,pid,pos),0) for y in years if y not in native_years|old_years)
        native_good=origin+r['window']<=2025 and nouts>=1500 and len(ns)>=2 and missing==0
        possible=origin+r['window']<=2025 and nouts+oouts>=1500 and len(ns)+len(os)>=2 and remaining==0
        checks=dict(native_observed_outs=nouts,native_measured_seasons=len(ns),native_missing_official_outs=missing,
            native_quality_available=native_good,older_pre2016_observed_outs=oouts,older_pre2016_measured_seasons=len(os),
            potential_observed_outs=nouts+oouts,potential_measured_seasons=len(ns)+len(os),remaining_unmeasured_official_outs=remaining,
            future_same_position_official_outs=sum(official.get((y,pid,pos),0) for y in years),
            potential_coverage_available=possible,potential_new_coverage=possible and not native_good,
            future_other_position_outs=sum(official.get((y,pid,p),0) for y in years for p in range(2,10) if p!=pos),
            window_mature=origin+r['window']<=2025)
        assert all(r[k]==v for k,v in checks.items()),(origin,pid,pos,r['window'])
    cells=read(PUBLIC/'support.json.gz')['cells']
    cache={}
    for cell in cells:
        key=cell['cutoff'],cell['window'],cell['held_fold']
        if key not in cache:
            selected=[r for r in rows if r['window']==cell['window'] and r['window_end']<=cell['cutoff']
                and r['player_id']%5!=cell['held_fold']
                and not origins[r['origin_year'],r['player_id'],r['position']]['prior_current_MLB_fielding']]
            groups=defaultdict(lambda:[set(),set(),set()])
            for r in selected:
                o=origins[r['origin_year'],r['player_id'],r['position']]
                keys=[('level',o['level']),('position',o['position']),('age_band',o['age_band']),
                    ('joint',o['level'],o['position'],o['age_band'],o['sample_band'],o['early_rookie_qualification'])]
                for k in keys:
                    groups[k][0].add(r['player_id'])
                    if r['native_quality_available']:groups[k][1].add(r['player_id'])
                    if r['potential_coverage_available']:groups[k][2].add(r['player_id'])
            cache[key]=(selected,groups)
        selected,groups=cache[key]
        if cell['kind']=='overall':
            cur=[r for r in selected if r['native_quality_available']]
            pot=[r for r in selected if r['potential_coverage_available']]
            cids={r['player_id'] for r in cur};pids={r['player_id'] for r in pot}
            assert cell['eligible_people']==len({r['player_id'] for r in selected})
            assert cell['native_people']==len(cids) and cell['potential_people']==len(pids)
            assert cell['new_people']==len(pids-cids)
            assert cell['native_origin_positions']==len(cur) and cell['potential_origin_positions']==len(pot)
            assert cell['latest_window_end']==max(r['window_end'] for r in selected)<=cell['cutoff']
            assert cell['source_counts_complete_potential_people']==len({r['player_id'] for r in pot
                if origins[r['origin_year'],r['player_id'],r['position']]['range_counts_complete']})
        else:
            k=(cell['kind'],cell[cell['kind']]) if cell['kind']!='joint' else ('joint',cell['level'],cell['position'],
                cell['age_band'],cell['sample_band'],cell['early_rookie_qualification'])
            assert [cell[f] for f in ['eligible_people','native_people','potential_people']]==[len(s) for s in groups[k]]
    # Full-population position centers, not the selected 500-inning overlap subset.
    # This inventories the coordinate systems; it changes no measurements/labels.
    centers=[]
    for year in range(2016,2022):
        for pos in range(3,10):
            os=[r for k,r in old.items() if k[0]==year and k[2]==pos and valid[k]]
            ns=[r for k,r in native.items() if k[0]==year and k[2]==pos and r['range_valid']]
            centers.append(dict(season=year,position=pos,older_people=len(os),native_people=len(ns),
                older_outs=sum(r['fielding_outs'] for r in os),native_outs=sum(r['native_outs'] for r in ns),
                older_runs=sum(r['older_conversion_runs'] for r in os),native_runs=sum(r['range_runs'] for r in ns),
                older_exposure_weighted_center=1500*sum(r['older_conversion_runs'] for r in os)/sum(r['fielding_outs'] for r in os),
                native_exposure_weighted_center=1500*sum(r['range_runs'] for r in ns)/sum(r['native_outs'] for r in ns)))
    write(PUBLIC/'independent-review.json.gz',dict(exposure_rows_replayed=len(old),coverage_windows_replayed=len(rows),
        support_cells_replayed=len(cells),source_hashes_checked=True,model_fits=0,quality_labels_created=0,
        full_population_position_centers=centers,player_walkthrough_status='pending',
        hashes={str(p):sha256_file(p) for p in [Path(__file__),PUBLIC/'audit-report.json.gz',PUBLIC/'support.json.gz',
            OUT/'potential-coverage.parquet',OUT/'exposure-qualification.parquet']}))
    protections()
    print(f'Replayed {len(old)} exposure rows, {len(rows)} windows and {len(cells)} support cells. No skill labels or forecasts created.',flush=True)


if __name__=='__main__':main()
