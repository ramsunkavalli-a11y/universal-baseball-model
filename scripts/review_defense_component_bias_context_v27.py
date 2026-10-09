"""Preserve unchanged opportunity and player-value context for reviewed cases."""
from pathlib import Path
import gzip
import json
import math
import polars as pl
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-component-bias-v27'


def read(p):
    with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)


def main():
    dest=PUBLIC/'player-value-context.json.gz';assert not dest.exists();protections()
    review=read(PUBLIC/'independent-review.json.gz');assert review['execution_integrity_pass']
    for p,h in {**review['hashes'],**review['source_hashes']}.items():assert sha256_file(Path(p))==h
    vpath=ROOT/'reports/generated/defense-reference-history-v26/value-predictions.parquet'
    cpath=ROOT/'reports/generated/defense-value-v12/channel-predictions.parquet'
    vals={r['row_id']:r for r in pl.read_parquet(vpath).to_dicts()}
    channels=pl.read_parquet(cpath).to_dicts();by={}
    for r in channels:by.setdefault(r['row_id'],[]).append(r)
    walks=read(PUBLIC/'player-walks.json.gz');context=[]
    for group in walks['groups']:
        records=[]
        for w in group['records']:
            r=vals[w['row_id']]
            assert math.isclose(r['centered_expanded'],r['batting_forecast']+(r['position_runs']+r['centered_defense'])/10,abs_tol=1e-8)
            if r['actual_expanded'] is not None:
                assert math.isclose(r['actual_expanded'],r['actual_batting']+(r['actual_position_runs']+r['actual_defense'])/10,abs_tol=1e-8)
            other=[dict(channel=c['channel'],history_rate=c['history_rate'],rate_unit=c['rate_unit'],
                        forecast_opportunities=c['repair_predicted_opportunities'],forecast_runs=c['repair_history'],
                        actual_opportunities=c['actual_native_opportunities'],actual_runs=c['actual_runs'],target_status=c['target_status'])
                   for c in by[w['row_id']] if c['channel'] in ('receiving','framing','throwing','blocking')]
            records.append(dict(value=r,other_applicable_components=other,
                interpretation='Existing custom batting-plus-position-plus-defined-defense common wins; not full WAR. No counterfactual value forecast produced.'))
        context.append(dict(selection=group['selection'],focal_player_id=group['focal_player_id'],channel=group['channel'],origin_year=group['origin_year'],records=records))
    note=dict(fits=0,forecasts_changed=False,records=sum(len(g['records']) for g in context),groups=context,
        whole_value_arithmetic_verified=True,hashes={str(p):sha256_file(p) for p in [Path(__file__),vpath,cpath,PUBLIC/'player-walks.json.gz',PUBLIC/'independent-review.json.gz']})
    with gzip.open(dest,'wt',encoding='utf8') as f:json.dump(note,f,allow_nan=False,separators=(',',':'))
    protections();print('All 56 unchanged player-value and catcher/receiving contexts preserved and arithmetic checked.')


if __name__=='__main__':main()
