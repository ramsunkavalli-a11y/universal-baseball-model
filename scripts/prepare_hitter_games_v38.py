"""Recover dated game involvement, reconcile old counts, and review before fits."""
import gzip
import json
from pathlib import Path
import numpy as np
import polars as pl
import prepare_practical_hitter_v31 as r
from universal_baseball.storage import sha256_file

OUT=r.ROOT/'reports/generated/practical-hitter-v38'
SOURCE=r.ROOT/'reports/generated/hitter-2020-cohort/features.parquet'
KEYS=['season','player_id','sport_id','team_id']
FIXED=[(592450,2016),(592450,2024),(691026,2023),(668715,2022),(701762,2024),(666158,2023)]


def write(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False,default=str),encoding='utf8')


def role(pa,games):
    return (pa+40)/(games+10)


def features(base,counts):
    lookup={(v['season'],v['player_id'],v['bucket']):v for v in counts.iter_rows(named=True)}
    rows=[]
    for o in base.select('row_id','origin_year','player_id').iter_rows(named=True):
        y,pid=o['origin_year'],o['player_id'];v={'row_id':o['row_id']}
        pooled={b:[0.,0.,0.] for b in r.BUCKETS}
        for lag,w in enumerate([1.,.8,.6]):
            year=y-lag;mlb=[0.,0.];minor=[0.,0.]
            for b in r.BUCKETS:
                c=lookup.get((year,pid,b));pa=float(c['plate_appearances']) if c else 0.;g=float(c['games_played']) if c else 0.
                exposure=g*(162/60 if b=='MLB' and year==2020 else 1.)
                pooled[b][0]+=w*exposure;pooled[b][1]+=w*pa;pooled[b][2]+=w*g
                target=mlb if b=='MLB' else minor;target[0]+=pa;target[1]+=g
            v[f'games_mlb_{lag}']=mlb[1]*(162/60 if year==2020 else 1.)
            v[f'role_mlb_{lag}']=role(*mlb)
            v[f'games_minor_{lag}']=minor[1];v[f'role_minor_{lag}']=role(*minor)
        for b,(exposure,pa,g) in pooled.items():
            v['games_pool_'+b]=exposure;v['role_pool_'+b]=role(pa,g)
        rows.append(v)
    added=pl.DataFrame(rows);cols=[c for c in added.columns if c!='row_id']
    assert len(cols)==40 and np.isfinite(added.select(cols).to_numpy()).all()
    out=base.join(added,on='row_id',validate='1:1');assert out.select(base.columns).equals(base)
    return out,cols


def main():
    OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'source-audit.json').exists()
    manifest_path=r.ROOT/'model_artifacts/prospect-destination-v3-source-repaired/source_manifest.json'
    paths=sorted({Path(s['path']) for s in r.read(manifest_path)['sources'] if Path(s['path']).name.startswith('hitting-offset-') or
        ('advanced-rookie-repair-v3' in s['path'] and Path(s['path']).name=='hitting.json.gz')})
    rows=[];hashes={str(manifest_path):sha256_file(manifest_path)}
    for path in paths:
        hashes[str(path)]=sha256_file(path)
        with gzip.open(path,'rt',encoding='utf8') as stream:payload=json.load(stream)
        for stat in payload['stats']:
            for s in stat['splits']:
                st=s['stat'];g=st.get('gamesPlayed');pa=st.get('plateAppearances')
                assert g is None or isinstance(g,int) and g>=0
                rows.append(dict(season=int(s['season']),player_id=int(s['player']['id']),sport_id=int(s['sport']['id']),team_id=int(s['team']['id']),
                    source_pa=int(pa or 0),games_played=g,games_known=g is not None))
    raw=pl.DataFrame(rows).unique();assert raw.unique(KEYS).height==raw.height,'Conflicting PA/game captures'
    old=pl.read_parquet(r.OUT/'dated-stints.parquet');f=old.join(raw,on=KEYS,how='left',validate='1:1')
    assert f['source_pa'].null_count()==0 and f['source_pa'].equals(f['plate_appearances'])
    audit=f.group_by('season','bucket').agg(pl.len().alias('stints'),pl.col('plate_appearances').sum().alias('pa'),
        pl.col('games_known').sum().alias('known_games_stints'),pl.col('games_played').sum().alias('games'),
        ((pl.col('plate_appearances')>0)&(pl.col('games_played')==0)).sum().alias('pa_without_game')).sort('season','bucket')
    audit.write_parquet(OUT/'source-coverage.parquet');f.write_parquet(OUT/'game-stints.parquet')
    assert f['games_known'].all() and f['games_played'].null_count()==0,'Unknown games must not become zero'
    assert f.filter((pl.col('plate_appearances')>0)&(pl.col('games_played')==0)).is_empty()
    assert f.filter(pl.col('plate_appearances')>12*pl.col('games_played')).is_empty(),'Implausible PA/game source'
    counts=f.group_by('season','player_id','bucket').agg(pl.col('plate_appearances','games_played').sum()).sort('season','player_id','bucket')
    counts.write_parquet(OUT/'game-counts.parquet')
    base=pl.read_parquet(SOURCE);out,cols=features(base,counts);out.write_parquet(OUT/'features.parquet')
    cases=[]
    for pid,y in FIXED:
        o=out.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)).to_dicts();assert len(o)==1;o=o[0]
        peers=out.filter((pl.col('origin_year')==y)&(pl.col('player_id')!=pid)&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut']))
        distance=sum(((pl.col(c)-o[c])/scale)**2 for c,scale in [('age',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('draft_rank',.25),('draft_known',1)])
        peers=peers.with_columns(distance.alias('distance')).sort('distance','player_id').head(3)
        ids=[pid,*peers['player_id'].to_list()]
        cases.append(dict(player_id=pid,player_name=o['player_name'],origin_year=y,row_id=o['row_id'],
            origin_inputs={c:o[c] for c in ['age','stage','source_position','pa_0','AAA_0_pa','AA_0_pa','last_stat_gap',*cols]},
            source_history=counts.filter(pl.col('player_id').is_in(ids)&pl.col('season').is_between(y-2,y)).to_dicts(),
            peers=peers.select('player_id','player_name','age','stage','pa_0','AAA_0_pa','AA_0_pa','distance').to_dicts()))
    write('source-cases.json',cases)
    for p in [SOURCE,r.OUT/'dated-stints.parquet',Path(__file__),r.ROOT/'docs/practical-hitter-v38-contract.md',
              OUT/'game-stints.parquet',OUT/'game-counts.parquet',OUT/'features.parquet',OUT/'source-coverage.parquet',OUT/'source-cases.json']:
        hashes[str(p)]=sha256_file(p)
    write('source-audit.json',dict(input_hashes=hashes,source_captures=len(paths),stints=len(f),missing_games=0,
        new_features=cols,features_rows=len(out),all_old_features_bit_exact=True,protected_outcomes_used=False,
        counts_pa_reconciled=True,source_walkthrough_status='pending',coverage=audit.to_dicts()))
    print(json.dumps(dict(captures=len(paths),stints=len(f),source_seasons=sorted(f['season'].unique()),
        coverage_cells=len(audit),unknown_games=0,feature_rows=len(out),new_features=len(cols),fixed_cases=len(cases)),indent=2),flush=True)


if __name__=='__main__':main()
