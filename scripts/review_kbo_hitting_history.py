"""Reconstruct complete KBO capture and extend the sealed source walks."""
import json
from pathlib import Path
import subprocess
import sys

from bs4 import BeautifulSoup
import polars as pl
import requests

import capture_kbo_hitting_history as collection
import probe_kbo_hitting_source as probe
import review_kbo_hitting_source as review
from universal_baseball.kbo_history import FIELDS1,FIELDS2
from universal_baseball.kbo_history_inputs import history_at
from universal_baseball.storage import sha256_file

ROOT,OUT,RAW=collection.ROOT,collection.OUT,probe.RAW
EVIDENCE=ROOT/'reports/model-evidence/kbo-hitting-history'


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def team_counts(path):
    meta=read(path.with_suffix('.json'))
    assert sha256_file(path)==meta['sha256'] and meta['url']==meta['returned_url'] and meta['http_status']==200
    soup=BeautifulSoup(path.read_bytes(),'html.parser')
    tables=soup.select('table.tData'); assert len(tables)==1
    headers=[x.get_text(strip=True) for x in tables[0].select('thead th')]
    return [dict(zip(headers,[x.get_text(strip=True) for x in tr.find_all('td',recursive=False)],strict=True))
            for tr in tables[0].select('tbody tr')]


def main():
    assert not (OUT/'review.json').exists(), 'Preserve complete review'
    report=read(OUT/'collection.json')
    for path,expected in report['source_code_hashes'].items():
        assert sha256_file(ROOT/path)==expected,('Capture changed',path)
    path=OUT/'first-team-batting.parquet'; assert sha256_file(path)==report['data_sha256']
    data=pl.read_parquet(path); records=data.to_dicts(); independent=[]
    for year in report['seasons']:
        receipt=read(OUT/f'{year}.json')
        assert sha256_file(OUT/f'{year}.json')==report['per_year_receipt_hashes'][str(year)]
        assert sha256_file(OUT/f'{year}.parquet')==receipt['data_sha256']
        groups=[]
        for group in receipt['check']['groups']:
            stem=f"qualification-{receipt['raw_capture_attempt']}-{year}-group{group['group']}"
            reconstructed={}
            for page in range(1,group['last_page']+1):
                suffix='-count-first.html' if page==1 else f'-page{page}.html'
                rows=review.raw_page(RAW/(stem+suffix),group['group'])
                assert not set(reconstructed)&set(rows)
                reconstructed.update(rows)
            assert len(reconstructed)==group['rows']
            groups.append(reconstructed)
        assert set(groups[0])==set(groups[1])
        part=data.filter(pl.col('season')==year)
        assert set(part['kbo_id'])==set(groups[0])
        for row in part.iter_rows(named=True):
            assert all(row[k]==v for k,v in {**groups[0][row['kbo_id']],**groups[1][row['kbo_id']]}.items())
        stem=('qualification-' if receipt['reused_qualified_season'] else 'bulk-')+receipt['raw_capture_attempt']+f'-{year}-teams-group'
        teams1=team_counts(RAW/(stem+'1-year.html')); teams2=team_counts(RAW/(stem+'2-year.html'))
        expected_teams=8 if year<=2012 else 9 if year<=2014 else 10
        assert len(teams1)==len(teams2)==expected_teams
        assert {t['팀명'] for t in teams1}=={t['팀명'] for t in teams2}
        header_map={**dict(zip(FIELDS1,['G','PA','AB','R','H','2B','3B','HR','TB','RBI','SAC','SF'])),
                    **dict(zip(FIELDS2,['BB','IBB','HBP','SO','GDP']))}
        for field,header in header_map.items():
            if field=='games':
                continue
            teams=teams1 if field in FIELDS1 else teams2
            assert part[field].sum()==sum(int(t[header]) for t in teams)
        independent.append(dict(season=year,reconstructed_rows=part.height,raw_count_fields=part.height*17,
                                independently_reconciled_team_count_fields=16,team_count=expected_teams))
    assert sum(r['reconstructed_rows'] for r in independent)==report['rows']==data.height
    original=read(review.OUT/'player-cases.json')['cases']
    focal=[(c['source_row'],c['identity'],c['selection_rule'],c['MLBAM']) for c in original]
    ordinary=data.filter((pl.col('season')==2013)&(pl.col('pa')>0)).sort('kbo_id').row(0,named=True)
    identity=review.english_case(requests.Session(),ordinary,None)
    focal.append((ordinary,identity,'lowest_KBO_ID_positive_PA_2013_expansion',None))
    cases=[]
    for row,identity,rule,mlb_id in focal:
        saved=data.filter((pl.col('season')==row['season'])&(pl.col('kbo_id')==row['kbo_id']))
        assert saved.height==1 and saved.row(0,named=True)==row
        h=history_at(records,row['kbo_id'],row['season'],report['seasons'])
        truncated=[r for r in records if r['season']<=row['season']]
        assert h==history_at(truncated,row['kbo_id'],row['season'],report['seasons'])
        altered=records+[dict(records[0],season=2099,kbo_id=row['kbo_id'],pa=99999,hr=999)]
        assert h==history_at(altered,row['kbo_id'],row['season'],report['seasons']+[2099])
        recent=[r for r in records if r['kbo_id']==row['kbo_id'] and row['season']-2<=r['season']<=row['season']]
        # Replay shared official English count checks for each positive-PA observed recent year.
        checks=[review.english_case(requests.Session(),r,mlb_id) for r in recent if r['pa']>0]
        cases.append(dict(source_row=row,identity=identity,MLBAM=mlb_id,selection_rule=rule,
                          english_display_name_missing=not bool(identity['kbo_english_name']),
                          recent_source_rows=recent,history=h,english_recent_checks=checks,
                          foreign_MLB_translation_fitted=False,future_MLB_outcomes_used=False,
                          old_probe_case_preserved=True if rule!='lowest_KBO_ID_positive_PA_2013_expansion' else None))
    probe.write_new(OUT/'player-cases.json',dict(cases=cases,MLBAM_scope='five_fixed_cases_only'))
    lines=['# Complete Korean batting history player review','',
           'Source only, not a new projection. All twenty first-team seasons are reconstructed and player totals reconciled to team records. The six earlier cases and their stats are preserved; a predeclared ordinary 2013 expansion-season case is added. Current English profiles supply static name/DOB and only cutoff-eligible season checks, not current salary, role, status or future MLB outcomes.','']
    for c in cases:
        r=c['source_row']; h=c['history']; i=c['identity']
        name=i['kbo_english_name'] or r['player_name_ko']+' (English display name unavailable)'
        lines += [f"## {name} at the {r['season']} origin",'',
                  f"Selection {c['selection_rule']}; KBO {r['kbo_id']}, MLBAM {c['MLBAM']}. DOB {i['birth_date']}. [Official English record]({i['english_meta']['url']}).",'',
                  '| Year | PA | H | 2B | 3B | HR | BB | IBB | K |',
                  '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
        for row in c['recent_source_rows']:
            lines.append('| '+' | '.join(str(row[k]) for k in ('season','pa','hits','doubles','triples','hr','bb','ibb','so'))+' |')
        lines += ['',f"Observed first-team history: {h['observed_history_pa']} PA in positive-PA seasons {h['observed_positive_pa_seasons']}. Recent-window complete: {h['recent_window_complete']}; missing coverage {h['recent_missing_coverage']}. Raw UBB/K/HR rates per full PA: {h['ubb_rate']}, {h['k_rate']}, {h['hr_rate']}; raw BABIP {h['babip']}. Future-row mutations and truncation leave this history unchanged.",'',
                  f"Recent zero-first-team-PA seasons with complete source coverage: {h['certified_recent_first_team_zero_pa_seasons']}. This is not a claim of zero talent, inactivity, health failure or zero Futures/other-league work. Before 2005, professional experience remains left-truncated.",'',
                  f"All thirteen shared English count fields match in {len(c['english_recent_checks'])} positive-PA recent season lines. These are the same official data in another rendering, not independent-provider validation. No raw KBO rate has been park-adjusted or converted to MLB talent.",'',
                  'No original or candidate forecast changed. See the preserved [initial source walkthrough](../kbo-hitting-source-probe/player-walkthrough.md) for unchanged saved intermediates and outcome-blind PA/K/HR peers. Player improvements, harms and realized MLB errors cannot be claimed without a fitted comparison.','']
    lines += ['## What this does and does not establish','',
              'The full source interval and cutoff-safe raw history are usable, including the 2013/2015 expansions and the real 2020 season. Pitcher batting and low samples remain present. The two groups do not supply bulk SB/CS, historical positions, stint-level park exposure or all-player DOB. Five fixed MLB identity joins are not an all-league crosswalk. League translation, dated employment context, matched original/addition evaluation and mature training support remain required. No automatic forecast promotion or full-hitter-goal completion follows from this source pass.']
    doc=OUT/'player-walkthrough.md'; assert not doc.exists()
    doc.write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    tests=subprocess.run([sys.executable,'-m','pytest','tests/test_kbo_history.py','tests/test_kbo_source_review.py',
                          'tests/test_kbo_history_inputs.py','-q'],cwd=ROOT,capture_output=True,text=True)
    assert tests.returncode==0,tests.stdout+tests.stderr
    freeze=subprocess.run([sys.executable,'scripts/verify_hitter_full_2026_freeze.py'],cwd=ROOT,capture_output=True,text=True)
    assert freeze.returncode==0,freeze.stdout+freeze.stderr
    result=dict(seasons=report['seasons'],rows=data.height,pa=int(data['pa'].sum()),
                zero_pa_rows=data.filter(pl.col('pa')==0).height,unenumerated_pa=int(data['unenumerated_pa'].sum()),
                independent_checks=independent,source_walks=len(cases),player_walkthrough_status='complete_for_source',
                fixed_MLBAM_joins=5,all_league_MLBAM_crosswalk_qualified=False,
                forecasts_changed=False,new_fits=0,MLB_translation_fitted=False,protected_2026_opened=False,
                tests=tests.stdout,protected_freeze=json.loads(freeze.stdout),
                hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [Path(__file__),
                    ROOT/'src/universal_baseball/kbo_history_inputs.py',OUT/'collection.json',path,
                    OUT/'player-cases.json',doc,review.OUT/'review.json',collection.CONTRACT]})
    probe.write_new(OUT/'review.json',result)
    probe.write_new(EVIDENCE/'review.json',result)
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    (EVIDENCE/'player-walkthrough.md').write_text(doc.read_text(encoding='utf8'),encoding='utf8',newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('hashes','independent_checks')},ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
