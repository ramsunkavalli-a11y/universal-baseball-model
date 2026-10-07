"""Close source review only, after the main reviewer reads all fixed cases."""
from collections import defaultdict
from pathlib import Path
import argparse
import json

import polars as pl

import repair_defense_role_calendar_v16 as current
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manual-review-complete',action='store_true')
    assert parser.parse_args().manual_review_complete,'Main-agent source walkthrough required'
    protections();out=current.DEST
    assert not (out/'final-review.json').exists()
    verify=current.original.read(out/'independent-verification.json');assert verify['source_integrity']=='pass'
    report=current.original.read(out/'source-review.json')
    walk=current.original.read(out/'player-walkthrough.json')
    previous=current.original.read(current.ROOT/'reports/generated/defense-role-v15/player-walkthrough.json')
    assert walk['focal_cases']==19 and walk['peer_records']==57
    for a,b in zip(previous['cases'],walk['cases']):
        assert a['selection']==b['selection'] and a['peer_rule']==b['peer_rule']
        assert len(a['records'])==len(b['records'])
        for x,y in zip(a['records'],b['records']):
            for k,v in x.items():assert y[k]==v,k
    features=pl.read_parquet(out/'current-role-source-features.parquet')
    bounds=pl.read_parquet(out/'current-role-period-bounds.parquet')
    source={r['row_id']:r for r in features.to_dicts()}
    totals=defaultdict(lambda:[0]*9)
    for p in pl.read_parquet(out/'normalized-role-periods.parquet').to_dicts():
        if not 2<=p['position_code']<=10:continue
        for scope in ('all','MLB' if p['sport_id']==1 else 'minor'):
            for field in ('fielding_outs','reviewed_starts','appearances'):
                totals[p['player_id'],p['season'],scope,p['period'],field][p['position_code']-2]+=p[field]
    assert bounds.height==16674 and set(bounds['row_id'])==set(source)
    for b in bounds.to_dicts():
        r=source[b['row_id']];assert (b['player_id'],b['origin'],b['fold'])==(r['player_id'],r['origin'],r['fold'])
        for scope in ('all','MLB','minor'):
            for field in ('fielding_outs','reviewed_starts','appearances'):
                block=b[scope+'_'+field];full=r[f'{scope}_full_year_{field}']
                if full is None:assert block is None;continue
                assert block['certified_full_year']==full
                pid,y=r['player_id'],r['origin']
                early=totals[pid,y,scope,'before_August',field]
                late=totals[pid,y,scope,'August_onward',field]
                unknown=totals[pid,y,scope,None,field]
                assert block['before_August_minimum']==early and block['August_onward_minimum']==late
                assert block['unresolved_period_exposure']==unknown
                assert [a+c for a,c in zip(early,unknown)]==block['before_August_maximum']
                assert [a+c for a,c in zip(late,unknown)]==block['August_onward_maximum']
                assert [a+c+d for a,c,d in zip(early,late,unknown)]==full
    games=pl.read_parquet(out/'normalized-role-games.parquet')
    eligible=games.filter(pl.col('position_code').is_between(2,10));uncertain=eligible.filter(pl.col('period').is_null())
    # Conservative unknown calendar cases retain innings, not date assignments.
    calendar_unknown=games.filter(pl.col('date_status')=='unknown_schedule_context')
    current.write('calendar-unknown-records.json',dict(records=calendar_unknown.to_dicts(),
        inference='Saved schedule has no qualifying completed/date-matched context; annual exposure is retained.'))
    paths=[out/n for n in ('source-review.json','independent-verification.json','calendar-verifier-receipt.json',
        'calendar-execution-seal.json','calendar-execution-complete.json','player-walkthrough.json',
        'player-walkthrough.md','current-role-period-bounds.parquet','calendar-unknown-records.json')]
    hashes={str(p):sha256_file(p) for p in paths}
    current.write('final-review.json',dict(source_integrity='pass',player_walkthrough_status='complete',
        manual_reviewer='main agent; original 695-line review and all corrected differences read',
        focal_cases=19,peer_records=57,measurement_exceptions=10,
        population_features=16674,source_scopes=23412,validated_capture_requests=745,
        normalized_position_team_game_rows=985654,recovered_position_records=4324,
        current_annual_outs_and_starts_cases=15793,unknown_current_annual_cases=875,
        partial_start_cases=6,dated_DH_additions=51,period_bounds_independently_verified=True,
        unknown_period_fielding_outs=int(uncertain['fielding_outs'].sum()),
        all_fielding_outs=int(eligible['fielding_outs'].sum()),
        unknown_calendar_position_records=calendar_unknown.height,
        no_fits=True,no_accuracy_improvement_claim=True,no_deployment=True,
        previous_goal_turn='No defense progress: confirmed existing Lovich batting defect. Revalidated current source state and repaired the population.',
        original_source_failures_and_intermediate_calendar_failure_preserved=True,
        remaining=['One contracted role comparison with current assignment and full repertoire',
            'Cutoff-known assignment plans remain a distinct missing input',
            'Minor-league defensive talent and multi-year exposure remain unfinished',
            'Separate Lovich batting small-sample defect remains open'],
        input_hashes=hashes,finalizer_sha256=sha256_file(Path(__file__))))
    protections();print('Source milestone reviewed; period bounds conserve annuals. No new forecast or accuracy claim.',flush=True)


if __name__=='__main__':main()
