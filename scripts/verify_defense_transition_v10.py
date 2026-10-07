"""Independent transition evidence, distributions, predictions and score replay."""

from collections import defaultdict
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections,save

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-transition-v10'
PUBLIC=ROOT/'reports/model-evidence/defense-transition-v10'
OLD=ROOT/'reports/generated/defense-repertoire-v9'


def read(p):return json.loads(p.read_text(encoding='utf8'))


def norm(v):
    a=np.asarray(v,float);return a/a.sum() if a.sum() else a


def main():
    protections();assert not (OUT/'independent-verification.json').exists()
    pre=read(OUT/'preflight.json');report=read(OUT/'fit-report.json')
    amendment=read(OUT/'execution-amendment.json') if (OUT/'execution-amendment.json').exists() else None
    recovery=read(OUT/'execution-recovery.json') if (OUT/'execution-recovery.json').exists() else None
    if recovery:
        assert recovery['previous_sha256']==amendment['corrected_sha256']
        assert sha256_file(Path(recovery['previous_snapshot']))==recovery['previous_sha256']
        for p,h in recovery['model_hashes'].items():assert sha256_file(Path(p))==h,p
    for p,h in {**pre['hashes'],**report['hashes']}.items():
        if amendment and p==amendment['modified_path']:
            assert h==amendment['original_sha256'] and sha256_file(Path(amendment['original_snapshot']))==h
            assert sha256_file(Path(p))==(recovery['corrected_sha256'] if recovery else amendment['corrected_sha256'])
        else:assert sha256_file(Path(p))==h,p
    assert sha256_file(OUT/'features.parquet')==pre['features_sha256']
    assert sha256_file(OUT/'profile-support.parquet')==pre['profile_sha256']
    f=pl.read_parquet(OUT/'features.parquet');q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    old=pl.read_parquet(OLD/'predictions.parquet').sort('row_id')
    assert q['row_id'].equals(old['row_id']) and q.height==12432
    for n in old.columns:assert q[n].equals(old[n]),n
    annual=defaultdict(list)
    for r in pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/annual-usage.parquet').to_dicts():annual[r['player_id']].append(r)
    panel=pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v68/predictions.parquet',
        columns=['row_id','player_id','origin_year','pa_0','pa_1','pa_2','prior_debut'])
    cache={r['row_id']:r for r in panel.to_dicts()}
    for r in f.to_dicts():
        original=cache[r['row_id']]
        for n in ('player_id','origin_year','pa_0','pa_1','pa_2','prior_debut'):assert r[n]==original[n]
        y=r['origin_year'];past=[h for h in annual[r['player_id']] if y-2<=h['season']<=y]
        older=[h for h in past if h['is_mlb'] and h['season']<y and h['defensive_outs']>0]
        own=r['repertoire_shares'];role=r['repertoire_primary_role'];returning=r['pa_0']==0 and bool(older);season=None
        if returning:
            season=max(h['season'] for h in older);oldseason=[h for h in past if h['is_mlb'] and h['season']==season]
            outs=[sum(h[f'outs_{p}'] for h in oldseason) for p in range(2,10)]
            starts=[sum(h[f'starts_{p}'] for h in oldseason) for p in range(2,11)]
            own=norm(outs);role=int(np.argmax(starts if sum(starts) else outs))+2
        pa=r['pa_0']+.5*r['pa_1']+.25*r['pa_2'];can_C=any(h['outs_2']>0 or h['starts_2']>0 for h in past) or str(r['source_position'])=='2'
        assert np.allclose(own,r['transition_shares'],atol=1e-14,rtol=0)
        assert role==r['transition_primary_role'] and returning==r['transition_returning_history'] and season==r['transition_return_season']
        assert can_C==r['transition_catching_evidence'] and pa==r['transition_evidence_PA'] and pa/(pa+100)==r['transition_weight']
        assert r['transition_status']==('prior_MLB' if r['prior_debut'] else 'no_prior_MLB')
        assert r['transition_unknown']==(sum(own)==0)
    distributions=forecasts=0;folds=[]
    for note in report['models']:
        path=Path(note['path']);assert sha256_file(path)==note['sha256'];m=read(path);y,k=m['origin'],m['fold']
        tr=f.filter((pl.col('target_year')<=y)&(pl.col('outer_fold')!=k)&(pl.col('next_pa')>0)&
            (sum(pl.col(f'actual_{p}') for p in range(2,10))>0))
        te=q.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k))
        assert sorted(tr['row_id'])==sorted(m['training_row_ids']) and sorted(te['row_id'])==sorted(m['test_row_ids'])
        assert not set(tr['player_id'])&set(te['player_id'])
        tables={tuple(c['key']):c for c in m['tables']}
        for key,c in tables.items():
            g=tr.filter(pl.col('transition_primary_role')==int(key[1]))
            if key[0]=='role_status':g=g.filter(pl.col('transition_status')==key[2])
            num=[int(g[f'actual_{p}'].sum()) for p in range(2,10)];den=sum(num)
            masses=g.group_by('player_id').agg(sum(pl.col(f'actual_{p}') for p in range(2,10)).sum().alias('mass'))
            eff=den**2/float((masses['mass'].cast(pl.Float64)**2).sum()) if den else 0.
            assert c['rows']==g.height and c['people']==masses.height and c['denominator_outs']==den and c['position_outs']==num
            assert np.isclose(c['effective_people'],eff,atol=1e-10,rtol=1e-12)
            assert c['shares']==([n/den for n in num] if den else None);distributions+=1
        conv=read(OLD/f'model-{y}-{k}.json')['native_conversions'];assert conv==m['native_conversions']
        for r in te.to_dicts():
            options=[('role_status',str(r['transition_primary_role']),r['transition_status']),('role',str(r['transition_primary_role']))]
            c=next((tables[key] for key in options if tables[key]['people']>=20 and tables[key]['effective_people']>=10 and tables[key]['denominator_outs']>0),None)
            own=np.array(r['transition_shares']);learn=np.array(c['shares']) if c else own.copy()
            if not r['transition_catching_evidence']:learn[0]=0
            learn=norm(learn)
            a=r['transition_evidence_PA']/(r['transition_evidence_PA']+100)
            shares=np.zeros(8) if r['transition_unknown'] else own if learn.sum()==0 else norm(a*own+(1-a)*learn)
            values=shares*r['repair_potential_outs']
            assert np.allclose(values,[r[f'transition_{p}'] for p in range(2,10)],atol=1e-9,rtol=1e-12)
            assert np.allclose(shares,r['transition_prediction_shares'],atol=1e-14,rtol=0)
            assert (json.loads(r['transition_prior_key']) if r['transition_prior_key'] else None)==(c['key'] if c else None)
            assert r['transition_unsupported']==(c is None)
            assert r['transition_10']==r['repair_10']
            assert np.isclose(sum(values)+r['transition_unallocated_outs'],r['repair_potential_outs'],atol=1e-9,rtol=0)
            if r['transition_unknown']==r['repertoire_unknown']:
                assert np.isclose(sum(values),r['repair_total_outs'],atol=1e-9,rtol=0)
            if not r['transition_catching_evidence']:assert values[0]==0
            for ch,cell in conv.items():
                exposure=values[0] if ch in ('framing','throwing','blocking') else sum(values[5:8]) if ch=='arm' else values[1]
                assert np.isclose(exposure*cell['rate'],r[f'transition_native_{ch}'],atol=1e-9,rtol=1e-12)
            forecasts+=1
        folds.append(dict(origin=y,fold=k,training_people=tr['player_id'].n_unique(),test_rows=te.height,
            unsupported_rows=int(te['transition_unsupported'].sum()),return_history_rows=int(te['transition_returning_history'].sum())))
    for s in report['overall']:
        year=q.filter(pl.col('origin_year')==s['origin']);a=year.select([f"{s['arm']}_{p}" for p in range(2,10)]).to_numpy()
        actual=year.select([f'actual_{p}' for p in range(2,10)]).to_numpy()
        assert np.isclose(np.sqrt(np.mean((a-actual)**2)),s['cell_rmse'],atol=1e-9,rtol=0)
    for s in report['placement']:
        g=q.filter((pl.col('origin_year')==s['origin'])&(sum(pl.col(f'actual_{p}') for p in range(2,10))>0))
        if s['subset']=='zero_current_MLB_PA':g=g.filter(pl.col('pa_0')==0)
        if s['subset']=='age_15_19':g=g.filter(pl.col('age_band')=='3')
        if g.is_empty():assert s['score'] is None;continue
        actual=g.select([f'actual_{p}' for p in range(2,10)]).to_numpy();actual=actual/actual.sum(axis=1)[:,None]
        if s['arm']=='transition':a=np.array(g['transition_prediction_shares'].to_list())
        else:
            a=g.select([f"{s['arm']}_{p}" for p in range(2,10)]).to_numpy();den=a.sum(axis=1)
            a=np.divide(a,den[:,None],out=np.zeros_like(a),where=den[:,None]>0)
        assert g.height==s['score']['rows'] and np.isclose(np.mean((a-actual)**2),s['score']['mean_cell_squared_share_error'],atol=1e-14,rtol=0)
    result=dict(integrity_pass=True,source_evidence_replayed=f.height,transition_distributions_replayed=distributions,forecasts_replayed=forecasts,
        anchors_identical=True,scalar_totals_and_DH_unchanged=True,no_unqualified_catcher_allocations=True,folds=folds,
        normalized_placement_scores_independently_replayed=True,full_MLB_and_matched_totals=read(OLD/'independent-verification.json')['matched_and_full_MLB'],
        protected_outcomes_used=False,forecast_or_explorer_changed=False,player_walkthrough_status='baseball_judgment_pending',
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'preflight.json',OUT/'fit-report.json',OUT/'predictions.parquet',OUT/'player-walkthrough.json']})
    if amendment:result['hashes'][str(OUT/'execution-amendment.json')]=sha256_file(OUT/'execution-amendment.json')
    if recovery:result['hashes'][str(OUT/'execution-recovery.json')]=sha256_file(OUT/'execution-recovery.json')
    save(OUT/'independent-verification.json',result);save(PUBLIC/'independent-verification.json',result)
    protections();print(json.dumps({k:result[k] for k in ['integrity_pass','source_evidence_replayed','transition_distributions_replayed','forecasts_replayed']}))


if __name__=='__main__':main()
