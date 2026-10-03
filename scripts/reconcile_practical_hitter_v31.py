"""Deterministic physical/state constraints, preserving raw fixed-fit output."""
import polars as pl
import prepare_practical_hitter_v31 as r
from universal_baseball.storage import sha256_file

def coherent(f):
    out=f
    for arm in ['base_hurdle','detail_hurdle']:
        out=out.with_columns(pl.col(arm+'_pa').alias(arm+'_unbounded_state_pa'))
        for i,lo,hi in [(1,1,199),(2,200,399),(3,400,800)]:
            c=f'{arm}_conditional_pa{i}'
            out=out.with_columns(pl.col(c).alias(c+'_raw'),pl.col(c).clip(lo,hi).alias(c))
        out=out.with_columns(sum(pl.col(f'{arm}_p{i}')*pl.col(f'{arm}_conditional_pa{i}') for i in [1,2,3]).alias(arm+'_pa'))
    out=out.with_columns(pl.col('direct_detail_value').alias('direct_detail_raw_value'),
        pl.when(pl.col('direct_detail_pa')==0).then(0.).otherwise(pl.col('direct_detail_value')).alias('direct_detail_value'))
    return out

def main():
    f=pl.read_parquet(r.OUT/'predictions.parquet');g=coherent(f)
    assert len(f)==len(g) and f['row_id'].equals(g['row_id'])
    for a in ['base_hurdle','detail_hurdle']:
        assert g[a+'_pa'].is_between(0,800).all()
        assert g.filter(pl.col(a+'_pa')>800*(1-pl.col(a+'_p0'))+1e-9).is_empty()
        assert f[a+'_value'].equals(g[a+'_value'])
    g.write_parquet(r.OUT/'predictions-coherent.parquet')
    changes=g.select('row_id','origin_year','player_id','player_name',*[c for a in ['base_hurdle','detail_hurdle'] for c in [a+'_pa',a+'_unbounded_state_pa']],
        'direct_detail_pa','direct_detail_value','direct_detail_raw_value').filter(
        (pl.col('base_hurdle_pa')!=pl.col('base_hurdle_unbounded_state_pa'))|(pl.col('detail_hurdle_pa')!=pl.col('detail_hurdle_unbounded_state_pa'))|
        (pl.col('direct_detail_value')!=pl.col('direct_detail_raw_value')))
    changes.write_parquet(r.OUT/'coherence-changes.parquet')
    r.write('coherence-report.json',dict(rows=len(g),changed_rows=len(changes),
        maximum_pa_change={a:float((g[a+'_pa']-g[a+'_unbounded_state_pa']).abs().max()) for a in ['base_hurdle','detail_hurdle']},
        source_hash=sha256_file(r.OUT/'predictions.parquet'),output_hash=sha256_file(r.OUT/'predictions-coherent.parquet'),
        new_fits=0,contract_sha256=sha256_file(r.ROOT/'docs/practical-hitter-v31-coherence-amendment.md')))
    print(r.read(r.OUT/'coherence-report.json'))

if __name__=='__main__':main()
