"""Post-test explanation only: no new fits, caps, selection or revised forecasts."""
import polars as pl
from fit_hitter_arrival_value_transfer_v1 import OUT
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.storage import sha256_file


def main():
    f=pl.read_parquet(OUT/'predictions.parquet').with_columns(
        (pl.col('B_pa')/pl.col('B_p')).alias('inherited_conditional_pa'),
        (pl.col('F_pa')/pl.col('B_pa')).alias('pa_ratio'))
    q=f.filter((pl.col('horizon')==1)&pl.col('prospect')&(pl.col('stage')=='Lower minors')&pl.col('complete_components'))
    q=q.with_columns(((pl.col('F_expanded')-pl.col('actual_expanded'))**2-
        (pl.col('B_expanded')-pl.col('actual_expanded'))**2).alias('additional_squared_error'))
    fields=['origin_year','player_id','player_name','level','B_p','F_p','B_pa','F_pa','actual_pa',
            'base_other_value','pa_ratio','B_expanded','F_expanded','F_expanded_fixed','actual_expanded','additional_squared_error']
    groups=[]
    for label,expr in [('future_active',pl.col('actual_pa')>0),('future_450plus',pl.col('actual_pa')>=450)]:
        g=f.filter(pl.col('prospect')&expr).group_by('horizon','origin_year').agg(pl.len().alias('rows'),
            pl.col('actual_pa').mean(),pl.col('inherited_conditional_pa').mean(),
            pl.col('conditional_pa').mean().alias('research_conditional_pa'),pl.col('F_p').mean(),pl.col('F_pa').mean())
        groups.extend(g.with_columns(pl.lit(label).alias('descriptive_group')).sort('horizon','origin_year').to_dicts())
    examples=f.filter((pl.col('origin_year')==2021)&pl.col('player_id').is_in([665161,677649,672580,678662])).select(
        'origin_year','player_id','player_name','horizon','F_p','inherited_conditional_pa','F_pa','actual_pa','rate','F_value','actual_value')
    save(OUT/'post-test-diagnostic.json',{'prediction_sha256':sha256_file(OUT/'predictions.parquet'),
        'interpretation':'Outcome-selected descriptions only; not training groups, calibration or acceptance tests',
        'largest_lower_minors_year1_scaling_errors':q.sort('additional_squared_error',descending=True).head(20).select(fields).to_dicts(),
        'future_selected_conditional_workload':groups,'illustrative_examples':examples.to_dicts(),
        'new_fits':0,'forecast_changes':False,'protected_outcomes_used':False})
    print('Post-test diagnosis saved; no forecasts or scores changed')


if __name__=='__main__':main()
