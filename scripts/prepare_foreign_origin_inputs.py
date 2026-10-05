"""Join reviewed foreign history and dated role evidence without new forecasts."""
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import sys

import polars as pl

import audit_foreign_mover_support_v2 as audit
from universal_baseball.foreign_mover_support import aggregate_foreign
from universal_baseball.foreign_origin_inputs import materialize_inputs, qualify_role
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file

ROOT = audit.ROOT
OUT = ROOT / 'reports/generated/foreign-origin-inputs'
SUPPORT = ROOT / 'reports/generated/foreign-mover-support-v2-npb-kbo'
ROLES = ROOT / 'reports/generated/hitter-preseason-population-source/reviewed-role-hints.parquet'
EVIDENCE = ROOT / 'reports/model-evidence/foreign-origin-inputs'
CONTRACT = ROOT / 'docs/hitter-foreign-role-input-amendment.md'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def main():
    assert not OUT.exists(), 'Inspect existing preparation; do not overwrite it'
    reviewed = read(SUPPORT / 'independent-review.json')
    for path, expected in reviewed['hashes'].items():
        assert sha256_file(ROOT / path) == expected, path
    final = read(ROOT / 'reports/generated/hitter-preseason-population-source/final-review.json')
    assert final['player_walkthrough_status'] == 'complete_for_source'
    for name, expected in final['artifact_hashes'].items():
        assert sha256_file(ROOT / 'reports/model-evidence/hitter-preseason-population-source' / name) == expected, name
    paths = [CONTRACT, audit.CONTRACT, audit.ORIGINAL_CONTRACT, Path(__file__),
             ROOT / 'src/universal_baseball/foreign_origin_inputs.py', audit.NPB, audit.KBO,
             audit.POPULATION, audit.DOMESTIC, ROLES, audit.ANCHOR, SUPPORT / 'pairs.json',
             SUPPORT / 'independent-review.json', ROOT / 'reports/generated/kbo-identity-overlay/review.json']
    hashes = {str(p.relative_to(ROOT)): sha256_file(p) for p in paths}
    population = pl.read_parquet(audit.POPULATION).to_dicts()
    hints = pl.read_parquet(ROLES).to_dicts()
    domestic = pl.read_parquet(audit.DOMESTIC).filter(pl.col('season') <= 2024).to_dicts()
    annual = aggregate_foreign(pl.read_parquet(audit.NPB).to_dicts(), 'NPB')
    annual += aggregate_foreign(pl.read_parquet(audit.KBO).to_dicts(), 'KBO')
    inputs = materialize_inputs(population, annual, domestic, hints)
    assert len({r['candidate_key'] for r in inputs}) == len(inputs)
    # Adversarial later foreign/domestic data cannot change any origin input.
    corrupt = [dict(r, pa=999999, hr=99999, season=2099) for r in annual[:2]]
    future = [dict(domestic[0], season=2099, plate_appearances=999999)]
    assert inputs == materialize_inputs(population, annual + corrupt, domestic + future, hints)
    for r in inputs:
        assert r['recent_foreign_pa'] > 0 and not r['MLB_translation_fitted']
        assert r['information_date'][:4] == str(r['origin_year'] + 1)
        assert all(g['season'] <= r['origin_year'] for g in r['foreign_history_counts'].values())
    OUT.mkdir(parents=True)
    audit.save(OUT / 'membership-seal.json', dict(candidate_keys=[r['candidate_key'] for r in inputs],
        population_source_rows=len(population), original_forecast_membership_changed=False,
        source_hashes=hashes, future_MLB_outcomes_used=False, forecast_eligibility_approved=False))
    audit.save(OUT / 'origin-inputs.json', dict(rows=inputs, raw_counts_not_MLB_translations=True))
    pairs = read(SUPPORT / 'pairs.json')['pairs']
    qualified = []
    for p in pairs:
        evidence = qualify_role(p, domestic, population, hints)
        qualified.append(dict(**p, role_evidence=evidence))
    audit.save(OUT / 'pair-role-evidence.json', dict(pairs=qualified, original_pair_membership_unchanged=True))
    groups = defaultdict(list)
    for origin in [2016, 2017, 2018, 2021, 2022, 2023, 2024]:
        for fold in range(5):
            for p in qualified:
                if p['through_year'] <= origin and p['fold'] != fold and not p['domestic_2020_exception']:
                    e = p['role_evidence']
                    key = (origin, fold, p['minimum_pa'], p['mechanism'], p['a'], p['b'], e['qualified_role'])
                    groups[key].append(p)
    support = [dict(origin=k[0], fold=k[1], minimum_pa=k[2], mechanism=k[3], a=k[4], b=k[5],
                    role=k[6], pairs=len(v), people=len({p['player_id'] for p in v})) for k, v in sorted(groups.items())]
    audit.save(OUT / 'qualified-fold-support.json', dict(groups=support))
    saved = pl.read_parquet(audit.ANCHOR, columns=['player_id', 'origin_year', 'player_name',
        'baseline_pa', 'baseline_p', 'baseline_conditional_pa', 'combined_rate', 'combined_value'])
    cases = []
    lookup = {(r['player_id'], r['origin_year']): r for r in inputs}
    original_cases = read(SUPPORT / 'cases.json')['cases']
    for c in original_cases:
        key = (c['player_id'], c['origin_year'])
        # Fukudome before 2008 is outside the 2012+ preseason population; preserve that limit.
        o = lookup.get(key)
        pool = [p for p in qualified if p['through_year'] <= c['origin_year']
                and p['fold'] != player_fold(c['player_id']) and p['minimum_pa'] == 30
                and not p['domestic_2020_exception'] and p['role_evidence']['supported_hitter']
                and p['mechanism'] == 'consecutive_season' and p['a'] == c['league'] and p['b'] == 'MLB']
        old = saved.filter((pl.col('player_id') == c['player_id']) & (pl.col('origin_year') == c['origin_year'])).to_dicts()
        cases.append(dict(name=c['name'], player_id=c['player_id'], origin_year=c['origin_year'],
            league=c['league'], origin_inputs=o, earlier_source_review=str(SUPPORT / 'player-walkthrough.md'),
            recent_source_counts=c['recent_counts'], origin_only_peers=c['origin_only_peers'],
            raw_role_direct_people=c['support']['direct_hitter_mover_people'],
            qualified_role_direct_people=len({p['player_id'] for p in pool}),
            qualified_direct_player_ids=sorted({p['player_id'] for p in pool}),
            unchanged_saved_forecast=old, new_forecast=None, realized_MLB_outcomes_used=False))
    audit.save(OUT / 'reviewed-cases.json', dict(cases=cases, player_walkthrough_status='complete_for_inputs_only'))
    lines = ['# Foreign professional model inputs and player review', '',
             'This is an additive model-input dataset, not new projections. Raw NPB/KBO production is separated from MLB job context and verified age. Every original source/forecast row remains; only a matched, future-blind subset receives foreign inputs. Missing other-league identity/history is not a certified zero.', '']
    for c in cases:
        lines += [f"## {c['name']} before {c['origin_year'] + 1}", '',
                  f"Raw source-role support: {c['raw_role_direct_people']} distinct direct hitter movers. Supplementing unknown metadata with dated hitter hints: {c['qualified_role_direct_people']}. Whole-player held-out and chronological restrictions remain unchanged. Sparse support is not cured merely by a role hint.", '',
                  'New actual origin inputs: ' + json.dumps(c['origin_inputs'], ensure_ascii=False) + '.', '',
                  'Unchanged saved forecast: ' + json.dumps(c['unchanged_saved_forecast'], ensure_ascii=False) + '.', '',
                  'No new forecast or MLB error is invented. The inputs distinguish a professional history from an empty domestic window; they do not guarantee an MLB job, health or a league-equivalent hitting rate.', '',
                  'Origin-only foreign exposure/age/contact/power comparisons: ' + json.dumps(c['origin_only_peers'], ensure_ascii=False) + '.', '']
    # Ordinary cases already selected before this overlay; retain their identity and source selection.
    ordinary = read(SUPPORT / 'ordinary-source-cases.json')['cases']
    lines += ['## Ordinary and unresolved cases', '', json.dumps(ordinary, ensure_ascii=False), '',
              'These existing low-ID source controls remain, without an assumed MLB job. A linked MLB identifier is not an arrival probability. The earlier full source reviews retain unmapped and no-MLB-ID cases.', '']
    (OUT / 'player-walkthrough.md').write_text('\n'.join(lines) + '\n', encoding='utf8', newline='\n')
    tests = subprocess.run([sys.executable, '-m', 'pytest', 'tests/test_foreign_origin_inputs.py', '-q'], cwd=ROOT, capture_output=True, text=True)
    assert tests.returncode == 0, tests.stdout + tests.stderr
    freeze = subprocess.run([sys.executable, 'scripts/verify_hitter_full_2026_freeze.py'], cwd=ROOT, capture_output=True, text=True)
    assert freeze.returncode == 0, freeze.stdout + freeze.stderr
    overall = []
    for league in ['NPB', 'KBO']:
        pool = [p for p in qualified if p['through_year'] <= 2024 and not p['domestic_2020_exception']
                and p['minimum_pa'] == 30 and p['a'] == league and p['b'] == 'MLB'
                and p['mechanism'] == 'consecutive_season' and p['role_evidence']['supported_hitter']]
        overall.append(dict(league=league, direct_people=len({p['player_id'] for p in pool}), pairs=len(pool)))
    report = dict(origin_inputs=len(inputs), distinct_players=len({r['player_id'] for r in inputs}),
        original_source_origins=sum(r['original_source_origin'] for r in inputs),
        added_source_origins=sum(not r['original_source_origin'] for r in inputs),
        original_source_population_preserved=len(population), existing_forecast_rows_preserved=saved.height,
        pair_roles_supplemented=sum(p['domestic_role'] == 'unknown' and p['role_evidence']['qualified_role'] != 'unknown' for p in qualified),
        overall_direct_support=overall, qualified_fold_groups=len(support), cases=len(cases),
        future_mutation_invariant=True, new_fits=0, forecasts_changed=False, eligibility_approved=False,
        player_walkthrough_status='complete_for_inputs_only', independent_reconstruction_status='pending',
        tests=tests.stdout, protected_freeze=json.loads(freeze.stdout), source_hashes=hashes,
        output_hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in OUT.iterdir()})
    audit.save(OUT / 'report.json', report)
    audit.save(EVIDENCE / 'report.json', report)
    (EVIDENCE / 'player-walkthrough.md').write_bytes((OUT / 'player-walkthrough.md').read_bytes())
    print(json.dumps({k: v for k, v in report.items() if k not in ['source_hashes', 'output_hashes']}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
