"""Close the completed diagnostic review without approving or changing forecasts."""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
import run_hitter_dated_context as run

ROOT, OUT = run.ROOT, run.OUT
PUBLIC = ROOT / 'reports/model-evidence/hitter-dated-context-integration'
RESULT = ROOT / 'docs/hitter-dated-context-integration-result.md'


def main():
    assert not (OUT / 'final-review.json').exists(), 'Preserve completed disposition'
    review = run.read(OUT / 'verification.json')
    run.verify(review['hashes'])
    pre = run.read(OUT / 'preflight.json'); run.verify(pre['input_hashes'])
    run.verify(run.read(OUT / 'fit-seal.json'))
    assert review['old_new_head_replays'] == 140 and review['cases'] == 13
    cases = run.read(OUT / 'reviewed-cases.json')['cases']
    fixed = {(808975, 2024), (808982, 2024), (673490, 2022), (519346, 2016),
             (592450, 2024), (701762, 2024), (680757, 2021), (691406, 2024)}
    assert fixed <= {(c['player_id'], c['origin_year']) for c in cases}
    manual = RESULT.read_text(encoding='utf8')
    for c in cases:
        assert c['name'] in manual and len(c['peers']) == 4
        assert c['head_traces']['ctx']['participation']['linked_probability'] >= 0
        p = c['candidate_same_fit_old_input_probe']; f = c['forecasts']
        assert np.isclose(p['own_input_effect'] + p['refit_effect'], f['ctx_pa'] - f['current_pa'])
        assert np.isclose(f['actual_relative_value'] - f['ctx_value'], f['opportunity_miss'] + f['hitting_miss'])
    # Diagnostic enumeration, not a new model or inferred job/rights status.
    old = pl.read_parquet(run.OLD / 'features.parquet')
    new = pl.read_parquet(OUT / 'features.parquet')
    pop = pl.read_parquet(run.POP / 'population.parquet')
    negatives = old.select('row_id', 'player_id', 'origin_year', 'on_40man').rename({'on_40man': 'old_listing'}).join(
        new.select('row_id', 'on_40man').rename({'on_40man': 'new_listing'}), on='row_id', validate='1:1').join(
        pop.select('player_id', 'origin_year', 'information_date', 'player_name', 'latest_event_date',
                   'latest_event_kinds', 'scope_exit_records', 'positive_context_records'),
        on=['player_id', 'origin_year'], validate='1:1').filter(
            (pl.col('old_listing') == 1) & (pl.col('new_listing') == 0)).sort('origin_year', 'player_id')
    same_day = negatives.filter(pl.col('latest_event_date') == pl.col('information_date'))
    assert negatives.height == 84 and same_day.height == 8
    captures = run.POP / 'captures'
    evidence = []; relevant_files = []
    for team in [147, 135]:
        path = captures / f'roster-2022-{team}-40Man.json'
        meta_path = path.with_suffix('.json.metadata.json')
        meta = run.read(meta_path)
        assert sha256_file(path) == meta['sha256']
        assert meta['params'] == dict(rosterType='40Man', season=2022, date='2022-03-18')
        rows = [r for r in run.read(path)['roster'] if r['person']['id'] == 572228]
        assert not rows
        evidence.append(dict(team_id=team, returned_rows=rows, metadata=meta))
        relevant_files += [path, meta_path]
    tx_path = captures / 'transactions-2022.json'
    tx_meta = tx_path.with_suffix('.json.metadata.json')
    assert sha256_file(tx_path) == run.read(tx_meta)['sha256']
    tx = [r for r in run.read(tx_path)['transactions'] if r.get('person', {}).get('id') == 572228]
    assert any(r['date'] == '2022-03-18' and r['typeDesc'] == 'Trade' for r in tx)
    assert any(r.get('effectiveDate') == '2022-03-18' and 'activated' in r['description'] for r in tx)
    relevant_files += [tx_path, tx_meta]
    source_note = dict(negative_source_changes=84, same_information_date_events=8,
        negative_changes=negatives.to_dicts(), same_day_changes=same_day.to_dicts(),
        voit=dict(player_id=572228, origin_year=2021, listings=evidence, transactions=tx),
        disposition='Returned negatives are not certified absence of rights or jobs; reconcile dates/status before deployment',
        no_fits=True, no_source_membership_or_forecast_changed=True,
        source_hashes={str(p): sha256_file(p) for p in relevant_files})
    run.write('source-conflict-diagnostic.json', source_note)
    tests = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        'tests/test_hitter_dated_context.py', 'tests/test_hitter_dated_context_scoring.py',
        'tests/test_hitter_value_ledger.py', 'tests/test_foreign_origin_inputs.py'],
        cwd=ROOT, text=True, capture_output=True)
    assert tests.returncode == 0, tests.stdout + tests.stderr
    frozen = subprocess.run([sys.executable, 'scripts/verify_hitter_full_2026_freeze.py'],
        cwd=ROOT, text=True, capture_output=True)
    assert frozen.returncode == 0, frozen.stdout + frozen.stderr
    freeze = json.loads(frozen.stdout)
    assert freeze['verified_files'] == 31 and not freeze['protected_2026_opened']
    run.write('checks.json', dict(tests=tests.stdout, stderr=tests.stderr, protected_freeze=freeze))
    support = pl.read_parquet(OUT / 'profile-support.parquet').group_by('head').agg(
        pl.len().alias('rows'), (pl.col('profile_people') == 0).sum().alias('zero_people'),
        (pl.col('profile_people') < 20).sum().alias('fewer_than_twenty_people')).sort('head').to_dicts()
    summaries = [dict(player_id=c['player_id'], origin_year=c['origin_year'], name=c['name'],
        original_saved_name=c['original_saved_name'], selection=c['selection'],
        own_source_changes=c['own_source_changes'], forecasts=c['forecasts'],
        diagnostic_probe=c['candidate_same_fit_old_input_probe'], support=c['profile_support'],
        peer_selection=c['origin_only_peer_selection'], peers=c['peers'],
        observed_conditional_hitting_available=c['forecasts']['actual_pa'] > 0,
        manual_judgment_document='docs/hitter-dated-context-integration-result.md') for c in cases]
    run.write('completed-case-manifest.json', dict(cases=summaries, player_walkthrough_status='complete',
        inactive_zero_rate_is_accounting_placeholder=True, no_model_approval_implied=True))
    # Export compact evidence only; retain raw/foreign bulk counts and fits privately.
    exports = {name: name for name in ['checks.json', 'source-conflict-diagnostic.json', 'completed-case-manifest.json']}
    exports.update({'scores.json': 'initial-common-reference-scores.json',
                    'intervals.json': 'initial-common-reference-intervals.json',
                    'public-benchmark.json': 'initial-public-benchmark.json'})
    for source, destination in exports.items():
        assert not (PUBLIC / destination).exists()
        (PUBLIC / destination).write_bytes((OUT / source).read_bytes())
    scores = {r['scope']: r for r in run.read(OUT / 'scores-relative.json')}
    benchmark = run.read(OUT / 'public-benchmark-relative-review.json')[0]
    public = scores['public']['scores']['ctx']
    paths = [Path(__file__), RESULT, ROOT / 'docs/hitter-dated-context-scoring-amendment.md',
        ROOT / 'scripts/review_hitter_dated_context.py', ROOT / 'scripts/review_hitter_dated_context_v2.py',
        ROOT / 'scripts/run_hitter_dated_context.py', ROOT / 'src/universal_baseball/hitter_dated_context.py',
        ROOT / 'tests/test_hitter_dated_context.py', ROOT / 'tests/test_hitter_dated_context_scoring.py',
        OUT / 'verification.json', OUT / 'completed-case-manifest.json', OUT / 'source-conflict-diagnostic.json',
        OUT / 'checks.json', OUT / 'preflight.json', OUT / 'fit-report.json', OUT / 'fit-seal.json']
    result = dict(execution_verification_status='complete', player_walkthrough_status='complete',
        cases=13, old_new_head_replays=140, source_rows=63282, forecast_rows=30506,
        changed_forecast_rows=182, profile_support=support,
        predictive_status='Appearance improvement; uncertain PA and value effect; public value slightly worse',
        public_pa_rmse_excess=public['pa_rmse'] / benchmark['rmse'] - 1,
        public_pa_mae_excess=public['pa_mae'] / benchmark['mae'] - 1,
        public_pa_rmse_allowance_pass=public['pa_rmse'] <= 1.10 * benchmark['rmse'],
        public_pa_mae_allowance_pass=public['pa_mae'] <= 1.15 * benchmark['mae'],
        baseball_reasonability_status='Deployment fails source/cutoff consistency and unresolved representation gaps',
        disposition='Retain diagnostic comparison; do not deploy or reject foreign production',
        next_work='Reconcile dated listing/contract/temporary status, integrate translated foreign production and qualified additions',
        new_foreign_forecasts=0, deployment_approved=False, full_goal_complete=False,
        protected_freeze=freeze,
        hashes={str(p): sha256_file(p) for p in paths},
        public_artifact_hashes={p.name: sha256_file(p) for p in PUBLIC.iterdir() if p.is_file()})
    run.write('final-review.json', result)
    assert not (PUBLIC / 'final-review.json').exists()
    (PUBLIC / 'final-review.json').write_bytes((OUT / 'final-review.json').read_bytes())
    print(json.dumps({k: v for k, v in result.items() if k not in ['hashes', 'public_artifact_hashes']}, indent=2))


if __name__ == '__main__':
    main()
