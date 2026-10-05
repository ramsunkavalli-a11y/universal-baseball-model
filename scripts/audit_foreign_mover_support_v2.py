"""Seal real mover support and source traces before interleague forecast fitting."""
import argparse
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
import subprocess
import sys

import polars as pl

from universal_baseball.foreign_mover_support_v2 import COUNTS, aggregate_foreign, make_pairs, role, support, profile_support
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'docs/hitter-foreign-2020-support-amendment.md'
ORIGINAL_CONTRACT = ROOT / 'docs/hitter-foreign-integration-readiness-contract.md'
DOMESTIC = ROOT / 'reports/generated/practical-hitter-v31/dated-stints.parquet'
NPB = ROOT / 'reports/generated/npb-hitting-history/reviewed-batting.parquet'
KBO = ROOT / 'reports/generated/kbo-identity-overlay/reviewed-batting.parquet'
POPULATION = ROOT / 'reports/generated/hitter-preseason-population-source/population.parquet'
ANCHOR = ROOT / 'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet'
FIXED = [(660271, 2017, 'Shohei Ohtani', 'NPB'), (673548, 2021, 'Seiya Suzuki', 'NPB'),
         (807799, 2022, 'Masataka Yoshida', 'NPB'), (493120, 2007, 'Kosuke Fukudome', 'NPB'),
         (660294, 2019, 'Yoshi Tsutsugo', 'NPB'), (547887, 2012, 'Kensuke Tanaka', 'NPB'),
         (808982, 2023, 'Jung Hoo Lee', 'KBO'), (673490, 2020, 'Ha-Seong Kim', 'KBO'),
         (808975, 2024, 'Hyeseong Kim', 'KBO'), (666560, 2015, 'Byung-Ho Park', 'KBO'),
         (519346, 2015, 'Eric Thames', 'KBO')]


def save(path, obj):
    assert not path.exists(), 'Preserve completed artifact'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf8', newline='\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--npb-only', action='store_true')
    args = parser.parse_args()
    name = 'npb' if args.npb_only else 'npb-kbo'
    out = ROOT / ('reports/generated/foreign-mover-support-v2-' + name)
    assert not (out / 'report.json').exists(), 'Preserve completed support audit'
    assert not out.exists(), 'Inspect partial audit before restarting'
    paths = [CONTRACT, ORIGINAL_CONTRACT, Path(__file__), ROOT / 'src/universal_baseball/foreign_mover_support_v2.py', ROOT / 'src/universal_baseball/foreign_mover_support.py',
             ROOT / 'src/universal_baseball/post_arrival_history.py', DOMESTIC, NPB, POPULATION, ANCHOR,
             ROOT / 'reports/generated/npb-hitting-history/review.json']
    if not args.npb_only:
        identity = json.loads((KBO.parent / 'collection.json').read_text(encoding='utf8'))
        assert identity['all_source_rows_preserved']
        for p, h in identity['output_hashes'].items():
            assert sha256_file(ROOT / p) == h
        paths += [KBO, KBO.parent / 'collection.json']
    hashes = {str(p.relative_to(ROOT)): sha256_file(p) for p in paths}
    src = pl.read_parquet(DOMESTIC).filter((pl.col('season') <= 2024) & pl.col('bucket').is_in(['MLB', 'AAA']))
    mapping = dict(pa='plate_appearances', ab='at_bats', hits='hits', doubles='doubles', triples='triples',
                   hr='home_runs', bb='base_on_balls', ibb='intentional_walks', hbp='hit_by_pitch', so='strike_outs', sf='sac_flies')
    domestic = src.group_by('season', 'player_id', 'bucket').agg(
        *[pl.col(v).sum().alias(k) for k, v in mapping.items()],
        pl.col('position').unique().alias('positions'), pl.col('player_name').first().alias('source_name')).rename({'bucket': 'league'})
    annual = [dict(r, role=role(r.pop('positions')), birth_date=None) for r in domestic.to_dicts()]
    foreign_rows = {'NPB': pl.read_parquet(NPB).to_dicts()}
    if not args.npb_only:
        foreign_rows['KBO'] = pl.read_parquet(KBO).to_dicts()
    for league, rows in foreign_rows.items():
        annual += aggregate_foreign(rows, league)
    pairs = make_pairs(annual, 30) + make_pairs(annual, 100)
    all_checks = [s for year in [2016, 2017, 2018, 2021, 2022, 2023, 2024] for fold in range(5)
                  for minimum in [30, 100] for s in support(pairs, year, fold, minimum=minimum)]
    # Build histories/case membership before reading saved forecast intermediates. No outcome labels.
    lut = defaultdict(list)
    for r in annual:
        lut[r['league'], r['player_id']].append(r)
    population = pl.read_parquet(POPULATION)
    cases = []
    for pid, origin, display_name, league in FIXED:
        if league not in foreign_rows:
            continue
        known = [r for r in lut[league, pid] if r['season'] <= origin]
        recent = sorted((r for r in known if r['season'] >= origin - 2), key=lambda r: r['season'])
        if not recent:
            raise ValueError(('Fixed source history absent', display_name, origin))
        birthday = recent[0]['birth_date']
        counts = {c: sum(r[c] for r in recent) for c in COUNTS}
        age = (date(origin, 12, 31) - date.fromisoformat(birthday)).days / 365.2425 if birthday else None
        spec = dict(league=league, age=age, contact_band='lowK' if counts['so'] / counts['pa'] < .15 else 'middleK' if counts['so'] / counts['pa'] < .25 else 'highK',
                    power_band='highHR' if counts['hr'] / counts['pa'] >= .04 else 'lowerHR')
        current_support = profile_support(pairs, spec, origin, player_fold(pid))
        before = support(pairs, origin, player_fold(pid))
        assert before == support([p for p in pairs if p['through_year'] <= origin], origin, player_fold(pid))
        assert pid not in current_support['direct_player_ids']
        source_context = population.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == origin)).to_dicts()
        peer_pool = []
        for (other_league, other_id), history in lut.items():
            if other_league != league or other_id == pid:
                continue
            h = [r for r in history if origin - 2 <= r['season'] <= origin]
            pa = sum(r['pa'] for r in h)
            birth = next((r['birth_date'] for r in h if r['birth_date']), None)
            if pa < 100 or not birth or age is None:
                continue
            other_age = (date(origin, 12, 31) - date.fromisoformat(birth)).days / 365.2425
            k = sum(r['so'] for r in h) / pa; hr = sum(r['hr'] for r in h) / pa
            distance = abs(age - other_age) / 5 + abs(counts['pa'] - pa) / 600 + abs(counts['so'] / counts['pa'] - k) / .1 + abs(counts['hr'] / counts['pa'] - hr) / .03
            peer_pool.append(dict(player_id=other_id, source_name=h[-1]['source_name'], age=other_age, pa=pa, k_rate=k, hr_rate=hr, distance=distance))
        peers = sorted(peer_pool, key=lambda r: (r['distance'], r['player_id']))[:3]
        cases.append(dict(player_id=pid, origin_year=origin, name=display_name, league=league,
                          selection='fixed_before_audit', recent_rows=recent, recent_counts=counts,
                          age=age, profile=spec, support=current_support, source_context=source_context,
                          origin_only_peers=peers, foreign_role_qualified=False))
    out.mkdir(parents=True)
    save(out / 'membership-seal.json', dict(case_keys=[[r['player_id'], r['origin_year']] for r in cases],
         source_hashes=hashes, future_MLB_outcomes_used=False, original_forecast_membership_changed=False))
    fields = ['player_id', 'origin_year', 'player_name', 'baseline_pa', 'baseline_p', 'baseline_conditional_pa',
              'combined_rate', 'combined_value']
    forecasts = pl.read_parquet(ANCHOR, columns=fields)
    for c in cases:
        c['unchanged_saved_forecast'] = forecasts.filter((pl.col('player_id') == c['player_id']) & (pl.col('origin_year') == c['origin_year'])).to_dicts()
        assert len(c['unchanged_saved_forecast']) <= 1
        c['candidate_forecast'] = None
    save(out / 'pairs.json', dict(pairs=pairs, translated_rates_fitted=False))
    save(out / 'cases.json', dict(cases=cases, player_walkthrough_status='complete_for_support_only'))
    lines = ['# Foreign hitter translation training support', '',
             'Source and support audit only. No new forecast, adjustment or MLB accuracy claim. Both directions and same-season versus consecutive moves remain separate; Bridge pairs with a domestic 2020 side are excluded from primary support; overseas 2020 to normal domestic 2021 stays. Player roles come from the dated domestic side, not a present-day foreign profile. All identity gaps remain in the original source.', '']
    for c in cases:
        h = c['recent_counts']; s = c['support']
        lines += [f"## {c['name']} before {c['origin_year'] + 1}", '',
                  f"Fixed case MLBAM {c['player_id']}, origin {c['origin_year']}; {c['league']} age at origin end {c['age']}. Three recent years: {h['pa']} PA, {h['hr']} HR, {h['so']} K and {h['bb'] - h['ibb']} unintentional BB. Counts are raw, not park neutral or MLB equivalents.", '',
                  f"In the actual chronological held-player fold: {s['direct_hitter_mover_people']} distinct direct hitter movers, {s['same_age_people']} in the same age band and {s['same_age_contact_power_people']} matching age/contact/power bands. The held player never appears in these counts. First MLB debut is not certified from absence in the left-truncated domestic source.", '',
                  'Recent actual source lines: ' + json.dumps(c['recent_rows'], ensure_ascii=False), '',
                  'Dated MLB context: ' + json.dumps(c['source_context'], ensure_ascii=False), '',
                  'Unchanged saved intermediates: ' + json.dumps(c['unchanged_saved_forecast'], ensure_ascii=False) + '. No forecast row is fabricated when absent.', '',
                  'Origin-only exposure/age/K/HR peers: ' + json.dumps(c['origin_only_peers'], ensure_ascii=False) + '. These are foreign batting-profile comparisons, not certified same-role MLB talent peers.', '',
                  'Interpretation: real professional history is available, but a large foreign source is not a large mover training sample. Sparse direct or age/profile support qualifies any future learned adjustment. No gains, harms or realized MLB errors exist for a model that was not fitted.', '']
    (out / 'player-walkthrough.md').write_text('\n'.join(lines) + '\n', encoding='utf8', newline='\n')
    tests = subprocess.run([sys.executable, '-m', 'pytest', 'tests/test_foreign_mover_support.py', 'tests/test_foreign_mover_support_v2.py', '-q'], cwd=ROOT, capture_output=True, text=True)
    assert tests.returncode == 0, tests.stdout + tests.stderr
    freeze = subprocess.run([sys.executable, 'scripts/verify_hitter_full_2026_freeze.py'], cwd=ROOT, capture_output=True, text=True)
    assert freeze.returncode == 0, freeze.stdout + freeze.stderr
    report = dict(leagues=list(foreign_rows), source_hashes=hashes, folds=all_checks,
        source_mapping=[dict(league=l, original_rows=len(rs), mapped_rows=sum(r['player_id'] is not None for r in rs)) for l, rs in foreign_rows.items()],
        cases=len(cases), player_walkthrough_status='complete_for_support_only', tests=tests.stdout,
        protected_freeze=json.loads(freeze.stdout), new_fits=0, forecasts_changed=False,
        source_support_not_MLB_validation=True, predictive_improvement_claimed=False,
        overall_pair_summary=[dict(**s) for minimum in [30, 100] for s in support(pairs, 2024, -1, minimum=minimum)],
        excluded_domestic_2020_pairs=sum(p['domestic_2020_exception'] for p in pairs),
        overseas_2020_normal_domestic_pairs=sum(p['touches_2020'] and not p['domestic_2020_exception'] for p in pairs),
        output_hashes={str(p.relative_to(ROOT)): sha256_file(p) for p in out.iterdir()})
    save(out / 'report.json', report)
    evidence = ROOT / ('reports/model-evidence/foreign-mover-support-v2-' + name)
    evidence.mkdir(parents=True, exist_ok=True)
    # Public evidence is bounded player narratives and aggregate counts, not the full pair dataset.
    compact = dict(report)
    compact['folds'] = [{k: v for k, v in s.items() if k != 'player_ids'} for s in all_checks]
    compact['overall_pair_summary'] = [{k: v for k, v in s.items() if k != 'player_ids'} for s in report['overall_pair_summary']]
    save(evidence / 'report.json', compact)
    (evidence / 'player-walkthrough.md').write_bytes((out / 'player-walkthrough.md').read_bytes())
    print(json.dumps(dict(cases=len(cases), leagues=list(foreign_rows), summary=compact['overall_pair_summary']), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
