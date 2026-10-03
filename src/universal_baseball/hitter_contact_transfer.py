"""Own-player, actual-league contact counts for a future-MLB test."""
import numpy as np
import polars as pl
from universal_baseball.batted_ball_direction import batted_ball_direction_expr
from universal_baseball.hitter_gradient_materialization import CONTACT_BINS

LEVELS={'aaa':'AAA','aa':'AA','a+':'Aplus','a':'A','a-':'Aminus'}


def bucket(level, league):
    if league==125:return 'MEX'
    if level=='MLB':return 'MLB'
    if league==130:return 'DSL'
    if level in LEVELS:return LEVELS[level]
    if level=='rk':return 'RK'+str(league) if league in {120,121,124,128,134} else 'RKother'
    raise ValueError((level,league))


def classify(f):
    d=batted_ball_direction_expr(pl.col('hc_x'),pl.col('hc_y'),pl.col('stand'))
    prefix=pl.when(d=='pull').then(pl.lit('PULL')).when(d=='center').then(pl.lit('CENTER')).when(d=='opposite').then(pl.lit('OPPO'))
    shape=pl.col('bb_type').replace_strict({'ground_ball':'GB','line_drive':'LD','fly_ball':'OFFB','popup':'IFFB'},default=None)
    return f.with_columns(pl.when(shape=='IFFB').then(pl.lit('IFFB')).otherwise(pl.concat_str(prefix,shape,separator='_')).alias('core_bin'))


def materialize(f, counts, official, buckets):
    keys=['season','player_id','bucket','core_bin']
    assert counts.unique(keys).height==len(counts) and (counts['contacts']>0).all()
    assert f['origin_year'].max()<=2024 and counts['season'].max()<=2024
    lut={}
    for s in counts.iter_rows(named=True):lut.setdefault((s['season'],s['player_id'],s['bucket']),{})[s['core_bin']]=s['contacts']
    ops={(s['season'],s['player_id'],s['bucket']):s['plate_appearances'] for s in official.iter_rows(named=True)}
    rows=[]
    for o in f.iter_rows(named=True):
        row={'row_id':o['row_id']}
        for b in buckets:
            hist=[(w,lut.get((o['origin_year']-lag,o['player_id'],b),{}),ops.get((o['origin_year']-lag,o['player_id'],b),0)) for lag,w in enumerate([1.,.8,.6])]
            by={c:sum(w*h.get(c,0) for w,h,_ in hist) for c in CONTACT_BINS};n=sum(by.values());den=sum(w*op for w,_,op in hist)
            for c in CONTACT_BINS:row[f'shape_{b}_{c}']=(by[c]+10)/(n+100)
            row[f'shape_{b}_log_n']=np.log1p(n)
            row[f'shape_{b}_coverage']=n/max(1,den)
            row[f'shape_{b}_available']=float(n>0)
            assert np.isclose(sum(row[f'shape_{b}_{c}'] for c in CONTACT_BINS),1)
        rows.append(row)
    q=pl.DataFrame(rows)
    return f.join(q,on='row_id',validate='1:1'),q.columns[1:]


def scaled(f, old_features, shape_features, old_matrix):
    x=f.select(shape_features).to_numpy().astype(float)
    for j,c in enumerate(shape_features):
        if c.endswith('_log_n'):x[:,j]/=6
        elif not c.endswith(('_coverage','_available')):x[:,j]/=.1
    return np.column_stack([old_matrix(f,old_features),x])
