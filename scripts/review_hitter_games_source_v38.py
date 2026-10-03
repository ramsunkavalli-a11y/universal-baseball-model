"""Complete the dated source checkpoint before the workload comparison."""
import prepare_hitter_games_v38 as s
from universal_baseball.storage import sha256_file


def main():
    audit=s.r.read(s.OUT/'source-audit.json')
    for p,h in audit['input_hashes'].items():assert sha256_file(s.Path(p))==h,p
    cases=s.r.read(s.OUT/'source-cases.json');notes_path=s.r.ROOT/'config/practical_hitter_v38_source_notes.json';notes=s.r.read(notes_path)
    assert len(cases)==len(notes)==6
    lines=['# V38 game-source review, before fitting','',
        'All 122,799 existing stints reconcile PA exactly; gamesPlayed is available for every stint. No positive PA with zero games, no negative games, no conflicting keyed captures or more than 12 PA/appearance. All old features remain bit-exact. These are team appearances, not dated starts, healthy days or diagnosed absences. No 2026 outcomes.','',
        'Fixed cases and three origin-only peers per case. Distance uses age, current MLB/AAA/AA PA and draft evidence, within the same origin/stage/debut group. Outcomes are not used in source selection.','']
    for c in cases:
        key=f"{c['player_name']}|{c['origin_year']}";assert key in notes
        lines.extend([f"## {c['player_name']}: origin {c['origin_year']}",'',notes[key],'',
            '| Player ID | Year | League | PA | Games | Raw PA/game |','|---:|---:|---|---:|---:|---:|'])
        for h in c['source_history']:
            ratio=f"{h['plate_appearances']/h['games_played']:.3f}" if h['games_played'] else 'undefined'
            lines.append(f"| {h['player_id']} | {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['games_played']} | {ratio} |")
        lines.extend(['','Actual new inputs: '+', '.join(f'{k}={v:.5g}' for k,v in c['origin_inputs'].items() if k.startswith(('games_','role_')))+'.',''])
    lines.extend(['## Scope and disposition','',
        'Source extraction is usable for the fixed model comparison. This is not a predictive win. Aggregate games cannot measure healthy-days fractions, date of promotion, actual starts or guarantee a future job. Existing foreign/inactive and historical roster qualifications remain. MLB 2020 exposure alone is schedule-scaled 162/60; no canceled minor games are invented. Proceed to the one predeclared workload fit, retaining existing batting rates and every test row.'])
    path=s.OUT/'source-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    s.write('source-review.json',dict(source_walkthrough_status='complete',source_extraction_usable=True,cases=6,
        notes_sha256=sha256_file(notes_path),source_audit_sha256=sha256_file(s.OUT/'source-audit.json'),
        walkthrough_sha256=sha256_file(path),predictive_claim=False,protected_outcomes_used=False))
    print('Six source walkthroughs complete; workload test may proceed.')


if __name__=='__main__':main()
