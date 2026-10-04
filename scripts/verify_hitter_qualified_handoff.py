"""Independent artifact checks and a separate browser-review receipt; no refit."""
import json
import shutil
from pathlib import Path
import polars as pl
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/generated/hitter-qualified-handoff'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def main():
    assert not (OUT / 'final-report.json').exists(), 'Preserve completed receipt'
    manifest = read(OUT / 'manifest.json')
    for key in ['input_hashes', 'output_hashes']:
        for path, digest in manifest[key].items():
            assert sha256_file(Path(path)) == digest, path
    rows = read(OUT / 'explorer/data.json')
    old = read(ROOT / 'reports/generated/hitter-comparative-handoff-v72/explorer/data.json')
    scored_path = ROOT / 'reports/generated/hitter-preseason-readiness-v68/scored-predictions.parquet'
    forecasts = pl.read_parquet(scored_path)
    lookup = {r['row_id']: r for r in forecasts.iter_rows(named=True)}
    assert len(rows) == len(lookup) == len(old) == 30506
    for a, b in zip(old, rows, strict=True):
        assert a == {k: v for k, v in b.items() if k != 'evidence'}
        q = lookup[b['row_id']]
        assert (b['player_id'], b['origin_year'], b['target_year']) == (q['player_id'], q['origin_year'], q['target_year'])
        assert b['baseline_rate'] == q['preseason_rate']
        for key, arm in [('candidate', 'preseason'), ('original', 'baseline')]:
            for field, suffix in [('p','p'), ('conditional_pa','conditional_pa'), ('pa','pa'), ('value','value')]:
                assert b['arms'][key][field] == q[arm + '_' + suffix]
        assert b['next_pa'] == q['next_pa'] and b['next_value'] == q['next_value']
        e = b['evidence']
        assert not e['medical_scope'] or e['recorded_unresolved'] is not None
        assert not e['clinical_recovery_certified']
        if not e['medical_scope']:
            assert e['recorded_unresolved'] is None
    html = (OUT / 'explorer/index.html').read_text(encoding='utf8')
    assert '<input id="actual" type="checkbox">' in html
    assert 'html+=sourcePanel(r)' in html and 'sourceMatch(r)' in html
    image = OUT / 'giants-browser-check.jpg'
    assert image.exists() and image.stat().st_size > 1000
    report = dict(manifest, browser_verification='complete', saved_v68_forecasts_independently_matched=30506,
        reviewed_browser_cases=['McLain 2025', 'Franco 2024', 'Thames 2017', 'Belt 2024', 'MLBAM 808975 2025'],
        reviewed_controls=['Giants upper minors 2025: 34 rows', 'original 293 PA versus candidate 322 PA',
            'listing mismatch 2025: 168 rows', 'actual results off/on/off', 'hitting-only sort and origin/source panels'],
        screenshot_sha256=sha256_file(image), predictive_validation_changed=False,
        completed_source_review='hitter-roster-provenance-audit: nine player walks',
        current_handoff_is_not_new_model_experiment=True,
        result_hashes={str(p):sha256_file(p) for p in [Path(__file__), scored_path,
            ROOT/'docs/hitter-qualified-handoff-result.md', ROOT/'tests/test_hitter_qualified_handoff.py']})
    (OUT / 'final-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    dest = ROOT / 'reports/model-evidence/hitter-qualified-handoff'
    dest.mkdir(parents=True, exist_ok=True)
    for name in ['manifest.json', 'final-report.json', 'giants-browser-check.jpg']:
        shutil.copy2(OUT / name, dest / name)
        assert sha256_file(OUT / name) == sha256_file(dest / name)
    print('30,506 rows independently matched to saved V68 forecasts; no forecast changes; browser receipt saved.')


if __name__ == '__main__':
    main()
