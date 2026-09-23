"""Predictor-only support inventory, run before the population ablation."""
from pathlib import Path
import json
import numpy as np
import polars as pl

from fit_player_path_value_bridge_v1 import BASE, DEBUT, REFERENCE, training, references
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_three_year_opportunity import attach_cohorts
from universal_baseball.six_year_hitter import extend_labels
from universal_baseball.player_path_distribution import age_groups
from universal_baseball.storage import sha256_file

OUT = Path('reports/generated/player-path-population-v1')
ANCHORS = Path('model_artifacts/hitter-anchored-development-v1-2026-09-22/historical-anchors.parquet')
FOLDS = [(y, 3, False) for y in (2016, 2019, 2021, 2022, 2025)] + [
    (y, 6, False) for y in (2016, 2017, 2018, 2019, 2025)] + [(2022, 3, True)]


def panel_data():
    targets = pl.read_parquet(BASE/'targets.parquet')
    return attach_cohorts(extend_labels(pl.read_parquet(BASE/'panel.parquet'), targets), pl.read_parquet(DEBUT), targets)


def eligible(panel, cutoff, horizon, excluded=()):
    if cutoff > 2025:
        raise ValueError('Protected cutoff')
    valid = (pl.col('origin_year')+horizon <= cutoff) & ~(
        (pl.col('origin_year') < 2020) & (pl.col('origin_year')+horizon >= 2020))
    valid &= ~pl.col('player_id').is_in(list(excluded))
    for h in range(1, horizon+1):
        valid &= pl.col(f'war_h{h}').is_not_null() & pl.col(f'pa_h{h}').is_not_null()
    return panel.filter(valid).sort('player_id', 'origin_year').with_columns(
        (1/pl.len().over('player_id')).alias('identity_weight'))


def support(frame):
    mass = frame.group_by('player_id').agg(pl.col('identity_weight').sum())['identity_weight'].to_numpy()
    return {'rows': frame.height, 'identities': len(mass),
            'identity_ess': float(mass.sum()**2/(mass@mass)) if len(mass) else 0.}


def inventory(frame):
    frame = frame.with_columns(pl.Series('age_band', age_groups(frame['age'].to_numpy())),
        (pl.col('pa_lag0')-pl.col('mlb_pa_lag0')).alias('minor_pa'))
    cells = []
    for keys, f in frame.partition_by('stage', 'age_band', as_dict=True).items():
        cells.append({'stage': keys[0], 'age_band': int(keys[1]), **support(f)})
    brief = frame.filter((pl.col('age') <= 23) & pl.col('mlb_pa_lag0').is_between(1,99))
    return {**support(frame), 'young_brief_mlb': support(brief), 'cells': cells,
        'level_rows': frame.group_by('level').len().sort('level').to_dicts(),
        'prior_debut_rows': frame.group_by('prior_debut').len().to_dicts(),
        'minor_pa_quantiles': frame.select(*[pl.col('minor_pa').quantile(q).alias(str(q)) for q in (0.,.25,.5,.75,1.)]).to_dicts()[0]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    panel = panel_data()
    anchors = pl.read_parquet(ANCHORS)
    if anchors.filter((pl.col('anchor_cutoff') != pl.col('origin_year')) | (
        pl.col('latest_anchor_target') > pl.col('anchor_cutoff'))).height:
        raise AssertionError('Unsafe anchor vintage')
    reports, lost = [], []
    for cutoff, h, cold in FOLDS:
        test = panel.filter(pl.col('origin_year') == cutoff)
        excluded = test['player_id'].to_list() if cold else ()
        all_rows = eligible(panel, cutoff, h, excluded)
        last = training(panel, cutoff, h, excluded).with_columns(pl.lit(1.).alias('identity_weight'))
        removed = all_rows.join(last.select('player_id','origin_year'), on=['player_id','origin_year'], how='anti')
        young = removed.filter(pl.col('age') <= 23)
        lost.append(young.select('player_id','player_name','origin_year','age','level','stage','mlb_pa_lag0','pa_lag0').with_columns(
            pl.lit(cutoff).alias('fit_cutoff'),pl.lit(h).alias('horizon'),pl.lit(cold).alias('cold')))
        anchored = all_rows.join(anchors.select('player_id','origin_year'), on=['player_id','origin_year'], how='inner')
        reports.append({'cutoff':cutoff,'horizon':h,'cold':cold,'latest':inventory(last),'all':inventory(all_rows),
            'removed_young_snapshots': young.height, 'anchored_snapshot_support':support(anchored),
            'anchored_origins': sorted(anchored['origin_year'].unique().to_list()),
            'query_reference_rows':test.join(references(h),on=['player_id','origin_year'],how='inner').height})
    earlier = []
    for y in range(2012,2016):
        for h in (3,6):
            f = eligible(panel,y,h)
            earlier.append({'origin':y,'horizon':h,**support(f),
                'reference_rows':references(h).filter(pl.col('origin_year')==y).height})
    pl.concat(lost).write_parquet(OUT/'removed-young-snapshots.parquet')
    sources = [BASE/'panel.parquet',BASE/'targets.parquet',BASE/'manifest.json',DEBUT,REFERENCE,ANCHORS,Path(__file__)]
    save(OUT/'support-audit.json', {'folds':reports,'earlier_origins':earlier,
        'promotion_timing':'Unknown in this annual panel; exposure totals cannot identify late promotion dates.',
        'anchors':{'origins':sorted(anchors['origin_year'].unique().to_list()),
            'target':'PA-weighted next-year batting-plus-replacement rate conditional on MLB playing, not pure latent talent.',
            'vintage_checks_pass':True,
            'complete_joint_residual_forecasts_available':False,
            'missing':'No complete cutoff-safe H1-H6 conditional rate + opportunity path forecasts for donor origins; existing anchor is H1, later challenger H2 only. H6 at 2016 has no eligible anchored snapshots.'},
        'protected_outcomes_used':False,'new_forecast_outcomes_scored':False,
        'hashes':{str(p):sha256_file(p) for p in sources}})
    print(json.dumps([{'cutoff':r['cutoff'],'h':r['horizon'],'cold':r['cold'],
        'latest_rows':r['latest']['rows'],'all_rows':r['all']['rows'],
        'latest_brief':r['latest']['young_brief_mlb'],'all_brief':r['all']['young_brief_mlb'],
        'anchor_rows':r['anchored_snapshot_support']['rows']} for r in reports],indent=2))


if __name__ == '__main__':
    main()
