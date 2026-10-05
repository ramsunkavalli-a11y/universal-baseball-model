"""Publish compact construction evidence, not bulk raw/foreign source tables."""
from pathlib import Path
import json
import polars as pl
from universal_baseball.storage import sha256_file
from prepare_hitter_production_2026 import ROOT,OUT,read,write
from freeze_hitter_selected_2026 import FROZEN

EVIDENCE=ROOT/'reports/model-evidence/hitter-selected-2026-freeze'


def main():
    assert not EVIDENCE.exists(),'Preserve published evidence'
    manifest=read(FROZEN/'freeze-manifest.json')
    assert sha256_file(FROZEN/'freeze-manifest.json')==(FROZEN/'freeze-manifest.sha256').read_text().strip()
    for f in manifest['files']:assert sha256_file(FROZEN/f['path'])==f['sha256']
    base=read(ROOT/'reports/generated/hitter-base-inputs-2025-reviewed/review.json')
    translated=read(ROOT/'reports/generated/hitter-translation-inputs-2025/review.json')
    training=read(ROOT/'reports/generated/hitter-tested-training-membership/review.json')
    availability=read(ROOT/'reports/generated/hitter-availability-2025-source/review.json')
    population=read(ROOT/'reports/generated/hitter-forecast-population-2025-review/review.json')
    replay=read(FROZEN/'independent-review.json');walks=read(FROZEN/'pre-freeze-player-walks.json')['walks']
    evidence_walks=[]
    for w in walks:
        s=w['source_walk']
        evidence_walks.append(dict(player_id=w['player_id'],name=w['name'],fold=w['fold'],stage=w['stage'],talent_route=w['talent_route'],
            source_history=s['source_history'] if s else None,actual_inputs=s['actual_inputs'] if s else w['actual_inputs'],
            intermediates=w['intermediates'],support=w['actual_training_support'],source_and_support_warnings=w['source_and_support_warnings'],
            rate_intercept=w['rate_intercept'],largest_rate_terms=w['rate_terms'][:12],
            participation_trace_reference=w['participation_logodds_trace']['reference'],
            participation_logodds=w['participation_logodds_trace']['raw_prediction'],
            largest_participation_path_effects=w['participation_logodds_trace']['feature_effects'][:8],
            conditional_pa_reference=w['conditional_pa_trace']['reference'],
            largest_conditional_pa_path_effects=w['conditional_pa_trace']['feature_effects'][:8],
            review_status=w['review_status'],realized_2026='Not opened at this frozen construction milestone'))
    support=pl.read_parquet(FROZEN/'profile-support.parquet')
    support_summary=support.group_by('head').agg(pl.col('row_id').n_unique().alias('forecast_rows'),
        pl.col('row_id').filter(pl.col('training_people')<20).n_unique().alias('any_sparse_profile'),
        pl.col('row_id').filter(pl.col('training_people')==0).n_unique().alias('any_unseen_profile')).sort('head').to_dicts()
    report=dict(status='candidate_frozen_construction_verified_final_outcomes_not_yet_opened',
        freeze_manifest_sha256=sha256_file(FROZEN/'freeze-manifest.json'),frozen_at_utc=manifest['frozen_at_utc'],
        frozen_files=len(manifest['files']),model_heads=25,population=4030,
        targets=manifest['targets'],coverage=manifest['coverage'],predictive_validation=False,
        original_legacy_freeze_unchanged=True,protected_outcomes_used=False,full_model_goal_complete=False,
        source_gates=dict(modern_base_rows_matched=63282,normal_origin_base_fields=base['base_fields_matched'],
            actual_job_model_features_matched=251,actual_tracked_model_features_matched=262,
            forecast_career_pa_rows_corrected=base['corrected_career_rows'],historical_training_cells_matched=training['saved_cells_checked'],
            repaired_2020_rows_retained=5133,translation_folds=translated['folds'],
            source_player_walks=base['source_player_walks'],base_peer_walks=base['peer_walks'],
            transaction_rows=availability['raw_transactions'],reported_retired=availability['reported_retired'],hard_unavailable=availability['hard_unavailable'],
            historical_availability_overrides_unchanged=availability['historical_overrides_checked'],
            all_level_status_completeness_certified=False,unmodeled_rostered_nonpitchers=3,mixed_role_members=population['mixed_role_inside']),
        training_rule=training['actual_retained_rule'],support_summary=support_summary,
        construction_review=dict(whole_forecast_replay=4030,exact_model_player_walks=len(walks),
            total_expected_pa=replay['expected_pa_total'],total_batting_contribution=replay['batting_contribution_total'],
            interpretation='Aggregate agreement is a sanity check, not independent accuracy or full-league coverage.'),
        source_corrections=['Initial base adapter copied raw V31 career exposure, not its corrected full-count definition; repaired before fitting.',
            'Preparation plan wrongly excluded repaired origin-2020 rows; actual retained training memberships verified and preserved.',
            'Initial status-table consumer inferred null-only columns; explicit nullable schema repair preserved raw captures and collector.'],
        known_gaps=read(ROOT/'reports/generated/hitter-forecast-population-2025-review/known-coverage-gaps.json'),
        player_walks=evidence_walks,
        next_steps=['Verify the self-contained frozen replay','Retrieve certified completed 2026 outcomes under recorded authorization',
            'Score once and walk big misses without retuning','Separate team-filtered explorer with forecasts, actuals and support/coverage warnings'],
        frozen_file_checksums=manifest['files'],evidence_exporter_sha256=sha256_file(Path(__file__)))
    EVIDENCE.mkdir(parents=True);write(EVIDENCE/'report.json',report)
    print(f'Compact frozen construction evidence saved: {len(walks)} fitted player walks; no 2026 outcomes.',flush=True)


if __name__=='__main__':main()
