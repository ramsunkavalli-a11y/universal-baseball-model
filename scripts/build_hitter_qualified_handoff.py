"""Expose reviewed origin evidence without changing any historical forecast."""
import json
from collections import Counter
from pathlib import Path
import polars as pl
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'reports/generated/hitter-comparative-handoff-v72'
OUT = ROOT / 'reports/generated/hitter-qualified-handoff'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def evidence_metadata(feature, context, medical, roster):
    """All decisions depend on cutoff evidence, never following-year outcomes."""
    flags = []
    state = context['availability_state']
    if roster['event_listing_conflict']:
        flags.append('Listing and dated event differ; not a proven roster error')
    if state in {'administrative_leave', 'restricted', 'finite_ineligible', 'suspended_unspecified'}:
        flags.append('Availability unresolved; model chance is not legal clearance')
    if context['foreign_performance_missing']:
        flags.append('Foreign production missing; not zero talent')
    if not medical['medical_scope']:
        flags.append('Medical capture coverage unknown; not known healthy')
    elif medical['recorded_unresolved']:
        flags.append('Reported medical spell unresolved; not a recovery diagnosis')
    if not feature['origin_evidence_bridge']:
        flags.append('Origin eligibility evidence unverified')
    return dict(
        listing_returned=bool(feature['on_40man']),
        roster_event_sign=roster['roster_event_sign'],
        roster_event_date=roster['roster_event_date'],
        roster_event_capture_scope=roster['roster_event_capture_scope'],
        event_listing_conflict=roster['event_listing_conflict'],
        date_conflict_count=roster['date_conflict_count'],
        availability_state=state,
        latest_context_date=str(context['latest_context_date']) if context['latest_context_date'] else None,
        medical_scope=medical['medical_scope'],
        recorded_unresolved=medical['recorded_unresolved'],
        reported_roster_returns730=medical['reported_roster_returns730'],
        observed_return_intervals730=medical['observed_return_intervals730'],
        clinical_recovery_certified=medical['clinical_recovery_certified'],
        foreign_performance_missing=context['foreign_performance_missing'],
        origin_evidence_bridge=bool(feature['origin_evidence_bridge']),
        corrected_medical_states_used_as_predictors=False,
        availability_states_used_as_predictors=False,
        source_flags=flags,
    )


EXTRA_JS = r"""
function sourceMatch(r){const e=r.evidence,v=by('evidence').value;return !v || (v==='listing'&&e.event_listing_conflict) || (v==='medical'&&!e.medical_scope) || (v==='foreign'&&e.foreign_performance_missing) || (v==='availability'&&['administrative_leave','restricted','finite_ineligible','suspended_unspecified'].includes(e.availability_state)) || (v==='eligibility'&&!e.origin_evidence_bridge);}
function sourcePanel(r){const e=r.evidence;return '<h3>Source evidence and availability</h3><p>Year-end 40Man request: '+(e.listing_returned?'player returned in the saved response':'player not returned in the saved response')+'. Neither establishes continuous reserve rights or a future job.</p><p>Latest narrowly classified roster event: '+esc(e.roster_event_sign)+' ('+esc(e.roster_event_date??'unknown date')+'). '+(e.event_listing_conflict?'This differs from the returned listing. Later ambiguous transactions can explain the difference; this is not a proven error.':'No mismatch in this narrow diagnostic; that does not certify the listing.')+' This is not a complete ordered rights reconstruction.</p><p>Captured availability state: '+esc(e.availability_state.replaceAll('_',' '))+'; latest context event '+esc(e.latest_context_date??'unknown')+'. These context states and corrected medical observations are not inputs to the current fitted opportunity heads. Permanent ineligibility and reported retirement are separate zero-opportunity rules.</p><p>Medical capture scope: '+(e.medical_scope?'covered by the available capture, not complete clinical records':'unknown; do not read as healthy')+'. Unresolved reported spell: '+(e.recorded_unresolved==null?'unknown':e.recorded_unresolved?'yes':'none identified in available observations')+'. Observed return intervals: '+n(e.observed_return_intervals730)+'; reported roster returns: '+n(e.reported_roster_returns730)+'. A roster activation or playing appearance is not medical clearance.</p><p>Foreign batting evidence: '+(e.foreign_performance_missing?'known production missing from this branch':'no missing foreign production identified by this limited source; completeness not certified')+'. Origin eligibility bridge: '+(e.origin_evidence_bridge?'some dated evidence available':'unverified; player remains in the comparison')+'.</p><ul>'+e.source_flags.map(f=>'<li>'+esc(f)+'</li>').join('')+'</ul><p class="muted">These warnings concern evidence quality. The training-support counts below concern available examples. Neither supplies a calibrated future-performance interval. No alternate or synthetic availability forecast has been substituted.</p>';}
"""


def qualified_html(text):
    def replace(old, new):
        nonlocal text
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    replace('Hitter forecast comparison</h1>', 'Hitter forecasts and source evidence</h1>')
    replace('<div class="controls">', '<p class="notice">Source review: returned roster lists are imperfect historical proxies. Availability warnings do not change forecasts. This research branch has no calibrated continuous prediction intervals. Protected 2026 outcomes were not used in these forecasts; an incidental current-player summary was encountered in a source search and is disclosed in the review.</p>\n<div class="controls">')
    replace('<label>Find a player', '<label>Evidence review<select id="evidence"><option value="">All evidence</option><option value="listing">Listing/event mismatch</option><option value="availability">Unresolved availability</option><option value="medical">Medical coverage unknown</option><option value="foreign">Foreign production missing</option><option value="eligibility">Origin evidence unverified</option></select></label>\n<label>Find a player')
    replace("const pos=v=>", EXTRA_JS + '\nconst pos=v=>')
    replace("r.target_year===y&&(!org", "r.target_year===y&&sourceMatch(r)&&(!org")
    replace("n(r.flags.length)+(r.reviewed?' · reviewed':'')", "esc(r.evidence.source_flags[0]??'No specific source warning identified')+'<span class=\"sub\">'+n(r.flags.length)+' model review flags</span>'")
    replace("html+='<h3>What was known", "html+=sourcePanel(r);\nhtml+='<h3>What was known")
    replace("['year','org','stage','actual','model']", "['year','org','stage','actual','model','evidence']")
    return text


def main():
    assert not (OUT / 'manifest.json').exists(), 'Preserve the existing handoff'
    old_manifest = read(OLD / 'manifest.json')
    for path, digest in old_manifest['artifact_hashes'].items():
        assert sha256_file(Path(path)) == digest, path
    audit = ROOT / 'reports/generated/hitter-roster-provenance-audit'
    integration = ROOT / 'reports/generated/hitter-candidate-integration-audit'
    for path in [audit / 'final-report.json', integration / 'final-report.json']:
        report = read(path)
        assert report['player_walkthrough_status'] == 'complete'
        for key in ['input_hashes', 'review_hashes']:
            for p, digest in report.get(key, {}).items():
                assert sha256_file(Path(p)) == digest, p
    feature_path = ROOT / 'reports/generated/hitter-preseason-readiness-v68/features.parquet'
    context_path = ROOT / 'reports/generated/practical-hitter-opportunity-status-v59/context.parquet'
    medical_path = ROOT / 'reports/generated/hitter-observed-return-v60/observation-states.parquet'
    roster_path = audit / 'states.parquet'
    features = pl.read_parquet(feature_path)
    sources = [pl.read_parquet(p) for p in [context_path, medical_path, roster_path]]
    lookups = [{r['row_id']: r for r in table.iter_rows(named=True)} for table in [features, *sources]]
    rows = read(OLD / 'explorer/data.json')
    assert len(rows) == len({r['row_id'] for r in rows}) == 30506
    for row in rows:
        f, c, m, s = [lookup[row['row_id']] for lookup in lookups]
        for source in [f, c, m]:
            assert (source['player_id'], source['origin_year']) == (row['player_id'], row['origin_year'])
        assert row['target_year'] <= 2025
        assert not c['latest_context_date'] or c['latest_context_date'].year <= row['origin_year']
        assert not s['roster_event_date'] or s['roster_event_date'] <= f"{row['origin_year']}-12-31"
        row['evidence'] = evidence_metadata(dict(f, origin_evidence_bridge=row['origin_evidence_bridge']), c, m, s)
    dest = OUT / 'explorer'
    dest.mkdir(parents=True, exist_ok=True)
    for name in ['history.json', 'reviews.json', 'scores.json', 'probability.json', 'comparison-reviews.json']:
        (dest / name).write_bytes((OLD / 'explorer' / name).read_bytes())
    (dest / 'data.json').write_text(json.dumps(rows, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n', encoding='utf8')
    (dest / 'index.html').write_text(qualified_html((OLD / 'explorer/index.html').read_text(encoding='utf8')), encoding='utf8')
    # Independent full-population comparison: the only addition is evidence.
    original = read(OLD / 'explorer/data.json')
    exported = read(dest / 'data.json')
    for before, after in zip(original, exported, strict=True):
        assert {k: v for k, v in after.items() if k != 'evidence'} == before
    counts = {key: sum(bool(r['evidence'][key]) for r in rows) for key in ['event_listing_conflict', 'medical_scope', 'foreign_performance_missing', 'origin_evidence_bridge']}
    inputs = [feature_path, context_path, medical_path, roster_path, OLD / 'manifest.json', audit / 'final-report.json', integration / 'final-report.json', Path(__file__)]
    manifest = dict(rows=len(rows), exact_original_row_and_forecast_preservation=True, source_counts=counts,
        availability_counts=dict(Counter(r['evidence']['availability_state'] for r in rows)),
        no_new_fits=True, actual_results_hidden_by_default=True, team_filter=True,
        calibrated_continuous_intervals_available=False, browser_verification='pending',
        protected_outcomes_used_in_calculations=False, incidental_search_exposure=read(audit / 'final-report.json')['incidental_public_search_exposure'],
        frozen_forecast_changed=False, deployed_explorer_changed=False, whole_goal_complete=False,
        input_hashes={str(p): sha256_file(p) for p in inputs},
        output_hashes={str(p): sha256_file(p) for p in dest.iterdir()})
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf8')
    print(json.dumps(dict(rows=len(rows), unchanged_forecasts=True, source_counts=counts)))


if __name__ == '__main__':
    main()
