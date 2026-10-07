"""Post-fit diagnostics only: replay shares/totals/support and explain cancellation.

No fit, parameter change, forecast overwrite or 2026 outcome access. Diagnostic
profile thresholds describe this result; they are not a tuned eligibility rule.
"""
from collections import defaultdict
import json

import numpy as np
import polars as pl

from run_defense_assignments_v17 import OUT, ARMS, ROLES, check, read, write, hashes


def near(a, b):
    assert np.allclose(a, b, atol=1e-7, rtol=0), (a, b)


def sample(r):
    n = r['job_evidence_PA']
    return '0' if n == 0 else '1-49' if n < 50 else '50-199' if n < 200 else '200+'


def joint(r):
    return (r['stage'], r['age_band'], r['assignment_current_role'], sample(r), r['assignment_coverage'])


def main():
    pre = check()
    assert read(OUT/'independent-verification.json')['status'] == 'passed'
    assert not (OUT/'diagnostic-review.json').exists()
    rows = pl.read_parquet(OUT/'predictions.parquet').to_dicts()
    features = {r['row_id']: r for r in pl.read_parquet(OUT/'features.parquet').to_dicts()}
    lineage = {r['row_id']: r for r in pl.read_parquet(OUT/'feature-lineage.parquet').to_dicts()}
    support = {r['row_id']: r for r in pl.read_parquet(OUT/'profile-support.parquet').to_dicts()}
    report = read(OUT/'report.json')
    assert len(rows) == 12432 and max(r['target_year'] for r in rows) == 2025
    replayed = 0
    for cell in pre['cells']:
        pools = defaultdict(set)
        for i in cell['training_row_ids']:
            r = features[i]
            pools[joint(r)].add(r['player_id'])
        for i in cell['test_row_ids']:
            count = len(pools[joint(features[i])])
            assert support[i]['joint_people'] == count
            assert support[i]['sparse_joint'] == (count < 20)
            replayed += 1
    for m in report['role_scores']:
        rs = [r for r in rows if r['origin_year'] == m['origin']]
        actual = np.array([r['actual_job_vector'] for r in rs], float)
        pred = np.array([[r[f'{m["arm"]}_{p}']*(r['origin_dh_outs'] if p == 10 else 1) for p in ROLES] for r in rs])
        positive = actual.sum(axis=1) > 0
        den = pred[positive].sum(axis=1, keepdims=True)
        shares = np.divide(pred[positive], den, out=np.zeros_like(pred[positive]), where=den > 0)
        observed = actual[positive]/actual[positive].sum(axis=1, keepdims=True)
        near([np.sqrt(np.mean((pred-actual)**2)), np.sqrt(np.mean((shares-observed)**2))],
             [m['job_cell_rmse'], m['conditional_share_rmse']])
        assert int(positive.sum()) == m['positive_actual_jobs']
        assert int((den[:, 0] == 0).sum()) == m['zero_predicted_mass_among_actual_jobs']
    for m in report['totals']:
        rs = [r for r in rows if r['origin_year'] == m['origin']]
        near([sum(r[f'{m["arm"]}_{p}'] for r in rs) for p in ROLES], m['predicted_roles'])
        near([sum(r[f'actual_{p}'] for r in rs) for p in ROLES], m['actual_matched_roles'])
        near(sum(r[f'{m["arm"]}_position_runs'] for r in rs), m['predicted_position_runs'])
    group_scores = []
    for y in (2022, 2023, 2024):
        for stage in sorted({r['stage'] for r in rows}):
            rs = [r for r in rows if r['origin_year'] == y and r['stage'] == stage]
            if not rs:
                continue
            entry = dict(origin=y, stage=stage, rows=len(rs), actual_defenders=sum(r['actual_fielding_outs'] > 0 for r in rs))
            for target in ('expanded', 'defense', 'position_runs'):
                measured = [r for r in rs if r['actual_'+target] is not None]
                entry[target] = dict(measured_rows=len(measured), **{arm: dict(
                    rmse=float(np.sqrt(np.mean([(r[arm+'_'+target]-r['actual_'+target])**2 for r in measured]))),
                    total=float(sum(r[arm+'_'+target] for r in measured)),
                    actual_total=float(sum(r['actual_'+target] for r in measured))) for arm in ('baseline', 'candidate')})
            group_scores.append(entry)
    measured = [r for r in rows if r['actual_expanded'] is not None]
    gains = [r for r in measured if (r['candidate_expanded']-r['actual_expanded'])**2 < (r['baseline_expanded']-r['actual_expanded'])**2]
    def worse(r, target):
        return abs(r['candidate_'+target]-r['actual_'+target]) > abs(r['baseline_'+target]-r['actual_'+target])
    gain_summary = dict(measured=len(measured), improving_value=len(gains),
        improving_value_with_worse_position=sum(worse(r, 'position_runs') for r in gains),
        improving_value_with_worse_defense=sum(worse(r, 'defense') for r in gains),
        improving_value_with_both_components_worse=sum(worse(r, 'position_runs') and worse(r, 'defense') for r in gains),
        qualification='Descriptive cancellation flags, not a significance test or automatic rejection of every flagged gain.')
    # Current-role specialists: origin-known selection, no future outcomes used.
    specialists = []
    for r in rows:
        l = lineage[r['row_id']]
        current = l['current_by_sport']['1']
        counts = np.array(current['counts'])
        if r['stage'] != 'Current MLB' or r['job_evidence_PA'] < 200 or not current['field_known'] or not current['DH_known'] or counts.sum() == 0:
            continue
        dom = int(counts.argmax())
        if counts[dom]/counts.sum() < .90:
            continue
        allcurrent = np.array(l['current_counts'])
        older = np.array(l['older_counts'])
        known = (allcurrent+older) > 0
        actual = np.array(r['actual_job_vector'], float)
        entry = dict(row_id=r['row_id'], player=r['player_name'], origin=r['origin_year'], dominant_role=ROLES[dom],
            current_MLB_dominant_share=float(counts[dom]/counts.sum()), actual_mass=float(actual.sum()))
        for arm in ('baseline', 'seed', 'candidate'):
            mass = np.array([r[f'{arm}_{p}']*(r['origin_dh_outs'] if p == 10 else 1) for p in ROLES])
            entry[arm] = dict(dominant_share=float(mass[dom]/mass.sum()) if mass.sum() else None,
                outside_observed_repertoire_share=float(mass[~known].sum()/mass.sum()) if mass.sum() else None)
        entry['actual'] = dict(dominant_share=float(actual[dom]/actual.sum()) if actual.sum() else None,
            outside_observed_repertoire_share=float(actual[~known].sum()/actual.sum()) if actual.sum() else None)
        specialists.append(entry)
    specialist_summary = []
    for y in (2022, 2023, 2024):
        rs = [r for r in specialists if r['origin'] == y]
        positive = [r for r in rs if r['actual_mass'] > 0]
        specialist_summary.append(dict(origin=y, rows=len(rs), actual_positive_jobs=len(positive),
            all_origin_predicted={a: float(np.mean([r[a]['dominant_share'] for r in rs if r[a]['dominant_share'] is not None])) for a in ('baseline','seed','candidate')},
            matched_actual_positive={a: dict(dominant_share=float(np.mean([r[a]['dominant_share'] for r in positive])),
                outside_observed_repertoire_share=float(np.mean([r[a]['outside_observed_repertoire_share'] for r in positive])))
                for a in ('baseline','seed','candidate','actual')}))
    focal = []
    walks = read(OUT/'player-walkthrough.json')
    lookup = {r['row_id']: r for r in rows}
    for case in walks['cases']:
        w = case['records'][0]
        r = lookup[w['row_id']]
        if r['actual_expanded'] is None:
            continue
        actual_batting = r['actual_expanded']-(r['actual_position_runs']+r['actual_defense'])/10
        errors = {}
        for a in ('baseline','candidate'):
            parts = [r['batting_forecast']-actual_batting,
                (r[a+'_position_runs']-r['actual_position_runs'])/10,
                (r[a+'_defense']-r['actual_defense'])/10]
            near(sum(parts), r[a+'_expanded']-r['actual_expanded'])
            errors[a] = dict(batting_error=parts[0], position_error=parts[1], defense_error=parts[2],
                total_error=sum(parts), sum_absolute_component_errors=sum(abs(v) for v in parts))
        focal.append(dict(player=w['name'], origin=w['origin'], selection=case['selection'], errors=errors))
    result = dict(status='passed', diagnostic_only=True, no_new_fit=True, support_profiles_replayed=replayed,
        role_metric_cells_replayed=len(report['role_scores']), position_total_cells_replayed=len(report['totals']),
        stage_scores=group_scores, cancellation=gain_summary, specialist_definition='Current MLB, >=200 origin evidence PA, independently certified MLB field/DH counts, >=90% starts-equivalent at one current MLB role. Empirical warning, not a ban on future role changes. Historical coverage remains left-truncated.',
        specialist_summary=specialist_summary, specialists=specialists, focal_error_decomposition=focal,
        player_walkthrough_status='pending_final_main_disposition', no_2026_outcomes=True, no_deployment=True,
        hashes=hashes([OUT/'preflight.json',OUT/'predictions.parquet',OUT/'feature-lineage.parquet',OUT/'report.json',OUT/'player-walkthrough.json']))
    write('diagnostic-review.json', result)
    print(json.dumps({k: result[k] for k in ('status','support_profiles_replayed','cancellation','specialist_summary','stage_scores')}, separators=(',',':')))


if __name__ == '__main__':
    main()
