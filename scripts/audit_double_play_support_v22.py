"""Raw native credit and provisional future-quality coverage; no model fitting."""
from collections import Counter,defaultdict
from pathlib import Path
import gzip
import json
import math

import polars as pl

from source_defensive_positions_v2 import embedded
from run_hitter_finite_return_baseline import protections
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-double-play-source-v22'


def write(name,data):
    p=PUBLIC/name;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(p,'wt',encoding='utf8') as f:json.dump(data,f,allow_nan=False,separators=(',',':'))


def main():
    protections()
    previous=ROOT/'reports/model-evidence/defense-minor-correction-v21/final-review.json.gz'
    with gzip.open(previous,'rt',encoding='utf8') as f:assert json.load(f)['player_walkthrough_status']=='complete'
    nativepath=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    mlbpath=ROOT/'reports/generated/defense-native-range-v3/origins.parquet'
    minorpath=ROOT/'reports/generated/defense-minor-counts-v18/origins.parquet'
    offpath=ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet'
    paths=[Path(__file__),ROOT/'docs/defense-double-play-source-v22-contract.md',previous,nativepath,mlbpath,minorpath,offpath]
    rawpaths=[ROOT/f'reports/generated/defensive-talent-position-v2/position-{y}.response' for y in range(2016,2026)]
    paths.extend(rawpaths)
    write('preflight.json.gz',dict(before_any_new_source_processing=True,model_fits=0,forecast_unchanged=True,no_2026_outcomes=True,
        hashes={str(p):sha256_file(p) for p in paths}))
    native=pl.read_parquet(nativepath).to_dicts();by={(r['season'],r['player_id'],r['position']):r for r in native}
    years=[];opportunity_fields=[]
    components=('range_runs','arm_runs','dp_runs','fielding_runs_prevented_on_rec1b','framing_runs','throwing_runs','blocking_runs')
    for year,path in zip(range(2016,2026),rawpaths,strict=True):
        text=path.read_text(encoding='utf8');params=embedded(text,'serverParams')
        assert int(params['seasonStart'])==int(params['seasonEnd'])==year
        rows=embedded(text,'data');assert len(rows)==len({(r['id'],r['pos_id']) for r in rows})
        for r in rows:
            assert math.isclose(sum(r[c] or 0 for c in components),r['total_runs'],abs_tol=1e-9)
            if 2<=r['pos_id']<=9:
                saved=by[year,r['id'],r['pos_id']];assert saved['dp_runs']==r['dp_runs'] and saved['native_outs']==int(r['outs_total'])
        infield=[r for r in native if r['season']==year and r['position'] in (3,4,5,6)]
        years.append(dict(season=year,infield_rows=len(infield),known_credit=sum(r['dp_runs'] is not None for r in infield),
            qualified_credit=sum(r['dp_runs'] is not None and r['exposure_valid'] for r in infield),
            positive=sum(r['dp_runs'] is not None and r['dp_runs']>0 for r in infield),
            negative=sum(r['dp_runs'] is not None and r['dp_runs']<0 for r in infield),
            native_credit_total=sum(r['dp_runs'] or 0 for r in infield)))
        opportunity_fields.append(dict(season=year,fields=sorted({k for r in rows for k in r if any(s in k.lower() for s in ('opportun','chance','pivot','initial','double','dp_'))})))
    official=pl.read_parquet(offpath).filter(pl.col('is_mlb') & pl.col('season').is_between(2016,2025)).to_dicts()
    off=defaultdict(int)
    for r in official:
        if str(r['position_code']).isdigit():off[r['season'],r['player_id'],int(r['position_code'])]+=r['fielding_outs']
    def target(r):
        year,pid,pos=r['origin_year'],r['player_id'],r['position'];annual=[];outs=0;runs=0.;missing=0;measured_years=0;official_outs=0
        for y in range(year+1,year+4):
            n=by.get((y,pid,pos));o=off.get((y,pid,pos),0);valid=n is not None and n['exposure_valid'] and n['dp_runs'] is not None
            # Years outside the source are unknown, not certified absences.
            unavailable=y<2016 or y>2025
            if valid:outs+=n['native_outs'];runs+=n['dp_runs'];measured_years+=int(n['native_outs']>0)
            gap=o if o>0 and not valid else 0;missing+=gap;official_outs+=o
            annual.append(dict(season=y,native=n,official_outs=o,measurement_valid=valid,unknown_source_year=unavailable))
        mature=year+3<=2025;source_complete=all(not a['unknown_source_year'] for a in annual)
        quality=1500*runs/outs if mature and source_complete and outs>=1500 and measured_years>=2 and missing==0 else None
        status='measured' if quality is not None else 'immature_window' if not mature else 'outside_native_history' if not source_complete else 'positive_exposure_missing_DP_measurement' if missing else 'no_same_position_MLB_exposure' if not official_outs else 'insufficient_measured_sample'
        return dict(**r,window_end=year+3,quality_rate=quality,quality_status=status,future_outs=outs,future_runs=runs,
                    missing_official_outs=missing,annual=annual)
    mlb=[dict(r,population='MLB_history',level='MLB') for r in pl.read_parquet(mlbpath).to_dicts() if r['origin_year']<=2022 and r['position'] in (3,4,5,6)]
    minor=[dict(r,population='minor_prospect') for r in pl.read_parquet(minorpath).to_dicts() if r['origin_year']<=2022 and r['position'] in (3,4,5,6) and not r['prior_current_MLB_fielding']]
    labels=[target(r) for r in mlb+minor];groups=[];folds=[]
    for population in ('MLB_history','minor_prospect'):
        for year in (2021,2022):
            rs=[r for r in labels if r['population']==population and r['origin_year']==year]
            for level,pos in sorted({(r['level'],r['position']) for r in rs}):
                these=[r for r in rs if r['level']==level and r['position']==pos]
                groups.append(dict(population=population,origin=year,level=level,position=pos,eligible=len(these),
                    measured_people=len({r['player_id'] for r in these if r['quality_rate'] is not None}),status_counts=dict(Counter(r['quality_status'] for r in these))))
            for fold in range(5):
                tr=[r for r in labels if r['population']==population and r['window_end']<=year and r['quality_rate'] is not None and r['player_id']%5!=fold]
                te=[r for r in rs if r['player_id']%5==fold]
                assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
                folds.append(dict(population=population,origin=year,held_fold=fold,training_people=len({r['player_id'] for r in tr}),
                    training_origins=sorted({r['origin_year'] for r in tr}),test_people=len({r['player_id'] for r in te}),
                    measured_test_people=len({r['player_id'] for r in te if r['quality_rate'] is not None}),
                    position_level_training_people=[dict(position=p,level=l,people=len({r['player_id'] for r in tr if r['position']==p and r['level']==l})) for p,l in sorted({(r['position'],r['level']) for r in tr})]))
    write('labels.json.gz',labels)
    write('source-support.json.gz',dict(years=years,opportunity_fields=opportunity_fields,source_rows_replayed=len(native),
        groups=groups,folds=folds,MLB_origins=len(mlb),minor_origins=len(minor),model_fits=0,accuracy_claim=False,
        target_units='Adjusted DP runs per 500 innings; not per eligible DP opportunity',player_walkthrough_status='pending',
        hashes={str(p):sha256_file(p) for p in [PUBLIC/'preflight.json.gz',PUBLIC/'labels.json.gz']}))
    print(json.dumps(dict(years=years,opportunity_fields=opportunity_fields,folds=[{k:v for k,v in f.items() if k!='position_level_training_people'} for f in folds]),indent=2),flush=True)
    protections()


if __name__=='__main__':main()
