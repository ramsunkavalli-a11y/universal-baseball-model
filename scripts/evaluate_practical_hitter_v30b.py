"""Single fixed linear-arm representation repair; preserve V30."""
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_practical_hitter_v30 as r
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file

OUT=r.ROOT/'reports/generated/practical-hitter-v30b'
FEATURES=[c for c in r.m.FEATURES if not c.startswith(('fraction_','league_rate_'))]
def write(n,x):(OUT/n).write_text(json.dumps(x,indent=2,allow_nan=False,default=str),encoding='utf8')
def main():
    old=r.read(r.OUT/'report.json');assert old['player_walkthrough_status']=='complete'
    r.check(old['input_hashes']);r.check(old['output_hashes'])
    OUT.mkdir(exist_ok=True);assert not (OUT/'preflight.json').exists()
    cells=[]
    for cell in r.read(r.OUT/'preflight.json')['cells']:
        y,k=cell['year'],cell['fold'];tr=pl.read_parquet(r.OUT/f'train-{y}-{k}.parquet');te=pl.read_parquet(r.OUT/f'test-{y}-{k}.parquet')
        audited=pl.read_parquet(r.OUT/'features.parquet').filter(pl.col('row_id').is_in(te['row_id'].implode()))
        _,note=preflight(tr,audited,cutoff=y,fold=k,features=FEATURES,expected_keys=te.select('row_id','horizon').iter_rows())
        cells.append(dict(year=y,fold=k,**note))
    hashes={**old['input_hashes'],str(r.OUT/'report.json'):sha256_file(r.OUT/'report.json'),
        str(Path(__file__)):sha256_file(Path(__file__)),str(r.ROOT/'docs/practical-hitter-v30b-contract.md'):sha256_file(r.ROOT/'docs/practical-hitter-v30b-contract.md')}
    write('preflight.json',dict(input_hashes=hashes,cells=cells,features=FEATURES,before_fitting=True))
    frames=[];fits=[]
    with threadpool_limits(limits=2):
        for c in cells:
            y,k=c['year'],c['fold'];tr=pl.read_parquet(r.OUT/f'train-{y}-{k}.parquet');te=pl.read_parquet(r.OUT/f'test-{y}-{k}.parquet')
            model=r.m.fit(r.m.learner('ridge'),'ridge',tr.select(FEATURES).to_numpy(),tr['next_pa'].to_numpy(),tr['origin_year'].to_numpy())
            raw=model.predict(te.select(FEATURES).to_numpy());pred=r.m.forecast(raw,te['hard_unavailable'])
            path=OUT/f'model-ridge-{y}-{k}.joblib';joblib.dump(model,path,compress=3)
            loaded=joblib.load(path);np.testing.assert_allclose(raw,loaded.predict(te.select(FEATURES).to_numpy()),atol=1e-10)
            fits.append(dict(year=y,fold=k,path=str(path),hash=sha256_file(path),low=int((raw<0).sum()),high=int((raw>800).sum())))
            frames.append(te.with_columns(pl.Series('ridge_b_raw_pa',raw),pl.Series('ridge_b_pa',pred),pl.Series('ridge_b_value',pred*te['v24_value'].to_numpy()/te['v24_pa'].to_numpy())))
    f=pl.concat(frames).sort('origin_year','player_id');f.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    scores=[]
    for scope in old['scores']:
        ids=pl.read_parquet(r.OUT/'predictions.parquet')
        name=scope['scope']
        if name=='all':g=f
        elif name=='public_active':g=f.filter((pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_pa').is_not_null())
        elif name.startswith('origin_'):g=f.filter(pl.col('origin_year')==int(name.split('_')[1]))
        elif name=='current_zero':g=f.filter(pl.col('pa_0')==0)
        elif name=='current_brief':g=f.filter(pl.col('pa_0').is_between(1,199))
        elif name=='current_partial':g=f.filter(pl.col('pa_0').is_between(200,399))
        elif name=='current_regular':g=f.filter(pl.col('pa_0')>=400)
        elif name=='debut_brief':g=f.filter((pl.col('elapsed')==0)&pl.col('pa_0').is_between(1,199))
        elif name=='current600':g=f.filter(pl.col('pa_0')>=600)
        else:g=f.filter((pl.col('pa_0')==0)&(pl.col('raw_MLB_1_pa')>=200))
        assert len(g)==scope['rows']
        scores.append(dict(scope=name,rows=len(g),scores={'ridge_b':r.m.score(g,'ridge_b'),**scope['scores']}))
    r.check(hashes);write('report.json',dict(input_hashes=hashes,scores=scores,player_walkthrough_status='pending',
        replayed_models=35,new_fits=35,frozen_forecast_changed=False,protected_2026_outcomes_used=False,
        output_hashes={str(OUT/n):sha256_file(OUT/n) for n in ['fits.json','predictions.parquet']}))
    print(json.dumps(scores[:2],indent=2))

if __name__=='__main__':main()
