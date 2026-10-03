"""Persist nine actual source-window reviews before any model fit."""
import prepare_hitter_late_role_v46 as s
from universal_baseball.storage import sha256_file


def main():
    cases=s.e.r.read(s.OUT/'source-cases.json');p=s.ROOT/'config/practical_hitter_late_role_v46_source_notes.json';notes=s.e.r.read(p);assert len(cases)==len(notes)==9
    manifest=s.e.r.read(s.OUT/'source-manifest.json')
    lines=['# Late-season role source review','',
        'All fifteen historical full-calendar-year MLB PA totals match prior official player-season counts exactly. Two nonoverlapping final thirty-day windows have valid counts inside annual totals. Sixty dated official requests, schedules deduplicated by gamePk and officialDate, no postponed entries treated as played. No 2026 outcomes.','',
        'Window gamesPlayed differs from annual team-summed source games for many people; the exact cause is not established. New game/PA-per-appearance predictors are withheld before fitting. The ten candidate inputs are availability, late/preceding PA and PA per scheduled league-average team game for current/prior years. They do not measure starts or diagnoses.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_id']}|{o['origin_year']}";assert key in notes
        lines.extend([f"## {o['player_name']} at {o['origin_year']} cutoff",'',
            '| Season | Annual MLB PA | Preceding PA | Late PA | Preceding average team games | Late average team games |','|---|---:|---:|---:|---:|---:|'])
        for w in c['windows']:lines.append(f"| {w['season']} | {w['annual_pa']} | {w['preceding_pa']} | {w['late_pa']} | {w['preceding_team_games']:.5f} | {w['late_team_games']:.5f} |")
        if not c['windows']:lines.append('| No own MLB record in these complete captures | 0 | 0 | 0 | Year-level denominators preserved | Year-level denominators preserved |')
        lines.extend(['','Actual added inputs: '+str(c['added_inputs'])+'.','',notes[key],''])
    lines.extend(['## Source decision','',
        'The ten PA-only timing inputs are usable for the one preregistered comparison. This is an execution/source conclusion, not a predictive gain. It does not establish minor-league jobs, finite-absence causes or future roster depth. The original 239 predictors and historical evaluation population are unchanged. Retrospective performance corrections and unverified roster-only universe entries remain qualified. Do not claim either the earlier rest-of-season result or these nine examples validates next-calendar-year performance.'])
    out=s.OUT/'source-walkthrough.md';out.write_text('\n'.join(lines)+'\n',encoding='utf8')
    s.write('source-review.json',dict(player_walkthrough_status='complete',source_usable=True,cases=9,features=10,annual_pa_exact=True,new_window_game_features_withheld=True,predictive_claim=False,
        manual_notes_sha256=sha256_file(p),walkthrough_sha256=sha256_file(out),protected_outcomes_used=False))
    print('Nine source reviews complete; ten PA-only timing inputs usable, no predictive claim.',flush=True)


if __name__=='__main__':main()
