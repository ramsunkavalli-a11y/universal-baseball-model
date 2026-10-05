"""Append corrected uncertainty and player traces without refitting or replacing evidence."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

import numpy as np
import polars as pl

from prepare_foreign_borrowed_stability import ROOT, OUT, INPUTS, DOMESTIC, read, save, verify
from review_foreign_borrowed_stability import score
from review_foreign_component_translation import independent_counts
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file

EVENTS = ['other', 'K', 'UBB', 'HBP', '1B', '2B', '3B', 'HR']
AMENDMENT = ROOT / 'docs/hitter-foreign-borrowed-stability-scoring-amendment.md'
RESULT = ROOT / 'docs/hitter-foreign-borrowed-stability-result.md'
WALK = ROOT / 'docs/hitter-foreign-borrowed-stability-player-review.md'


def fixed_cluster_intervals(rows, draws=2000, seed=84):
    """Retain original equal-origin row weights; verify each draw two ways."""
    sizes = Counter(r['origin_year'] for r in rows)
    weights = np.array([1 / (len(sizes) * sizes[r['origin_year']]) for r in rows])
    people = sorted({r['player_id'] for r in rows})
    index = {p: j for j, p in enumerate(people)}
    groups = np.array([index[r['player_id']] for r in rows])
    mass = np.bincount(groups, weights=weights, minlength=len(people))
    rng = np.random.default_rng(seed)
    # Same paired cluster draws for all losses.
    multiplicities = np.array([np.bincount(rng.integers(len(people), size=len(people)),
        minlength=len(people)) for _ in range(draws)])
    result = {}
    for loss in ['logloss', 'brier', 'K_sq', 'HR_sq']:
        differences = np.array([r['borrowed_' + loss] - r['affine_' + loss] for r in rows])
        sums = np.bincount(groups, weights=weights * differences, minlength=len(people))
        aggregated = (multiplicities @ sums) / (multiplicities @ mass)
        row_level = []
        for counts in multiplicities:
            w = weights * counts[groups]
            row_level.append(np.dot(w, differences) / w.sum())
        assert np.allclose(aggregated, row_level, rtol=0, atol=1e-12)
        point = np.dot(weights, differences) / weights.sum()
        result[loss] = dict(delta=float(point),
            nominal_player_cluster_interval=np.quantile(aggregated, [.025, .975]).tolist(),
            independently_checked_draws=draws,
            shared_season_selection_and_repeated_development_uncertainty_not_covered=True)
    return dict(intervals=result, people=len(people), rows=len(rows), seed=seed,
        draws=draws, original_origin_sizes=dict(sizes), fixed_original_row_weights=True,
        row_level_and_player_aggregate_resamples_agree=True)


def prepare():
    assert not (OUT / 'review-supplement.json').exists(), 'Preserve completed supplement'
    review = read(OUT / 'independent-review.json'); verify(review['hashes'])
    receipt = read(OUT / 'fit-receipt.json'); verify(receipt['source_hashes']); verify(receipt['artifact_hashes'])
    assert AMENDMENT.exists(), 'Seal scoring amendment before corrected computation'
    cohort = read(OUT / 'scored-component-cohort.json')['rows']
    active = [r for r in cohort if 'borrowed_logloss' in r]
    corrected = fixed_cluster_intervals(active)
    original = read(OUT / 'scores.json')['all_supported_active']
    assert score(active) == original
    for loss in ['logloss', 'brier']:
        assert abs(corrected['intervals'][loss]['delta'] -
            (original['borrowed'][loss] - original['affine'][loss])) < 1e-12
    inputs = {r['candidate_key']: r for r in read(INPUTS / 'origin-inputs.json')['rows']}
    models = {m['fit_key']: m for m in read(OUT / 'fits.json')['fits']}
    profiles = {(p['player_id'], p['origin_year']): p for p in read(OUT / 'profiles.json')['profiles']
        if p['outer_fold'] == player_fold(p['player_id'])}
    rows = pl.read_parquet(DOMESTIC).filter(
        (pl.col('season') <= 2025) & (pl.col('bucket') == 'MLB')).to_dicts()
    annual = defaultdict(lambda: np.zeros(8))
    for r, counts in zip(rows, independent_counts(rows, True)):
        annual[r['player_id'], r['season']] += counts

    def history(pid, origin):
        return [dict(season=y, counts=annual[pid, y].tolist(), pa=int(annual[pid, y].sum()))
            for y in range(origin - 2, origin + 1) if (pid, y) in annual]

    def peer_coordinates(p):
        part = max(p['leagues'], key=lambda x: x['recency_weighted_exposure'])
        own = part['own_pooled_probability']
        age = inputs[p['candidate_key']]['age_at_information_date']
        return part['league'], age, p['raw_recent_foreign_pa'], own[1], own[7]

    def peers(p):
        league, age, pa, krate, hrate = peer_coordinates(p)
        if age is None:
            return dict(status='missing_focal_age', rows=[])
        candidates = []
        for (pid, origin), q in profiles.items():
            if origin != p['origin_year'] or pid == p['player_id'] or not q['leagues']:
                continue
            l, a, n, k, h = peer_coordinates(q)
            if l != league or a is None:
                continue
            distance = abs(a - age)/5 + abs(np.log1p(n)-np.log1p(pa)) + abs(k-krate)/.1 + abs(h-hrate)/.03
            candidates.append(dict(player_id=pid, origin_year=origin, league=l, age=a,
                source_pa=n, pooled_K=k, pooled_HR=h, distance=float(distance),
                dated_role_hint=inputs[q['candidate_key']]['dated_role_hint']))
        selected = sorted(candidates, key=lambda x: (x['distance'], x['player_id']))[:3]
        # Selection is complete before next-year counts are consulted.
        for q in selected:
            c = annual.get((q['player_id'], q['origin_year']+1), np.zeros(8))
            q.update(next_MLB_PA=int(c.sum()), next_MLB_probability=(c/c.sum()).tolist() if c.sum() else None)
        return dict(rule='same origin and dominant foreign league; nearest age/5 + log exposure + K/.1 + HR/.03; stable ID ties; no job matching', rows=selected)

    def mechanics(p):
        if p is None:
            return None
        model = models[p['fit_key']]
        pieces = []
        for part in p['leagues']:
            league = part['league']
            z = np.log(np.array(p['MLB_reference']))
            z -= z.mean()
            for j, event in enumerate(EVENTS):
                z[j] += model['domestic_intercepts'][j] + model['foreign_offsets'][league][j] + model['domestic_slopes'][j] * part['source_relative_clr'][j]
            q = np.exp(z-z.max()); q /= q.sum()
            if part['mover_people']:
                assert np.allclose(q, part['translated_probability'], rtol=0, atol=1e-12)
            pieces.append(dict(league=league, source_relative_clr=part['source_relative_clr'],
                domestic_intercepts=model['domestic_intercepts'], domestic_slopes=model['domestic_slopes'],
                foreign_offsets=model['foreign_offsets'][league], MLB_reference=p['MLB_reference'],
                output_probability=part['translated_probability'], foreign_mover_people=part['mover_people'],
                domestic_people=model['domestic_people'], domestic_profile_support=model['domestic_profile_support'],
                domestic_coordinate_extrapolation=part['domestic_coordinate_extrapolation']))
        return pieces

    saved = read(OUT / 'reviewed-cases.json')
    fixed = [dict(name=c['name'], player_id=c['player_id'], origin_year=c['origin_year'],
        source_input=c['source_input'], source_case_reference='reviewed-cases.json',
        actual_origin_MLB_history=history(c['player_id'], c['origin_year']),
        borrowed_probability=c['borrowed_profile']['translated_probability'] if c['borrowed_profile'] else None,
        affine_probability=c['repaired_profile']['translated_probability'] if c['repaired_profile'] else None,
        actual_next_MLB_PA=c['observed_next_MLB_PA'], actual_probability=c['observed_next_MLB_probability'],
        mechanics=mechanics(c['borrowed_profile']), peers=c['origin_only_peers'],
        unchanged_saved_forecast=c['unchanged_saved_forecast']) for c in saved['fixed_cases']]
    selected = []
    for category, r in saved['score_selected_cases'].items():
        p = r['borrowed_profile']
        selected.append(dict(category=category, name=r['player_name'], player_id=r['player_id'],
            origin_year=r['origin_year'], source_input=inputs[p['candidate_key']],
            actual_origin_MLB_history=history(r['player_id'], r['origin_year']),
            affine_probability=r['affine_profile']['translated_probability'],
            borrowed_probability=p['translated_probability'], actual_probability=r['actual_probability'],
            actual_next_MLB_PA=r['next_pa'], logloss_delta=r['borrowed_logloss']-r['affine_logloss'],
            source_profile=p, mechanics=mechanics(p), origin_only_peers=peers(p),
            unchanged_current_PA=r['unchanged_current_pa'], new_full_hitter_forecast=None))
    role_counts = Counter(inputs[r['borrowed_profile']['candidate_key']]['dated_role_hint'] for r in cohort)
    save(OUT / 'intervals-fixed-origin-weights.json', corrected)
    sensitivity = score([r for r in active if r['next_pa'] >= 100])
    supplement = dict(status='diagnostics_ready_manual_pending', fixed_cases=fixed, selected_cases=selected,
        original_cohort=253, active_rows=28, nonarrival_rows=225, source_role_hints=dict(role_counts),
        future_100_PA_diagnostic=sensitivity, future_100_PA_diagnostic_not_primary=True,
        supported_profiles=3205-sum(p['missing_translation'] for p in read(OUT / 'profiles.json')['profiles']),
        original_intervals_preserved=True, full_hitter_forecasts_changed=False,
        corrected_intervals=corrected,
        source_hashes={**review['hashes'], str(AMENDMENT.relative_to(ROOT)): sha256_file(AMENDMENT),
            str(Path(__file__).relative_to(ROOT)): sha256_file(Path(__file__))})
    save(OUT / 'review-supplement.json', supplement)
    print(json.dumps(dict(intervals=corrected, sensitivity=sensitivity, roles=dict(role_counts))), flush=True)


def seal():
    assert not (OUT / 'final-review.json').exists(), 'Preserve final review'
    supplement = read(OUT / 'review-supplement.json'); verify(supplement['source_hashes'])
    assert RESULT.exists() and WALK.exists(), 'Manual review must precede disposition'
    text = WALK.read_text(encoding='utf8')
    for c in supplement['fixed_cases'] + supplement['selected_cases']:
        assert str(c['player_id']) in text and str(c['origin_year']) in text
    review = read(OUT / 'independent-review.json')
    receipt = read(OUT / 'fit-receipt.json'); verify(receipt['source_hashes']); verify(receipt['artifact_hashes'])
    paths = [RESULT, WALK, OUT/'review-supplement.json', OUT/'intervals-fixed-origin-weights.json',
        OUT/'independent-review.json', Path(__file__)]
    final = dict(status='review_complete_retain_for_whole_model_comparison',
        player_walkthrough_status='complete_for_component_comparison',
        primary_comparison='borrowed_stability_vs_repaired_affine_not_current_UBM_or_public_systems',
        scores=read(OUT/'scores.json'), corrected_intervals=supplement['corrected_intervals'],
        future_100_PA_diagnostic=supplement['future_100_PA_diagnostic'],
        domestic_optima_checked=review['domestic_optima_checked'],
        foreign_offset_estimates_checked=review['foreign_offset_estimates_checked'],
        profiles_reconstructed=review['profiles_reconstructed'], tests=review['tests'],
        protected_freeze=review['protected_freeze'], source_role_hints=supplement['source_role_hints'],
        full_hitter_forecasts_changed=False, deployment_approved=False, whole_model_gain_established=False,
        goal_achieved=False, source_hashes=receipt['source_hashes'],
        artifact_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in paths})
    save(OUT/'final-review.json', final)
    evidence = ROOT/'reports/model-evidence/foreign-borrowed-stability'
    save(evidence/'final-review.json', final)
    # Publish bounded case comparisons, not bulk licensed source exports or calibration rows.
    compact = [dict(name=c['name'], player_id=c['player_id'], origin_year=c['origin_year'],
        affine_probability=c['affine_probability'], borrowed_probability=c['borrowed_probability'],
        actual_probability=c['actual_probability'], actual_next_MLB_PA=c['actual_next_MLB_PA'],
        category=c.get('category', 'fixed_before_fit')) for c in supplement['fixed_cases']+supplement['selected_cases']]
    save(evidence/'case-comparison.json', dict(event_order=EVENTS, cases=compact,
        readable_review=str(WALK.relative_to(ROOT)), private_supplement_sha256=sha256_file(OUT/'review-supplement.json')))
    print(json.dumps(dict(review='complete', deployment=False, whole_model_gain=False)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['prepare', 'seal'])
    args = parser.parse_args()
    prepare() if args.action == 'prepare' else seal()
