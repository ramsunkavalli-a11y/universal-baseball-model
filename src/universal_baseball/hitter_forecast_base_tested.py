"""Production base arithmetic, including the sealed prefit career-PA repair.

The first source build reproduced raw V31, not its corrected production inputs.
Keep that builder and receipt unchanged; explicitly apply its documented repair.
The canceled-origin cohort has its own source construction and is not admitted
here or to the selected production training procedure.
"""
import polars as pl
from .hitter_forecast_base import base_inputs


def tested_base_inputs(snapshots, stints, counts, values, debuts, roster, *, source_cutoff):
    if (snapshots['origin_year'] == 2020).any():
        raise ValueError('Canceled-origin rows require their separate builder and are excluded from this candidate')
    if debuts['mlb_debut_date'].max().year > source_cutoff:
        raise ValueError('Future debut census: bound the source explicitly')
    if counts['plate_appearances'].null_count() or (counts['plate_appearances'] < 0).any():
        raise ValueError('Invalid source PA')
    result = base_inputs(snapshots, stints, counts, values, debuts, roster, source_cutoff=source_cutoff)
    mlb = counts.filter(pl.col('bucket') == 'MLB')
    frames = []
    for year in sorted(result['origin_year'].unique()):
        career = mlb.filter(pl.col('season') <= year).group_by('player_id').agg(
            pl.col('plate_appearances').sum().alias('_complete_career_pa'))
        frames.append(result.filter(pl.col('origin_year') == year).join(career, on='player_id', how='left', validate='1:1')
                      .with_columns(pl.col('_complete_career_pa').fill_null(0).alias('career_mlb_observed_pa'))
                      .drop('_complete_career_pa'))
    return pl.concat(frames).sort('row_id')
