"""Complete a source-only audit after readable review; never authorize fits."""
from pathlib import Path
import json

from universal_baseball.storage import sha256_file
from audit_hitter_mlb_events import ROOT, OUT, read, verify, save


def main():
    public = ROOT / 'reports/model-evidence/hitter-mlb-events-source-audit/report.json'
    assert not public.exists() and not (OUT / 'final-review.json').exists()
    audit = read(OUT / 'audit.json'); verify(audit['hashes'])
    assert audit['fitted_models'] == 0 and audit['column_checks'] == 2215990
    cases = read(OUT / 'source-walks.json')
    assert len(cases) == len({r['row_id'] for r in cases}) == 17
    doc = ROOT / 'docs/hitter-mlb-events-source-audit-result.md'
    content = doc.read_text(encoding='utf8')
    assert all(r['player_name'].split()[-1] in content for r in cases)
    assert all(r['future_mutation_unchanged'] for r in cases)
    final = dict(audit, source_walkthrough_status='complete', source_gate_status='Reconstruction passed; reliability and raw-environment interpretation qualified',
                 disposition='Sources eligible for one prospective contract; no fitted or predictive result, no deployment',
                 fit_authorized=False, research_goal_remains_active=True,
                 completion_hashes={str(p): sha256_file(p) for p in [Path(__file__), doc, OUT / 'audit.json', OUT / 'source-walks.json']})
    public.parent.mkdir(parents=True, exist_ok=True)
    public.write_text(json.dumps(dict(final, player_source_cases=cases, readable_result='docs/hitter-mlb-events-source-audit-result.md'),
                                 indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf8', newline='\n')
    save('final-review.json', dict(final, public_report=str(public), public_report_sha256=sha256_file(public)))
    print('Seventeen source walks complete. No fits or forecasts changed; next experiment still requires its prospective contract.')


if __name__ == '__main__':
    main()
