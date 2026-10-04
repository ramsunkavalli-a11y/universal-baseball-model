"""Independent unit reconstruction and actual reviews; no refits or tuning."""
import json
import shutil

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import VALUES, EVENTS
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from score_practical_hitter_v31 import score, rate_score
from score_hitter_reliability_v50 import rate_interval
import evaluate_hitter_talent_bridge_v74 as e

NOTES = e.ROOT / 'config/hitter_talent_bridge_v74_review.json'


def scope(q, name):
    never = q.filter(pl.col('prior_debut') == 0)
    choices = {'all': q, 'never_debut': never,
               'upper_never_debut': never.filter(pl.col('stage') == 'Upper minors'),
               'lower_never_debut': never.filter(pl.col('stage') == 'Lower minors'),
               'public': q.filter((pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null()),
               'new_draftees': never.filter(pl.col('new_draftee')), 'thin_pro': never.filter(pl.col('thin_pro')),
               'current_brief': q.filter(pl.col('pa_0').is_between(1, 199)),
               'current_regular': q.filter(pl.col('pa_0') >= 400)}
    if name in choices:
        return choices[name]
    if name.startswith('never_origin_'):
        return never.filter(pl.col('origin_year') == int(name.rsplit('_', 1)[1]))
    if name.startswith('never_rank_'):
        return never.filter(pl.col('rank_band') == int(name.rsplit('_', 1)[1]))
    raise ValueError(name)


def verify():
    pre = e.read(e.OUT / 'preflight.json')
    for p, h in pre['input_hashes'].items():
        assert sha256_file(e.Path(p)) == h, p
    q = pl.read_parquet(e.OUT / 'scored-predictions.parquet')
    source = pl.read_parquet(e.previous.OUT / 'features.parquet')
    paired = q.join(source.select('row_id', pl.col('next_batting_rate').alias('contract_rate')), on='row_id', validate='1:1')
    assert paired['row_id'].equals(q['row_id']), 'Response reconstruction order changed'
    counts = q.select(['count_' + x for x in EVENTS]).to_numpy()
    target_index = q.select(['target_env_' + x for x in EVENTS]).to_numpy() @ VALUES
    active = q['next_pa'].to_numpy() > 0
    reconstructed = np.zeros(len(q))
    reconstructed[active] = ((counts[active] @ VALUES) / q['next_pa'].to_numpy()[active] - target_index[active]) * UNIT
    assert np.allclose(reconstructed, paired['contract_rate'], atol=1e-10, rtol=0)
    assert np.array_equal(counts.sum(1), q['next_pa'].to_numpy())
    rate_frame = paired.drop('next_batting_rate').rename({'contract_rate': 'next_batting_rate'})
    legacy = e.read(e.OUT / 'scores.json')
    corrected = []
    with threadpool_limits(limits=2):
        for s in legacy:
            g, contract = scope(q, s['scope']), scope(rate_frame, s['scope'])
            assert len(g) == s['rows']
            for a, expected in s['scores'].items():
                got = score(g, a)
                assert all(np.isclose(v, got[k], atol=1e-10, rtol=0) for k, v in expected.items())
            for a, expected in s['rate'].items():
                got = rate_score(g, a + '_rate')
                for k in ['rmse', 'mae', 'bias']:
                    assert expected[k] is None and got[k] is None or np.isclose(expected[k], got[k], atol=1e-10, rtol=0)
            result = dict(s)
            result['common_origin_rate_sensitivity'] = {
                a: dict(v, unit='fixed-event batting wins per 600 PA above origin MLB average; not the training target')
                for a, v in s['rate'].items()}
            # Public event forecasts have their own origin-environment assumptions.
            # Keep those common-index scores, not a false exact relative-talent comparison.
            result['rate'] = {a: rate_score(contract, a + '_rate') for a in s['unweighted_rate']}
            result['unweighted_rate'] = {a: rate_score(contract, a + '_rate', False) for a in s['unweighted_rate']}
            corrected.append(result)
        replayed = 0
        for cell in pre['cells']:
            y, k = cell['year'], cell['fold']
            f = pl.read_parquet(e.OUT / f'features-{k}.parquet')
            te = f.filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('row_id')
            pred = q.filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('row_id')
            for h in e.read(e.OUT / f'fit-{y}-{k}.json')['heads']:
                assert sha256_file(e.Path(h['path'])) == h['sha256']
                model = joblib.load(h['path'])
                assert np.allclose(model.predict(safe_matrix(te, pre['features'][h['arm']])),
                                   pred[h['arm'] + '_all_rate'], atol=1e-10, rtol=0)
                replayed += 1
        intervals = []
        for s in ['never_debut', 'upper_never_debut', 'lower_never_debut']:
            for a in e.ARMS:
                intervals.append(dict(scope=s, **rate_interval(scope(rate_frame, s), a, 'preseason')))
    e.write('scores-contract.json', corrected)
    e.write('intervals-contract-rate.json', intervals)
    low, high = -target_index * UNIT, (VALUES.max() - target_index) * UNIT
    corrected_bounds = {a: int(((q[a + '_rate'].to_numpy() < low) | (q[a + '_rate'].to_numpy() > high)).sum())
                        for a in ['preseason', *e.ARMS, *[a + '_all' for a in e.ARMS]]}
    e.write('score-unit-correction.json', dict(original_verification=e.read(e.OUT / 'verification.json'),
                corrected_rate_physical_violations=corrected_bounds, minimum_rate_bound=float(low.min()),
                maximum_rate_bound=float(high.max()), actual_rate_reconstruction=True, every_initial_score_recomputed=True,
                prediction_heads_replayed=replayed, fitting_or_forecasts_changed=False, console_failure_after_outputs=True,
                original_rate_label_difference_maximum=float(np.max(np.abs(reconstructed - q['next_batting_rate'].to_numpy()))),
                protected_outcomes_used=False, primary_rate_response='relative to realized target MLB environment',
                delivered_value_response='common origin environment; mechanical fixed-PA integration'))
    for s in corrected[:7]:
        print(s['scope'], {a: (round(s['rate'][a]['rmse'], 4) if s['rate'][a]['rmse'] is not None else None,
                               round(s['scores'][a]['value_rmse'], 6)) for a in ['preseason', *e.ARMS]}, flush=True)
    print('Scoring units independently corrected; forecasts unchanged.', flush=True)


def finalize():
    correction = e.read(e.OUT / 'score-unit-correction.json')
    assert correction['prediction_heads_replayed'] == 105 and correction['actual_rate_reconstruction']
    assert not any(correction['corrected_rate_physical_violations'].values())
    notes = e.read(NOTES)
    cases = e.read(e.OUT / 'cases.json')
    assert set(notes) == {str(c['origin']['row_id']) for c in cases}
    source = pl.read_parquet(e.previous.OUT / 'features.parquet')
    history = pl.read_parquet(e.COUNTS)
    forecasts = pl.read_parquet(e.OUT / 'scored-predictions.parquet')
    lines = ['# Player review of prospect hitting alternatives', '',
             'All 16 selected cases are retained. Rate forecasts are batting wins per 600 PA above the expected future MLB average; observed rates here use the realized target MLB average. Delivered values use the separate common-origin event reference and are not full WAR. Non-arrivals have no observed hitting rate. Playing time is fixed throughout.', '',
             'Cases include nine fixed players and every arm’s largest gains, harms, false highs/lows and ordinary active cases. Peers are selected from same-origin stage, prior debut, age, minor PA and ranking without future outcomes. Outcomes are shown only afterward. Input probes explain saved-model mechanics, not causal effects or validated alternative forecasts.', '']
    reviewed = []
    for c in cases:
        r = c['origin']
        rid = str(r['row_id'])
        actual_rate = float(source.filter(pl.col('row_id') == r['row_id'])['next_batting_rate'][0])
        comment = notes[rid]
        assert len(comment) > 120
        support = [s for s in c['training_profiles'] if s['arm'] == 'translated_ridge' and s['kind'] == 'active']
        latest = [s for s in c['source_history'] if s['season'] == r['origin_year']]
        lines += [f"## {r['player_name']} before {r['target_year']}", '',
                  f"Selection: {', '.join(c['selection'])}. Age {r['age']:.1f}; {r['stage']}; fold {r['outer_fold']}. Information cutoff {c['information_date']}.", '',
                  'Known latest-season counts below are PA / K / unintentional BB / HR. Earlier two seasons and all 220 actual inputs are saved in the machine-readable reviewed cases.', '']
        lines += [f"- {s['season']} {s['bucket']}: {s['plate_appearances']} / {s['strike_outs']} / {s['unintentional_walks']} / {s['home_runs']}." for s in latest]
        if not latest:
            lines += ['- No current-season statistical row; missing evidence is not poor performance.']
        lines += ['', f"Translated supported exposure {c['profile']['translation_supported_pa']:.1f} of {c['profile']['translation_total_pa']:.1f} recency-weighted PA; buckets {c['profile']['translation_buckets'] or 'none'}. The graph has {c['graph']['pair_count']} pairs and {c['graph']['people']} distinct people, cutoff {c['graph']['cutoff']}, held fold {c['graph']['held_fold']}. Broad/refined active-profile support: " + ', '.join(f"{s['profile_kind']} {s['profile_people']} people" for s in support) + '. Sparse support remains a limitation.', '',
                  '| Estimate | Hitting rate | Delivered batting value |', '| --- | ---: | ---: |']
        for a, label in [('preseason', 'Existing'), ('scout_ridge', 'Rankings'), ('translated_ridge', 'Rankings and translation'), ('translated_hist', 'Same inputs with trees')]:
            lines += [f"| {label} | {r[a + '_rate']:+.3f} | {r[a + '_value']:+.3f} |"]
        actual_text = f'{actual_rate:+.3f}' if r['next_pa'] > 0 else 'Unobserved'
        lines += [f"| Actual | {actual_text} | {r['next_value']:+.3f} |", '',
                  f"Expected MLB PA {r['preseason_pa']:.1f}; actual {r['next_pa']}. Appearance chance {r['preseason_p']:.3f}; conditional PA {r['preseason_conditional_pa']:.1f}. These quantities do not change in this test.", '', comment, '']
        terms = c['saved_traces']['translated_ridge']['effects']
        block_rank = sum(t['effect'] for t in terms if t['feature'].startswith('scout_'))
        block_translation = sum(t['effect'] for t in terms if t['feature'].startswith('translated_'))
        lines += [f"Saved linear-head replay: rankings contribute {block_rank:+.3f}, and the entire translation block {block_translation:+.3f}, to the head’s fitted sum. These terms are not the total change from the old model because other coefficients were refitted. Its strongest terms: " + '; '.join(f"{t['feature']} {t['effect']:+.3f}" for t in terms[:4]) + '.', '',
                  f"The same tree fit with only the centered translated event deviations set to zero gives {c['same_fit_neutral_profile_probes']['translated_hist']:+.3f}; unchanged exposures/ranks make this potentially artificial. All cumulative tree predictions and original linear sums are saved. Established-player primary forecasts deliberately ignore the newly fitted head; the all-player sensitivity is separate.", '',
                  'Origin-selected comparisons:', '']
        peers = []
        for peer in c['peers']:
            h = history.filter((pl.col('player_id') == peer['player_id']) & pl.col('season').is_between(r['origin_year'] - 2, r['origin_year'])).sort('season', 'bucket').to_dicts()
            peers.append(dict(peer, source_history=h))
            lines += [f"- {peer['player_name']}: age {peer['age']:.1f}, {peer['minor_pa_0']:.0f} current minor PA, rank score {peer['new_scout_rank_score_0']:.2f}; later {peer['next_pa']} MLB PA. Existing/new translated values {peer['preseason_value']:+.3f}/{peer['translated_ridge_value']:+.3f}. This peer was not selected for that outcome."]
        supplemental = []
        if r['prior_debut'] == 1:
            g = forecasts.filter((pl.col('origin_year') == r['origin_year']) & (pl.col('stage') == r['stage']) &
                    (pl.col('prior_debut') == 1) & (pl.col('pa_0') > 0) & (pl.col('player_id') != r['player_id']))
            g = g.with_columns((((pl.col('age') - r['age']) / 3) ** 2 +
                    ((pl.col('pa_0') - r['pa_0']) / 300) ** 2 +
                    ((pl.col('quality_0') - r['quality_0']) / 2) ** 2).alias('distance')).sort('distance', 'player_id').head(4)
            lines += ['', 'Supplemental review comparisons for an already debuted hitter use current MLB PA and origin-known batting quality instead of minor PA/rank. This addresses the weak original peer match; original peers remain. The rule was added for diagnosis after review, without changing any forecast or score.', '']
            for peer in g.iter_rows(named=True):
                h = history.filter((pl.col('player_id') == peer['player_id']) & pl.col('season').is_between(r['origin_year'] - 2, r['origin_year'])).sort('season', 'bucket').to_dicts()
                supplemental.append(dict(player_id=peer['player_id'], player_name=peer['player_name'], age=peer['age'],
                            origin_pa=peer['pa_0'], origin_quality=peer['quality_0'], distance=peer['distance'],
                            actual_next_pa=peer['next_pa'], source_history=h))
                lines += [f"- {peer['player_name']}: age {peer['age']:.1f}, origin MLB PA {peer['pa_0']:.0f}, origin quality {peer['quality_0']:+.3f}; later {peer['next_pa']} MLB PA."]
        lines += ['']
        reviewed.append(dict(c, actual_relative_rate=actual_rate if r['next_pa'] > 0 else None,
                             baseball_review=comment, peers_with_source_history=peers, supplemental_established_peers=supplemental))
    e.write('reviewed-cases.json', reviewed)
    (e.OUT / 'player-walkthrough.md').write_text('\n'.join(lines).rstrip() + '\n', encoding='utf8')
    evidence = e.ROOT / 'reports/model-evidence/hitter-talent-bridge-v74'
    evidence.mkdir(parents=True, exist_ok=True)
    keep = ['preflight.json', 'scores.json', 'scores-contract.json', 'intervals.json', 'intervals-contract-rate.json',
            'score-unit-correction.json', 'verification.json', 'prefit-source-cases.json', 'reviewed-cases.json', 'player-walkthrough.md']
    for name in keep:
        if name == 'preflight.json':
            # Preserve every field and identity, without a million indentation lines.
            (evidence / name).write_text(json.dumps(e.read(e.OUT / name), ensure_ascii=False,
                allow_nan=False, separators=(',', ':')) + '\n', encoding='utf8')
            assert e.read(evidence / name) == e.read(e.OUT / name)
        else:
            shutil.copyfile(e.OUT / name, evidence / name)
    input_paths = [NOTES, e.CONTRACT, e.Path(__file__), e.ROOT / 'scripts/review_hitter_talent_bridge_v74_source.py',
                   e.ROOT / 'docs/hitter-talent-bridge-v74-prefit-repair.md', e.ROOT / 'docs/hitter-talent-bridge-v74-score-unit-correction.md',
                   e.ROOT / 'tests/test_hitter_talent_bridge.py', e.ROOT / 'tests/test_hitter_talent_bridge_units.py',
                   e.ROOT / 'docs/hitter-talent-bridge-v74-result.md', e.ROOT / 'src/universal_baseball/hitter_compatible_value.py',
                   e.ROOT / 'scripts/score_practical_hitter_v31.py', e.ROOT / 'scripts/score_hitter_reliability_v50.py']
    pre = e.read(e.OUT / 'preflight.json')
    outputs = list(e.OUT.glob('*.joblib')) + list(e.OUT.glob('forecast-*.parquet')) + list(e.OUT.glob('fit-*.json'))
    outputs += [e.OUT / n for n in keep] + [e.OUT / 'predictions.parquet', e.OUT / 'scored-predictions.parquet', e.OUT / 'fits.json']
    e.write('report.json', dict(player_walkthrough_status='complete', cases=len(reviewed), fitting_heads=105,
               input_hashes={**pre['input_hashes'], **{str(p): sha256_file(p) for p in input_paths}},
               output_hashes={str(p): sha256_file(p) for p in outputs}, scoring_units_corrected=True,
               predictive_disposition='modest_conditional_hitting_gain_delivered_value_uncertain',
               full_population_support=False, primary_established_unchanged=True,
               current_candidate_changed=False, protected_outcomes_used=False, frozen_forecast_changed=False,
               goal_complete=False, reasonability='coherent_but_sparse_profiles_and_major_readiness_errors_remain'))
    shutil.copyfile(e.OUT / 'report.json', evidence / 'report.json')
    print('Sixteen actual player reviews completed; evidence sealed; no deployment or whole-goal completion.', flush=True)


if __name__ == '__main__':
    import sys
    {'verify': verify, 'finalize': finalize}[sys.argv[1]]()
