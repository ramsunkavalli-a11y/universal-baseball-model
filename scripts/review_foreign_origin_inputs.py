"""Reconstruct the additive foreign inputs independently, without fitting a model."""
from collections import defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/foreign-origin-inputs'
PUBLIC = ROOT / 'reports/model-evidence/foreign-origin-inputs'
FIELDS = ('pa', 'ab', 'hits', 'doubles', 'triples', 'hr', 'bb', 'ibb', 'hbp', 'so', 'sf')
HITTER = {str(n) for n in range(2, 11)} | {'O', 'I', 'Y'}


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def fold(pid):
    # Repeat the published split rule, not the production helper.
    return int.from_bytes(hashlib.sha256(f'ubm-prospect-v8:{pid}'.encode()).digest()[:8], 'big') % 5


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8', newline='\n')


def main():
    assert not (OUT / 'independent-review.json').exists(), 'Preserve completed review'
    report = read(OUT / 'report.json')
    for section in ('source_hashes', 'output_hashes'):
        for path, expected in report[section].items():
            assert sha256_file(ROOT / path) == expected, path
    population_rows = pl.read_parquet(ROOT / 'reports/generated/hitter-preseason-population-source/population.parquet').to_dicts()
    population = {(p['player_id'], p['origin_year']): p for p in population_rows}
    assert len(population) == len(population_rows) == report['original_source_population_preserved']
    hints = {(p['player_id'], p['origin_year']): p['reviewed_role_hint'] for p in
             pl.read_parquet(ROOT / 'reports/generated/hitter-preseason-population-source/reviewed-role-hints.parquet').to_dicts()}
    histories = defaultdict(list)
    for league, source in [('NPB', 'npb-hitting-history'), ('KBO', 'kbo-identity-overlay')]:
        rows = pl.read_parquet(ROOT / f'reports/generated/{source}/reviewed-batting.parquet')
        assert rows['season'].max() <= 2024
        for r in rows.iter_rows(named=True):
            if r['player_id'] is not None:
                histories[r['player_id']].append(dict(r, league=league))
    domestic = defaultdict(list)
    for r in pl.read_parquet(ROOT / 'reports/generated/practical-hitter-v31/dated-stints.parquet').iter_rows(named=True):
        if r['season'] <= 2024:
            domestic[r['player_id']].append(r)
    inputs = read(OUT / 'origin-inputs.json')['rows']
    expected_keys = set()
    for (pid, origin), p in population.items():
        if any(origin - 2 <= r['season'] <= origin and r['pa'] > 0 for r in histories[pid]):
            expected_keys.add(p['candidate_key'])
    assert {r['candidate_key'] for r in inputs} == expected_keys
    assert len(inputs) == len(expected_keys) == report['origin_inputs']
    field_checks = 0
    for r in inputs:
        pid, origin = r['player_id'], r['origin_year']
        p = population[pid, origin]
        known = [h for h in histories[pid] if h['season'] <= origin]
        recent = [h for h in known if h['season'] >= origin - 2]
        birthdays = {h['birth_date'] for h in known if h['birth_date']}
        assert len(birthdays) <= 1
        birth = next(iter(birthdays), None)
        assert r['birth_date'] == birth
        age = (date.fromisoformat(p['information_date']) - date.fromisoformat(birth)).days / 365.2425 if birth else None
        assert r['age_at_information_date'] == age
        for league in ('NPB', 'KBO'):
            for lag in range(3):
                selected = [h for h in recent if h['league'] == league and h['season'] == origin - lag]
                g = r['foreign_history_counts'][f'{league}_{lag}']
                assert g['season'] == origin - lag
                assert g['counts'] == {f: sum(h[f] for h in selected) for f in FIELDS}
                assert g['league_source_year_covered'] == (2005 <= origin - lag <= 2024)
                assert g['player_identity_and_stat_observed'] == bool(selected)
                assert g['absent_group_is_not_certified_zero'] == (not bool(selected))
                field_checks += len(FIELDS)
        assert r['observed_foreign_history_pa'] == sum(h['pa'] for h in known)
        assert r['recent_foreign_pa'] == sum(h['pa'] for h in recent)
        recent_domestic = [h for h in domestic[pid] if origin - 2 <= h['season'] <= origin]
        assert r['recent_observed_domestic_pa'] == sum(h['plate_appearances'] for h in recent_domestic)
        assert r['recent_observed_MLB_pa'] == sum(h['plate_appearances'] for h in recent_domestic if h['sport_id'] == 1)
        for field, original in [('information_date', 'information_date'), ('original_source_origin', 'current_model_origin'),
                                ('roster_hitter_codes', 'roster_position_codes'), ('returned_40man', 'returned_40man'),
                                ('roster_team_ids', 'roster_team_ids'), ('positive_MLB_context', 'origin_has_positive_context')]:
            assert r[field] == p[original]
        assert r['dated_role_hint'] == hints.get((pid, origin), 'unknown')
        assert not any(r[f] for f in ('forecast_eligibility_approved', 'MLB_translation_fitted',
                                     'foreign_role_fully_qualified', 'historical_rights_fully_verified'))
    pairs = read(OUT / 'pair-role-evidence.json')['pairs']
    original_pairs = read(ROOT / 'reports/generated/foreign-mover-support-v2-npb-kbo/pairs.json')['pairs']
    assert [dict((k, v) for k, v in p.items() if k != 'role_evidence') for p in pairs] == original_pairs
    reconstructed = []
    for p in pairs:
        pid, year = p['player_id'], p['domestic_year']
        codes = {s['position'] for s in domestic[pid] if s['season'] == year and s['plate_appearances'] > 0}
        context = population.get((pid, year - 1))
        hint = hints.get((pid, year - 1), 'unknown') if context else 'unknown'
        assert context is None or int(context['information_date'][:4]) <= year
        h = bool(codes & HITTER) or hint in {'hitter_hint', 'two_way_hint', 'two_way_or_conflicting_hints'}
        pitcher = '1' in codes or hint == 'pitcher_hint'
        role = p['domestic_role']
        basis = 'recorded_domestic_side_role'
        if role == 'unknown':
            role = 'conflicting_hints' if h and pitcher else 'hitter_hint' if h else 'pitcher_hint' if pitcher else 'unknown'
            basis = 'same_year_domestic_stints_or_dated_preseason_hint' if role != 'unknown' else 'unresolved'
        e = dict(original_role=p['domestic_role'], qualified_role=role, role_basis=basis,
                 dated_preseason_hint=hint, dated_information_date=context['information_date'] if context else None,
                 same_year_domestic_positions=sorted(codes), supported_hitter=role in {'hitter', 'mixed', 'hitter_hint'},
                 full_historical_position_qualified=False)
        assert p['role_evidence'] == e
        reconstructed.append(dict(p, role_evidence=e))
    grouped = defaultdict(list)
    for origin in (2016, 2017, 2018, 2021, 2022, 2023, 2024):
        for held in range(5):
            for p in reconstructed:
                assert p['fold'] == fold(p['player_id'])
                if p['through_year'] <= origin and p['fold'] != held and not p['domestic_2020_exception']:
                    key = (origin, held, p['minimum_pa'], p['mechanism'], p['a'], p['b'], p['role_evidence']['qualified_role'])
                    grouped[key].append(p)
    saved_groups = read(OUT / 'qualified-fold-support.json')['groups']
    expected_groups = [dict(origin=k[0], fold=k[1], minimum_pa=k[2], mechanism=k[3], a=k[4], b=k[5],
                            role=k[6], pairs=len(v), people=len({p['player_id'] for p in v})) for k, v in sorted(grouped.items())]
    assert saved_groups == expected_groups
    cases = read(OUT / 'reviewed-cases.json')['cases']
    lookup = {(r['player_id'], r['origin_year']): r for r in inputs}
    forecasts = pl.read_parquet(ROOT / 'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet',
        columns=['player_id', 'origin_year', 'player_name', 'baseline_pa', 'baseline_p', 'baseline_conditional_pa', 'combined_rate', 'combined_value'])
    assert forecasts.height == report['existing_forecast_rows_preserved'] == 30506
    for c in cases:
        pid, origin = c['player_id'], c['origin_year']
        assert c['origin_inputs'] == lookup.get((pid, origin))
        pool = [p for p in reconstructed if p['through_year'] <= origin and p['fold'] != fold(pid)
                and p['minimum_pa'] == 30 and not p['domestic_2020_exception']
                and p['role_evidence']['supported_hitter'] and p['mechanism'] == 'consecutive_season'
                and p['a'] == c['league'] and p['b'] == 'MLB']
        ids = sorted({p['player_id'] for p in pool})
        assert c['qualified_direct_player_ids'] == ids and pid not in ids
        assert c['qualified_role_direct_people'] == len(ids)
        assert c['unchanged_saved_forecast'] == forecasts.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == origin)).to_dicts()
        assert c['new_forecast'] is None and not c['realized_MLB_outcomes_used']
    # The Kim example must retain a normal 2021 MLB season and qualify only its unknown role.
    kim = [p for p in reconstructed if p['player_id'] == 673490 and p['a'] == 'KBO' and p['b'] == 'MLB'
           and p['from_year'] == 2020 and p['through_year'] == 2021 and p['minimum_pa'] == 30]
    assert len(kim) == 1
    assert not kim[0]['domestic_2020_exception'] and kim[0]['domestic_role'] == 'unknown'
    assert kim[0]['role_evidence']['supported_hitter'] and kim[0]['role_evidence']['dated_information_date'].startswith('2021-')
    result = dict(status='source_reconstruction_complete', origin_inputs=len(inputs), count_fields_reconstructed=field_checks,
        pair_role_checks=len(pairs), qualified_fold_groups=len(saved_groups), player_cases=len(cases),
        dated_Kim_role_check=True, original_population_and_forecast_preserved=True,
        player_walkthrough_status='complete_for_inputs_only', forecasts_changed=False, new_fits=0,
        translation_approved=False, eligibility_approved=False, predictive_improvement_established=False,
        reviewer_sha256=sha256_file(Path(__file__)),
        hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in [OUT / 'report.json', OUT / 'origin-inputs.json',
            OUT / 'pair-role-evidence.json', OUT / 'qualified-fold-support.json', OUT / 'reviewed-cases.json']})
    save(OUT / 'independent-review.json', result)
    save(PUBLIC / 'independent-review.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'hashes'}), flush=True)


if __name__ == '__main__':
    main()
