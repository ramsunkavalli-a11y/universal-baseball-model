"""Append modern-base equivalence and independently checked source-player walks."""
from pathlib import Path
import json
import numpy as np
import polars as pl
from universal_baseball.hitter_forecast_base_tested import tested_base_inputs
from universal_baseball.hitter_forecast_inputs import pooled_inputs
from universal_baseball.hitter_forecast_tracking import materialize_tracking
from universal_baseball.historical_prospect_rank import features as rank_features
from universal_baseball.storage import sha256_file
from assemble_hitter_base_inputs_2025 import historical_snapshots, OLD
from prepare_hitter_games_v38 import features as game_features

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/hitter-base-inputs-2025-reviewed'
INITIAL = ROOT/'reports/generated/hitter-base-inputs-2025'


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def write(p, value):
    assert not p.exists(), f'Preserve {p}'
    p.write_text(json.dumps(value, indent=2, allow_nan=False, default=str)+'\n', encoding='utf8', newline='\n')


def compare(a, b, names):
    a, b = a.sort('row_id'), b.sort('row_id')
    assert a['row_id'].equals(b['row_id'])
    for c in names:
        if a[c].dtype in [pl.Float64, pl.Float32]:
            assert np.allclose(a[c].to_numpy(), b[c].to_numpy(), rtol=0, atol=1e-12, equal_nan=True), c
        else:
            assert a[c].equals(b[c], check_dtypes=False), c


def families(base, counts, draft, games, ranks, annual, *, cutoff):
    out = base.join(pooled_inputs(base, counts, draft, source_cutoff=cutoff), on='row_id', validate='1:1')
    out, _ = game_features(out, games)
    lookup = {(r['season'], r['player_id']): r['rank'] for r in ranks.iter_rows(named=True)}
    capacities = {r['season']: r['list_capacity'] for r in ranks.iter_rows(named=True)}
    records = [dict(row_id=r['row_id'], **rank_features(r['player_id'], r['origin_year']+1, lookup, capacities))
               for r in out.iter_rows(named=True)]
    overlay = pl.DataFrame(records, schema_overrides={c:pl.Float64 for c in records[0] if c.startswith('scout_')})
    scout = [c for c in overlay.columns if c.startswith('scout_')]
    out = out.join(overlay.with_columns(pl.col(scout).fill_null(-1.)), on='row_id', validate='1:1')
    out, _, _ = materialize_tracking(out, annual, source_cutoff=cutoff)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT/'review.json').exists(), 'Preserve completed review'
    original = read(INITIAL/'assembly-review.json')
    for p, h in original['input_hashes'].items():
        assert sha256_file(Path(p)) == h, p
    for p, h in original['output_hashes'].items():
        assert sha256_file(Path(p)) == h, p
    paths = dict(stints=ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet',
        counts=ROOT/'reports/generated/practical-hitter-v31/counts.parquet',
        values=ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet',
        debuts=ROOT/'reports/generated/hitter-arrival-source-repair-v1/debut-dates.parquet',
        roster=ROOT/'reports/generated/hitter-arrival-source-repair-v1/year-end-rosters.parquet',
        saved=OLD/'opportunity-history-sources-v2/tables/hitter_snapshots.parquet',
        exits=ROOT/'model_artifacts/post-arrival-support-v17/panel.parquet',
        raw=ROOT/'reports/generated/practical-hitter-v31/features.parquet',
        modern=ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet',
        draft=OLD/'draft-history/draft-history.parquet', games=ROOT/'reports/generated/practical-hitter-v38/game-counts.parquet',
        ranks=ROOT/'reports/generated/hitter-preseason-readiness-v67/ranks.parquet',
        annual=ROOT/'reports/generated/hitter-tracking-2025-audit/annual-launch-features-through-2025.parquet')
    s = {k: pl.read_parquet(p) for k, p in paths.items()}
    modern = s['modern'].filter(pl.col('origin_year') != 2020).sort('row_id')
    snaps = historical_snapshots(s['raw'], s['exits'], s['saved']).filter(pl.col('origin_year') != 2020)
    assert len(snaps) == len(modern) == 58149
    hist = tested_base_inputs(snaps, s['stints'].filter(pl.col('season') <= 2024), s['counts'].filter(pl.col('season') <= 2024),
        s['values'].filter(pl.col('season') <= 2024), s['debuts'].filter(pl.col('mlb_debut_date').dt.year() <= 2024),
        s['roster'], source_cutoff=2024)
    compare(hist, modern, hist.columns)
    hist_all = families(hist, s['counts'].filter(pl.col('season') <= 2024), s['draft'].filter(pl.col('draft_year') <= 2024),
        s['games'].filter(pl.col('season') <= 2024), s['ranks'], s['annual'].filter(pl.col('season') <= 2024), cutoff=2024)
    numeric = read(ROOT/'reports/generated/practical-hitter-numeric-repair-v53/preflight.json')['rate_features']
    pa_names = read(ROOT/'reports/generated/hitter-preseason-readiness-v68/preflight.json')['pa_features']
    compare(hist_all, modern, sorted(set(numeric+pa_names)))
    tracking_path = ROOT/'reports/generated/hitter-statcast-next-year/features.parquet'
    tracking_preflight_path = tracking_path.parent/'preflight.json'
    tracked_names = read(tracking_preflight_path)['arms']['ridge_measurements']
    compare(hist_all, pl.read_parquet(tracking_path).filter(pl.col('origin_year') != 2020), tracked_names)
    membership = pl.read_parquet(INITIAL/'membership.parquet')
    full_roster = pl.concat([s['roster'], pl.read_parquet(ROOT/'reports/generated/hitter-rosters-2025-source/year-end-2025.parquet')], how='vertical_relaxed')
    current = tested_base_inputs(membership, s['stints'], s['counts'], s['values'], s['debuts'], full_roster, source_cutoff=2025)
    ranks = pl.concat([s['ranks'], pl.read_parquet(ROOT/'reports/generated/hitter-preseason-2026-archive-probe/preseason-2026-ranks.parquet')])
    assembled = families(current, s['counts'], s['draft'].filter(pl.col('draft_year') <= 2025), s['games'], ranks, s['annual'], cutoff=2025)
    assert not any(c.startswith('next_') for c in assembled.columns)
    old = pl.read_parquet(INITIAL/'assembled-before-translation.parquet').sort('row_id')
    compare(assembled, old, [c for c in old.columns if c != 'career_mlb_observed_pa'])
    changes = old.select('row_id','player_id','player_name','career_mlb_observed_pa').rename({'career_mlb_observed_pa': 'initial_career_pa'}).join(
        current.select('row_id','career_mlb_observed_pa'), on='row_id', validate='1:1').filter(pl.col('initial_career_pa') != pl.col('career_mlb_observed_pa'))
    assembled.write_parquet(OUT/'assembled-before-translation.parquet')
    changes.write_parquet(OUT/'career-pa-corrections.parquet')
    # Recheck actual inputs independently from aggregate source counts, not just
    # source->adapter identity. This gate deliberately has no forecast/outcome.
    cases = read(INITIAL/'source-player-cases.json')['cases']; completed = []
    counts = s['counts']; draft = s['draft']; raw_ranks = {(r['season'],r['player_id']):r['rank'] for r in ranks.iter_rows(named=True)}
    for case in cases:
        pid = case['player_id']; peers = [p['player_id'] for p in case['peers']]; walks = []
        for ident in [pid, *peers]:
            a = assembled.filter(pl.col('player_id') == ident).row(0, named=True)
            history = counts.filter((pl.col('player_id') == ident) & pl.col('season').is_between(2023,2025))
            career = counts.filter((pl.col('player_id') == ident) & (pl.col('bucket') == 'MLB') & (pl.col('season') <= 2025))['plate_appearances'].sum()
            assert a['career_mlb_observed_pa'] == career
            for k in range(3):
                h = history.filter(pl.col('season') == 2025-k)
                mp = h.filter(pl.col('bucket') == 'MLB')['plate_appearances'].sum()
                assert a[f'pa_{k}'] == mp and a[f'minor_pa_{k}'] == h['plate_appearances'].sum()-mp
                for bucket in ['MLB', 'AAA', 'AA', 'DSL']:
                    h0 = history.filter(pl.col('bucket') == bucket)
                    expected = sum((1.,.8,.6)[2025-r['season']]*r['plate_appearances'] for r in h0.iter_rows(named=True))
                    assert np.isclose(a[f'pooled_{bucket}_pa'], expected, atol=1e-12)
            assert a['scout_listed_0'] == int((2026, ident) in raw_ranks)
            annual = s['annual'].filter((pl.col('player_id') == ident) & (pl.col('season') == 2025))
            # Tracking values reviewed independently in the preceding source gate.
            walks.append(dict(player_id=ident, name=a['player_name'], age=a['age'], age_unknown=bool(a['age_unknown']),
                stage=a['stage'], membership=membership.filter(pl.col('player_id') == ident).to_dicts()[0],
                actual_inputs={c:a[c] for c in ['prior_debut','elapsed','source_position','on_40man','career_mlb_observed_pa',
                    'pa_0','pa_1','pa_2','minor_pa_0','minor_pa_1','minor_pa_2','pooled_MLB_pa','pooled_AAA_pa','pooled_AA_pa','pooled_DSL_pa',
                    'draft_known','draft_year','draft_rank','draft_elapsed','scout_listed_0','scout_rank_score_0','sc_tracked']},
                source_history=history.to_dicts(), current_tracking=annual.to_dicts(),
                judgments=['Own-origin PA and weighted level exposure reproduce from source counts.',
                    'Career MLB exposure includes split-level MLB appearances.',
                    'No observed 2025 production means inactive stage, not zero future talent or exclusion.' if a['pa_0']+a['minor_pa_0']==0
                    else 'Stage follows observed 2025 competition; forecast arrival is not inferred from stage alone.',
                    'Age is explicitly unknown with the fixed fallback.' if a['age_unknown'] else 'Recorded origin age is available.',
                    'Preseason rank is origin-known evidence, not an outcome or a guaranteed job.']))
        completed.append(dict(player_id=pid, primary=walks[0], exposure_peers=walks[1:], review_status='source_checks_complete',
                              predictive_reasonability='Not yet assessed: no candidate forecasts fitted or outcomes opened.'))
    write(OUT/'completed-player-walks.json', dict(cases=completed, source_only=True, future_outcomes_used=False))
    excluded = s['modern'].filter(pl.col('origin_year') == 2020)
    excluded.select('row_id','player_id','origin_year','target_year').write_parquet(OUT/'excluded-origin-2020.parquet')
    extra = s['modern'].join(s['raw'].select('row_id'), on='row_id', how='anti')
    assert len(extra) == 4536 and set(extra['origin_year']) == {2020} and len(excluded) == 5133
    module = ROOT/'src/universal_baseball/hitter_forecast_base_tested.py'
    inputs = [*paths.values(), INITIAL/'assembly-review.json', INITIAL/'membership.parquet', INITIAL/'source-player-cases.json',
              Path(__file__), module, ROOT/'docs/hitter-2025-base-equivalence-amendment.md', tracking_path, tracking_preflight_path]
    write(OUT/'review.json', dict(raw_build_preserved=True, modern_rows=63282, eligible_non2020_rows=58149,
        excluded_origin2020_rows=5133, added_origin2020_rows=4536, base_fields_matched=len(hist.columns),
        base_field_comparisons=len(hist)*len(hist.columns), actual_model_features_matched=len(set(numeric+pa_names)),
        tracking_model_features_matched=len(tracked_names),
        historical_model_input_equivalence=True, forecast_population=len(assembled), corrected_career_rows=len(changes),
        source_player_walks=len(completed), peer_walks=sum(len(c['exposure_peers']) for c in completed),
        source_player_walkthrough_status='complete', predictive_reasonability_status='not_yet_fitted',
        candidate_ready_to_fit=False, candidate_frozen=False, protected_outcomes_used=False,
        remaining=['held-player own-origin translation','availability evidence','qualified foreign/new entrant coverage'],
        input_hashes={str(p):sha256_file(p) for p in inputs},
        output_hashes={str(p):sha256_file(p) for p in OUT.iterdir() if p.suffix in ['.parquet','.json']}))
    print(f'Corrected base and {len(set(numeric+pa_names))} model inputs reproduce on {len(hist)} eligible historical rows; {len(changes)} forecast career repairs.', flush=True)


if __name__ == '__main__':
    main()
