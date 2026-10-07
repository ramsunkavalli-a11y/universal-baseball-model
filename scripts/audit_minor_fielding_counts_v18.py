"""Recover count coverage, then audit genuine later-MLB talent support; no fit."""
from collections import defaultdict
from pathlib import Path
import argparse
import gzip
import json
import math

import polars as pl

from universal_baseball.minor_fielding_counts import COUNT_FIELDS, CATCHER_FIELDS, extract, age_band, sample_band, pool_quality
from universal_baseball.position_role_source import baseball_innings_to_outs
from universal_baseball.storage import sha256_file
from build_defense_native_range_v3 import identity
from run_hitter_finite_return_baseline import protections, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/defense-minor-counts-v18'
PUBLIC = ROOT/'reports/model-evidence/defense-minor-counts-v18'
USAGE = ROOT/'reports/generated/defense-position-opportunity-v7'
NATIVE = ROOT/'reports/generated/defense-native-range-v3'
CATCHER = ROOT/'reports/generated/catcher-throw-block-v5'
FIXED = (683146,665742,682626,682928,678882,671185,672275,663728,643446,805811)
KEY = ('source_id','season','usage_scope','player_id','position_code')


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def write(name, value):
    for dest in (OUT,PUBLIC):
        dest.mkdir(parents=True,exist_ok=True)
        save(dest/name,value)


def hashes(paths):
    return {str(p):sha256_file(p) for p in paths}


def verify(values):
    for p, h in values.items():
        assert sha256_file(Path(p)) == h, p


def source():
    protections()
    assert not (OUT/'source-preflight.json').exists(), 'Preserve previous source audit'
    OUT.mkdir(parents=True,exist_ok=True)
    review = read(USAGE/'source-review.json')
    verify(review['output_hashes'])
    frame = pl.read_parquet(USAGE/'source.parquet').filter(~pl.col('is_mlb') & (pl.col('season') <= 2024))
    accepted = {tuple(r[k] for k in KEY):r for r in frame.to_dicts()}
    assert len(accepted) == len(frame)
    captures = []
    for name, h in review['input_hashes'].items():
        p = Path(name)
        is_early = p.name.startswith('fielding-') and p.suffix == '.gz'
        repair = p.name == 'fielding.json.gz' and 'advanced-rookie-repair' in name
        modern = p.name.startswith('fielding_offset_') and 'historical' in name
        if is_early or repair or modern:
            assert sha256_file(p) == h, name
            captures.append((p,'early' if is_early else 'repair2019' if repair else 'modern'))
    assert sum(k == 'early' for _,k in captures) == 66
    assert sum(k == 'repair2019' for _,k in captures) == 1
    paths = [Path(__file__),ROOT/'docs/defense-minor-counts-v18-contract.md',
        ROOT/'src/universal_baseball/minor_fielding_counts.py',ROOT/'tests/test_minor_fielding_counts.py',
        USAGE/'source-review.json',USAGE/'source.parquet',*[p for p,_ in captures]]
    write('source-preflight.json',dict(before_extraction=True,no_fit=True,accepted_minor_rows=len(frame),
        captures=[dict(path=str(p),kind=k) for p,k in captures],hashes=hashes(paths),
        protected_hashes_checked=True,no_2026_outcomes=True))
    rows=[];seen=set();skipped_mlb=0
    for p,kind in captures:
        if p.suffix == '.gz':
            with gzip.open(p,'rt',encoding='utf8') as stream:
                payload=json.load(stream)
        else:
            payload=read(p)
        splits=payload['splits'] if kind == 'early' else payload['stats'][0]['splits']
        if kind == 'early':
            assert len(splits) == payload['expected']
        for index,s in enumerate(splits):
            y=int(s['season']);league=int(s['league']['id']);pid=int(s['player']['id']);pos=str(s['position']['code'])
            if kind == 'modern' and league in (103,104):
                skipped_mlb+=1;continue
            sport=int(s['sport']['id']) if 'sport' in s else None
            scope=f'sport:{sport}' if kind == 'early' else f'league:{league}'
            key=(kind,y,scope,pid,pos)
            assert key in accepted and key not in seen, key
            seen.add(key);r=accepted[key];stat=s['stat']
            assert r['fielding_outs'] == baseball_innings_to_outs(stat['innings'])
            assert r['games_started'] == int(stat['gamesStarted']) and r['games_played'] == int(stat['gamesPlayed'])
            assert r['league_id'] == league and r['team_id'] == int(s['team']['id'])
            rows.append({**r,**extract(stat),'capture_path':str(p),'capture_split_index':index,
                'raw_num_teams':s.get('numTeams'),'source_age_raw':str(stat.get('age')) if stat.get('age') is not None else None})
    assert seen == set(accepted) and len(rows) == len(frame)
    counts=pl.DataFrame(rows,infer_schema_length=None).sort(list(KEY))
    counts.write_parquet(OUT/'counts.parquet')
    groups=[]
    for (y,level,pos),g in counts.filter(pl.col('position_code').is_in([str(p) for p in range(2,10)])).group_by('season','normalized_level','position_code'):
        rs=g.to_dicts();applicable=[f for f in COUNT_FIELDS if pos == '2' or f not in CATCHER_FIELDS]
        groups.append(dict(season=y,level=level,position=int(pos),rows=len(rs),people=len({r['player_id'] for r in rs}),
            outs=sum(r['fielding_outs'] for r in rs),subtype_certified=all(r['level_subtype_certified'] for r in rs),
            fields={f:dict(recorded=sum(r[f+'_status']=='recorded' for r in rs),missing=sum(r[f+'_status']=='missing' for r in rs),
                invalid=sum(r[f+'_status']=='invalid' for r in rs),nonzero=sum(r[f] is not None and r[f]>0 for r in rs)) for f in applicable},
            chances_identity_failures=sum(r['chances_identity'] is False for r in rs),
            throwing_subset_failures=sum(r['throwing_subset_identity'] is False for r in rs)))
    write('source-review.json',dict(status='extracted_pending_independent_and_player_review',rows=len(rows),
        source_captures=len(captures),skipped_duplicate_MLB_capture_rows=skipped_mlb,groups=sorted(groups,key=lambda g:(g['season'],g['level'],g['position'])),
        years=sorted(counts['season'].unique()),counts_vs_usage_identities_and_exposure_replayed=True,
        historical_source_retrospectively_captured=True,team_exposure_not_certified=True,
        early_rookie_subtypes_not_certified=True,no_fit=True,no_2026_outcomes=True,
        player_walkthrough_status='pending',hashes=hashes([OUT/'source-preflight.json',OUT/'counts.parquet'])))
    protections()
    print(json.dumps(dict(minor_rows=len(rows),captures=len(captures),years=sorted(counts['season'].unique()),
        chances_failures=sum(g['chances_identity_failures'] for g in groups),throwing_subset_failures=sum(g['throwing_subset_failures'] for g in groups))),flush=True)


def support():
    protections()
    sr=read(OUT/'source-review.json');verify(sr['hashes']);verify(read(OUT/'source-preflight.json')['hashes'])
    assert not (OUT/'support-preflight.json').exists(), 'Preserve support audit'
    raw=pl.read_parquet(OUT/'counts.parquet').filter(pl.col('position_code').is_in([str(p) for p in range(2,10)]))
    official=pl.read_parquet(USAGE/'source.parquet').filter(pl.col('is_mlb'))
    usage=defaultdict(lambda:defaultdict(int));all_usage=defaultdict(lambda:defaultdict(int))
    for r in official.to_dicts():
        pos=int(r['position_code'])
        if 2<=pos<=9:
            usage[r['player_id'],pos][r['season']]+=r['fielding_outs']
            all_usage[r['player_id']][r['season']]+=r['fielding_outs']
    bios,ages,agepaths=identity()
    source_by=defaultdict(list)
    for r in raw.to_dicts():
        source_by[r['season'],r['player_id'],int(r['position_code'])].append(r)
    origins=[]
    for (y,pid,pos),rs in sorted(source_by.items()):
        n=sum(r['fielding_outs'] for r in rs)
        if n<25:
            continue
        bylevel=defaultdict(int)
        for r in rs:bylevel[r['normalized_level']]+=r['fielding_outs']
        level=sorted(bylevel,key=lambda k:(-bylevel[k],k))[0]
        dob=bios.get(pid);age=y-dob.year-((7,1)<(dob.month,dob.day)) if dob else ages.get((y,pid))
        if age is not None and (not math.isfinite(age) or not 15<=age<=55):age=None
        has_mlb=any(v>0 and s<=y for s,v in all_usage[pid].items())
        r=dict(origin_year=y,player_id=pid,player_name=rs[0]['player_name'],position=pos,
            level=level,level_exposure=dict(bylevel),minor_outs=n,age=age,
            age_basis='birthdate_july1' if dob else 'dated_panel' if age is not None else 'unknown',
            age_band=age_band(age),sample_band=sample_band(n),prior_current_MLB_fielding=has_mlb,
            early_rookie_qualification=any(not t['level_subtype_certified'] for t in rs),
            source_scope_rows=len(rs),missing_2020_not_zero=True)
        applicable=[f for f in COUNT_FIELDS if pos==2 or f not in CATCHER_FIELDS]
        for f in applicable:
            known=[t for t in rs if t[f] is not None]
            r[f]=sum(t[f] for t in known) if len(known)==len(rs) else None
            r[f+'_known_outs']=sum(t['fielding_outs'] for t in known)
        r['range_counts_complete']=all(r[f] is not None for f in ('putOuts','assists','errors','chances','throwingErrors','doublePlays'))
        r['steal_counts_complete']=pos==2 and r.get('caughtStealing') is not None and r.get('stolenBases') is not None
        r['blocking_counts_complete']=pos==2 and r.get('passedBall') is not None
        origins.append(r)
    f=pl.DataFrame(origins,infer_schema_length=None)
    f.write_parquet(OUT/'origins.parquet')
    paths=[OUT/'source-review.json',OUT/'counts.parquet',OUT/'origins.parquet',NATIVE/'component-ledger.parquet',
        NATIVE/'final-review.json',CATCHER/'extension-annual.parquet',CATCHER/'talent-final-review.json',
        ROOT/'docs/defense-traditional-to-savant-target-contract.md',ROOT/'docs/defense-traditional-to-savant-target-result.json',*agepaths,
        Path(__file__),ROOT/'src/universal_baseball/minor_fielding_counts.py',ROOT/'docs/defense-minor-counts-v18-contract.md']
    # The retained qualified tables must still match their independent source receipts.
    verify({str(NATIVE/'component-ledger.parquet'):read(NATIVE/'source-review.json')['hashes'][str(NATIVE/'component-ledger.parquet')]})
    er=read(CATCHER/'extension-review.json')
    verify({str(CATCHER/'extension-annual.parquet'):er['hashes'][str(CATCHER/'extension-annual.parquet')]})
    write('support-preflight.json',dict(before_target_support=True,no_fit=True,origin_position_rows=len(origins),
        source_only_origin_descriptors=True,hashes=hashes(paths),no_2026_outcomes=True))
    measured=defaultdict(dict)
    for r in pl.read_parquet(NATIVE/'component-ledger.parquet').to_dicts():
        if 3<=r['position']<=9:
            measured['range',r['player_id'],r['position']][r['season']]=dict(valid=r['range_valid'],
                opportunities=r['native_outs'],runs=r['range_runs'],season=r['season'])
    for r in pl.read_parquet(CATCHER/'extension-annual.parquet').to_dicts():
        measured[r['component'],r['player_id'],2][r['season']]=dict(valid=r['measurement_valid'],
            opportunities=r['opportunities'],runs=r['runs'],season=r['season'])
    labels=[]
    for r in origins:
        pid,pos,y=r['player_id'],r['position'],r['origin_year']
        components=('throwing','blocking') if pos==2 else ('range',)
        for c in components:
            for w in (3,5):
                q=pool_quality(y,w,c,pos,usage[pid,pos],measured[c,pid,pos])
                other=sum(v for s,v in all_usage[pid].items() if y<s<=min(y+w,2025))-q['future_official_position_outs']
                labels.append({**r,'component':c,'window':w,**q,'future_other_position_outs':other,
                    'source_counts_complete':r['range_counts_complete'] if c=='range' else r['steal_counts_complete'] if c=='throwing' else r['blocking_counts_complete']})
    lab=pl.DataFrame(labels,infer_schema_length=None);lab.write_parquet(OUT/'labels.parquet')
    cohorts=[];cells=[];supportrows=[]
    def profile(r):
        return (r['level'],r['position'],r['age_band'],r['sample_band'],r['prior_current_MLB_fielding'])
    grouped=defaultdict(list)
    for r in labels:grouped[r['component'],r['window']].append(r)
    for (c,w),pool in grouped.items():
        for y in sorted({r['origin_year'] for r in pool}):
            cohort=[r for r in pool if r['origin_year']==y]
            for level in sorted({r['level'] for r in cohort}):
                rs=[r for r in cohort if r['level']==level];q=[r for r in rs if r['quality_rate'] is not None]
                cohorts.append(dict(component=c,window=w,origin=y,level=level,rows=len(rs),people=len({r['player_id'] for r in rs}),
                    measured_rows=len(q),measured_people=len({r['player_id'] for r in q}),
                    unknown_age_rows=sum(r['age'] is None for r in rs),
                    source_complete_rows=sum(r['source_counts_complete'] for r in rs),
                    statuses={s:sum(r['quality_status']==s for r in rs) for s in sorted({r['quality_status'] for r in rs})}))
            if y+w>2025:
                continue
            for fold in range(5):
                tr=[r for r in pool if r['window_end']<=y and r['quality_rate'] is not None and r['player_id']%5!=fold]
                te=[r for r in cohort if r['player_id']%5==fold]
                assert {r['player_id'] for r in tr}.isdisjoint(r['player_id'] for r in te)
                tables=defaultdict(set);available=defaultdict(set);stage=defaultdict(set)
                for r in tr:
                    tables[profile(r)].add(r['player_id']);stage[r['level'],r['position']].add(r['player_id'])
                    if r['source_counts_complete']:available[profile(r)].add(r['player_id'])
                cells.append(dict(component=c,window=w,origin=y,fold=fold,training_people=len({r['player_id'] for r in tr}),
                    source_complete_training_people=len({r['player_id'] for r in tr if r['source_counts_complete']}),
                    training_origins=sorted({r['origin_year'] for r in tr}),training_rows=len(tr),test_rows=len(te),
                    train_keys=[[r['origin_year'],r['player_id'],r['position']] for r in tr],
                    test_keys=[[r['origin_year'],r['player_id'],r['position']] for r in te]))
                for r in te:
                    supportrows.append(dict(component=c,window=w,origin_year=y,player_id=r['player_id'],position=r['position'],fold=fold,
                        level=r['level'],joint_people=len(tables[profile(r)]),source_complete_joint_people=len(available[profile(r)]),
                        level_position_people=len(stage[r['level'],r['position']]),training_people=len({t['player_id'] for t in tr}),
                        quality_observed=r['quality_rate'] is not None))
    pl.DataFrame(supportrows,infer_schema_length=None).write_parquet(OUT/'profile-support.parquet')
    write('support-review.json',dict(status='pending_independent_and_player_review',origins=len(origins),label_rows=len(labels),
        cohorts=cohorts,cells=cells,no_fit=True,no_2026_outcomes=True,player_walkthrough_status='pending',
        hashes=hashes([OUT/'support-preflight.json',OUT/'origins.parquet',OUT/'labels.parquet',OUT/'profile-support.parquet'])))
    protections()
    compact=[dict(component=c,window=w,origin=y,measured_people=len({r['player_id'] for r in grouped[c,w] if r['origin_year']==y and r['quality_rate'] is not None}),
        training_people_range=[min(t['training_people'] for t in cells if (t['component'],t['window'],t['origin'])==(c,w,y)),
                              max(t['training_people'] for t in cells if (t['component'],t['window'],t['origin'])==(c,w,y))])
        for c,w,y in sorted({(t['component'],t['window'],t['origin']) for t in cells}) if y in (2017,2019,2021,2022)]
    print(json.dumps(dict(origins=len(origins),label_rows=len(labels),examples=compact)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['source','support']);args=p.parse_args();globals()[args.mode]()
