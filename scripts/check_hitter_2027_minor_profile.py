"""Compatible benchmark for saved minor profile predictions, without fitting."""
from pathlib import Path
import gzip,json
import numpy as np
import polars as pl
from universal_baseball.defense_reference_history import annual_references,origin_reference
from universal_baseball.defense_first_base_prior import reference
from universal_baseball.minor_range_talent import design,ridge_predict
from universal_baseball.storage import sha256_file
from capture_hitter_2027_origin_counts import ROOT,write_once

PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'


def main():
    assert not (PUBLIC/'minor-profile-compatible-test.json').exists()
    pred=ROOT/'reports/generated/defense-minor-range-v19/predictions.parquet'
    native=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    fitpath=ROOT/'reports/model-evidence/defense-minor-range-v19/fit-report.json.gz'
    paths=[pred,native,fitpath,Path(__file__),ROOT/'docs/hitter-2027-minor-profile-compatibility.md']
    write_once(PUBLIC/'minor-profile-compatible-preflight.json',dict(no_fitting=True,preserve_prior_predictions=True,
        hashes={str(p):sha256_file(p) for p in paths}))
    rows=pl.read_parquet(pred).to_dicts();records=pl.read_parquet(native).to_dicts()
    refs=annual_references(records)
    fits=json.loads(gzip.decompress(fitpath.read_bytes()))['cells']
    cells={(c['cutoff'],c['outer_fold']):c for c in fits if c['kind']=='outer'}
    fb={(y,f):reference(records,y,f) for y in [2021,2022] for f in range(5)}
    for r in rows:
        y,p,f=r['origin_year'],r['position'],r['fold']
        assert f==r['player_id']%5
        r['reference']=fb[y,f]['rate'] if p==3 else origin_reference(y,p,f,refs)
        c=cells[y,f];fit=c['fits'][f"baseline-{r['baseline_alpha']}"]
        x=design([r],np.zeros((1,4)),c['age_median'],False)
        replay=float(ridge_predict(fit,x)[0]);assert np.isclose(replay,r['baseline'],atol=1e-10)
        r['compatibility_profile_supported']=bool(c['fit_supported']) and not bool(((x[0]<np.array(fit['training_min'])-1e-10)|(x[0]>np.array(fit['training_max'])+1e-10)).any())
    def score(rr):
        measured=[r for r in rr if r['quality_rate'] is not None]
        people={r['player_id'] for r in measured};counts={pid:sum(r['player_id']==pid for r in measured) for pid in people}
        result=dict(forecasts=len(rr),measured_positions=len(measured),measured_people=len(people))
        if not measured:return result
        weights=np.array([1/counts[r['player_id']] for r in measured])
        for name in ['neutral','reference','baseline']:
            e=np.array([r[name]-r['quality_rate'] for r in measured])
            result[name]=dict(RMSE=float(np.sqrt(np.average(e*e,weights=weights))),MAE=float(np.average(abs(e),weights=weights)))
        return result
    metrics=[]
    for y in [2021,2022]:
        yy=[r for r in rows if r['origin_year']==y]
        metrics.append(dict(origin=y,group='all',value='all',**score(yy)))
        for field in ['position','level']:
            for val in sorted({r[field] for r in yy}):metrics.append(dict(origin=y,group=field,value=val,**score([r for r in yy if r[field]==val])))
    selected={}
    def select(r,why):selected.setdefault((r['origin_year'],r['player_id'],r['position']),[]).append(why)
    for r in rows:
        if r['player_name'] in ['Jacob Young','Ceddanne Rafaela','Zach Neto','Anthony Volpe','Bobby Witt Jr.','Jeremy Peña']:select(r,'fixed_prior_case')
    measured=[r for r in rows if r['origin_year']==2022 and r['quality_rate'] is not None]
    gain=lambda r:(r['reference']-r['quality_rate'])**2-(r['baseline']-r['quality_rate'])**2
    select(max(measured,key=gain),'largest_gain');select(min(measured,key=gain),'largest_harm')
    select(max(measured,key=lambda r:r['baseline']-r['quality_rate']),'false_high')
    select(min(measured,key=lambda r:r['baseline']-r['quality_rate']),'false_low')
    select(sorted(measured,key=lambda r:abs(r['baseline']-r['quality_rate']))[len(measured)//2],'ordinary')
    walks=[]
    for key,reasons in selected.items():
        r=next(r for r in rows if (r['origin_year'],r['player_id'],r['position'])==key)
        pool=[s for s in rows if s['player_id']!=r['player_id'] and s['origin_year']==r['origin_year'] and s['position']==r['position'] and s['level']==r['level']]
        peers=sorted(pool,key=lambda s:(abs((s['age'] or 23)-(r['age'] or 23)),abs(s['minor_outs']-r['minor_outs']),s['player_id']))[:3]
        def detail(s):
            c=cells[s['origin_year'],s['fold']];fit=c['fits'][f"baseline-{s['baseline_alpha']}"]
            x=design([s],np.zeros((1,4)),c['age_median'],False)[0]
            terms=(x-np.array(fit['mean']))/np.array(fit['scale'])*np.array(fit['coefficients'])
            return dict(row=s,coefficient_contributions=dict(zip(fit['names'],terms.tolist())),intercept=fit['target_mean'],
                reference=fb[s['origin_year'],s['fold']] if s['position']==3 else
                    [dict(season=y,**refs[y,s['position'],s['fold']]) for y in range(s['origin_year']-2,s['origin_year']+1) if (y,s['position'],s['fold']) in refs],
                future_native=[n for n in records if n['player_id']==s['player_id'] and n['position']==s['position'] and s['origin_year']<n['season']<=s['origin_year']+3])
        walks.append(dict(reasons=reasons,primary=detail(r),peers=[detail(s) for s in peers]))
    path=PUBLIC/'minor-profile-compatible-player-walks.json.gz';assert not path.exists();path.write_bytes(gzip.compress(json.dumps(walks,allow_nan=False,default=str).encode(),mtime=0))
    write_once(PUBLIC/'minor-profile-compatible-test.json',dict(metrics=metrics,cases=len(walks),all_saved_baseline_predictions_replayed=True,
        interpretation='pending_written_review',release_approved=False,walk_sha256=sha256_file(path)))
    print(json.dumps([m for m in metrics if m['group']=='all']),flush=True)
    for w in walks:
        r=w['primary']['row'];print(r['player_name'],r['origin_year'],r['position'],w['reasons'],[r[k] for k in ['reference','baseline','quality_rate']],flush=True)


if __name__=='__main__':main()
