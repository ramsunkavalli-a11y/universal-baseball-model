"""Five source/control walks; no new fit, predictive score or frozen edit."""
import json
from pathlib import Path

import polars as pl

from universal_baseball.known_suspension_budget import apply_to_role, budget
from universal_baseball.storage import sha256_file
from run_hitter_linked_employment_recency import ROOT, read, verify

OUT = ROOT / 'reports/model-evidence/known-suspension-budget'
CASES = [(665487, 2022), (665487, 2023), (677551, 2023), (672779, 2024), (680776, 2024)]
# League-opening dates, announced before the reviewed January cutoffs. These
# validate preseason scope; no future actual schedule/results are counted.
START = {2023: '2023-03-30', 2024: '2024-03-20', 2025: '2025-03-18'}
SCHEDULE_SOURCES = {
    2023: 'https://www.mlb.com/press-release/press-release-mlb-announces-2023-regular-season-schedule',
    2024: 'https://www.mlb.com/orioles/news/mlb-world-tour-2024',
    2025: 'https://www.mlb.com/press-release/press-release-mlb-announces-2025-regular-season-schedule',
}
JUDGMENTS = {
    (665487, 2022): 'Finite missed games do not explain the old near-exit probability. Remaining-game accounting is repaired; an independent role/health baseline is still required. Do not multiply the 61-PA forecast by another absence factor.',
    (665487, 2023): 'Subsequent origin-known MLB use resolves continuing suspension absence. Do not charge the original sentence again. Medical uncertainty remains independent.',
    (677551, 2023): 'Unresolved parallel leave/restriction does not have a known numerical return factor. The old high participation is not certified by talent/roster evidence; scenarios are required, not a retroactive permanent ban.',
    (672779, 2024): 'Permanent ineligibility has a factual zero opportunity budget. This does not erase his latent hitting talent or validate rare learned status effects.',
    (680776, 2024): 'Explicit suspension resolution leaves no current restriction budget. Ordinary participation/health risk remains with the role model; do not reapply past games.',
}


def main():
    assert not OUT.exists(), 'Preserve completed evidence'
    obsbase = ROOT / 'reports/generated/hitter-nonmedical-observation'
    verify(read(obsbase / 'final-review.json')['hashes'])
    ledger_path = ROOT / 'reports/generated/hitter-status-evidence-v2/status-ledger.json'
    obs_path = obsbase / 'active-origin-evidence.json'
    oldwalk_path = ROOT / 'reports/generated/hitter-nonmedical-opportunity/player-walks.json'
    facts_path = ROOT / 'config/reported_suspension_season_budgets.json'
    oldreturn_path = ROOT / 'config/hitter_status_return_reports.json'
    forecasts_path = ROOT / 'reports/generated/hitter-nonmedical-opportunity/predictions.parquet'
    anchor_path = ROOT / 'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet'
    ledger = {r['candidate_key']: r for r in read(ledger_path)['rows']}
    observations = read(obs_path)['origins']
    oldwalks = {(r['origin']['player_id'], r['origin']['origin_year']): r for r in read(oldwalk_path)['cases']}
    facts = read(facts_path)['events']
    q = pl.read_parquet(forecasts_path)
    anchor = pl.read_parquet(anchor_path)
    cases = []
    for pid, y in CASES:
        key = f'{y}:{pid}'
        source, walk = ledger[key], oldwalks[pid, y]
        observation = observations.get(key)
        if observation is None:
            # No active legal channels means there was nothing for the active-
            # origin adapter to repair. Verify, rather than inventing a clear.
            assert not source['absence']['active_restrictions']
            observation = dict(hard_unavailable=source['absence']['hard_unavailable'],
                observation_unresolved_channels=source['absence']['active_restrictions'])
        o = q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == y)).row(0, named=True)
        assert o['ctx_information_date'] == source['information_date'] and o['target_year'] == y + 1
        result = budget(observation, facts, player_id=pid, cutoff=source['information_date'],
                        target_year=y + 1, season_games=162, season_start=START[y + 1])
        peers = walk['origin_only_peers']
        cases.append(dict(player_id=pid, origin=y, target=y + 1, player_name=o['player_name'],
            cutoff=source['information_date'], budget=result, judgment=JUDGMENTS[pid, y],
            prior_counts=[{n: s[n] for n in ['season', 'bucket', 'plate_appearances', 'home_runs',
                                            'strike_outs']} for s in walk['domestic_counts']],
            clinical_spells=source['clinical_spells'],
            literal_40man=source['literal_returned_40man'], historical_MLB_link=source['status_major_link'],
            old_forecast={n: o[n] for n in ['observation_p', 'observation_conditional_pa', 'observation_pa',
                'observation_rate', 'observation_value', 'next_pa', 'actual_relative_value']},
            medical_recovery_certified=False,
            prior_source_to_path_receipt=dict(path=str(oldwalk_path), row_id=o['row_id']),
            origin_only_peers_retained=peers, new_full_player_forecast=None))
    tatis = cases[0]
    r = tatis['budget']
    assert r['original_sentence_games'] == 80 and r['eligible_games'] == 142
    assert r['source_report']['remaining_games_at_season_start'] == 20
    oldreturn = read(oldreturn_path)['events'][0]
    assert oldreturn['known_date'] == r['source_report']['known_date']
    assert oldreturn['reported_return_date'] == r['source_report']['reported_eligibility_date']
    # Arithmetic demonstration ONLY. These inputs are not fitted Tatis estimates.
    demo = apply_to_role(.97, 600., 1.313, r, excludes_known_suspension=True)
    assert abs(demo['expected_pa'] - .97 * 600 * 142 / 162) < 1e-10
    try:
        apply_to_role(tatis['old_forecast']['observation_p'],
            tatis['old_forecast']['observation_conditional_pa'],
            tatis['old_forecast']['observation_rate'], r, excludes_known_suspension=False)
    except ValueError:
        baseline_blocked = True
    else:
        raise AssertionError('Already-adjusted invalid baseline accepted')
    assert cases[1]['budget']['known_suspension_fraction'] == 1.
    assert cases[2]['budget']['known_suspension_fraction'] is None
    assert cases[3]['budget']['known_suspension_fraction'] == 0.
    assert cases[4]['budget']['known_suspension_fraction'] == 1.
    public = anchor.filter((pl.col('player_id') == 665487) & (pl.col('origin_year') == 2022))
    assert public.height == 1
    public_smell = dict(saved_steamer_PA=public['steamer_pa'][0],
        exact_archive_vintage_unknown=True, used_as_model_input=False, compared_for_predictive_gain=False)
    selected = ROOT / 'model_artifacts/hitter-selected-2026-frozen-2026-10-05/freeze-manifest.json'
    final2026 = ROOT / 'reports/model-evidence/hitter-final-2026/report.json'
    assert sha256_file(selected) == 'a1d819ffcdd98a9ee62feecf5637b5ebe1f93b6e931d77d2b7d692ed928da67a'
    assert sha256_file(final2026) == '8c2acfeb42ece7d109d3b35542a6b79ec372467d7027d5945a4ba800cde913bb'
    paths = [Path(__file__), ROOT / 'src/universal_baseball/known_suspension_budget.py',
        ROOT / 'tests/test_known_suspension_budget.py', ROOT / 'docs/known-suspension-budget-contract.md',
        ROOT / 'docs/hitter-case-repair-queue.md', ledger_path, obs_path, oldwalk_path, facts_path,
        oldreturn_path, forecasts_path, anchor_path, selected, final2026]
    report = dict(player_walkthrough_status='complete', component='Known finite suspension game budget',
        source_math_repair_complete=True, full_Tatis_forecast_repair_complete=False,
        new_fits=0, forecasts_changed=False, deployment_approved=False, protected_2026_outcomes_used=False,
        arithmetic_demonstration=dict(inputs_not_fitted_player_estimates=True, probability=.97,
            conditional_pa_before_suspension=600., result=demo),
        old_adjusted_baseline_rejected=baseline_blocked, public_smell_test=public_smell,
        cases=cases, scope='Five locked source/control cases; no cohort accuracy experiment or improvement claim',
        schedule_scope_sources=SCHEDULE_SOURCES,
        hashes={str(p): sha256_file(p) for p in paths})
    OUT.mkdir(parents=True)
    (OUT / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    print('Five source/control walks complete. Remaining-game component repaired; independent role forecast still required.')


if __name__ == '__main__':
    main()
