"""Origin-only pooled evidence and saved draft pedigree; preflight before fits."""
from pathlib import Path
import numpy as np
import polars as pl
import prepare_practical_hitter_v31 as r
from universal_baseball.forecast_validation import preflight
from universal_baseball.practical_hitter_v30 import EVENTS
from universal_baseball.storage import sha256_file

OUT=r.ROOT/'reports/generated/practical-hitter-v33'
DRAFT=r.OLD/'draft-history/draft-history.parquet'
PED=['draft_known','draft_rank','draft_elapsed','draft_hs','draft_jc','draft_college',
    'draft_class_unknown','draft_rank_low_exposure']

def write(name,obj):
    import json
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False,default=str),encoding='utf8')

def materialize(f,counts,draft):
    assert draft['draft_year'].max()<=2024
    d=draft.filter(pl.col('drafted')&(pl.col('pick_number')>0)).select('player_id','draft_year','pick_number','school_class').unique()
    assert d.unique(['player_id','draft_year']).height==d.height,'Conflicting dated picks'
    picks={}
    for s in d.sort('draft_year').iter_rows(named=True):picks.setdefault(s['player_id'],[]).append(s)
    lut={(s['player_id'],s['season'],s['bucket']):s for s in counts.filter(pl.col('season')<=2024).iter_rows(named=True)}
    assert len(lut)==len(counts.filter(pl.col('season')<=2024))
    rows=[]
    for o in f.iter_rows(named=True):
        year,pid=o['origin_year'],o['player_id'];row={'row_id':o['row_id']}
        for bucket in r.BUCKETS:
            h=[(w,lut.get((pid,year-lag,bucket))) for lag,w in enumerate([1.,.8,.6])]
            pa=sum(w*s['plate_appearances'] for w,s in h if s)
            row[f'pooled_{bucket}_pa']=pa
            for ev,(num,den,prior) in EVENTS.items():
                n=sum(w*s[num] for w,s in h if s);d0=sum(w*s[den] for w,s in h if s)
                row[f'pooled_{bucket}_{ev}']=(n+100*prior)/(d0+100)
        pa=sum(w*o[f'pa_{lag}'] for lag,w in enumerate([1.,.8,.6]))
        row['pooled_mlb_quality']=sum(w*o[f'quality_{lag}']*(o[f'pa_{lag}']+1200) for lag,w in enumerate([1.,.8,.6]))/(pa+1200)
        eligible=[s for s in picks.get(pid,[]) if s['draft_year']<=year];pick=eligible[-1] if eligible else None
        rank=1-np.log(pick['pick_number'])/np.log(2000) if pick else 0
        school=(pick['school_class'] or '').strip().upper() if pick else ''
        row.update(draft_year=pick['draft_year'] if pick else None,pick_number=pick['pick_number'] if pick else None,
            draft_school_class=school,draft_known=int(pick is not None),draft_rank=float(np.clip(rank,0,1)),
            draft_elapsed=(year-pick['draft_year'])/10 if pick else 0,
            draft_hs=int(school.startswith('HS')),draft_jc=int(school.startswith('JC')),
            draft_college=int(school.startswith('4YR') or school in ['FR','SO','JR','SR']),
            draft_class_unknown=int(not school),draft_rank_low_exposure=float(np.clip(rank,0,1))*100/(100+sum(o[f'{b}_{lag}_pa'] for b in r.BUCKETS for lag in range(3))))
        rows.append(row)
    return f.join(pl.DataFrame(rows,schema_overrides={'draft_year':pl.Int64,'pick_number':pl.Int64}),on='row_id',validate='1:1')

def safe_matrix(f,features):
    x=f.select(features).to_numpy().astype(float)
    for i,c in enumerate(features):
        if c=='career_mlb_observed_pa':x[:,i]/=6000
        elif c.endswith('_pa'):x[:,i]/=600
        elif c=='last_stat_gap':x[:,i]/=5
        elif c.startswith('pooled_') and c.rsplit('_',1)[-1] in EVENTS:
            x[:,i]=(x[:,i]-EVENTS[c.rsplit('_',1)[-1]][2])/.1
    return x

def main():
    assert r.read(r.ROOT/'reports/generated/practical-hitter-v32/report.json')['player_walkthrough_status']=='complete'
    OUT.mkdir(parents=True,exist_ok=True);pre=r.read(r.OUT/'preflight-ready.json')
    draft=pl.scan_parquet(DRAFT).filter(pl.col('draft_year')<=2024).collect()
    draft.write_parquet(OUT/'draft-evidence.parquet')
    f=materialize(pl.read_parquet(pre['ready_features']),pl.read_parquet(r.OUT/'counts.parquet'),draft)
    pooled=[f'pooled_{b}_{e}' for b in r.BUCKETS for e in ['pa',*EVENTS]]+['pooled_mlb_quality']
    arms={'pooled':pre['base_features']+pooled,'pedigree':pre['base_features']+pooled+PED}
    assert all(not c.startswith('next_') for cols in arms.values() for c in cols)
    assert np.isfinite(safe_matrix(f,arms['pedigree'])).all()
    f.write_parquet(OUT/'features.parquet');cells=[];supports=[]
    for cell in pre['cells']:
        tr=f.filter(pl.col('row_id').is_in(cell['training_row_ids']));te=f.filter(pl.col('row_id').is_in(cell['test_row_ids']))
        sup,note=preflight(tr,te,cutoff=cell['year'],fold=cell['fold'],features=arms['pedigree'],expected_keys=te.select('row_id','horizon').iter_rows())
        assert tr['target_year'].max()<=cell['year']
        for head,sub in [('all',tr),('active',tr.filter(pl.col('next_pa')>0))]:
            keys=['stage','prior_debut','age_group','draft_known','thin_entry']
            def profile(g):return g.with_columns((pl.col('age')//5).alias('age_group'),
                (pl.sum_horizontal([pl.col(f'{b}_{lag}_pa') for b in r.BUCKETS for lag in range(3)])<100).alias('thin_entry'))
            a=profile(sub);b=profile(te);cnt=a.group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_players'))
            supports.append(b.select('row_id',*keys).join(cnt,on=keys,how='left',validate='m:1').with_columns(pl.col('profile_players').fill_null(0),
                pl.lit(head).alias('head'),pl.lit(cell['year']).alias('origin_year'),pl.lit(cell['fold']).alias('fold')))
        cells.append(dict(**cell,v33_preflight=note))
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    hashes={str(p):sha256_file(p) for p in [OUT/'features.parquet',OUT/'draft-evidence.parquet',OUT/'support.parquet',
        r.OUT/'preflight-ready.json',r.OUT/'counts.parquet',r.ROOT/'docs/practical-hitter-v33-contract.md',Path(__file__)]}
    audit=dict(before_fitting=True,input_hashes=hashes,cells=cells,features=arms,source_rows=len(f),
        draft_coverage=f.group_by('origin_year').agg(pl.len().alias('rows'),pl.col('draft_known').sum().alias('draft_matches')).sort('origin_year').to_dicts(),
        draft_source=str(DRAFT),draft_source_sha256=sha256_file(DRAFT),draft_maximum_join_year=2024,
        signing_amounts_not_used=True,protected_outcomes_used=False)
    write('preflight.json',audit);print('Ready:',len(f),'source rows;',len(cells),'cells;', {k:len(v) for k,v in arms.items()})
    print(f.filter(pl.col('player_id')==701762).select('origin_year','player_id','draft_known','pick_number','draft_school_class','draft_rank_low_exposure'))

if __name__=='__main__':main()
