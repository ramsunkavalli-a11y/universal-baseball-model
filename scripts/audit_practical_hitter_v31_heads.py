"""Conditional-head support: do not infer it from total classifier rows."""
from pathlib import Path
import polars as pl
import prepare_practical_hitter_v31 as r

def main():
    pre=r.read(r.OUT/'preflight-ready.json');f=pl.read_parquet(pre['ready_features'])
    notes=[];flags=[]
    for c in pre['cells']:
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids']))
        for head,sub in [('active_rate',tr.filter(pl.col('next_pa')>0)),*[(f'conditional_state_{i}',tr.filter(pl.col('next_state')==i)) for i in [1,2,3]]]:
            # Source-stage/age/debut support counts distinct people, not repeated rows.
            a=sub.with_columns((pl.col('age')//5).alias('age_band'));b=te.with_columns((pl.col('age')//5).alias('age_band'))
            keys=['stage','prior_debut','age_band'];n=a.group_by(keys).agg(pl.col('player_id').n_unique().alias('conditional_profile_players'))
            z=b.select('row_id','origin_year','player_id',*keys).join(n,on=keys,how='left',validate='m:1').with_columns(pl.col('conditional_profile_players').fill_null(0),
                pl.lit(head).alias('head'),pl.lit(c['fold']).alias('outer_fold'))
            flags.append(z);notes.append(dict(year=c['year'],fold=c['fold'],head=head,training_rows=len(sub),training_players=sub['player_id'].n_unique(),
                training_lower_players=sub.filter(pl.col('stage')=='Lower minors')['player_id'].n_unique(),
                unseen_rows=int((z['conditional_profile_players']==0).sum()),sparse_rows=int((z['conditional_profile_players']<20).sum())))
    pl.concat(flags).write_parquet(r.OUT/'conditional-head-support.parquet')
    r.write('conditional-head-support.json',dict(cells=notes,
        timing='Supplemental audit while fixed fits execute, before score-based decisions; full-population preflights preceded all fits. This conditional-head audit is not retroactively described as prefit.',
        already_completed_cells=[p.name for p in sorted(r.OUT.glob('forecast-*.parquet'))],
        interpretation='Conditional-active talent for lower-level players often lacks direct training destinations. Keep rows and forecasts, flag unsupported extrapolation; do not label as measured current MLB ability.'))
    print(pl.DataFrame(notes).group_by('head').agg(pl.col('unseen_rows','sparse_rows').sum()))

if __name__=='__main__':main()
