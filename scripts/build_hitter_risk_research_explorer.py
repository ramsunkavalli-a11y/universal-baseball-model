"""Expose sealed historical means and coherent risk, without new fits or 2026."""
import json
import math
import shutil
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
import evaluate_hitter_event_count_risk as e

OUT = e.ROOT/'reports/generated/hitter-risk-research-explorer'
DIST = Path('D:/UBM-Source-Cache/hitter-risk-research-explorer/dist')
TEMPLATE = e.ROOT/'src/universal_baseball/templates/hitter_risk_research'
TEAM = e.ROOT/'reports/generated/hitter-team-record-v75'
ARMS = ['associated', 'independent', 'normal', 'fixed']
HISTORY_FIELDS = ['season', 'bucket', 'plate_appearances', 'home_runs', 'unintentional_walks',
                  'strike_outs', 'doubles', 'triples', 'babip_hits', 'babip_opportunities']


def write(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)+'\n',
                 encoding='utf8', newline='\n')


def encoded(values):
    return [None if not math.isfinite(float(x)) else float(x) for x in values]


def row(record, context, support, dates, reviewed):
    r = record; known = context['context_reason'] == 'known' and context['context_parent'] is not None
    answer = dict(row_id=r['row_id'], player_id=r['player_id'], player_name=r['player_name'],
        origin_year=r['origin_year'], target_year=r['target_year'], age=r['age'], position=r['source_position'],
        stage=r['stage'], org=context['context_parent'] if known else 'Unknown affiliation',
        club=context['context_club'], club_year=context['context_club_year'],
        team_basis=context['context_basis'], team_reason=context['context_reason'], rights_date=context['context_rights_date'],
        information_date=dates[str(r['target_year'])], rate=r['preseason_rate'], p=r['preseason_p'],
        conditional_pa=r['preseason_conditional_pa'], pa=r['preseason_pa'], value=r['preseason_value'],
        replacement_rate=r['origin_replacement_rate'], next_pa=r['next_pa'], next_value=r['next_value'],
        next_rate=r['next_batting_rate'] if r['next_pa'] > 0 else None,
        calibration_people=r['calibration_people'], participation_people=support['participation'],
        workload_people=support['conditional_pa'], draft_known=bool(r['draft_known']), draft_year=r['draft_year'],
        pick_number=r['pick_number'], draft_class=r['draft_school_class'],
        scout_listed=r['new_scout_listed_0'], scout_rank_score=r['new_scout_rank_score_0'],
        reviewed=r['row_id'] in reviewed,
        public_match=bool(r['pa_0'] > 0 and r['steamer_index'] is not None and r['zips_index'] is not None))
    answer['ranges'] = {a: [r[a+'_q10'], r[a+'_q50'], r[a+'_q90'], r[a+'_p_negative'],
        r[a+'_p_two'], r[a+'_impossible_mass']] for a in ARMS}
    flags = []
    if r['calibration_people'] == 0: flags.append('No earlier active players match the refined risk profile; uncertainty borrows globally.')
    elif r['calibration_people'] < 20: flags.append('Few earlier active players match the refined risk profile; uncertainty is not certified for this exact profile.')
    if support['participation'] < 20: flags.append('Sparse or absent appearance-model profile support; prospect readiness may be unreliable.')
    if support['conditional_pa'] < 20: flags.append('Sparse or absent active-workload profile support; PA if active may be unreliable.')
    if not known: flags.append('Origin-year organization is unresolved; no future affiliation is substituted.')
    if not r['origin_evidence_bridge']: flags.append('Roster-only eligibility lacks the own-history/debut/draft bridge; this is unknown, not zero talent.')
    if r['needs_availability_scenario']: flags.append('Exceptional availability needs a separate scenario; generic hitting spread does not solve it.')
    if r['reported_retired']: flags.append('Cutoff-known reported retirement affects opportunity while unreversed, not hitting ability.')
    if r['hard_unavailable']: flags.append('A dated permanent-status rule affects opportunity, separately from model ability.')
    flags.append('Linked rate/workload slope reached the predeclared bound; this simple dependence form is restrictive.')
    flags.append('No fielding, catching, position bonus or baserunning is included in this offense target.')
    answer['flags'] = flags
    return answer


def main():
    OUT.mkdir(parents=True, exist_ok=True); DIST.mkdir(parents=True, exist_ok=True)
    final = e.read(e.OUT/'final-report.json'); e.old.check_hashes(final['evidence_hashes']); e.old.check_hashes(final['local_output_hashes'])
    assert final['player_walkthrough_status'] == 'complete' and final['selected_research_law'] == 'associated'
    point = e.read(e.old.current.OUT/'report.json')
    assert point['player_walkthrough_status'] == 'complete'
    source = e.read(TEAM/'source-report.json'); e.old.check_hashes(source['input_hashes'])
    assert sha256_file(TEAM/'features.parquet') == source['output_sha256']
    sr = e.read(TEAM/'source-review.json'); e.old.check_hashes(sr['review_hashes'])
    q = pl.read_parquet(e.WORK/'scored-predictions.parquet').sort('row_id'); f = e.old.context()
    assert len(q) == 30506 and q['row_id'].n_unique() == 30506 and q['target_year'].max() == 2025
    contexts = {r['row_id']: r for r in pl.read_parquet(TEAM/'features.parquet').select(
        'row_id', *[c for c in pl.read_parquet(TEAM/'features.parquet').columns if c.startswith('context_')]).iter_rows(named=True)}
    profiles = pl.read_parquet(e.old.current.OUT/'profile-support.parquet').filter((pl.col('arm') == 'preseason') & (pl.col('kind') == 'refined'))
    support = {}
    for p in profiles.iter_rows(named=True):
        support.setdefault(p['row_id'], {})[p['head']] = p['profile_people']
    assert set(q['row_id']) <= set(support)
    point_pre = e.read(e.old.current.OUT/'preflight.json'); names = point_pre['pa_features']
    rate_pre = e.read(e.old.OUT/'preflight.json'); rnames = rate_pre['rate_features']
    assert len(names) == 251 and len(rnames) == 199
    dates = {str(c['year']+1): c['information_date'] for c in point_pre['cells']}
    cases = e.read(e.OUT/'reviewed-cases.json'); reviewed = {c['origin']['row_id'] for c in cases}
    for c in cases:
        r = c['origin']; write(DIST/f'reviews/{r["row_id"]}.json', dict(note=c['baseball_review'],
            selection=c['selection'], peers=c['peers'], peer_limit=c['peer_limit']))
    output = [row(r, contexts[r['row_id']], support[r['row_id']], dates, reviewed) for r in q.iter_rows(named=True)]
    counts_path = e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    counts = pl.scan_parquet(counts_path).filter(pl.col('season') <= 2024).collect()
    histories = {}
    for h in counts.iter_rows(named=True):
        histories.setdefault(h['player_id'], []).append([h[k] for k in HISTORY_FIELDS])
    for year in sorted(q['target_year'].unique()):
        rows = [r for r in output if r['target_year'] == year]; ids = {r['player_id'] for r in rows}
        history = {str(pid): sorted([h for h in histories.get(pid, []) if year-3 <= h[0] <= year-1], key=lambda h:(h[0], h[1])) for pid in ids}
        write(DIST/f'years/{year}.json', dict(rows=rows, history=history))
    risk_fits = {(c['year'], c['fold']): c for c in e.read(e.OUT/'fit-report.json')['cells']}
    old_fits = {(c['year'], c['fold']): c for c in e.read(e.old.OUT/'fit-report.json')['cells']}
    head_hashes = {}; model_replays = []
    with threadpool_limits(limits=2):
        for c in point_pre['cells']:
            y, k = c['year'], c['fold']; te = q.filter((pl.col('origin_year') == y) & (pl.col('outer_fold') == k))
            ft = f.filter(pl.col('row_id').is_in(te['row_id'])).sort('row_id'); assert ft['row_id'].equals(te['row_id'])
            h = old_fits[y, k]['outer_rate_model']; assert sha256_file(Path(h['path'])) == h['sha256']
            model = joblib.load(h['path']); rx = safe_matrix(ft, rnames); contributions = rx*model.coef_
            rates = model.predict(rx); assert np.allclose(rates, te['preseason_rate'], atol=1e-10, rtol=0)
            assert np.allclose(model.intercept_+contributions.sum(1), rates, atol=1e-10, rtol=0)
            head_hashes[h['path']] = h['sha256']
            px = ft.select(names).to_numpy(); point_fit = e.read(e.old.current.OUT/f'fit-{y}-{k}.json')
            for head in point_fit['heads']:
                assert sha256_file(Path(head['path'])) == head['sha256']; m = joblib.load(head['path'])
                raw = m.predict_proba(px)[:,1] if head['head'] == 'participation' else m.predict(px)
                target = 'preseason_raw_p' if head['head'] == 'participation' else 'preseason_raw_conditional_pa'
                assert np.allclose(raw, te[target], atol=1e-10, rtol=0)
                head_hashes[head['path']] = head['sha256']
            for i, r in enumerate(te.iter_rows(named=True)):
                write(DIST/f'details/{r["row_id"]}.json', dict(row_id=r['row_id'], rate_intercept=float(model.intercept_),
                    rate_inputs=encoded(rx[i]), rate_contributions=encoded(contributions[i]), replayed_rate=float(rates[i]),
                    opportunity_inputs=encoded(px[i]), count_parameters=risk_fits[y,k]['parameters'],
                    workload_log_center=r['workload_log_center']))
            model_replays.append(dict(year=y, fold=k, rows=len(te), rate_and_both_opportunity_heads_replayed=True))
            print('Exported actual model evidence', y, k, len(te), flush=True)
    public = next(s for s in e.read(e.old.current.OUT/'scores.json') if s['scope'] == 'public_broad')
    risk_scores = e.read(e.OUT/'scores.json')
    metadata = dict(title='Hitter research candidate', target_years=sorted(q['target_year'].unique().to_list()),
        forecasts=len(q), people=q['player_id'].n_unique(), information_dates=dates,
        rate_features=rnames, opportunity_features=names, public_benchmark=public, risk_scores=risk_scores,
        model_card=[
            'Hitting ability: a regularized linear model uses three seasons of MLB and minor-league outcome counts, kept in separate level groups, with age, listed position and draft evidence. It learns future MLB hitting from actual MLB participants, weighted by their PA. It is not a forecast that the player stays in his current minor level.',
            'Playing time: two scikit-learn histogram gradient-tree models predict any MLB PA and PA if active, using 251 count/history, level, age, draft, roster/status and dated prospect-ranking inputs. Expected PA multiplies those two quantities. Recent workload is not a diagnosis of health or proof of a future job.',
            'Delivered offense: predicted hitting and expected PA produce fixed-event batting plus replacement in custom win units. The associated count law adds a coherent next-year distribution around that same expected offense. It does not supply full WAR, salary surplus, trade value or six years of club control.',
            'Every displayed forecast excluded the tested player group from training and used mature earlier targets. All displayed historical results have already been used for development; this is not a pristine holdout. Historical sources and affiliations are retrospective reconstructions, not certified archived preseason snapshots.'
        ], limits=[
            'Elite-thin entrants remain systematically difficult: Kurtz, Reynolds and earlier Judge/Alonso cases expose readiness and hitting misses. Zero future MLB PA is not zero latent or career talent.',
            'Risk profiles are missing for 19,800 forecasts, and all 35 rate/workload slopes reach the predeclared bound. Valid integer support does not establish reliable profile-specific calibration.',
            'The current candidate does not use the separately tested raw contact block, explicit learned park adjustments, a complete diagnosed-injury model or team record. Their earlier failures do not reject those ideas generally.',
            'The known-player cohorts undercount some advancing-player PA and overcount others. Organization totals are not reconciled to a complete future roster, and unknown/new entrants are not fabricated.',
            'No defensive/catcher, running or positional components are included here. Full player-value and supported multi-year/control paths remain unfinished. The protected 2026 forecast and existing published explorer are unchanged.'
        ])
    write(DIST/'metadata.json', metadata)
    for name in ['index.html', 'app.js', 'app.css']: shutil.copyfile(TEMPLATE/name, DIST/name)
    paths = [Path(__file__), counts_path, TEAM/'source-report.json', TEAM/'source-review.json', TEAM/'features.parquet',
        e.OUT/'final-report.json', e.OUT/'reviewed-cases.json', e.OUT/'scores.json', e.WORK/'scored-predictions.parquet',
        e.old.current.OUT/'report.json', e.old.current.OUT/'preflight.json', e.old.current.OUT/'profile-support.parquet',
        e.old.current.OUT/'scores.json', *[TEMPLATE/n for n in ['index.html','app.js','app.css']]]
    artifacts = {str(p.relative_to(DIST)): sha256_file(p) for p in sorted(DIST.rglob('*')) if p.is_file()}
    e.write(OUT/'build-report.json', dict(forecasts=30506, detail_files=30506, reviewed_cases=len(cases),
        target_years=metadata['target_years'], player_membership_unchanged=True, means_unchanged=True,
        unknown_affiliations=sum(r['org']=='Unknown affiliation' for r in output), source_stats_cutoff=2024,
        actual_rate_and_opportunity_model_replays=model_replays, saved_head_hashes=head_hashes,
        protected_outcomes_used=False, frozen_forecast_changed=False, existing_explorers_changed=False,
        new_models_fitted=0, output_directory=str(DIST), source_hashes={str(p): sha256_file(p) for p in paths},
        output_hashes=artifacts, browser_verification_status='pending', full_goal_complete=False))
    print('Built research explorer', DIST, 'with', len(output), 'forecasts and complete per-row model evidence', flush=True)


if __name__ == '__main__': main()
