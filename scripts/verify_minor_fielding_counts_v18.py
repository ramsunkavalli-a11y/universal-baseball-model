"""Independent raw-count, origin, future-label and held-person support replay."""
from collections import defaultdict
from datetime import date
from pathlib import Path
import gzip
import json
import math

import polars as pl

from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/generated/defense-minor-counts-v18'
PUBLIC = ROOT/'reports/model-evidence/defense-minor-counts-v18'
FIELDS = ('putOuts','assists','errors','chances','throwingErrors','doublePlays',
          'caughtStealing','stolenBases','passedBall','wildPitches','catchersInterference','pickoffs')
KEY = ('source_id','season','usage_scope','player_id','position_code')


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def check_hashes(values):
    for name, h in values.items():
        assert sha256_file(Path(name)) == h, name


def close(a, b):
    assert (a is None and b is None) or (a is not None and b is not None and math.isclose(a,b,abs_tol=1e-10)), (a,b)


def profile(r):
    return (r['level'],r['position'],r['age_band'],r['sample_band'],r['prior_current_MLB_fielding'])


def main():
    protections()
    assert not (OUT/'independent-review.json').exists()
    for name in ('source-preflight','source-review','support-preflight','support-review'):
        check_hashes(read(OUT/f'{name}.json')['hashes'])
    counts = pl.read_parquet(OUT/'counts.parquet').to_dicts()
    originals = pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet').to_dicts()
    accepted = {tuple(r[k] for k in KEY):r for r in originals if not r['is_mlb'] and r['season']<=2024}
    bypath = defaultdict(list)
    for r in counts:bypath[r['capture_path']].append(r)
    checked = 0
    for name, rows in bypath.items():
        p = Path(name)
        if p.suffix == '.gz':
            with gzip.open(p,'rt',encoding='utf8') as f:data = json.load(f)
        else:data = read(p)
        splits = data['splits'] if 'splits' in data else data['stats'][0]['splits']
        for r in rows:
            s = splits[r['capture_split_index']];stat = s['stat']
            assert (int(s['season']),int(s['player']['id']),str(s['position']['code'])) == (r['season'],r['player_id'],r['position_code'])
            whole, _, frac = str(stat['innings']).partition('.')
            assert frac in ('','0','1','2')
            assert 3*int(whole)+int(frac or 0) == r['fielding_outs']
            assert int(stat['gamesPlayed']) == r['games_played'] and int(stat['gamesStarted']) == r['games_started']
            old = accepted[tuple(r[k] for k in KEY)]
            assert all(r[k] == old[k] for k in old)
            for f in FIELDS:
                raw = stat.get(f)
                if raw is None or str(raw).strip()=='':x,status = None,'missing'
                else:
                    try:
                        v = float(raw)
                        good = math.isfinite(v) and v>=0 and int(v)==v
                        x,status = (int(v),'recorded') if good else (None,'invalid')
                    except (ValueError,TypeError):x,status = None,'invalid'
                assert r[f] == x and r[f+'_status'] == status
            assert r['chances_identity'] == (None if any(r[f] is None for f in FIELDS[:4]) else r['chances']==r['putOuts']+r['assists']+r['errors'])
            assert r['throwing_subset_identity'] == (None if r['throwingErrors'] is None or r['errors'] is None else r['throwingErrors']<=r['errors'])
            checked+=1
    assert checked==len(accepted)==len(counts)
    print(f'Raw source replay: {checked} rows',flush=True)
    usage = defaultdict(lambda:defaultdict(int));total = defaultdict(lambda:defaultdict(int))
    for r in originals:
        pos=int(r['position_code'])
        if r['is_mlb'] and 2<=pos<=9:
            usage[r['player_id'],pos][r['season']]+=r['fielding_outs']
            total[r['player_id']][r['season']]+=r['fielding_outs']
    bios = {}
    for name in ('defensive-talent-position-v2/identity.parquet','hitter-2020-cohort/birthdates.parquet'):
        for r in pl.read_parquet(ROOT/'reports/generated'/name,columns=['player_id','birth_date']).to_dicts():
            if r['birth_date']:
                dob=date.fromisoformat(str(r['birth_date']))
                assert r['player_id'] not in bios or bios[r['player_id']]==dob
                bios[r['player_id']]=dob
    ages = {(r['origin_year'],r['player_id']):r['age'] for r in pl.read_parquet(ROOT/'reports/generated/multiyear-hitter-components-v1/component-panel.parquet',columns=['origin_year','player_id','age']).to_dicts()}
    originraw = defaultdict(list)
    for r in counts:
        if 2<=int(r['position_code'])<=9:originraw[r['season'],r['player_id'],int(r['position_code'])].append(r)
    expectedkeys = {k for k,rs in originraw.items() if sum(r['fielding_outs'] for r in rs)>=25}
    origins = pl.read_parquet(OUT/'origins.parquet').to_dicts()
    actualkeys = {(r['origin_year'],r['player_id'],r['position']) for r in origins}
    assert len(actualkeys)==len(origins) and actualkeys==expectedkeys
    for r in origins:
        y,pid,pos=r['origin_year'],r['player_id'],r['position'];rs=originraw[y,pid,pos]
        n=sum(t['fielding_outs'] for t in rs);levels=defaultdict(int)
        for t in rs:levels[t['normalized_level']]+=t['fielding_outs']
        assert r['minor_outs']==n and r['level']==min(levels,key=lambda k:(-levels[k],k))
        assert {k:v for k,v in r['level_exposure'].items() if v is not None}==dict(levels)
        dob=bios.get(pid)
        age=y-dob.year-int((dob.month,dob.day)>(7,1)) if dob else ages.get((y,pid))
        if age is not None and (not math.isfinite(age) or not 15<=age<=55):age=None
        close(r['age'],age)
        assert r['age_basis']==('birthdate_july1' if dob else 'dated_panel' if age is not None else 'unknown')
        assert r['age_band']==('unknown' if age is None else '<=19' if age<=19 else '20-22' if age<=22 else '23-25' if age<=25 else '26+')
        assert r['sample_band']==('25-299' if n<300 else '300-1499' if n<1500 else '1500+')
        assert r['prior_current_MLB_fielding']==any(s<=y and v>0 for s,v in total[pid].items())
        for f in FIELDS if pos==2 else FIELDS[:6]:
            vals=[t[f] for t in rs]
            assert r[f]==(sum(vals) if None not in vals else None)
            assert r[f+'_known_outs']==sum(t['fielding_outs'] for t in rs if t[f] is not None)
        assert r['source_scope_rows']==len(rs) and r['early_rookie_qualification']==any(not t['level_subtype_certified'] for t in rs)
        assert r['range_counts_complete']==all(r[f] is not None for f in FIELDS[:6])
        assert r['steal_counts_complete']==(pos==2 and r['caughtStealing'] is not None and r['stolenBases'] is not None)
        assert r['blocking_counts_complete']==(pos==2 and r['passedBall'] is not None)
    print(f'Origin replay: {len(origins)} rows',flush=True)
    native = {}
    for r in pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').to_dicts():
        if 3<=r['position']<=9:native['range',r['season'],r['player_id'],r['position']] = (r['range_valid'],r['native_outs'],r['range_runs'])
    for r in pl.read_parquet(ROOT/'reports/generated/catcher-throw-block-v5/extension-annual.parquet').to_dicts():
        native[r['component'],r['season'],r['player_id'],2] = (r['measurement_valid'],r['opportunities'],r['runs'])
    labels=pl.read_parquet(OUT/'labels.parquet').to_dicts();groups=defaultdict(list)
    originmap={(r['origin_year'],r['player_id'],r['position']):r for r in origins}
    for r in labels:
        y,pid,pos,c,w=r['origin_year'],r['player_id'],r['position'],r['component'],r['window']
        base=originmap[y,pid,pos];assert all(r[k]==v for k,v in base.items())
        years=range(y+1,min(y+w,2025)+1);runs=0.;opp=seasons=missing=official=other=0
        for s in years:
            official+=usage[pid,pos].get(s,0);other+=total[pid].get(s,0)-usage[pid,pos].get(s,0)
            m=native.get((c,s,pid,pos))
            if m is not None and m[0]:
                assert m[1]>0 and math.isfinite(m[2]);opp+=m[1];runs+=m[2];seasons+=1
            else:missing+=usage[pid,pos].get(s,0)
        unit,minimum={'range':(1500,1500),'throwing':(100,100),'blocking':(1000,3000)}[c]
        mature=y+w<=2025;valid=mature and seasons>=2 and opp>=minimum and missing==0
        status='measured' if valid else 'window_incomplete' if not mature else 'missing_measurement' if missing else 'no_same_position_exposure' if official==0 else 'insufficient_measurement'
        for k,v in dict(window_end=y+w,window_mature=mature,future_opportunities=opp,future_measured_seasons=seasons,future_official_position_outs=official,unmeasured_official_outs=missing,quality_status=status,unit=unit,window_has_2020=2020 in years,future_other_position_outs=other).items():assert r[k]==v,(k,r[k],v)
        close(r['future_runs'],runs);close(r['quality_rate'],unit*runs/opp if valid else None)
        assert r['source_counts_complete']==base[{'range':'range_counts_complete','throwing':'steal_counts_complete','blocking':'blocking_counts_complete'}[c]]
        groups[c,w].append(r)
    assert len(labels)==sum((4 if r['position']==2 else 2) for r in origins)
    print(f'Future quality replay: {len(labels)} rows',flush=True)
    supports = {(r['component'],r['window'],r['origin_year'],r['player_id'],r['position']):r for r in pl.read_parquet(OUT/'profile-support.parquet').to_dicts()}
    summary=[];used=set()
    cells=read(OUT/'support-review.json')['cells']
    for cell in cells:
        c,w,y,fold=cell['component'],cell['window'],cell['origin'],cell['fold'];pool=groups[c,w]
        tr=[r for r in pool if r['window_end']<=y and r['quality_status']=='measured' and r['player_id']%5!=fold]
        te=[r for r in pool if r['origin_year']==y and r['player_id']%5==fold]
        keys=lambda rows:{(r['origin_year'],r['player_id'],r['position']) for r in rows}
        assert set(map(tuple,cell['train_keys']))==keys(tr) and set(map(tuple,cell['test_keys']))==keys(te)
        assert cell['training_people']==len({r['player_id'] for r in tr}) and cell['training_rows']==len(tr) and cell['test_rows']==len(te)
        assert cell['training_origins']==sorted({r['origin_year'] for r in tr})
        assert cell['source_complete_training_people']==len({r['player_id'] for r in tr if r['source_counts_complete']})
        joint=defaultdict(set);complete=defaultdict(set);lp=defaultdict(set)
        for r in tr:
            joint[profile(r)].add(r['player_id']);lp[r['level'],r['position']].add(r['player_id'])
            if r['source_counts_complete']:complete[profile(r)].add(r['player_id'])
        for r in te:
            k=(c,w,y,r['player_id'],r['position']);s=supports[k];used.add(k)
            assert s['fold']==fold and s['joint_people']==len(joint[profile(r)]) and s['source_complete_joint_people']==len(complete[profile(r)])
            assert s['level_position_people']==len(lp[r['level'],r['position']]) and s['training_people']==cell['training_people']
            assert s['quality_observed']==(r['quality_rate'] is not None)
        if y in (2017,2019,2021,2022):
            for prior in (False,True):
                ts=[r for r in tr if r['prior_current_MLB_fielding']==prior]
                vs=[r for r in te if r['prior_current_MLB_fielding']==prior]
                for level in sorted({r['level'] for r in vs}):
                    ev=[r for r in vs if r['level']==level];train=[r for r in ts if r['level']==level]
                    summary.append(dict(component=c,window=w,origin=y,fold=fold,prior_MLB=prior,level=level,
                        test_rows=len(ev),measured_people=len({r['player_id'] for r in ev if r['quality_rate'] is not None}),
                        stage_training_people=len({r['player_id'] for r in train}),all_training_people=len({r['player_id'] for r in ts}),
                        zero_joint_rows=sum(len(joint[profile(r)])==0 for r in ev),sparse_joint_rows=sum(len(joint[profile(r)])<20 for r in ev)))
    assert used==set(supports)
    print(f'Chronological support replay: {len(used)} rows, {len(cells)} cells',flush=True)
    receipt=dict(status='independently_replayed_pending_player_review',raw_rows=checked,origin_rows=len(origins),label_rows=len(labels),support_rows=len(used),fold_cells=len(cells),
        summary=summary,no_fit=True,no_2026_outcomes=True,origins_reconstructed_without_future_measurements=True,
        independent_of_count_and_pool_helpers=True,player_walkthrough_status='pending',
        hashes={str(p):sha256_file(p) for p in (Path(__file__),OUT/'source-preflight.json',OUT/'support-preflight.json',OUT/'counts.parquet',OUT/'origins.parquet',OUT/'labels.parquet',OUT/'profile-support.parquet')})
    for folder in (OUT,PUBLIC):save(folder/'independent-review.json',receipt)
    protections()


if __name__=='__main__':main()
