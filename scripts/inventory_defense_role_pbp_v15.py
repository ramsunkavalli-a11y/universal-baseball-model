"""Inventory dated fielder snapshots without pretending they measure innings."""
from pathlib import Path
import json

import polars as pl

from capture_defense_role_v15 import ROOT, OUT, read, receipt
from audit_defense_role_v15 import source_check_seal
from run_hitter_finite_return_baseline import protections
from universal_baseball.storage import sha256_file


def main():
    protections(); source_check_seal()
    assert not (OUT/'pbp-inventory.json').exists()
    base=ROOT/'data/working/pbp-opportunity-foundation-v1'
    files=sorted(p for p in base.glob('season=*/level=*/terminal/*.parquet')
                 if int(p.parts[-4].split('=')[1])<=2024)
    ids={r['player_id'] for r in read(OUT/'explicit-scope-manifest.json')['cases']}
    records=[];observed=[]
    fields=[f'fielder_{p}' for p in range(2,10)]
    for path in files:
        y=int(path.parts[-4].split('=')[1]);level=path.parts[-3].split('=')[1]
        f=pl.read_parquet(path,columns=['game_pk','game_date','season',*fields])
        day=pl.col('game_date').str.to_date('%Y-%m-%d',strict=False)
        # Null IDs and nonpositive sentinel IDs are not observed fielders.
        stats=f.select(pl.len().alias('rows'),pl.col('game_pk').n_unique().alias('represented_games'),
            pl.col('game_date').null_count().alias('missing_dates'),
            (pl.col('game_date').is_not_null() & day.is_null()).sum().alias('unparseable_dates'),
            (day.dt.year()!=y).fill_null(False).sum().alias('wrong_date_year'),
            (pl.col('season')!=y).fill_null(True).sum().alias('wrong_partition_season'),
            pl.all_horizontal([pl.col(c).is_not_null() & (pl.col(c)>0) for c in fields]).sum().alias('all_eight_present'),
            day.min().cast(pl.String).alias('first_date'),day.max().cast(pl.String).alias('last_date'),
            *[pl.col(c).is_null().sum().alias(c+'_missing') for c in fields],
            *[(pl.col(c)<=0).fill_null(False).sum().alias(c+'_nonpositive') for c in fields]).to_dicts()[0]
        records.append(dict(source=str(path),sha256=sha256_file(path),season=y,level=level,**stats))
        long=f.unpivot(on=fields,index=['game_pk','game_date','season'],
                       variable_name='fielder_column',value_name='player_id').filter(pl.col('player_id').is_in(ids))
        if long.height:
            observed.append(long.with_columns(pl.lit(level).alias('level'),
                pl.col('fielder_column').str.replace('fielder_','').cast(pl.Int64).alias('position_code'))
                .select('season','level','game_pk','game_date','player_id','position_code').unique())
    assert records
    assert all(r['wrong_date_year']==r['wrong_partition_season']==0 for r in records)
    presence=pl.concat(observed).unique().sort('player_id','season','level','game_date','game_pk','position_code')
    presence.write_parquet(OUT/'pbp-case-presence.parquet')
    summaries=[]
    for key in sorted({(r['season'],r['level']) for r in records}):
        subset=[r for r in records if (r['season'],r['level'])==key]
        total=sum(r['rows'] for r in subset)
        summaries.append(dict(season=key[0],level=key[1],files=len(subset),rows=total,
            missing_dates=sum(r['missing_dates'] for r in subset),
            unparseable_dates=sum(r['unparseable_dates'] for r in subset),
            all_eight_present_rows=sum(r['all_eight_present'] for r in subset),
            all_eight_present_fraction=sum(r['all_eight_present'] for r in subset)/total if total else None,
            fielder_missing={str(p):sum(r[f'fielder_{p}_missing'] for r in subset) for p in range(2,10)},
            fielder_nonpositive={str(p):sum(r[f'fielder_{p}_nonpositive'] for r in subset) for p in range(2,10)},
            first_date=min(r['first_date'] for r in subset if r['first_date']),
            last_date=max(r['last_date'] for r in subset if r['last_date'])))
    receipt('pbp-inventory.json',dict(files=len(files),rows=sum(r['rows'] for r in records),
        represented_seasons=sorted({r['season'] for r in records}),
        missing_calendar_seasons=[2020],case_presence_rows=presence.height,
        summaries=summaries,source_files=records,
        qualification='Coverage of existing terminal-PA snapshots only. These do not certify full games, '
                      'exact defensive innings, starting positions, DH use or absence when a fielder is missing. '
                      '2020 MiLB cancellation is not a zero-quality season. Rookie snapshots do not certify DSL coverage.',
        no_fits=True,no_accuracy_claim=True,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'pbp-case-presence.parquet']}))
    protections()
    print(f'{len(files)} files, {sum(r["rows"] for r in records)} terminal-PA snapshots inventoried; '
          f'{presence.height} distinct case position-game presences. Not innings.',flush=True)


if __name__=='__main__':main()
