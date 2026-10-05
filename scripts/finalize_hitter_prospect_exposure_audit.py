"""Publish completed source-aligned review without modifying earlier receipts."""
import json
from pathlib import Path
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/hitter-prospect-exposure-allocation-audit-source-aligned'
PUBLIC=ROOT/'reports/model-evidence/hitter-prospect-exposure-allocation-audit'


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def main():
    assert not (OUT/'review-completion.json').exists(), 'Preserve review receipt'
    verification=read(OUT/'verification.json')
    for key in ['input_hashes','output_hashes']:
        for p,h in verification[key].items():
            assert sha256_file(Path(p))==h,p
    source=read(OUT/'source-check.json')
    assert source['fields_compared']==2827104 and not any(c['mismatches'] for c in source['checks'])
    assert source['diagnostic_groups_use_actual_fitted_inputs'] and source['forecast_changes'] is False
    accounting=read(OUT/'accounting.json');walks=read(OUT/'player-walks.json')
    assert walks['focal_cases']==14 and walks['total_replayed_cases']==39
    assert walks['mechanical_replay_status']=='complete' and walks['models_refitted']==0
    docs=[ROOT/'docs/hitter-prospect-exposure-allocation-audit-result.md',
          ROOT/'docs/hitter-prospect-exposure-allocation-player-review.md',
          ROOT/'docs/hitter-prospect-exposure-audit-execution-note.md']
    assert all(p.exists() for p in docs)
    for v in ['historical','evaluated2026']:
        for r in accounting[v]:
            delta=r['conditional_error']-r['active_probability_discount']+r['nonarrival_allocation']
            assert abs(delta-r['total_forecast_error'])<1e-7
    report=dict(diagnostic_review_complete=True,new_fits=0,changed_forecasts=0,
        source_integrity_pass=True,player_walkthrough_status='complete',
        predictive_improvement_established=False,deployment_approved=False,
        disposition='Close missing level-PA hypothesis and repeated specialization; retain evaluated reference',
        next_boundary='Entrant source coverage and comparable public benchmark before another prospect fit',
        focal_cases=14,replayed_cases=39,pa_heads_replayed=78,
        historical_losses='Pooled equal-record diagnostic; not a new equal-year improvement',
        final2026_used='Already exposed explanatory splits only; no candidate selection or tuning',
        source_checks=source,accounting=accounting,selection=read(OUT/'selection.json'),
        player_walks=walks,completed_readable_review_hashes={str(p):sha256_file(p) for p in docs},
        input_hashes=verification['input_hashes'],audit_output_hashes=verification['output_hashes'],
        finalization_script_sha256=sha256_file(Path(__file__)))
    PUBLIC.mkdir(parents=True,exist_ok=True)
    path=PUBLIC/'report.json';assert not path.exists()
    path.write_text(json.dumps(report,indent=2,allow_nan=False,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
    receipt=dict(player_walkthrough_status='complete',focal_cases=14,replayed_cases=39,
        models_refitted=0,forecast_changes=0,predictive_gain=False,deployment_approved=False,
        source_and_mechanical_integrity=True,reasonability='Failures qualified; no universal boost justified',
        interrupted_artifacts_preserved=True,earlier_pending_receipts_superseded_not_overwritten=True,
        report_sha256=sha256_file(path),readable_review_hashes=report['completed_readable_review_hashes'])
    (OUT/'review-completion.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':
    main()
