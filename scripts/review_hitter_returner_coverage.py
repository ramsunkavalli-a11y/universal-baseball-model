"""Independent source review; preserve both completed no-fit audit receipts."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
import audit_hitter_returner_coverage as a

NOTES = {
    (624424,2022): 'Conforto has 233 MLB PA/nine HR in 2020 and 479/fourteen in 2021, then no 2022 MLB season. The January 2023 forecast has no origin row: neither snapshot nor elapsed-0–5 support includes him, and roster status is not an inclusion source. January 6 official signing precedes the January 26 rank-information date. A December roster can legitimately miss that signing; the later ranking overlay deliberately did not update other December inputs. This is incomplete preseason population coverage, not evidence of zero talent or a failed individual forecast. Actual 470 PA diagnoses the consequence, not eligibility.',
    (593934,2023): 'Sano has 532 MLB PA/thirty HR in 2021 and 71/one in 2022, then no 2023 affiliated production. Neither origin snapshot nor support includes him. His January 23 agreement was reported before the January 26 ranking date, while the player transaction page records February 1. Keep reported agreement and official-record timing distinct; do not fabricate a pre-cutoff official roster row. Actual 95 PA demonstrates modest missing coverage, not a mandate for high workload or restored pre-injury talent.',
    (493316,2018): 'Cespedes has 543/321/157 MLB PA and 31/17/nine HR across 2016–18. The snapshot retains him and the stored roster is present, despite elapsed six being outside the support source. The existing forecast remains in scoring when he receives zero next-year PA. An absent future season does not erase the known player or become an observed zero hitting rate. This contrasts with Conforto: the older support cap is not itself a universal exclusion if the snapshot retains a player.',
    (431151,2017): 'Wright has 174 MLB PA/five HR in 2015 and 164/seven in 2016, then no 2017 MLB PA. Snapshot and roster retain him despite elapsed thirteen, while the support source has no row. Actual three PA is a very limited return, not proof of recovered regular capacity. Absence alone therefore does not remove every older player, and adding generic availability cannot be assumed to fix missing membership.',
    (453064,2018): 'Tulowitzki has 544 MLB PA/24 HR in 2016 and 260/seven in 2017, with no 2018 MLB PA. The snapshot retains him despite elapsed twelve and absent year-end roster/support. Actual thirteen PA illustrates a low-use return and shows why roster absence cannot certify retirement or remove a person automatically. Source membership and roster-derived features are different mechanisms.',
    (501981,2022): 'Davis has 99 MLB PA/two HR in 2020 and 114/three in 2021. The snapshot, support and roster omit his 2022 origin, just like Conforto. Actual zero PA supplies the necessary non-return contrast; it does not justify retrospectively treating every similar former player as permanently unavailable. No individual forecast is manufactured for this omitted person.',
    (474832,2024): 'Belt has 298 MLB PA/eight HR in 2022 and 404/nineteen in 2023, then no 2024 MLB PA. His 2024 origin is absent from snapshot, support and roster and he receives zero MLB PA in 2025. This differs from his retained 2023 origin forecasting 2024, whose surprising non-employment miss was already reviewed. Do not confuse origins or use the later absence to rewrite that earlier forecast.',
    (595751,2024): 'Alfaro has 274 MLB PA/seven HR in 2022 and 52/one in 2023. His 2024 origin is absent from snapshot, support and roster. The Brewers January 16 transaction precedes the January 24 ranking date, yet the ranking-only overlay cannot create a missing player row. Actual 39 PA is small. The corrective task is dated inclusion, not an inferred large playing-time entitlement from any minor contract.',
    (110029,2016): 'Abreu enters the permissive audit from 155 MLB PA/one HR in 2014 with latest source position X, rather than a certified current fielding position. No snapshot, support or roster row includes him at 2016 and no 2017 MLB PA occurs. This deliberately unglamorous non-return stresses the review rule: positive old batting is not enough to assume an active job. No confirmed retirement fact is invented from the missing roster.',
}
SOURCES = [
    dict(player_id=624424,event_date='2023-01-06',url='https://www.mlb.com/press-release/giants-agree-to-two-year-contract-with-outfielder-michael-conforto',fact='Giants officially announced Conforto signing on January 6, 2023.',kind='team_press_release',contemporaneous_page_snapshot=False),
    dict(player_id=593934,event_date='2024-01-23',url='https://www.espn.com/mlb/story/_/id/39372420/miguel-sano-signs-minor-league-deal-angels',fact='ESPN reported Sano agreement on January 23, 2024.',kind='dated_original_reporting',contemporaneous_page_snapshot=False),
    dict(player_id=593934,event_date='2024-02-01',url='https://www.mlb.com/player/miguel-sano-593934',fact='Current transaction history records Sano signing February 1, 2024.',kind='retrospective_transaction_table',contemporaneous_page_snapshot=False),
    dict(player_id=595751,event_date='2025-01-16',url='https://www.mlb.com/brewers/roster/transactions/2025/01',fact='Brewers transaction table dates Alfaro signing January 16, 2025.',kind='retrospective_transaction_table',contemporaneous_page_snapshot=False),
]


def read(p): return json.loads(Path(p).read_text(encoding='utf8'))


def write(name,obj):
    path=a.OUT/name; assert not path.exists(), 'Preserve original receipts'
    path.write_text(json.dumps(obj,ensure_ascii=False,allow_nan=False,default=str,indent=2)+'\n',encoding='utf8')
    target=a.EVIDENCE/name; assert not target.exists(); shutil.copyfile(path,target)


def main():
    assert not (a.OUT/'final-review.json').exists()
    audit=read(a.OUT/'audit.json')
    for p,h in audit['source_hashes'].items(): assert sha256_file(Path(p))==h,p
    ledger=a.ROOT/'reports/model-evidence/hitter-season-value-ledger'
    for p,h in read(ledger/'audit.json')['source_hashes'].items(): assert sha256_file(Path(p))==h,p
    final=read(ledger/'final-review.json')
    for p,h in final['artifact_hashes'].items(): assert sha256_file(ledger/p)==h,p
    assert sha256_file(a.ROOT/'scripts/review_hitter_season_value_ledger.py')==final['reviewer_sha256']
    rows=read(a.OUT/'rows.json'); s=pl.read_parquet(a.PATHS['stints'])
    # Alternative construction: latest annual season, then its largest source stint.
    mlb=s.filter((pl.col('sport_id')==1)&(pl.col('plate_appearances')>0))
    for y in a.YEARS:
        past=mlb.filter(pl.col('season').is_between(y-2,y))
        latest=past.group_by('player_id').agg(pl.col('season').max())
        primary=past.join(latest,on=['player_id','season'],validate='m:1').sort('player_id','plate_appearances','team_id',descending=[False,True,False]).unique('player_id',keep='first')
        expected=set(primary.filter(pl.col('position')!='1')['player_id'])
        actual=[v for v in rows if v['origin_year']==y]
        assert expected=={v['player_id'] for v in actual} and len(actual)==len(expected)
        nextpa=dict(mlb.filter(pl.col('season')==y+1).group_by('player_id').agg(pl.col('plate_appearances').sum()).iter_rows())
        for v in actual: assert v['diagnostic_next_pa']==nextpa.get(v['player_id'],0)
    prepath=a.ROOT/'reports/generated/hitter-preseason-readiness-v68/preflight.json'
    info={c['year']:c['information_date'] for c in read(prepath)['cells']}
    cases=read(a.OUT/'cases.json')
    alfaro=next(v for v in rows if (v['player_id'],v['origin_year'])==(595751,2024))
    cases.append(dict(selection='all_positive_omissions_reviewed',record=alfaro))
    q=pl.read_parquet(a.PATHS['predictions'])
    lines=['# Player source walks for missing returners','',
           'No new fits or forecasts. Missing forecast rows are not predicted zeros. Next-year PA is diagnostic only. The permissive review rule does not certify current hitter roles, health or employment.','']
    for c in cases:
        v=c.get('record'); pid=c.get('player_id',v['player_id']);y=c.get('origin_year',v['origin_year'])
        assert (pid,y) in NOTES
        c['source_review']=NOTES[pid,y];c['ranking_information_date']=info[y]
        # Own peers selected without next-year use. Same origin and MLB absence gap.
        peers=[r for r in rows if r['origin_year']==y and r['player_id']!=pid and r['last_mlb_season']==v['last_mlb_season']]
        def distance(r):
            x={h['season']:h['plate_appearances'] for h in v['own_history']}
            z={h['season']:h['plate_appearances'] for h in r['own_history']}
            return sum(((x.get(t,0)-z.get(t,0))/300)**2 for t in range(y-2,y+1))
        c['origin_selected_peers']=sorted(peers,key=lambda r:(distance(r),r['player_id']))[:4]
        c['peer_limit']='Same last MLB season and three-season PA similarity, not equivalent talent, age, contract or health.'
        match=q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y))
        c['existing_forecast']=match.select('row_id','preseason_p','preseason_conditional_pa','preseason_pa','combined_rate','combined_value','next_pa').to_dicts()
        assert bool(c['existing_forecast'])==v['in_current_panel']
        for r in c['existing_forecast']: assert np.isclose(r['preseason_p']*r['preseason_conditional_pa'],r['preseason_pa'],atol=1e-10,rtol=0)
        lines += [f"## {v['player_name']} at {y} origin",'',NOTES[pid,y],'',
            f"Snapshot {v['in_snapshot']}; support {v['in_support']}; stored roster {v['in_stored_roster']}; current panel {v['in_current_panel']}. Ranking information date {info[y]}.",'']
        for h in v['own_history']: lines.append(f"- {h['season']}: {h['plate_appearances']} PA, {h['home_runs']} HR, {h['strike_outs']} K, {h['unintentional_walks']} unintentional walks.")
        lines+=['', 'Existing saved forecast/intermediates: '+json.dumps(c['existing_forecast'])+'.','',
            'Origin-selected peers (panel membership; next-year PA attached after selection): '+ '; '.join(f"{r['player_name']} ({r['in_current_panel']}; {r['diagnostic_next_pa']})" for r in c['origin_selected_peers'])+'.','',c['peer_limit'],'']
    write('reviewed-cases.json',dict(cases=cases,peer_rule='Same origin and last played MLB season; minimum three-season PA squared distance, player-ID ties; no future results in selection.',player_walkthrough_status='complete_for_source_diagnosis'))
    text='\n'.join(lines)+'\n'; path=a.OUT/'player-walkthrough.md'; assert not path.exists(); path.write_text(text,encoding='utf8');shutil.copyfile(path,a.EVIDENCE/path.name)
    write('dated-signing-review.json',dict(sources=SOURCES,ranking_information_dates=info,preflight_sha256=sha256_file(prepath),
        source_design='V67 changed only scouting vintage; other inputs and membership intentionally remained through prior December.',
        source_design_paths={str(p):sha256_file(p) for p in [a.ROOT/'scripts/prepare_hitter_preseason_readiness_v67.py',a.ROOT/'scripts/evaluate_hitter_preseason_readiness_v68.py']},
        original_web_sources_reviewed=True,dated_sources_not_model_inputs=True,all_three_returning_omissions_have_pre_rank_date_agreement_evidence=True,
        precise_historical_roster_reconstruction_complete=False,new_prediction=False))
    freeze=subprocess.run([sys.executable,'-X','utf8','scripts/verify_hitter_full_2026_freeze.py'],cwd=a.ROOT,check=True,capture_output=True,text=True)
    tests=subprocess.run([sys.executable,'-X','utf8','-m','pytest','-p','no:cacheprovider','tests/test_hitter_value_ledger.py','tests/test_hitter_research_export.py','-q'],cwd=a.ROOT,check=True,capture_output=True,text=True)
    write('final-review.json',dict(execution_verification_status='complete',player_walkthrough_status='complete_for_source_diagnosis',
        distinct_reviewed_player_origins=len({(c['record']['player_id'],c['record']['origin_year']) for c in cases}),candidate_rows_reconstructed=len(rows),
        all_original_ledger_hashes_verified=True,all_current_forecasts_unchanged=True,new_fits=0,protected_freeze=json.loads(freeze.stdout),tests=tests.stdout,
        reviewer_sha256=sha256_file(Path(__file__)),artifact_hashes={p.name:sha256_file(p) for p in a.EVIDENCE.iterdir()},
        inclusion_rule_approved=False,full_goal_complete=False,decision='Fix full-preseason membership timing under a new source contract; do not add all former hitters or tune to returning names.'))
    print('Reviewed',len(rows),'source candidates and',len({(c['record']['player_id'],c['record']['origin_year']) for c in cases}),'distinct player origins; previous accounting audit preserved.')


if __name__=='__main__': main()
