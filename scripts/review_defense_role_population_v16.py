"""Fixed player/peer walks and honest bounds for unresolved resumed-game dates."""
from pathlib import Path
import json

import polars as pl

from capture_defense_role_population_v16 import ROOT, OUT, PUBLIC, read
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file

DEST=OUT/'scope-repair'
FIELDS=('fielding_outs','reviewed_starts','appearances')


def write(name,value):
    save(DEST/name,value);save(PUBLIC/'scope-repair'/name,value)


def bounds(r,scope,field):
    """No forced point date: early + late + unknown conserve certified annuals."""
    full=r[f'{scope}_full_year_{field}']
    if full is None:return None
    records=[p for p in r['current_role_periods'] if scope=='all' or (p['sport_id']==1)==(scope=='MLB')]
    def vec(part):return [sum(p[field] for p in records if p['position_code']==position and p['period']==part)
                          for position in range(2,11)]
    early,late,unknown=vec('before_August'),vec('August_onward'),vec(None)
    assert [a+b+c for a,b,c in zip(early,late,unknown)]==full
    return dict(certified_full_year=full,before_August_minimum=early,
        August_onward_minimum=late,unresolved_period_exposure=unknown,
        before_August_maximum=[a+b for a,b in zip(early,unknown)],
        August_onward_maximum=[a+b for a,b in zip(late,unknown)],
        exact_periods=not any(unknown))


def describe(vector):
    if vector is None:return 'unknown measurement'
    return ', '.join(f'{p} {v}' for p,v in zip(('C','1B','2B','3B','SS','LF','CF','RF','DH'),vector) if v) or 'certified zero'


def main():
    protections();verification=read(DEST/'independent-verification.json')
    assert verification['source_integrity']=='pass' and not (DEST/'player-walkthrough.json').exists()
    f=pl.read_parquet(DEST/'current-role-source-features.parquet')
    lookup={r['player_id']:r['player_name'] for r in f.to_dicts()}
    by_pair={(r['player_id'],r['origin']):r for r in f.to_dicts()}
    all_bounds=[]
    for r in f.to_dicts():
        record=dict(row_id=r['row_id'],player_id=r['player_id'],origin=r['origin'],fold=r['fold'])
        for scope in ('all','MLB','minor'):
            for field in FIELDS:record[f'{scope}_{field}']=bounds(r,scope,field)
        all_bounds.append(record)
    pl.DataFrame(all_bounds,infer_schema_length=None).write_parquet(DEST/'current-role-period-bounds.parquet')
    bounded={r['player_id']:r for r in all_bounds if r['origin']==2024}
    old=read(ROOT/'reports/generated/defense-role-v15/player-walkthrough.json');cases=[]
    lines=['# Current assignments and qualified dates across the role population','',
        'This is a source review, not a new forecast. Full-season use is distinct from older repertoire, '
        'recent assignment, defensive skill and future playing time. The original fixed nineteen focal '
        'cases and 57 origin-blind peers remain. Every saved source history, model input, prediction and '
        'later outcome is retained in the numerical walkthrough.','',
        'A null exact period does not erase the entire season. Known early use, known late use and '
        'unresolved-date exposure add to the certified annual total. Bounds show the possible late '
        'assignment without putting resumed innings on a guessed date.','']
    for c in old['cases']:
        records=[]
        for previous in c['records']:
            pid,y=previous['player_id'],previous['origin'];r=by_pair[pid,y]
            record=dict(previous,population_role_source=r,
                qualified_period_bounds={f'{s}_{field}':bounds(r,s,field) for s in ('MLB','minor') for field in FIELDS},
                current_source_corrected=True,new_forecast=None,no_new_fit=True)
            records.append(record)
        cases.append(dict(selection=c['selection'],peer_rule=c['peer_rule'],records=records))
        focal=records[0]
        lines += [f"## {focal['name']} origin {focal['origin']}",'',focal['baseball_judgment'],'']
        for index,r in enumerate(records):
            source=r['population_role_source'];role=r['old_role_inputs']
            lines += [f"{'Focal' if index==0 else 'Origin blind peer'} {r['name']}; age {r['age']}; {r['stage']}; fold {r['fold']}.",
                f"Current MLB outs: {describe(source['MLB_full_year_fielding_outs'])}. "
                f"Current minor outs: {describe(source['minor_full_year_fielding_outs'])}.",
                f"Current MLB starts: {describe(source['MLB_full_year_reviewed_starts'])}. "
                f"Current minor starts: {describe(source['minor_full_year_reviewed_starts'])}.",
                f"Older allocation used {role['evidence_kind']}, own-evidence weight {role['own_weight']:.4f}. "
                f"PA stays {r['expected_PA_unchanged']:.2f}; actual later PA {r['later_reality_only']['PA']}."]
            for scope in ('MLB','minor'):
                b=r['qualified_period_bounds'][scope+'_fielding_outs']
                if b is not None:
                    lines.append(f"{scope} known late outs: {describe(b['August_onward_minimum'])}; "
                        f"unresolved-period outs: {describe(b['unresolved_period_exposure'])}. "
                        'Unresolved exposure is not added to a guessed late-season point.')
            lines += ['No new rate, role or value forecast; fixed quality and later outcomes remain separate.','']
    report=read(DEST/'source-review.json')
    exceptions=[]
    lines += ['## Remaining measurement differences and suspended game records','']
    for s in report['residual_mismatches']:
        differences=[p for p in s['comparisons'] if p['annual']!=p['log']]
        exceptions.append(dict(**s,name=lookup.get(s['player_id'],'Source name unavailable'),
            new_forecast=None,no_new_fit=True))
        deltas='; '.join(f"position {d['position_code']}: annual {d['annual']}, log {d['log']}" for d in differences)
        lines += [f"{lookup.get(s['player_id'],s['player_id'])}, origin {s['origin']}, sport {s['sport_id']}: {deltas}.",
            'Matching outs remain available. Starts or appearances that disagree stay unknown; '
            'there is no player-specific correction or invented DH role.','']
    for s in report['resumed_two_team_scopes']:
        lines += [f"Player {s['player_id']}, origin {s['origin']}: two certified opposing-team position records."]
        for r in s['team_grain_resumption_records']:
            lines.append(f"Game {r['game_id']}, team {r['team_id']}: {r['fielding_outs']} outs, "
                         f"{r['raw_starts']} raw starts; schedule dates {r['schedule_dates']}.")
        lines += ['Both segments count toward annual innings; neither is assigned to a guessed period.','']
    lines += ['## Source judgment and next model comparison','',
        'The fixed cases support preserving current assignment separately from older roles: '
        'Witt has current SS and older 3B; Buxton returned to CF after his DH season; '
        'Ohtani has observed pure DH, not unknown hitter role; Eldridge has current 1B/DH '
        'and older RF rather than the 2B/3B jobs of a broad first-base prior. Carter, Chourio '
        'and Dawson still require both minor records and tiny higher-level stints. None of '
        'these source facts measures unobserved defensive quality.','',
        'The population is ready for one current-assignment/full-repertoire comparison. '
        'Its inputs must use certified annual roles and qualified dated evidence or explicit '
        'uncertainty. Keep fixed PA, batting, native defensive quality, capacities and reserves. '
        'No new model, accuracy improvement, promotion or frozen-forecast change occurred.','']
    write('player-walkthrough.json',dict(player_walkthrough_status='pending_manual_read',
        focal_cases=len(cases),peer_records=sum(len(c['records'])-1 for c in cases),cases=cases,
        measurement_exceptions=exceptions,resumed_two_team_scopes=report['resumed_two_team_scopes'],
        no_fits=True,no_accuracy_claim=True,no_deployment=True,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),DEST/'independent-verification.json',
            DEST/'current-role-period-bounds.parquet',ROOT/'reports/generated/defense-role-v15/player-walkthrough.json']}))
    text='\n'.join(lines).rstrip()+'\n'
    for folder in (DEST,PUBLIC/'scope-repair'):(folder/'player-walkthrough.md').write_text(text,encoding='utf8',newline='\n')
    protections();print(f'Review prepared: {len(cases)} focal cases, 57 peers and {len(exceptions)} source exceptions.',flush=True)


if __name__=='__main__':main()
