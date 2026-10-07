"""Decompose an exposed totals miss without changing any forecast or target."""
from pathlib import Path
import polars as pl
from universal_baseball.storage import sha256_file
from verify_defense_reference_history_v26 import ROOT,PUBLIC,OUT,NATIVE,read,eq
from verify_double_play_support_v22 import write


def main():
    dest=PUBLIC/'totals-diagnosis.json.gz';assert not dest.exists()
    report=read(PUBLIC/'report.json.gz')
    f=pl.read_parquet(OUT/'value-predictions.parquet');ids=f.filter(pl.col('actual_defense').is_not_null())['row_id'].to_list()
    c=pl.read_parquet(OUT/'OF-predictions.parquet').filter(pl.col('row_id').is_in(ids))
    o=pl.read_parquet(ROOT/'reports/generated/defense-value-v12/channel-predictions.parquet').filter(pl.col('row_id').is_in(ids))
    of=c.group_by(['origin_year','position']).agg(pl.col('legacy_runs').sum(),pl.col('centered_runs').sum(),pl.col('actual_relative_runs').sum()).sort(['origin_year','position']).to_dicts()
    other=o.filter(~pl.col('channel').is_in(['range_7','range_8','range_9'])).group_by(['origin_year','channel']).agg(pl.col('repair_history').sum(),pl.col('actual_runs').sum()).sort(['origin_year','channel']).to_dicts()
    n=pl.read_parquet(NATIVE/'component-ledger.parquet')
    full=n.filter((pl.col('season')>=2023)&pl.col('range_valid')).group_by(['season','position']).agg(pl.len().alias('rows'),pl.col('native_outs').sum(),pl.col('range_runs').sum()).sort(['season','position']).to_dicts()
    for y in (2022,2023,2024):
        os=[r for r in of if r['origin_year']==y];ns=[r for r in other if r['origin_year']==y]
        actual=sum(r['actual_relative_runs'] for r in os)+sum(r['actual_runs'] for r in ns)
        for arm,field in [('legacy','legacy_runs'),('centered','centered_runs')]:
            predicted=sum(r[field] for r in os)+sum(r['repair_history'] for r in ns)
            score=next(s for s in report['value']['defense']['per_origin'] if s['origin']==y and s['arm']==arm+'_defense')
            eq(actual,score['actual_total']);eq(predicted,score['predicted_total'])
    paths=[Path(__file__),OUT/'value-predictions.parquet',OUT/'OF-predictions.parquet',NATIVE/'component-ledger.parquet',ROOT/'reports/generated/defense-value-v12/channel-predictions.parquet',PUBLIC/'report.json.gz']
    write(dest,dict(model_fits=0,diagnostic_only=True,all_forecasts_and_targets_unchanged=True,
        matched_OF_channel_totals=of,matched_non_OF_channel_totals=other,full_qualified_position_totals=full,
        claim_limit='Exposed component totals locate misses; they do not establish a replacement prior, a universal zero-sum target or a FanGraphs WAR equivalence.',
        hashes={str(p):sha256_file(p) for p in paths}))
    print('All matched channel totals reproduce the saved aggregate miss. No forecasts changed.')


if __name__=='__main__':main()
