"""Sealed V17 assignment contrast. Never changes skill, PA or old forecasts."""
from collections import defaultdict
from pathlib import Path
import argparse
import json

import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball import defense_assignments as assign
from universal_baseball.defense_jobs import reconcile
from universal_baseball.defense_opportunity_bridge import native_from_outs
from universal_baseball.defense_value import position_value, score_rows, paired_interval
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/defense-assignments-v17'
PUBLIC = ROOT/'reports/model-evidence/defense-assignments-v17'
OLD = ROOT/'reports/generated/defense-jobs-v14'
SOURCE = ROOT/'reports/generated/defense-role-v16/calendar-repair'
ANNUAL = ROOT/'reports/generated/defense-position-opportunity-v7'
DH = ROOT/'reports/generated/defense-budget-v13'
VALUE = ROOT/'reports/generated/defense-value-v12'
ARMS = ('reference', 'baseline', 'seed', 'candidate')
ROLES = assign.ROLES


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def write(name, data):
    for dest in (OUT, PUBLIC):
        save(dest/name, data)


def hashes(paths):
    return {str(p): sha256_file(p) for p in paths}


def verify(h):
    for path, expected in h.items():
        assert sha256_file(Path(path)) == expected, path


def sample(row):
    n = row['job_evidence_PA']
    return '0' if n == 0 else '1-49' if n < 50 else '50-199' if n < 200 else '200+'


def profile(row, kind):
    if kind == 'stage_role':
        return (row['stage'], row['assignment_current_role'])
    if kind == 'joint':
        return (row['stage'], row['age_band'], row['assignment_current_role'],
                sample(row), row['assignment_coverage'])
    return (row[kind],)


def prepare():
    protections()
    for dest in (OUT, PUBLIC):
        dest.mkdir(parents=True, exist_ok=True)
    assert not (OUT/'preflight.json').exists(), 'Preserve sealed preflight'
    assert not any(OUT.glob('model-*.json')), 'No prepare after fit'
    source_review = read(SOURCE/'final-review.json')
    assert source_review['player_walkthrough_status'] == 'complete'
    oldpre = read(OLD/'preflight.json')
    old = pl.read_parquet(OLD/'features.parquet').filter(pl.col('origin_year').is_between(2021,2024))
    current = {r['row_id']: r for r in pl.read_parquet(SOURCE/'current-role-source-features.parquet').to_dicts()}
    bounds = {r['row_id']: r for r in pl.read_parquet(SOURCE/'current-role-period-bounds.parquet').to_dicts()}
    scopes = {(r['player_id'], r['origin'], r['sport_id']): r for r in read(SOURCE/'scope-comparisons.json')['scopes']}
    assert old['row_id'].n_unique() == len(old) == len(current) == len(bounds) == 16674
    assert set(old['row_id']) == set(current) == set(bounds)
    dh = {(r['season'], r['player_id']): r['certified_dual_DH_starts']
          for r in pl.read_parquet(DH/'reviewed-DH-starts.parquet').to_dicts()}
    history = defaultdict(list)
    for a in pl.read_parquet(ANNUAL/'annual-usage.parquet').to_dicts():
        if a['is_mlb']:
            a['starts_10'] += dh.get((a['season'], a['player_id']), 0)
        history[a['player_id']].append(a)
    rows, lineage = [], []
    for r in old.to_dicts():
        f = assign.features(r, current[r['row_id']], bounds[r['row_id']], scopes, history[r['player_id']])
        r.update(f['inputs'])
        r.update(assignment_current_role=f['current_dominant_role'], assignment_coverage=f['current_coverage'],
                 assignment_fallback=f['fallback_shares'], assignment_fallback_kind=f['fallback_kind'])
        rows.append(r)
        lineage.append(dict(row_id=r['row_id'], player_id=r['player_id'], origin=r['origin_year'],
            fold=r['outer_fold'], current_counts=f['current_counts'], older_counts=f['older_counts'],
            current_by_sport=f['current_raw'], source_current_row=current[r['row_id']],
            certified_period_bounds=bounds[r['row_id']],
            older_history=[a for a in history[r['player_id']] if a['season'] < r['origin_year']]))
    f = pl.DataFrame(rows, infer_schema_length=None).sort('row_id')
    f.write_parquet(OUT/'features.parquet')
    pl.DataFrame(lineage, infer_schema_length=None).write_parquet(OUT/'feature-lineage.parquet')
    lookup = {r['row_id']: r for r in rows}
    profiles, cells = [], []
    for c in oldpre['cells']:
        y, k = c['origin'], c['fold']
        train = [lookup[i] for i in c['training_row_ids']]
        test = [lookup[i] for i in c['test_row_ids']]
        assert all(r['outer_fold'] != k and 2022 <= r['target_year'] <= y and
                   r['target_year'] == r['origin_year']+1 and r['next_pa'] > 0 and sum(r['actual_job_vector']) > 0 for r in train)
        assert all(r['outer_fold'] == k and r['origin_year'] == y and r['target_year'] == y+1 for r in test)
        assert {r['player_id'] for r in train}.isdisjoint(r['player_id'] for r in test)
        kinds = ('stage_role', 'joint', 'stage', 'age_band', 'assignment_current_role', 'assignment_coverage')
        tables = {kind: defaultdict(set) for kind in kinds}
        for r in train:
            for kind in kinds:
                tables[kind][profile(r, kind)].add(r['player_id'])
        for r in test:
            counts = {kind: len(tables[kind][profile(r,kind)]) for kind in kinds}
            profiles.append(dict(row_id=r['row_id'], player_id=r['player_id'], origin=y, fold=k,
                stage=r['stage'], age_band=r['age_band'], current_role=r['assignment_current_role'],
                MLB_sample=sample(r), coverage=r['assignment_coverage'],
                **{kind+'_people': n for kind,n in counts.items()},
                unseen_stage_role=counts['stage_role'] == 0, sparse_joint=counts['joint'] < 20,
                unknown_role=r['job_unknown']))
        cells.append(dict(origin=y, fold=k, training_row_ids=c['training_row_ids'], test_row_ids=c['test_row_ids'],
            training_people=len({r['player_id'] for r in train}), training_target_years=sorted({r['target_year'] for r in train}),
            person_weight_sum=float(assign.person_weights([r['player_id'] for r in train]).sum()),
            support={kind: [dict(key=list(key), people=len(pids)) for key,pids in sorted(table.items(),key=lambda z:str(z[0]))]
                     for kind,table in tables.items()}, player_disjoint=True))
    assert len(cells) == 15 and len(profiles) == 12432 and len({p['row_id'] for p in profiles}) == 12432
    pl.DataFrame(profiles, infer_schema_length=None).write_parquet(OUT/'profile-support.parquet')
    paths = [Path(__file__), ROOT/'scripts/verify_defense_assignments_v17.py', ROOT/'scripts/review_defense_assignments_v17.py',
        ROOT/'docs/defense-assignments-v17-contract.md', ROOT/'src/universal_baseball/defense_assignments.py',
        ROOT/'tests/test_defense_assignments.py', ROOT/'src/universal_baseball/defense_jobs.py',
        ROOT/'src/universal_baseball/defense_value.py', ROOT/'src/universal_baseball/defense_opportunity_bridge.py',
        OLD/'preflight.json', OLD/'features.parquet', OLD/'predictions.parquet', OLD/'channel-predictions.parquet',
        OLD/'fit-report.json', OLD/'final-review.json', SOURCE/'final-review.json', SOURCE/'readback-review.json',
        SOURCE/'current-role-source-features.parquet', SOURCE/'current-role-period-bounds.parquet',
        SOURCE/'scope-comparisons.json', ANNUAL/'annual-usage.parquet', DH/'reviewed-DH-starts.parquet',
        ROOT/'reports/generated/defense-role-v15/player-walkthrough.json', VALUE/'channel-predictions.parquet']
    paths += [OLD/f"model-{c['origin']}-{c['fold']}.json" for c in cells]
    write('preflight.json', dict(before_fitting=True, cells=cells, features=assign.names(), source_hashes=hashes(paths),
        output_hashes=hashes([OUT/'features.parquet', OUT/'feature-lineage.parquet', OUT/'profile-support.parquet']),
        input_rows=16674, evaluation_rows=12432, sparse_joint=sum(p['sparse_joint'] for p in profiles),
        unseen_stage_role=sum(p['unseen_stage_role'] for p in profiles), unknown_role=sum(p['unknown_role'] for p in profiles),
        no_2026_outcomes=True, no_deployment=True, player_walkthrough_status='pending',
        previous_goal_turn='No defense progress: read-only Lovich diagnosis confirmed an existing separate defect.',
        qualification='Observed assignments are not defensive talent. Sparse profile counts and missing data remain explicit.'))
    print(json.dumps(dict(status='sealed_before_fit', rows=16674, forecasts=12432,
        sparse_joint=sum(p['sparse_joint'] for p in profiles), unseen_stage_role=sum(p['unseen_stage_role'] for p in profiles))), flush=True)


def check():
    protections()
    pre = read(OUT/'preflight.json')
    assert pre['before_fitting'] and pre['no_2026_outcomes'] and pre['no_deployment']
    verify(pre['source_hashes']); verify(pre['output_hashes'])
    return pre


def fit():
    pre = check()
    assert not (OUT/'fit-report.json').exists(), 'Preserve completed fits'
    frame = pl.read_parquet(OUT/'features.parquet')
    lookup = {r['row_id']: r for r in frame.to_dicts()}
    saved = {r['row_id']: r for r in pl.read_parquet(OLD/'predictions.parquet').to_dicts()}
    supports = {r['row_id']: r for r in pl.read_parquet(OUT/'profile-support.parquet').to_dicts()}
    predictions, notes = [], []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k = c['origin'],c['fold']; path = OUT/f'model-{y}-{k}.json'
            if path.exists():
                m = read(path); assert m['training_row_ids'] == c['training_row_ids'] and m['test_row_ids'] == c['test_row_ids']
                assert m['preflight_sha256'] == sha256_file(OUT/'preflight.json')
            else:
                tr = [lookup[i] for i in c['training_row_ids']]
                x = np.array([[r[n] for n in pre['features']] for r in tr])
                targets = np.array([r['actual_job_vector'] for r in tr], float)
                targets /= targets.sum(axis=1,keepdims=True)
                m = assign.fit(x, targets, [r['player_id'] for r in tr])
                m.update(origin=y, fold=k, features=pre['features'], training_row_ids=c['training_row_ids'],
                    test_row_ids=c['test_row_ids'], preflight_sha256=sha256_file(OUT/'preflight.json'))
                save(path,m)
            notes.append(dict(path=str(path),sha256=sha256_file(path)))
            test = [lookup[i] for i in c['test_row_ids']]
            learned = assign.predict([[r[n] for n in pre['features']] for r in test],m)
            for r,p in zip(test,learned):
                old = saved[r['row_id']]
                q = dict(old)
                for n in pre['features']:
                    q[n] = r[n]
                for n in ('assignment_current_role','assignment_coverage','assignment_fallback','assignment_fallback_kind'):
                    q[n] = r[n]
                for n,v in old.items():
                    if n.startswith('candidate_'):
                        q['baseline_'+n.removeprefix('candidate_')] = v
                support = supports[r['row_id']]
                shares = assign.allowed_shares(p,r['assignment_fallback'], unseen=support['unseen_stage_role'],
                    catching=r['job_catching_evidence'], unknown=r['job_unknown'])
                q['assignment_learned_shares'] = p.tolist()
                q['assignment_allowed_shares'] = shares.tolist()
                q['assignment_unseen_fallback'] = support['unseen_stage_role']
                q['assignment_sparse_joint'] = support['sparse_joint']
                for j,pos in enumerate(ROLES):
                    q[f'seed_{pos}'] = old['job_total']*shares[j]/(old['origin_dh_outs'] if pos==10 else 1.)
                predictions.append(q)
            print(f'Saved/replayed assignment fold {y}/{k}: {m["training_people"]} people, gradient {m["max_gradient"]:.3g}',flush=True)
    budgets = []
    for budget in read(OLD/'fit-report.json')['budgets']:
        y = budget['origin']; rows = sorted([r for r in predictions if r['origin_year']==y],key=lambda r:r['row_id'])
        seed = np.array([[r[f'seed_{pos}']*(r['origin_dh_outs'] if pos==10 else 1.) for pos in ROLES] for r in rows])
        candidate, receipt = reconcile(seed,np.array(budget['caps']))
        assert sum(r['job_unknown_mass'] for r in rows) == budget['unknown_role_reserve']
        assert np.isclose(receipt['global_mass_factor'],budget['global_mass_factor'],atol=1e-12,rtol=0)
        budgets.append(dict(origin=y, caps=budget['caps'], full_capacity=budget['full_capacity'],
            outside_reserve=budget['outside_reserve'], unknown_role_reserve=budget['unknown_role_reserve'],
            unknown_per_position=budget['unknown_per_position'], **receipt))
        for r,values in zip(rows,candidate):
            r['candidate_global_job_factor'] = receipt['global_mass_factor']
            r['candidate_column_multipliers'] = receipt['multipliers']
            for j,pos in enumerate(ROLES):
                r[f'candidate_{pos}'] = values[j]/(r['origin_dh_outs'] if pos==10 else 1.)
    channels = defaultdict(list)
    for r in pl.read_parquet(OLD/'channel-predictions.parquet').to_dicts():
        channels[r['row_id']].append(r)
    conversions = {(c['origin'],c['fold']): read(OLD/f"model-{c['origin']}-{c['fold']}.json")['native_conversions'] for c in pre['cells']}
    details = []
    for r in predictions:
        conv = conversions[r['origin_year'],r['outer_fold']]
        assert len(channels[r['row_id']]) == 12
        byarm = {}
        for arm in ('seed','candidate'):
            native = native_from_outs([r[f'{arm}_{pos}'] for pos in ROLES],conv)
            for name,value in native.items():
                r[f'{arm}_native_{name}'] = value
            runs = {}
            for channel in channels[r['row_id']]:
                name = channel['channel']
                exposure = r[f'{arm}_{name[-1]}'] if name.startswith('range_') else native[name]
                runs[name] = exposure*channel['history_quality']/channel['rate_unit']
            r[arm+'_position_runs'] = position_value(r,arm)
            r[arm+'_defense'] = sum(runs.values())
            r[arm+'_expanded'] = r['batting_forecast']+(r[arm+'_position_runs']+r[arm+'_defense'])/10
            r[arm+'_no_framing'] = r[arm+'_expanded']-runs['framing']/10
            byarm[arm] = runs
        for channel in channels[r['row_id']]:
            q = {n:v for n,v in channel.items() if not n.endswith('_runs') or n=='actual_runs'}
            q.update(reference_runs=channel['reference_runs'],baseline_runs=channel['candidate_runs'],
                seed_runs=byarm['seed'][channel['channel']],candidate_runs=byarm['candidate'][channel['channel']])
            details.append(q)
        assert r['preseason_pa'] == saved[r['row_id']]['preseason_pa']
        assert r['batting_forecast'] == saved[r['row_id']]['batting_forecast']
    f = pl.DataFrame(predictions,infer_schema_length=None).sort('row_id')
    assert len(f) == f['row_id'].n_unique() == 12432 and f['target_year'].max() == 2025
    f.write_parquet(OUT/'predictions.parquet')
    pl.DataFrame(details,infer_schema_length=None).write_parquet(OUT/'channel-predictions.parquet')
    write('fit-report.json',dict(status='unscored_pending_review',models=notes,budgets=budgets,forecasts=len(f),
        hashes=hashes([OUT/'preflight.json',OUT/'predictions.parquet',OUT/'channel-predictions.parquet']),
        no_2026_outcomes=True,no_deployment=True,player_walkthrough_status='pending'))
    protections()


def score():
    check(); note=read(OUT/'fit-report.json'); verify(note['hashes']); verify({m['path']:m['sha256'] for m in note['models']})
    assert not (OUT/'report.json').exists()
    f = pl.read_parquet(OUT/'predictions.parquet'); rows=f.to_dicts(); metrics={}; intervals=[]
    for target in ('expanded','defense','position_runs','no_framing'):
        fields=[arm+'_'+target for arm in ARMS]
        metrics[target]=dict(all_observed=score_rows(rows,fields,'actual_'+target),
            actual_defenders=score_rows([r for r in rows if r['actual_fielding_outs']>0],fields,'actual_'+target),
            known_quality=score_rows([r for r in rows if r['known_quality_channels']>0],fields,'actual_'+target))
        for anchor in ('baseline','reference'):
            intervals.append(paired_interval(rows,'candidate_'+target,anchor+'_'+target,'actual_'+target))
    groups=[]
    for y in (2022,2023,2024):
        for stage in sorted(f['stage'].unique()):
            for band in ('<=24','25-29','30+','unknown'):
                rs=[r for r in rows if r['origin_year']==y and r['stage']==stage and
                    ('unknown' if r['age'] is None else '<=24' if r['age']<=24 else '25-29' if r['age']<=29 else '30+')==band]
                if rs:
                    groups.append(dict(origin=y,stage=stage,age_band=band,rows=len(rs),
                        actual_defenders=sum(r['actual_fielding_outs']>0 for r in rs),
                        expanded=score_rows(rs,[a+'_expanded' for a in ARMS],'actual_expanded'),
                        position=score_rows(rs,[a+'_position_runs' for a in ARMS],'actual_position_runs')))
    role_scores=[]; totals=[]
    for y in (2022,2023,2024):
        rs=[r for r in rows if r['origin_year']==y]
        actual=np.array([r['actual_job_vector'] for r in rs],float)
        positive=actual.sum(axis=1)>0
        actual_shares=actual[positive]/actual[positive].sum(axis=1,keepdims=True)
        for arm in ARMS:
            pred=np.array([[r[f'{arm}_{p}']*(r['origin_dh_outs'] if p==10 else 1.) for p in ROLES] for r in rs])
            den=pred[positive].sum(axis=1,keepdims=True)
            shares=np.divide(pred[positive],den,out=np.zeros_like(pred[positive]),where=den>0)
            role_scores.append(dict(origin=y,arm=arm,rows=len(rs),positive_actual_jobs=int(positive.sum()),
                job_cell_rmse=float(np.sqrt(np.mean((pred-actual)**2))),
                conditional_share_rmse=float(np.sqrt(np.mean((shares-actual_shares)**2))),
                zero_predicted_mass_among_actual_jobs=int((den[:,0]==0).sum())))
            totals.append(dict(origin=y,arm=arm,predicted_roles=[sum(r[f'{arm}_{p}'] for r in rs) for p in ROLES],
                actual_matched_roles=[sum(r[f'actual_{p}'] for r in rs) for p in ROLES],
                predicted_position_runs=sum(r[arm+'_position_runs'] for r in rs),
                actual_position_runs=sum(r['actual_position_runs'] for r in rs)))
    channels=pl.read_parquet(OUT/'channel-predictions.parquet'); cs=[]
    for (name,),g in channels.group_by('channel'):
        rs=g.to_dicts()
        for label,s in [('all_observed',rs),('actual_exposure',[r for r in rs if r['actual_official_exposure']>0]),
                        ('measured_history',[r for r in rs if r['quality_evidence_observed']])]:
            cs.append(dict(channel=name,scope=label,metrics=score_rows(s,[a+'_runs' for a in ARMS],'actual_runs')))
    failures=[]
    for target in ('position_runs','defense'):
        for y in (2022,2023,2024):
            stats=metrics[target]['all_observed']['per_origin']
            old=next(m['rmse'] for m in stats if m['origin']==y and m['arm']=='baseline_'+target)
            new=next(m['rmse'] for m in stats if m['origin']==y and m['arm']=='candidate_'+target)
            if new>1.05*old:
                failures.append(dict(origin=y,metric=target,relative_deterioration=new/old-1))
    write('report.json',dict(status='provisional_pending_player_review',metrics=metrics,intervals=intervals,
        groups=groups,role_scores=role_scores,totals=totals,channels=cs,component_tolerance_failures=failures,
        sparse_profiles=read(OUT/'preflight.json')['sparse_joint'],
        complete_value_rows=f.filter(pl.col('actual_expanded').is_not_null()).height,
        partial_value_rows=f.filter(pl.col('actual_expanded').is_null()).height,
        no_2026_outcomes=True,no_deployment=True,player_walkthrough_status='pending',hashes=note['hashes']))
    print(json.dumps({name:m['all_observed']['equal_origin'] for name,m in metrics.items()},indent=2),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['prepare','fit','score'])
    args=parser.parse_args(); globals()[args.mode]()
