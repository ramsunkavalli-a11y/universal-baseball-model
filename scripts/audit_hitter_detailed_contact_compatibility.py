"""Review old contact evidence against current sources; never fit or change forecasts."""
from pathlib import Path
import json
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
from universal_baseball.hitter_target_architecture import expanding_year_folds

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/hitter-detailed-contact-compatibility'
KEY = ['origin_year', 'player_id']
FIXED = [(592450, 2024), (665742, 2023), (668804, 2018),
         (608475, 2017), (701762, 2024), (694671, 2023)]


def reconstruct(frame):
    columns = [c for c in frame.columns if c.startswith('contact_cell_rate__')]
    if len(columns) != 90:
        raise ValueError('Exactly ninety saved contact cells are required')
    if not len(frame):
        return columns, np.empty((0, 90), dtype=np.int64)
    rates = frame.select(columns).to_numpy()
    counts = rates * (frame['contact_events'].to_numpy()[:, None] + 45.) - .5
    if not np.all(np.isfinite(counts)) or np.min(counts) < -1e-8:
        raise ValueError('Contact cells are missing or negative')
    if not np.allclose(counts, np.rint(counts), atol=1e-8, rtol=0):
        raise ValueError('Saved cell rates do not reconstruct integer counts')
    counts = np.rint(counts).astype(np.int64)
    if not np.array_equal(counts.sum(axis=1), frame['contact_events'].to_numpy()):
        raise ValueError('Contact cells fail exposure accounting')
    return columns, counts


def peer_rows(frame, row):
    pool = frame.filter((pl.col('origin_year') == row['origin_year']) &
                        (pl.col('player_id') != row['player_id']) &
                        (pl.col('stage') == row['stage']) &
                        (pl.col('prior_debut') == row['prior_debut']))
    distance = sum(((pl.col(c) - row[c]) / scale) ** 2
                   for c, scale in [('age', 3), ('pa_0', 250),
                                    ('AAA_0_pa', 250), ('AA_0_pa', 250)])
    return pool.with_columns(distance.alias('distance')).sort('distance', 'player_id').head(4)


def memberships(panel):
    rows = []
    for fold in expanding_year_folds(panel['origin_year'].unique().to_list()):
        train = panel.filter(pl.col('origin_year').is_in(fold.train_origins))
        test = panel.filter(pl.col('origin_year') == fold.test_origin)
        if train['target_season'].max() > fold.test_origin:
            raise ValueError('Unmatured historical labels')
        shared = set(train['player_id']) & set(test['player_id'])
        rows.append(dict(origin=fold.test_origin, train_rows=len(train), test_rows=len(test),
                         train_people=train['player_id'].n_unique(),
                         test_people=test['player_id'].n_unique(), shared_people=len(shared),
                         test_rows_with_prior_training_identity=len(test.filter(pl.col('player_id').is_in(shared))),
                         max_training_target=train['target_season'].max()))
    return rows


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                     allow_nan=False, default=str) + '\n', encoding='utf8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'report.json').exists():
        raise FileExistsError('Preserve the first audit; do not overwrite it')
    paths = {
        'annual': ROOT / 'reports/generated/hitter-value-panel-v2/tables/hitter-contact-features.parquet',
        'panel': ROOT / 'reports/generated/hitter-contact-neutralization-v2/tables/modeling-panel.parquet',
        'detail': ROOT / 'reports/generated/hitter-model-finalist-tuning-v2/tables/finalist-ensemble-predictions.parquet',
        'stats': ROOT / 'reports/generated/hitter-contact-block-ensemble-v2/tables/stats_only-predictions.parquet',
        'official': ROOT / 'reports/generated/practical-hitter-v31/counts.parquet',
        'current': ROOT / 'reports/generated/hitter-preseason-readiness-v68/scored-predictions.parquet',
        'old_source_report': ROOT / 'reports/generated/hitter-value-panel-v2/report.json',
        'neutral_report': ROOT / 'reports/generated/hitter-contact-neutralization-v2/report.json',
        'ensemble_report': ROOT / 'reports/generated/hitter-model-finalist-tuning-v2/finalist-report.json',
        'ablation_report': ROOT / 'reports/generated/hitter-contact-block-ensemble-v2/report.json',
        'contract': ROOT / 'docs/hitter-detailed-contact-compatibility-contract.md',
        'runner': Path(__file__),
        'panel_code': ROOT / 'src/universal_baseball/hitter_value_panel.py',
        'fold_code': ROOT / 'src/universal_baseball/hitter_target_architecture.py',
        'ablation_code': ROOT / 'scripts/evaluate_hitter_contact_block_ensemble_v2.py',
        'neutral_code': ROOT / 'src/universal_baseball/hitter_contact_neutralization.py',
        'ensemble_code': ROOT / 'scripts/summarize_hitter_finalists_v2.py',
    }
    hashes = {str(p): sha256_file(p) for p in paths.values()}
    source_report = json.loads(paths['old_source_report'].read_text(encoding='utf8'))
    neutral_report = json.loads(paths['neutral_report'].read_text(encoding='utf8'))
    ensemble_report = json.loads(paths['ensemble_report'].read_text(encoding='utf8'))
    for name, report, key in [('annual', source_report, 'artifacts'),
                              ('panel', neutral_report, None), ('detail', ensemble_report, None)]:
        artifact = (report[key]['contact_features'] if key else
                    report['modeling_panel_artifact'] if name == 'panel' else report['artifact'])
        assert hashes[str(paths[name])] == artifact['file_sha256']
    annual = pl.read_parquet(paths['annual']).filter(pl.col('season') <= 2024)
    assert annual.unique(['season', 'player_id']).height == len(annual)
    columns, cells = reconstruct(annual)
    hr = cells[:, [i for i, c in enumerate(columns) if c.endswith('___HR')]].sum(axis=1)
    annual = annual.with_columns(pl.Series('reconstructed_contact_hr', hr))
    official = pl.read_parquet(paths['official']).filter(pl.col('season') <= 2024)
    allcounts = official.group_by('season', 'player_id').agg(
        pl.col('plate_appearances').sum().alias('official_all_pa'),
        pl.col('home_runs').sum().alias('official_all_hr'))
    bridge = annual.join(allcounts, on=['season', 'player_id'], how='left', validate='1:1')
    bridge = bridge.with_columns(
        pl.col('official_all_pa').is_null().alias('official_missing'),
        (pl.col('contact_events') > pl.col('official_all_pa')).fill_null(False).alias('excess_contacts'),
        (pl.col('reconstructed_contact_hr') > pl.col('official_all_hr')).fill_null(False).alias('excess_hr'))
    bad = bridge.filter(pl.any_horizontal('official_missing', 'excess_contacts', 'excess_hr'))
    bad.select('season', 'player_id', 'contact_events', 'contact_highest_level',
               'reconstructed_contact_hr', 'official_all_pa', 'official_all_hr',
               'official_missing', 'excess_contacts', 'excess_hr').write_parquet(OUT / 'source-conflicts.parquet')
    panel = pl.read_parquet(paths['panel'])
    assert panel['target_season'].max() <= 2025
    current = pl.read_parquet(paths['current'])
    assert len(current) == 30506 and current['target_year'].max() <= 2025
    detail = pl.read_parquet(paths['detail']).select(*KEY, 'actual_active', 'actual_component_war',
        pl.col('prediction_candidate_equal_mean').alias('old_detail_value'))
    stats = pl.read_parquet(paths['stats']).select(*KEY,
        pl.col('actual_component_war').alias('stats_actual'),
        pl.col('ensemble_prediction').alias('old_stats_value'))
    ablation = detail.join(stats, on=KEY, validate='1:1')
    assert len(ablation) == len(detail) == 28183
    assert np.array_equal(ablation['actual_component_war'], ablation['stats_actual'])
    joined = current.join(ablation, on=KEY, how='left', validate='1:1').join(
        panel.select(*KEY, 'target_mlb_pa', 'target_component_war'), on=KEY, how='left', validate='1:1')
    matched = joined.filter(pl.col('old_detail_value').is_not_null()).with_columns(
        (((pl.col('old_detail_value') - pl.col('actual_component_war')) ** 2) -
         ((pl.col('old_stats_value') - pl.col('actual_component_war')) ** 2)).alias('old_detail_loss_change'))
    chosen = {key: ['fixed'] for key in FIXED}
    rules = [('largest_old_contact_gain', matched.sort('old_detail_loss_change', 'row_id')),
             ('largest_old_contact_harm', matched.sort('old_detail_loss_change', 'row_id', descending=[True, False])),
             ('old_false_high', matched.filter(pl.col('next_pa') == 0).sort('old_detail_value', descending=True)),
             ('old_false_low', matched.with_columns((pl.col('actual_component_war') - pl.col('old_detail_value')).alias('miss')).sort('miss', descending=True)),
             ('ordinary_active', matched.filter((pl.col('next_pa') > 0) &
                  ((pl.col('old_detail_value') - pl.col('actual_component_war')).abs() < .05)).sort('row_id'))]
    for why, frame in rules:
        row = frame.row(0, named=True)
        chosen.setdefault((row['player_id'], row['origin_year']), []).append(why)
    dump('selected-cases.json', [dict(player_id=pid, origin_year=y, reasons=why)
                                 for (pid, y), why in chosen.items()])
    cases = []
    current_fields = ['row_id', 'player_name', 'age', 'stage', 'prior_debut', 'source_position',
                      'pa_0', 'AAA_0_pa', 'AA_0_pa', 'on_40man', 'preseason_p',
                      'preseason_conditional_pa', 'preseason_pa', 'preseason_rate', 'preseason_value',
                      'next_pa', 'next_value', 'old_detail_value', 'old_stats_value',
                      'actual_component_war', 'target_mlb_pa']
    for (pid, y), why in chosen.items():
        row = joined.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == y)).row(0, named=True)
        old = panel.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == y))
        a = annual.filter((pl.col('player_id') == pid) & pl.col('season').is_between(y - 2, y))
        ccols, cc = reconstruct(a)
        ah = []
        for i, ar in enumerate(a.to_dicts()):
            ah.append(dict(season=ar['season'], contacts=ar['contact_events'],
                           by_level={c: ar[c] for c in a.columns if c.startswith('contacts_level__')},
                           nonzero_cells={c.removeprefix('contact_cell_rate__'): int(cc[i, k])
                                          for k, c in enumerate(ccols) if cc[i, k]}))
        peers = peer_rows(current, row).select('player_id', 'player_name', 'age', 'stage',
            'source_position', 'pa_0', 'AAA_0_pa', 'AA_0_pa', 'preseason_pa', 'next_pa', 'next_value', 'distance')
        cases.append(dict(player_id=pid, origin_year=y, selection=why,
            forecasts={c: row[c] for c in current_fields},
            actual_separate_level_history=official.filter((pl.col('player_id') == pid) &
                pl.col('season').is_between(y - 2, y)).sort('season', 'bucket').to_dicts(),
            reconstructed_contact_history=ah,
            old_actual_lag_inputs=old.select([c for c in old.columns if c.startswith(('lag0__contact', 'lag1__contact', 'lag2__contact'))]).to_dicts(),
            current_model_features_limit='Current probabilities/rate are unchanged saved outputs; no new fit or fit-path replay',
            old_model_features_limit='Saved ablation outputs and exact lag inputs, not a new old-model path explanation',
            peers=peers.to_dicts(), peer_limit='Not matched on health, role, park, handedness or scouting; outcomes do not explain away a talent miss'))
    dump('cases.json', cases)
    years = sorted(matched['origin_year'].unique())
    membership = memberships(panel)
    report = dict(source_player_seasons=len(annual), reconstructed_cells=90,
        source_by_season=bridge.group_by('season').agg(pl.len().alias('rows'),
            pl.col('contact_events').sum(), pl.col('contacts_level__MLB').sum(),
            pl.col('official_missing').sum(), pl.col('excess_contacts').sum(), pl.col('excess_hr').sum()).sort('season').to_dicts(),
        source_conflict_rows=len(bad), source_conflict_people=bad['player_id'].n_unique(),
        source_conflict_contacts=int(bad['contact_events'].sum()),
        old_folds=membership, old_evaluation_rows=len(detail), current_evaluation_rows=len(current),
        matched_rows=len(matched), old_only_rows=len(detail.join(current.select(KEY), on=KEY, how='anti')),
        current_without_old_rows=len(current) - len(matched),
        matched_pa_label_disagreements=int((matched['target_mlb_pa'] != matched['next_pa']).sum()),
        matched_zero_old_positive_current=int(((matched['target_mlb_pa'] == 0) & (matched['next_pa'] > 0)).sum()),
        old_current_value_labels_max_difference=float((matched['actual_component_war'] - matched['next_value']).abs().max()),
        old_evaluation_origins=years,
        old_current_mlb_contact_coverage=panel.filter(pl.col('origin_year').is_in(years) &
            (pl.col('lag0__pa_level__MLB') > 0)).select(pl.len().alias('rows'),
                *[(pl.col(f'lag{k}__contact_events').fill_null(0) > 0).sum().alias(f'lag{k}_has_minor_contact') for k in range(3)]).to_dicts(),
        old_raw_cells_park_adjusted=False, old_cells_pooled_across_levels=True,
        neutral_event_fold_formula='(player_id * 1000003 + 97) modulo 2',
        neutral_outer_forecast_fold_exclusion_demonstrated=False,
        model_predictive_walkthrough_status='not_replayed_no_new_model_test',
        source_walkthrough_status='pending_manual_review',
        new_fit=False, forecasts_changed=False, protected_2026_used=False,
        interpretation='Compatibility audit only; old saved errors are not compared with current as an isolated contact treatment',
        input_hashes=hashes,
        output_hashes={str(OUT / n): sha256_file(OUT / n) for n in ['source-conflicts.parquet', 'cases.json', 'selected-cases.json']})
    dump('report.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in ['input_hashes', 'output_hashes', 'old_current_mlb_contact_coverage']}, indent=2))
    print('Cases:', [(c['forecasts']['player_name'], c['origin_year'], c['selection']) for c in cases])


if __name__ == '__main__':
    main()
