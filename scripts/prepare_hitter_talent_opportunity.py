"""Reconcile sources and seal every nested membership before talent fits."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_talent_opportunity import rate_membership, estimable, profile_counts
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
import evaluate_hitter_preseason_readiness_v68 as current

ROOT = current.ROOT
OUT = ROOT / 'reports/generated/hitter-talent-opportunity'
RATE = ROOT / 'reports/generated/practical-hitter-numeric-repair-v53'
LEGACY = ROOT / 'model_artifacts/hitter-talent-workload-v1-2026-09-23'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/name).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n', encoding='utf8')


def verify(paths):
    for path, digest in paths.items():
        assert sha256_file(Path(path)) == digest, path


def main():
    assert not (OUT/'preflight.json').exists(), 'Preserve sealed preparation'
    reviewed = read(ROOT/'reports/generated/hitter-workload-risk/final-report.json')
    assert reviewed['player_walkthrough_status'] == 'complete'
    verify(reviewed['source_and_execution_hashes']); verify(reviewed['review_hashes'])
    old = read(current.OUT/'preflight.json')
    verify(old['input_hashes'])
    rate = read(RATE/'preflight.json')
    names = rate['rate_features']
    f = pl.read_parquet(current.OUT/'features.parquet').sort('row_id')
    rf = pl.read_parquet(RATE/'features.parquet').sort('row_id')
    q = pl.read_parquet(current.OUT/'scored-predictions.parquet').sort('row_id')
    assert len(f) == 63282 and len(q) == 30506 and len(names) == 199
    assert not any('scout' in n or n.startswith(('next_', 'target_')) for n in names)
    assert f.select('row_id', *names, 'next_pa', 'next_batting_rate').equals(
        rf.select('row_id', *names, 'next_pa', 'next_batting_rate'))
    assert np.isfinite(safe_matrix(f, names)).all()
    assert np.isfinite(f.filter(pl.col('next_pa') > 0)['next_batting_rate'].to_numpy()).all()
    assert f.select('player_id', 'outer_fold').unique().group_by('player_id').len()['len'].max() == 1
    assert f['target_year'].max() == 2025
    # A design reconciliation, not retroactive recertification of legacy scores.
    legacy = pl.read_parquet(LEGACY/'predictions.parquet')
    lp = legacy.filter(pl.col('prospect'))
    assert np.allclose(lp['TP_pa'], lp['fixed_p']*lp['TP_conditional'], atol=1e-9, rtol=0)
    lf = read(LEGACY/'fit-manifest.json')
    legacy_note = dict(prospect_rows=len(lp), prior_probability_fixed=True,
        horizons=sorted(legacy['horizon'].unique()),
        annual_origins=sorted(legacy.filter(pl.col('horizon') == 1)['origin_year'].unique()),
        workload_fits=len(lf['workload_fits']), inner_contexts=len(lf['inner_fits']),
        legacy_walkthrough_recertified=False,
        interpretation='Old fixed-participation conditional test is not this cold-player all-population arrival test')
    dates = read(current.SOURCE/'source-report.json')['release_evidence']
    graphs = {}; cells = []; memberships = []; support = []; profiles = []
    for c in old['cells']:
        y, k = c['year'], c['fold']
        tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
        te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
        assert not (tr['outer_fold'] == k).any()
        checks = {}
        for head, sub in [('participation', tr), ('conditional_pa', tr.filter(pl.col('next_pa') > 0))]:
            s, note = preflight(sub, te, cutoff=y, fold=k, features=old['pa_features'],
                expected_keys=te.select('row_id', 'horizon').iter_rows())
            checks[head] = note
            support.append(s.with_columns(pl.lit('outer_'+head).alias('scope'), pl.lit(k).alias('held_outer_fold')))
            profiles.append(profile_counts(sub, te, current.tagged).with_columns(
                pl.lit('outer_'+head).alias('scope'), pl.lit(k).alias('held_outer_fold')))
        uses = []
        groups = tr.select('origin_year', 'outer_fold').unique().sort('origin_year', 'outer_fold')
        for s, j in [*groups.iter_rows(), (y, k)]:
            val = te if j == k else tr.filter((pl.col('origin_year') == s) & (pl.col('outer_fold') == j))
            inner = rate_membership(tr, s, j)
            excluded = [k] if j == k else sorted([k, j])
            tag = f"rate-{s}-" + '-'.join(map(str, excluded))
            assert not set(inner['player_id']) & set(val['player_id'])
            assert not set(te['player_id']) & set(inner['player_id'])
            ready = estimable(inner)
            if ready:
                assert max(dates[str(t)]['date'] for t in inner['target_year'].unique()) < dates[str(s+1)]['date']
                supp, note = preflight(inner, val, cutoff=s, fold=j, features=names,
                    expected_keys=val.select('row_id', 'horizon').iter_rows())
                support.append(supp.with_columns(pl.lit('nested_rate').alias('scope'), pl.lit(k).alias('held_outer_fold')))
                profiles.append(profile_counts(inner, val, current.tagged).with_columns(
                    pl.lit('nested_rate').alias('scope'), pl.lit(k).alias('held_outer_fold')))
            else:
                note = dict(integrity_pass=None, training_rows=len(inner),
                    training_players=inner['player_id'].n_unique(),
                    training_origins=inner['origin_year'].n_unique(),
                    status='unestimated_origin_history_not_zero_talent')
            training_ids = inner['row_id'].to_list()
            if tag not in graphs:
                graphs[tag] = dict(tag=tag, cutoff=s, excluded_folds=excluded,
                    training_row_ids=training_ids, validation_row_ids=set(),
                    estimated=ready, training_rows=len(inner),
                    training_people=inner['player_id'].n_unique(), training_origins=inner['origin_year'].n_unique(),
                    validation_checks=[])
            g = graphs[tag]
            assert g['training_row_ids'] == training_ids and g['estimated'] == ready
            g['validation_row_ids'].update(val['row_id'].to_list())
            g['validation_checks'].append(dict(outer_year=y, outer_fold=k, held_inner_fold=j, preflight=note))
            uses.append(dict(tag=tag, row_ids=val['row_id'].to_list(), estimated=ready,
                kind='outer_test' if j == k else 'outer_training'))
            memberships.extend(dict(outer_year=y, outer_fold=k, row_id=r, tag=tag,
                estimated=ready, kind='outer_test' if j == k else 'outer_training') for r in val['row_id'])
        assert set(r for u in uses for r in u['row_ids']) == set(c['training_row_ids']) | set(c['test_row_ids'])
        cells.append(dict(year=y, fold=k, information_date=c['information_date'],
            training_row_ids=c['training_row_ids'], test_row_ids=c['test_row_ids'], uses=uses,
            outer_preflight=checks))
        print(f'Prepared nested rate memberships and outer checks {y}/{k}', flush=True)
    for g in graphs.values():
        g['validation_row_ids'] = sorted(g['validation_row_ids'])
    OUT.mkdir(parents=True, exist_ok=True)
    pl.concat(support, how='diagonal_relaxed').write_parquet(OUT/'support.parquet')
    pl.concat(profiles, how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet')
    pl.DataFrame(memberships).write_parquet(OUT/'memberships.parquet')
    write('legacy-source-reconciliation.json', legacy_note)
    paths = [Path(__file__), ROOT/'src/universal_baseball/hitter_talent_opportunity.py',
        ROOT/'tests/test_hitter_talent_opportunity.py', ROOT/'docs/hitter-talent-opportunity-contract.md',
        current.OUT/'features.parquet', current.OUT/'preflight.json', current.OUT/'scored-predictions.parquet',
        current.SOURCE/'source-report.json', RATE/'features.parquet', RATE/'preflight.json',
        LEGACY/'predictions.parquet', LEGACY/'fit-manifest.json',
        ROOT/'reports/generated/hitter-workload-risk/final-report.json',
        ROOT/'scripts/prepare_practical_hitter_v33.py', ROOT/'scripts/fit_practical_hitter_v31.py',
        ROOT/'src/universal_baseball/forecast_validation.py', OUT/'support.parquet',
        OUT/'profile-support.parquet', OUT/'memberships.parquet', OUT/'legacy-source-reconciliation.json']
    write('preflight.json', dict(before_fitting=True, new_fits=0, source_rows=63282,
        fixed_forecasts=30506, rate_features=names, pa_features=old['pa_features'],
        settings=old['settings'], ridge_alpha=100, graphs=list(graphs.values()), cells=cells,
        distinct_rate_contexts=len(graphs), estimated_rate_contexts=sum(g['estimated'] for g in graphs.values()),
        fallback_rate_contexts=sum(not g['estimated'] for g in graphs.values()),
        input_hashes={str(p):sha256_file(p) for p in paths}, protected_outcomes_used=False,
        second_stage_preflight='required_after_generation_before_any_opportunity_fit'))
    print('Prepared',len(graphs),'distinct contexts;',sum(g['estimated'] for g in graphs.values()),'estimated', flush=True)


if __name__ == '__main__':
    main()
