"""Verify and persist player source traces without claiming a predictive result."""
import json
from pathlib import Path
import polars as pl
from universal_baseball.storage import sha256_file
import source_hitter_team_record_v75 as source


def main():
    report = json.loads((source.OUT/'source-report.json').read_text(encoding='utf8'))
    for p, h in report['input_hashes'].items():
        assert sha256_file(Path(p)) == h, p
    assert sha256_file(source.OUT/'features.parquet') == report['output_sha256']
    f = pl.read_parquet(source.OUT/'features.parquet').sort('row_id')
    first = pl.read_parquet(source.OUT/'features-first-pass.parquet').sort('row_id')
    old = pl.read_parquet(source.previous.OUT/'features.parquet').sort('row_id')
    assert f.select(old.columns).equals(old) and first.select(old.columns).equals(old)
    anchor_path = source.previous.OUT/'scored-predictions.parquet'
    q = pl.read_parquet(anchor_path).sort('row_id')
    q = q.with_columns(pl.col('preseason_p').alias('current_p'),
                      pl.col('preseason_conditional_pa').alias('current_conditional_pa'),
                      pl.col('preseason_pa').alias('current_pa'),
                      pl.col('preseason_value').alias('current_value'))
    counts_path = source.ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    counts = pl.read_parquet(counts_path)
    ctx_cols = [c for c in f.columns if c.startswith('context_') or c.startswith('org_record_')]
    pa_features = json.loads((source.previous.OUT/'preflight.json').read_text(encoding='utf8'))['pa_features']
    cases = []
    notes = {
        701762: 'Stockton and the draft signing independently point to Oakland. A 69-win club may create opportunity, but team record cannot itself make ten expected PA adequate or prove Kurtz MLB-ready.',
        694671: 'Hickory and draft signing point to Texas. The 90-win club is an opposite-risk control: contenders can also give elite young hitters full-season opportunity.',
        677594: 'December 31 roster points to Seattle, a 90-win club. Elite readiness and roster context already exist; any record effect must be incremental rather than replacing those predictors.',
        624413: 'Dated Las Vegas affiliation is the Mets, not its later Oakland parent. The 77-win record is plausible opportunity context but 693 actual PA is not attributable to that record.',
        641355: 'Tulsa belongs to the 91-win Dodgers in this source season. This successful debut on a strong club prevents imposing a universal bad-team boost.',
        702616: 'Aberdeen belongs to the 101-win Orioles. Current expected PA exceeds observed PA. This is a competing direction against the underpredicted elite debutants, not evidence that all strong clubs block prospects.',
        670867: 'Last batting alone incorrectly points to Atlanta. Transaction 338890, known December 16, establishes the Angels. The general rule corrects ownership, not his unchanged approximately two expected PA. No MLB arrival is preserved.',
        592450: 'December 31 Yankees roster is direct dated evidence. The primary proposed experiment must leave this established hitter forecast unchanged; any all-player sensitivity remains separately labeled.',
    }
    for c in report['source_cases']:
        pid, year = c['player_id'], c['origin_year']
        r = f.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == year)).row(0, named=True)
        b = q.filter(pl.col('row_id') == r['row_id']).row(0, named=True)
        peers = []
        for p in c['peers']:
            peer = q.filter((pl.col('player_id') == p['player_id']) & (pl.col('origin_year') == year)).row(0, named=True)
            peers.append(dict(**p, current_pa=peer['current_pa'], current_p=peer['current_p'],
                              current_value=peer['current_value'], next_value=peer['next_value']))
        cases.append(dict(player_id=pid, player_name=r['player_name'], origin_year=year,
            row_id=r['row_id'], fold=r['outer_fold'], selection='Fixed source cases from prefit contract',
            source_history=counts.filter((pl.col('player_id') == pid) & pl.col('season').is_between(year-2, year)).sort('season', 'bucket').to_dicts(),
            original_opportunity_inputs={n:r[n] for n in pa_features}, proposed_context={n:r[n] for n in ctx_cols},
            first_pass_context=first.filter(pl.col('row_id') == r['row_id']).select([n for n in ctx_cols if n in first.columns]).to_dicts()[0],
            unchanged_current_forecast={n:b[n] for n in ['current_p','current_conditional_pa','current_pa','baseline_rate','current_value']},
            future_MLB_observation={n:b[n] for n in ['target_year','next_pa','next_value']},
            actual_MLB_counts=counts.filter((pl.col('player_id') == pid) & (pl.col('season') == year+1) & (pl.col('bucket') == 'MLB')).to_dicts(),
            peers=peers, peer_selection='Same origin, stage and debut state; closest age, minor PA and ranking, without future outcomes',
            review=notes[pid], model_mechanism='No new fits or predictions. Context is an input candidate, not an applied PA adjustment.'))
    evaluated = f.filter(pl.col('row_id').is_in(q['row_id'].to_list()))
    known = int(evaluated['org_record_known'].sum())
    assert len(evaluated) == 30506 and q['target_year'].max() == 2025
    assert next(c for c in cases if c['player_id']==670867)['proposed_context']['context_parent_id'] == 108
    source.write('reviewed-source-cases.json', cases)
    paths = [source.OUT/'source-report.json', source.OUT/'source-first-pass.json', source.OUT/'features-first-pass.parquet',
             source.OUT/'reviewed-source-cases.json', anchor_path, counts_path, Path(__file__),
             source.ROOT/'docs/hitter-team-record-v75-source-review.md']
    source.write('source-review.json', dict(source_review_status='complete_with_ownership_coverage_qualification',
        player_walkthrough_status='complete_for_source_only', cases=len(cases),
        source_rows=len(f), evaluation_rows=len(evaluated), evaluation_context_known=known,
        never_debut_known=int(evaluated.filter(pl.col('prior_debut')==0)['org_record_known'].sum()),
        source_hashes=report['input_hashes'], review_hashes={str(p):sha256_file(p) for p in paths},
        features_sha256=sha256_file(source.OUT/'features.parquet'),
        original_251_inputs_unchanged=True, no_models_fitted=True, no_predictive_improvement_claim=True,
        protected_outcomes_used=False, frozen_forecast_changed=False,
        next_step='Full/active actual fold preflights followed by the locked coverage-control versus record comparison; subsequent saved-model player review required.'))
    print('Source-only review complete', len(cases), known, '/', len(evaluated), flush=True)


if __name__ == '__main__':
    main()
