"""Complete actual source cases; accept rank fields, withhold mixed-vintage grades."""
from pathlib import Path
from prepare_historical_scouting_v47 import ROOT,OUT,write
import json
from universal_baseball.storage import sha256_file


def main():
    cases=json.loads((OUT/'source-cases.json').read_text(encoding='utf8'))
    notespath=ROOT/'config/practical_hitter_scouting_v47_source_notes.json'
    notes=json.loads(notespath.read_text(encoding='utf8'));assert len(cases)==len(notes)==9
    lines=['# Historical prospect rank source and nine player reviews','',
        'Accepted for a qualified historical rank-only development comparison, not a verified historical scouting-grade panel. Fourteen publisher-year captures provide 1,348 ranking identities. The 2020 and 2021 captures omit rank 100: observed positives remain usable but absent players stay unknown. This does not turn the canceled MiLB season into zero production. Current biographies, tool grades, ETA and research-dataset outcome labels are excluded.','',
        'The separate research dataset contains 9,175 rows, 8,118 with valid positive numeric MLBAM IDs. There are 787 repeated player/year/source groups and 782 have discordant hit/power/ETA values. Duplicates may represent legitimately different list types or report updates; the dataset does not provide sufficient publication provenance to choose among them automatically. Its 2013–2019 coverage also cannot provide later prospect updates. Do not import its debut-by-age-24 outcome rule or call the dataset unusable for every future application.','']
    for c in cases:
        o=c['origin'];key=f"{o['player_id']}|{o['origin_year']}";assert key in notes
        lines += [f"## {o['player_name']} at the end of {o['origin_year']}",'',
            f"MLBAM {o['player_id']}; age {o['age']}; {o['stage']}; origin MLB PA {o['pa_0']}, minor PA {o['minor_pa_0']}. Ranking: {c['current_list_rank'] if c['current_list_rank'] is not None else 'not listed in the complete current-year list'}. This review makes no new forecast.",'',
            '| Season | Level | PA | HR | K | Unintentional walks |','|---|---|---:|---:|---:|---:|']
        for h in c['source_history']:lines.append(f"| {h['season']} | {h['bucket']} | {h['plate_appearances']} | {h['home_runs']} | {h['strike_outs']} | {h['unintentional_walks']} |")
        lines += ['',f"Actual three-year rank inputs: {c['inputs']}",'',notes[key],'']
    lines += ['## Provenance and decision','',
        'Publisher-selected list slug and context year agree, ranks and identities reconcile, and complete versus partial lists are distinguished. These are retrospective captures, not archived publication-time editions. Current display fields are explicitly omitted. The rank-only source can support a bounded comparison with coverage qualifications; it does not yet establish a gain or solve newly drafted/fast-rising unlisted prospects. All nine source reviews precede fits.','',
        'Independent publisher references: [2016 retrospective list](https://www.mlb.com/news/2016-top-100-mlb-prospects-list-c301608606), [2022 dated release](https://www.mlb.com/dodgers/news/top-100-prospects-list-mlb-pipeline-2022). These corroborate selected ranks, not every field or every historical list revision. The full saved year-specific request manifests preserve the actual sources.']
    path=OUT/'source-walkthrough.md';path.write_text('\n'.join(lines)+'\n',encoding='utf8')
    write('source-review.json',dict(player_walkthrough_status='complete',cases=9,rank_source_usable=True,
        grades_eta_text_withheld=True,source_eligibility_qualified=True,predictive_claim=False,
        manual_notes_sha256=sha256_file(notespath),walkthrough_sha256=sha256_file(path),protected_2026_outcomes_used=False))
    print('Nine source reviews complete; qualified rank-only comparison permitted, no new forecast yet.')


if __name__=='__main__':main()
