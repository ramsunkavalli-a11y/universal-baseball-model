"""Independent annual aggregation, period masks and fixed-player source review."""
from collections import defaultdict
from datetime import date
from pathlib import Path
import gzip
import json

import numpy as np
import polars as pl

from capture_defense_role_population_v16 import ROOT, OUT, PUBLIC, SOURCE, SPORTS, read
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file

DEST=OUT/'scope-repair'
FIELDS=('fielding_outs','reviewed_starts','appearances')


def write(name,value):
    save(DEST/name,value);save(PUBLIC/'scope-repair'/name,value)


def independent_calendar():
    """Read raw dates directly, not the role parser's context projection."""
    schedules={}
    for year in range(2021,2025):
        for sport in (1,11,12,13,14,16):
            if sport==1:
                p=ROOT/'reports/generated/hitter-injury-history-v2/source/captures'/f'schedule-{year}.json'
                payload=read(p)
            else:
                p=ROOT/'reports/generated/hitter-minor-statcast-capture/official-context'/f'schedule-{year}-{sport}.json.gz'
                payload=json.loads(gzip.decompress(p.read_bytes()))
            grouped=defaultdict(list)
            for day in payload['dates']:
                for g in day['games']:grouped[g['gamePk']].append((day['date'],g))
            for pk,entries in grouped.items():
                all_dates={d for d,g in entries}|{g['officialDate'] for d,g in entries}
                all_dates|={g[k] for d,g in entries for k in ('resumeGameDate','resumedFromDate') if g.get(k)}
                periods={'before_August' if date.fromisoformat(d).month<8 else 'August_onward' for d in all_dates}
                teams={tuple(sorted(g['teams'][s]['team']['id'] for s in ('home','away'))) for d,g in entries}
                originals={g['officialDate'] for d,g in entries}
                valid=len(teams)==len(originals)==1 and all(g['status']['abstractGameState']=='Final' for d,g in entries)
                schedules[year,sport,pk]=dict(dates=sorted(all_dates),
                    period=next(iter(periods)) if valid and len(periods)==1 else None)
    return schedules


def main():
    protections();assert not (DEST/'independent-verification.json').exists()
    report=read(DEST/'source-review.json');manifest=read(OUT/'manifest.json')
    for field in ('input_hashes','output_hashes'):
        for path,digest in report[field].items():assert sha256_file(Path(path))==digest,path
    complete=read(OUT/'capture-complete.json')
    for path,digest in complete['hashes'].items():assert sha256_file(Path(path))==digest,path
    assert len(manifest['requests'])==745 and complete['all_manifest_requests_completed']
    scopes=read(DEST/'scope-comparisons.json')['scopes']
    scope_lookup={(s['player_id'],s['origin'],s['sport_id']):s for s in scopes}
    expected_keys={(pid,j['origin'],j['sport_id']) for j in manifest['requests'] for pid in j['player_ids']}
    assert set(scope_lookup)==expected_keys and len(scope_lookup)==23412
    games=pl.read_parquet(DEST/'normalized-role-games.parquet')
    assert games.height==985654 and games['season'].max()==2024
    key=['player_id','game_id','team_id','position_code']
    assert games.unique(key).height==games.height
    old=pl.read_parquet(OUT/'verified-role-games.parquet')
    fields=['fielding_outs','raw_starts','reviewed_starts','appearances','certified_dual_DH_addition']
    paired=old.select(key+fields).join(games.select(key+fields),on=key,how='left',suffix='_new',validate='1:1')
    assert paired.height==old.height and paired['fielding_outs_new'].null_count()==0
    for f in fields:assert paired[f].equals(paired[f+'_new'])
    # Annual expectations recomputed directly from the original source.
    expected=defaultdict(lambda:defaultdict(lambda:dict(fielding_outs=0,raw_starts=0,appearances=0)))
    for r in pl.read_parquet(SOURCE).filter(pl.col('season').is_between(2021,2024)).to_dicts():
        k=(r['player_id'],r['season'],SPORTS[r['normalized_level']])
        if k not in expected_keys:continue
        d=expected[k][r['league_id'],int(r['position_code'])]
        d['fielding_outs']+=r['fielding_outs'];d['raw_starts']+=r['games_started'];d['appearances']+=r['games_played']
    actual=defaultdict(dict)
    sums=games.group_by('player_id','season','sport_id','league_id','position_code').agg(
        *[pl.col(f).sum() for f in fields])
    for r in sums.to_dicts():actual[r['player_id'],r['season'],r['sport_id']][r['league_id'],r['position_code']]=r
    calendar=independent_calendar();unknown=defaultdict(lambda:defaultdict(int))
    vectors=defaultdict(lambda:np.zeros(9,dtype=np.int64))
    for r in games.iter_rows(named=True):
        g=calendar[r['season'],r['sport_id'],r['game_id']]
        assert r['period']==g['period'] and r['schedule_dates']==g['dates']
        if r['period'] is None:
            for f in FIELDS:
                if r[f]>0:unknown[r['player_id'],r['season'],r['sport_id']][f]+=r[f]
        if 2<=r['position_code']<=10:
            for scope in ('all','MLB' if r['sport_id']==1 else 'minor'):
                for part in ('full_year',r['period']):
                    if part is None:continue
                    for f in FIELDS:vectors[r['player_id'],r['season'],scope,part,f][r['position_code']-2]+=r[f]
    raw_fields={'fielding_outs':'fielding_outs','reviewed_starts':'raw_starts','appearances':'appearances'}
    zero=dict(fielding_outs=0,raw_starts=0,appearances=0)
    for k,s in scope_lookup.items():
        positions=set(expected[k])|set(actual[k])
        for f,raw in raw_fields.items():
            matches=all(expected[k].get(p,zero)[raw]==actual[k].get(p,zero)[raw] for p in positions)
            cert=s['measurements'][f]
            assert cert['full_year']==matches and cert['periods']==(matches and unknown[k][f]==0)
            assert cert['uncertain_exposure']==unknown[k][f]
        assert len(s['comparisons'])==len(positions)
    corrected=games.filter(pl.col('certified_dual_DH_addition')>0)
    assert corrected.height==51 and corrected['player_id'].unique().to_list()==[660271]
    assert corrected.unique(['player_id','game_id']).height==51 and corrected['position_code'].unique().to_list()==[10]
    assert corrected['fielding_outs'].sum()==0 and corrected['raw_starts'].sum()==0
    features=pl.read_parquet(DEST/'current-role-source-features.parquet')
    lookup={r['row_id']:r for r in features.to_dicts()}
    assert set(lookup)=={r['row_id'] for r in manifest['input_cases']}
    for case in manifest['input_cases']:
        r=lookup[case['row_id']];pid,y=case['player_id'],case['origin']
        assert r['player_id']==pid and r['origin']==y and r['fold']==case['fold']
        for scope in ('all','MLB','minor'):
            sports=[s for s in case['declared_sports'] if scope=='all' or (s==1)==(scope=='MLB')]
            for part in ('full_year','before_August','August_onward'):
                for f in FIELDS:
                    known=bool(sports) and all(scope_lookup[pid,y,s]['measurements'][f][
                        'full_year' if part=='full_year' else 'periods'] for s in sports)
                    name=f'{scope}_{part}_{f}'
                    assert r[name+'_known']==known
                    if known:assert r[name]==vectors[pid,y,scope,part,f].tolist()
                    else:assert r[name] is None
    periods=pl.read_parquet(DEST/'normalized-role-periods.parquet')
    for f in fields:assert periods[f].sum()==games[f].sum()
    notes=dict(source_integrity='pass',feature_rows=16674,source_scopes=23412,
        raw_capture_hashes_checked=745,original_validated_rows_preserved=old.height,
        recovered_position_records=games.height-old.height,all_annual_measurement_flags_recomputed=True,
        all_calendar_periods_recomputed=True,all_nullable_feature_vectors_recomputed=True,
        all_current_identities_preserved=True,dated_DH_additions=51,no_fits=True,
        no_accuracy_claim=True,no_deployment=True,player_walkthrough_status='pending',
        source_receipt_sha256=sha256_file(DEST/'source-review.json'),verifier_sha256=sha256_file(Path(__file__)))
    write('independent-verification.json',notes);protections()
    print(json.dumps(notes),flush=True)


if __name__=='__main__':main()
