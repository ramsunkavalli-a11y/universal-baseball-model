"""Independent population reconstruction and player source walkthrough."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import polars as pl
import capture_hitter_preseason_population as c
from universal_baseball.hitter_preseason_role import role_from_position, role_from_transaction, reconcile_hints
from universal_baseball.storage import sha256_file

ROOT, OUT = c.ROOT,c.OUT
EVIDENCE = ROOT/'reports/model-evidence/hitter-preseason-population-source'
REPORT = ROOT/'docs/hitter-preseason-population-source-result.md'
# Dated supplementary role evidence, not an eligibility exception or talent bonus.
TWO_WAY = dict(player_id=660271,known_date='2017-12-08',role='two_way_hint',
    url='https://www.mlb.com/news/shohei-ohtani-agrees-to-deal-with-angels-c263134146',
    fact='Contemporaneous MLB report identifies a two-way Japanese professional agreeing with the Angels.',
    model_feature=False,nationality_bonus=False)


def encoded(row):
    return json.dumps(row,sort_keys=True,ensure_ascii=False,separators=(',',':'))


def dates(row):
    values = [str(row.get(n))[:10] for n in ['date','effectiveDate','resolutionDate'] if row.get(n)]
    return max(values) if row.get('date') else None


def main():
    assert not (OUT/'final-review.json').exists(), 'Preserve completed source review'
    report = c.read(OUT/'population-report.json')
    for path,h in {**report['input_hashes'],**report['output_hashes']}.items():
        assert sha256_file(Path(path))==h,path
    ledger = pl.read_parquet(OUT/'population.parquet')
    panel = pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet')
    stints = pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    qpath = ROOT/'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet'
    assert sha256_file(qpath)==report['forecast_sha256']
    per_year, role_rows = [], []
    with zipfile.ZipFile(EVIDENCE/'raw-captures.zip') as z:
        for path in (OUT/'captures').iterdir():
            assert z.read(path.name)==path.read_bytes(),path
    for origin in range(2011,2025):
        year = origin+1
        cutoff = c.read(c.CONFIG)[str(year)]['date']
        mlb_teams = {r['id'] for r in c.read(OUT/f'captures/teams-{year}.json')['teams']}
        listing = defaultdict(list)
        for team in mlb_teams:
            payload = c.read(OUT/f'captures/roster-{year}-{team}-40Man.json')
            assert isinstance(payload['roster'],list)
            for row in payload['roster']:
                listing[row['person']['id']].append((team,row))
        transactions = c.read(OUT/f'captures/transactions-{year}.json')['transactions']
        monthly = []
        for path in sorted((OUT/'captures').glob(f'transactions-{year}-*.json')):
            if path.name.endswith('.metadata.json'):
                continue
            monthly.extend(c.read(path)['transactions'])
        assert Counter(map(encoded,transactions))==Counter(map(encoded,monthly))
        event_map = defaultdict(list)
        unique_events = {}
        for row in transactions:
            assert f'{origin}-10-01'<=row['date'][:10]<=cutoff
            pid = row.get('person',{}).get('id')
            if not pid or not {row.get('fromTeam',{}).get('id'),row.get('toTeam',{}).get('id')} & mlb_teams:
                continue
            day = dates(row)
            if day and day<=cutoff:
                unique_events[encoded(row)]=row
        for row in unique_events.values():
            event_map[row['person']['id']].append(row)
        old = panel.filter(pl.col('origin_year')==origin)
        part = ledger.filter(pl.col('origin_year')==origin)
        expected = set(old['player_id'])|set(listing)|set(event_map)
        assert set(part['player_id'])==expected and len(part)==len(expected)
        assert part.filter(pl.col('current_model_origin')).select(pl.col('current_row_id').alias('row_id'),'player_id').sort('row_id').equals(old.select('row_id','player_id').sort('row_id'))
        historic = stints.filter((pl.col('season')<=origin)&(pl.col('plate_appearances')>0))
        recent = historic.filter(pl.col('season')>=origin-2).group_by('player_id').agg(
            pl.col('plate_appearances').sum().alias('pa'),
            pl.when(pl.col('sport_id')==1).then(pl.col('plate_appearances')).otherwise(0).sum().alias('mlb'))
        known = {r['player_id']:(r['pa'],r['mlb']) for r in recent.iter_rows(named=True)}
        history_positions = defaultdict(list)
        for row in historic.select('player_id','position').iter_rows(named=True):
            history_positions[row['player_id']].append({'code':row['position']})
        for row in part.iter_rows(named=True):
            pid = row['player_id']
            assert row['returned_40man']==bool(listing[pid])
            assert row['roster_team_ids']==sorted({t for t,_ in listing[pid]})
            assert row['eligible_mlb_team_event_records']==len(event_map[pid])
            assert (row['recent_domestic_pa'],row['recent_mlb_pa'])==known.get(pid,(0,0))
            hints = [role_from_position(x) for x in history_positions[pid]]
            hints.extend(role_from_position(raw.get('position',{})) for _,raw in listing[pid])
            hints.extend(role_from_transaction(e) for e in event_map[pid])
            supplement = TWO_WAY if pid==TWO_WAY['player_id'] and TWO_WAY['known_date']<=cutoff else None
            if supplement:
                hints.append(supplement['role'])
            role_rows.append(dict(candidate_key=row['candidate_key'],origin_year=origin,player_id=pid,
                                  original_role_status=row['role_status'],reviewed_role_hint=reconcile_hints(hints),
                                  dated_supplementary_role=bool(supplement),hitter_eligibility_approved=False))
        per_year.append(dict(origin_year=origin,independent_membership_rows=len(part),all_original_rows_retained=True,
                             independent_roster_event_and_workload_checks=True))
    roles = pl.DataFrame(role_rows).sort('origin_year','player_id')
    roles.write_parquet(OUT/'reviewed-role-hints.parquet')
    cases = c.read(OUT/'source-cases.json')['cases']
    lines = ['# Preseason source player walkthrough','',
        'These are source checks, not new forecasts. All original projections are unchanged. New rows have no predicted talent or workload yet. Roles are evidence hints, not verified fielding positions or guaranteed MLB jobs. Later MLB PA is attached only after the population is sealed.','']
    for case in cases:
        origin,pid = case['origin_year'],case['player_id']
        row = case['source_row']
        role = roles.filter((pl.col('origin_year')==origin)&(pl.col('player_id')==pid))
        case['reviewed_role_hint'] = role['reviewed_role_hint'][0] if len(role) else 'no_source_candidate'
        case['dated_supplementary_role'] = TWO_WAY if pid==660271 else None
        for forecast in case['existing_forecast']:
            assert abs(forecast['preseason_p']*forecast['preseason_conditional_pa']-forecast['preseason_pa'])<1e-8
        lines.extend([f"## {case['display_name']} after {origin}",'',
            f"Preseason cutoff {c.read(c.CONFIG)[str(origin+1)]['date']}; selection {case['selection'].replace('_',' ')}.",'',
            f"Source role hint {case['reviewed_role_hint'].replace('_',' ')}. " +
            (f"Old model row {row['current_model_origin']}; returned 40Man {row['returned_40man']}; returned teams {row['roster_team_ids']}; eligible positive context records {row['positive_context_records']}." if row else
             'No source candidate or original forecast. Official bounded transactions did not recover this reported agreement.'),''])
        for h in case['own_history']:
            lines.append(f"- {h['season']} {h['bucket']}: {h['plate_appearances']} PA, {h['home_runs']} HR, {h['unintentional_walks']} UBB, {h['strike_outs']} K; reported age {h['reported_age']}.")
        if not case['own_history']:
            lines.append('No domestic batting observations in these source windows; foreign performance is missing, not zero talent.')
        lines.extend(['','Cutoff-eligible raw event descriptions:'])
        for event in (case['raw_source'] or {}).get('eligible_events',[]):
            lines.append(f"- {event['available_date']}: {event['raw']['description']}")
        lines.extend(['','Original saved forecast intermediates: '+json.dumps(case['existing_forecast'],ensure_ascii=False)+'.','',
                      f"Following-year MLB PA {case['diagnostic_next_pa']}; no new prediction is fabricated.",'',
                      'Origin-selected comparisons: '+ '; '.join(f"{v['player_name']} ({v['player_id']}; {v['recent_mlb_pa']} recent MLB PA)" for v in case['origin_selected_peers'])+'.',
                      case['peer_limit'],''])
    lines.extend(['## Baseball interpretation','',
        'Conforto and Alfaro are genuine recovered source candidates, not automatic playing-time upgrades. Sano remains a coverage gap because the official record follows the reported agreement. Ohtani is a dated two-way professional despite a pitcher-only signing description and no January reserve listing. Suzuki uses generic OF code O, which the original numeric role hint missed; the additive role review recognizes it without rewriting the original ledger. Yoshida, Lee and Kim have dated acquisition/listing context but lack foreign production inputs.','',
        'Wright was already retained and listed; a source refresh cannot explain away his very limited return. Belt remains an unsigned player with strong recent production, not a known zero-talent or retirement case. Pollock, Canha and Devers have other preseason teams, not their later Giants affiliation. Solano is the fixed lowest-ID listed regular outside the diagnostic set, not an outcome-selected success.','',
        'Domestic-exposure comparisons for foreign players are poor talent peers: the original Ohtani pool contains pitchers, and the old Suzuki role is unknown. Empty comparison sets for Yoshida, Lee and Kim are a support warning, not evidence of a worthless profile. The reviewed role overlay is not a retrained projection or a newly validated set of comparables.','',
        'No model improvement/deterioration categories apply because no fit or forecast changed. Review completion does not certify deployment, historical rights, medical clearance, foreign translations or a complete hitter universe.',''])
    walkthrough = OUT/'player-walkthrough.md'
    walkthrough.write_text('\n'.join(lines),encoding='utf8',newline='\n')
    c.write(OUT/'reviewed-cases.json',dict(cases=cases,player_walkthrough_status='complete_for_source',new_fits=0,
                                        future_performance_not_used_for_roles=True))
    freeze = subprocess.run([sys.executable,'-X','utf8','scripts/verify_hitter_full_2026_freeze.py'],cwd=ROOT,check=True,capture_output=True,text=True)
    tests = subprocess.run([sys.executable,'-X','utf8','-m','pytest','-p','no:cacheprovider',
        'tests/test_hitter_preseason_population.py','tests/test_hitter_preseason_role.py','tests/test_hitter_research_export.py','-q'],
        cwd=ROOT,check=True,capture_output=True,text=True)
    assert sha256_file(qpath)==report['forecast_sha256']
    assert len(cases)==14 and len({(r['player_id'],r['origin_year']) for r in cases})==14
    for name in ['probe.json','probe-adjudication.json','capture-report-v3.json','population.parquet',
                 'population-membership-seal.json','population-report.json','source-cases.json',
                 'reviewed-role-hints.parquet','reviewed-cases.json','player-walkthrough.md']:
        target = EVIDENCE/name
        assert not target.exists()
        shutil.copyfile(OUT/name,target)
    assert REPORT.exists(), 'Save manual interpretation before final review'
    final = dict(independent_source_checks=per_year,original_rows=63282,source_population_rows=len(ledger),
        distinct_player_origin_walks=14,player_walkthrough_status='complete_for_source',
        original_forecast_sha256=report['forecast_sha256'],forecasts_unchanged=True,new_fits=0,
        tests=tests.stdout,protected_freeze=json.loads(freeze.stdout),foreign_talent_solution_complete=False,
        new_hitter_eligibility_approved=False,full_roster_admission_allowed=False,full_goal_complete=False,
        reviewer_sha256=sha256_file(Path(__file__)),
        interpretation_hashes={str(p):sha256_file(p) for p in [REPORT,ROOT/'src/universal_baseball/hitter_preseason_role.py',
            ROOT/'tests/test_hitter_preseason_role.py']},
        artifact_hashes={p.name:sha256_file(p) for p in EVIDENCE.iterdir()},
        next_action='Use dated population and role evidence in a fixed integration contract; acquire/translate foreign performance before certifying foreign-player forecasts.')
    c.write(OUT/'final-review.json',final)
    shutil.copyfile(OUT/'final-review.json',EVIDENCE/'final-review.json')
    print('Independent source reconstruction and fourteen player walks complete;',tests.stdout.strip(),flush=True)


if __name__=='__main__': main()
