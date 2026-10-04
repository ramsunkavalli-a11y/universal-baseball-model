"""Independent KBO source reconstruction and fixed player identity/count walks."""
from datetime import datetime,date
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlsplit,parse_qs

from bs4 import BeautifulSoup
import polars as pl
import requests

import probe_kbo_hitting_source as probe
from universal_baseball.kbo_history import FIELDS1,FIELDS2
from universal_baseball.storage import sha256_file

ROOT,RAW,OUT=probe.ROOT,probe.RAW,probe.OUT
EVIDENCE=ROOT/'reports/model-evidence/kbo-hitting-source-probe'
FIXED=[(2023,'이정후',808982),(2020,'김하성',673490),(2024,'김혜성',808975),
       (2015,'박병호',666560),(2015,'테임즈',519346)]


def latin_key(value):
    return re.sub(r"[\s.'-]",'',value).casefold()


def raw_page(path,group):
    meta=json.loads(path.with_suffix('.json').read_text(encoding='utf8'))
    assert meta['http_status']==200 and meta['url']==meta['returned_url']
    assert sha256_file(path)==meta['sha256']
    soup=BeautifulSoup(path.read_bytes(),'html.parser')
    result={}
    for tr in soup.select('table.tData01 tbody tr'):
        cells=tr.find_all('td',recursive=False)
        if not cells:
            continue
        anchor=cells[1].find('a')
        key=parse_qs(urlsplit(anchor['href']).query)['playerId'][0]
        fields=FIELDS1 if group==1 else FIELDS2
        values={field:int(cells[index].get_text()) for index,field in enumerate(fields,4)}
        assert key not in result
        result[key]=values
    return result


def english_case(session,row,mlb_id):
    kbo_id=row['kbo_id']
    url='https://eng.koreabaseball.com/Teams/PlayerInfoHitter/Summary.aspx?pcode='+kbo_id
    soup,meta=probe.request(session,'review-english-identity-'+kbo_id,url)
    profile_codes=[parse_qs(urlsplit(a['href']).query).get('pcode',[None])[0]
                   for a in soup.find_all('a',href=True)
                   if 'PlayerInfoHitter/' in a['href'] and 'pcode=' in a['href']]
    assert profile_codes and set(profile_codes)=={kbo_id}, 'English profile identity navigation mismatch'
    profiles=[]
    for ul in soup.find_all('ul'):
        items=[x.get_text(' ',strip=True) for x in ul.find_all('li',recursive=False)]
        if any(x.startswith('Name :') for x in items):
            profiles.append(items)
    assert len(profiles)==1
    # Whitelist stable identity fields; current salary, position, debut/status are excluded.
    items={x.split(':',1)[0].strip():x.split(':',1)[1].strip() for x in profiles[0] if ':' in x}
    name=items['Name']; birthday=datetime.strptime(items['Born'],'%d/%m/%Y').date().isoformat()
    tables=[t for t in soup.find_all('table') if [x.get_text(strip=True) for x in t.select('thead th')][:3]==['YEAR','TEAM','AVG']]
    assert len(tables)==1
    headers=[x.get_text(strip=True) for x in tables[0].select('thead th')]
    candidates=[]
    for tr in tables[0].select('tbody tr'):
        cells=[x.get_text(strip=True) for x in tr.find_all(['th','td'],recursive=False)]
        if cells and cells[0]==str(row['season']):
            assert len(cells)==len(headers)
            candidates.append(dict(zip(headers,cells,strict=True)))
    assert len(candidates)==1,(kbo_id,row['season'],candidates)
    observed=candidates[0]
    fields={'games':'G','ab':'AB','runs':'R','hits':'H','doubles':'2B','triples':'3B',
            'hr':'HR','tb':'TB','rbi':'RBI','bb':'BB','hbp':'HBP','so':'SO','gdp':'GIDP'}
    for field,header in fields.items():
        assert int(observed[header])==row[field],(kbo_id,row['season'],field)
    mlb=None
    if mlb_id is not None:
        # Static fields only: do not request hydrated stats, career dates or current team.
        mlb_url='https://statsapi.mlb.com/api/v1/people/'+str(mlb_id)+'?fields=people,id,fullName,firstName,lastName,birthDate'
        _,mlb_meta=probe.request(session,'review-mlbam-identity-'+str(mlb_id),mlb_url)
        mlb_payload=json.loads((RAW/('review-mlbam-identity-'+str(mlb_id)+'.html')).read_bytes())
        people=mlb_payload['people']; assert len(people)==1
        mlb=people[0]
        assert mlb['id']==mlb_id and mlb['birthDate']==birthday
        assert latin_key(name)==latin_key(mlb['lastName']+mlb['firstName']),(name,mlb)
    else:
        mlb_meta=None
    age=(date(row['season'],12,31)-date.fromisoformat(birthday)).days/365.2425
    return dict(kbo_english_name=name,birth_date=birthday,origin_end_age=age,
                identity_fields_only=True,english_meta=meta,mlb_identity=mlb,mlb_identity_meta=mlb_meta,
                english_origin_count_fields_checked=len(fields),raw_english_origin_stats=observed,
                historical_salary_position_status_used=False,mlb_crosswalk_scope='fixed_cases_only')


def main():
    assert not (OUT/'review.json').exists(), 'Preserve completed review'
    q=json.loads((OUT/'qualification.json').read_text(encoding='utf8'))
    assert q['code_sha256']==sha256_file(ROOT/'scripts/qualify_kbo_hitting_source.py')
    assert q['parser_sha256']==sha256_file(ROOT/'src/universal_baseball/kbo_history.py')
    archived_receipts=[json.loads(p.read_text(encoding='utf8')) for p in RAW.glob('*.json')
                       if not p.name.endswith('.request.json')]
    for receipt in q['captures']:
        assert receipt in archived_receipts
    path=OUT/'qualified-seasons.parquet'
    assert q['data_sha256']==sha256_file(path)
    data=pl.read_parquet(path); reconstructed=0
    for check in q['checks']:
        year=check['season']; group_rows=[]
        for group in check['groups']:
            stem=f"qualification-{q['attempt']}-{year}-group{group['group']}"
            result={}
            for page in range(1,group['last_page']+1):
                suffix='-count-first.html' if page==1 else f'-page{page}.html'
                rows=raw_page(RAW/(stem+suffix),group['group'])
                assert not set(rows)&set(result)
                result.update(rows)
            assert len(result)==group['rows']
            group_rows.append(result)
        assert set(group_rows[0])==set(group_rows[1])
        part=data.filter(pl.col('season')==year)
        assert set(part['kbo_id'])==set(group_rows[0])
        for row in part.iter_rows(named=True):
            reconstructed+=1
            combined={**group_rows[0][row['kbo_id']],**group_rows[1][row['kbo_id']]}
            assert all(row[k]==value for k,value in combined.items())
        # Default AVG rank covers qualifiers; count order must include limited PA.
        assert check['small_pa']>0 and check['zero_pa']>0
    assert reconstructed==q['rows']==data.height
    cases=[]
    for year,name,mlb_id in FIXED:
        selected=data.filter((pl.col('season')==year)&(pl.col('player_name_ko')==name))
        assert selected.height==1,(year,name)
        cases.append((selected.row(0,named=True),mlb_id,'fixed_before_source_test'))
    ordinary=data.filter((pl.col('season')==2005)&(pl.col('pa')>0)).sort('kbo_id').row(0,named=True)
    cases.append((ordinary,None,'lowest_KBO_ID_positive_PA_2005'))
    session=requests.Session()
    # Whitelist prediction columns; never read next-year labels/public forecasts.
    pred_path=ROOT/'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet'
    fields=['player_id','origin_year','baseline_pa','baseline_p','baseline_conditional_pa','combined_rate','combined_value']
    predictions=pl.read_parquet(pred_path,columns=fields)
    original_hash=sha256_file(pred_path)
    walks=[]
    for row,mlb_id,rule in cases:
        identity=english_case(session,row,mlb_id)
        row_rate=lambda r:(r['so']/r['pa'],r['hr']/r['pa'])
        focal_k,focal_hr=row_rate(row)
        candidates=[]
        for peer in data.filter((pl.col('season')==row['season'])&(pl.col('pa')>=100)).iter_rows(named=True):
            if peer['kbo_id']==row['kbo_id']:
                continue
            k,hr=row_rate(peer)
            distance=abs(peer['pa']-row['pa'])/600+abs(k-focal_k)/.1+abs(hr-focal_hr)/.03
            candidates.append((distance,peer))
        peers=[dict(p,selection_distance=distance,MLB_outcomes_used_for_selection=False)
               for distance,p in sorted(candidates,key=lambda x:(x[0],x[1]['kbo_id']))[:3]]
        saved=predictions.filter((pl.col('player_id')==mlb_id)&(pl.col('origin_year')==row['season'])) if mlb_id else predictions.head(0)
        assert saved.height<=1
        walks.append(dict(source_row=row,identity=identity,MLBAM=mlb_id,selection_rule=rule,peers=peers,
                          rates=dict(k=focal_k,hr=focal_hr,ubb=(row['bb']-row['ibb'])/row['pa']),
                          unchanged_saved_forecast=saved.to_dicts(),candidate_forecast=None,
                          foreign_MLB_translation_fitted=False,future_MLB_outcomes_used=False))
    probe.write_new(OUT/'player-cases.json',dict(cases=walks,MLBAM_scope='five_fixed_cases_not_full_crosswalk'))
    lines=['# Korean batting source player review','',
           'Source test only. Requested years and complete pages are verified; player sums match independent official team tables in all sixteen summable count fields. No projection changed. Current identity pages supply stable English name/DOB only; current salary, position, status and later career results are not projection inputs. English season lines are a second official rendering, not an independent statistical provider.','']
    for walk in walks:
        r=walk['source_row']; i=walk['identity']; rates=walk['rates']
        lines += [f"## {i['kbo_english_name']} after {r['season']}",'',
                  f"Selection {walk['selection_rule']}; KBO ID {r['kbo_id']}; MLBAM {walk['MLBAM']}; DOB {i['birth_date']}; age at origin year end {i['origin_end_age']:.2f}.",'',
                  f"Raw KBO: {r['pa']} PA, {r['ab']} AB, {r['hits']} H, {r['doubles']} doubles, {r['triples']} triples, {r['hr']} HR, {r['bb']} BB including {r['ibb']} IBB, {r['hbp']} HBP and {r['so']} K. AVG/OBP/SLG {r['raw_avg']}/{r['raw_obp']}/{r['raw_slg']}; unenumerated PA {r['unenumerated_pa']}.",'',
                  f"K/PA {rates['k']:.4f}, HR/PA {rates['hr']:.4f}, UBB/PA {rates['ubb']:.4f}. No park, opponent, age or league-strength adjustment has been fitted. A displayed team is not verified team-stint/park exposure.",'',
                  f"English origin-season line matches thirteen count fields. Static MLB identity/DOB join {'verified for this fixed case' if walk['MLBAM'] else 'not attempted; no inferred MLB participation'}. [Official English source]({i['english_meta']['url']}). [Official historical records](https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx).",'',
                  'Unchanged saved forecast: '+json.dumps(walk['unchanged_saved_forecast'],ensure_ascii=False)+'. No candidate prediction or future MLB label is fabricated.','',
                  'Origin-only PA/K/HR peers, without an age-match claim:','']
        for peer in walk['peers']:
            lines.append(f"- {peer['player_name_ko']} (KBO {peer['kbo_id']}): {peer['pa']} PA, {peer['hr']} HR, {peer['so']} K; selected without any MLB outcome. Peer DOB/role is not certified by this count-only comparison.")
        lines += ['','Interpretation: these are real first-team professional observations, not domestic zero talent. The source can represent power/contact differences and limited samples; it cannot by itself establish an MLB job, translated talent, durability or delivered WAR.','']
    lines += ['## Limits and disposition','',
              'Five historical seasons are source-qualified, not the full 2005–2024 history. Bulk SB/CS, positions, DOB and MLBAM links are not supplied by these two stat groups. All returned rows, including pitcher batting and zero PA, remain preserved. Fixed-case links do not certify a population-wide crosswalk. No fitted gain/loss/outcome categories exist in this source-only test. A bounded complete-history collection and identity/translation work remain necessary; the full hitter goal is not complete.']
    doc=OUT/'player-walkthrough.md'
    assert not doc.exists()
    doc.write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    tests=subprocess.run([sys.executable,'-m','pytest','tests/test_kbo_history.py','-q'],cwd=ROOT,capture_output=True,text=True)
    assert tests.returncode==0,tests.stdout+tests.stderr
    freeze=subprocess.run([sys.executable,'scripts/verify_hitter_full_2026_freeze.py'],cwd=ROOT,capture_output=True,text=True)
    assert freeze.returncode==0,freeze.stdout+freeze.stderr
    assert sha256_file(path)==q['data_sha256'] and sha256_file(pred_path)==original_hash
    result=dict(seasons=q['seasons'],checks=q['checks'],rows=reconstructed,
                source_walks=len(walks),independent_count_fields_reconstructed=reconstructed*17,
                english_case_fields_checked=13*len(walks),fixed_MLB_identity_joins=5,
                all_league_MLBAM_crosswalk_qualified=False,player_walkthrough_status='complete_for_source',
                historical_scope_qualified=True,full_2005_2024_collected=False,forecasts_changed=False,
                new_fits=0,MLB_translation_fitted=False,protected_2026_opened=False,
                tests=tests.stdout,protected_freeze=json.loads(freeze.stdout),
                hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [
                    Path(__file__),ROOT/'scripts/qualify_kbo_hitting_source.py',Path(probe.__file__),
                    ROOT/'src/universal_baseball/kbo_history.py',probe.CONTRACT,OUT/'qualification.json',
                    OUT/'qualified-seasons.parquet',OUT/'player-cases.json',doc]})
    probe.write_new(OUT/'review.json',result)
    probe.write_new(EVIDENCE/'review.json',result)
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    (EVIDENCE/'player-walkthrough.md').write_text(doc.read_text(encoding='utf8'),encoding='utf8',newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k!='hashes'},ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
