"""Reconstruct mover membership independently and audit all source-origin profiles."""
from collections import defaultdict
from datetime import date
import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file
import audit_foreign_mover_support as audit

ROOT = audit.ROOT


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--npb-only', action='store_true')
    args = parser.parse_args()
    label = 'npb' if args.npb_only else 'npb-kbo'
    out = ROOT / ('reports/generated/foreign-mover-support-' + label)
    assert not (out / 'independent-review.json').exists(), 'Preserve completed review'
    report = read(out / 'report.json')
    for mapping in [report['source_hashes'], report['output_hashes']]:
        for path, expected in mapping.items():
            assert sha256_file(ROOT / path) == expected, path
    npb_review = read(audit.NPB.parent / 'review.json')
    for path, expected in npb_review['hashes'].items():
        assert sha256_file(ROOT / path) == expected, path
    if not args.npb_only:
        identity = read(audit.KBO.parent / 'review.json')
        assert identity['player_walkthrough_status'] == 'complete_for_identity_source'
        for path, expected in identity['hashes'].items():
            assert sha256_file(ROOT / path) == expected, path
    source = {'NPB': pl.read_parquet(audit.NPB).to_dicts()}
    if not args.npb_only:
        source['KBO'] = pl.read_parquet(audit.KBO).to_dicts()
    sums = {}; names = {}; positions = defaultdict(set); birthdays = {}
    domestic = pl.read_parquet(audit.DOMESTIC).filter((pl.col('season') <= 2024) & pl.col('bucket').is_in(['MLB', 'AAA']))
    mapping = dict(pa='plate_appearances', ab='at_bats', hits='hits', doubles='doubles', triples='triples',
                   hr='home_runs', bb='base_on_balls', ibb='intentional_walks', hbp='hit_by_pitch', so='strike_outs', sf='sac_flies')
    for r in domestic.iter_rows(named=True):
        key = (r['player_id'], r['season'], r['bucket'])
        counts = sums.setdefault(key, {c: 0 for c in audit.COUNTS})
        for c, field in mapping.items():
            counts[c] += r[field]
        positions[key].add(r['position'])
        names[key] = r['player_name']
    for league, rows in source.items():
        for r in rows:
            assert r['season'] <= 2024
            if r['player_id'] is None:
                continue
            key = (r['player_id'], r['season'], league)
            counts = sums.setdefault(key, {c: 0 for c in audit.COUNTS})
            for c in audit.COUNTS:
                counts[c] += r[c]
            if key in birthdays:
                assert birthdays[key] == r['birth_date']
            birthdays[key] = r['birth_date']
            names[key] = r.get('english_name') or r.get('player_name_ja') or r.get('player_name_ko')
    expected = set()
    def domestic_role(key):
        # X is genuinely Unknown in archived MLB records, not an alias for Hitter.
        codes = positions[key]
        h = bool(codes & ({str(i) for i in range(2, 11)} | {'I', 'O', 'Y'})); p = '1' in codes
        return 'mixed' if h and p else 'hitter' if h else 'pitcher' if p else 'unknown'
    for (pid, year, league), counts in sums.items():
        if league not in source:
            continue
        for domestic_league in ['MLB', 'AAA']:
            for minimum in [30, 100]:
                if counts['pa'] < minimum:
                    continue
                same = (pid, year, domestic_league)
                if same in sums and sums[same]['pa'] >= minimum:
                    expected.add((pid, year, year, league, domestic_league, 'same_season', minimum, domestic_role(same)))
                later = (pid, year + 1, domestic_league)
                if later in sums and sums[later]['pa'] >= minimum:
                    expected.add((pid, year, year + 1, league, domestic_league, 'consecutive_season', minimum, domestic_role(later)))
                earlier = (pid, year - 1, domestic_league)
                if earlier in sums and sums[earlier]['pa'] >= minimum:
                    expected.add((pid, year - 1, year, domestic_league, league, 'consecutive_season', minimum, domestic_role(earlier)))
    pairs = read(out / 'pairs.json')['pairs']
    observed = {(p['player_id'], p['from_year'], p['through_year'], p['a'], p['b'], p['mechanism'], p['minimum_pa'], p['domestic_role']) for p in pairs}
    assert len(observed) == len(pairs) and observed == expected
    for p in pairs:
        assert p['from_counts'] == sums[p['player_id'], p['from_year'], p['a']]
        assert p['to_counts'] == sums[p['player_id'], p['through_year'], p['b']]
        assert p['fold'] == player_fold(p['player_id'])
        assert p['touches_2020'] == (2020 in [p['from_year'], p['through_year']])
    for s in report['folds']:
        eligible = [p for p in pairs if p['through_year'] <= s['cutoff'] and p['fold'] != s['held_fold']
                    and p['minimum_pa'] == s['minimum_pa'] and not p['touches_2020']
                    and (p['a'], p['b'], p['mechanism'], p['domestic_role']) == (s['a'], s['b'], s['mechanism'], s['domestic_role'])]
        assert len(eligible) == s['pairs']
        assert sorted({p['player_id'] for p in eligible}) == s['player_ids']
    population = pl.read_parquet(audit.POPULATION)
    profile_rows = []
    for candidate in population.iter_rows(named=True):
        pid, origin = candidate['player_id'], candidate['origin_year']
        if origin not in [2016, 2017, 2018, 2021, 2022, 2023, 2024]:
            continue
        for league in source:
            recent = [(key, value) for key, value in sums.items() if key[0] == pid and key[2] == league and origin - 2 <= key[1] <= origin]
            total = sum(value['pa'] for _, value in recent)
            if not total:
                continue
            birth = next((birthdays[key] for key, _ in recent if birthdays[key]), None)
            age = (date.fromisoformat(candidate['information_date']) - date.fromisoformat(birth)).days / 365.2425 if birth else None
            age_band = 'unknown' if age is None else 'under25' if age < 25 else '25to29' if age < 30 else '30to34' if age < 35 else '35plus'
            k = sum(value['so'] for _, value in recent) / total
            hr = sum(value['hr'] for _, value in recent) / total
            contact = 'lowK' if k < .15 else 'middleK' if k < .25 else 'highK'
            power = 'highHR' if hr >= .04 else 'lowerHR'
            pool = [p for p in pairs if p['a'] == league and p['b'] == 'MLB'
                    and p['mechanism'] == 'consecutive_season' and p['minimum_pa'] == 30
                    and p['through_year'] <= origin and p['fold'] != player_fold(pid)
                    and not p['touches_2020'] and p['domestic_role'] in {'hitter', 'mixed'}]
            exact = [p for p in pool if p['foreign_age_band'] == age_band and
                     p['foreign_contact_band'] == contact and p['foreign_power_band'] == power]
            ids = {p['player_id'] for p in pool}; matches = {p['player_id'] for p in exact}
            assert pid not in ids
            profile_rows.append(dict(candidate_key=candidate['candidate_key'], player_id=pid, origin=origin,
                league=league, information_date=candidate['information_date'], fold=player_fold(pid),
                existing_model_origin=candidate['current_model_origin'], role_hint=candidate['role_status'],
                positive_MLB_context=candidate['origin_has_positive_context'], foreign_pa=total,
                foreign_age=age, age_band=age_band, contact_band=contact, power_band=power,
                direct_training_people=len(ids), age_contact_power_people=len(matches),
                source_candidate_not_approved_eligibility=True))
    profiles = pl.DataFrame(profile_rows)
    profiles.write_parquet(out / 'all-source-origin-profile-support.parquet')
    summary = profiles.group_by('origin', 'league', 'existing_model_origin', 'role_hint').agg(
        pl.len().alias('rows'), pl.col('direct_training_people').min().alias('least_direct_people'),
        pl.col('direct_training_people').max().alias('most_direct_people'),
        (pl.col('age_contact_power_people') == 0).sum().alias('zero_profile_support_rows')).sort('origin', 'league', 'existing_model_origin', 'role_hint').to_dicts()
    # A low-ID older overseas hitter provides a contrary ordinary case, not another MLB success.
    fixed_ids = {pid for pid, _, _, _ in audit.FIXED}
    ordinary_keys = sorted(key for key, count in sums.items() if key[1] == 2024 and key[2] in source
                           and key[0] not in fixed_ids and count['pa'] >= 100)
    ordinary = []
    for league in source:
        key = next(k for k in ordinary_keys if k[2] == league)
        ordinary.append(dict(player_id=key[0], origin=2024, league=league, name=names[key],
                             source_counts=sums[key], birth_date=birthdays[key],
                             selection='lowest_MLBAM_known_source_ID_100PA_2024_not_fixed',
                             selection_uses_MLB_outcomes=False, candidate_forecast=None,
                             interpretation='Source identity and production do not establish a dated MLB job or historical role. No new forecast or accuracy result exists.'))
    audit.save(out / 'ordinary-source-cases.json', dict(cases=ordinary))
    result = dict(independent_pair_membership_checks=len(pairs), independent_pair_count_fields=len(pairs) * 22,
                  verified_fold_groups=len(report['folds']), all_source_origin_profiles=profiles.height,
                  profiles=summary, ordinary_cases=ordinary, player_walkthrough_status='complete_for_support_only',
                  forecasts_changed=False, new_fits=0, historical_role_unknowns_retained=True,
                  translation_approved=False, universal_forecast_claim_approved=False,
                  reviewer_sha256=sha256_file(Path(__file__)),
                  hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in [out / 'report.json', out / 'pairs.json',
                       out / 'all-source-origin-profile-support.parquet', out / 'ordinary-source-cases.json']})
    audit.save(out / 'independent-review.json', result)
    evidence = ROOT / ('reports/model-evidence/foreign-mover-support-' + label)
    audit.save(evidence / 'independent-review.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ['hashes', 'profiles', 'ordinary_cases']}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
