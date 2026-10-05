"""No-fit origin-profile diagnosis of the completed count comparison."""
from pathlib import Path
import json
import joblib
import numpy as np
import polars as pl
from universal_baseball.hitter_error_geometry import change,decompose
from universal_baseball.hitter_evidence_representation import RECENCY,foreign_precision,domestic_event_counts
from universal_baseball.hitter_count_baseline import probabilities
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.storage import sha256_file
from run_hitter_count_baseline import ROOT,GEN,OUT as COUNT,REF,FUTURE,TARGET,FEATURES,EVENTS,read,verify,source_data,matrix,offset
from fit_practical_hitter_v31 import weights

OUT=GEN/'hitter-count-error-diagnosis'
PRIORITY=['MLB','AAA','AA','Aplus','A','Aminus','DSL','RK120','RK121','RK124','RK128','RK134','RKother','MEX','NPB','KBO']


def save(name,obj):
    p=OUT/name;assert not p.exists(),f'Preserve {p}'
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def band(x,edges,labels):
    return labels[int(np.searchsorted(edges,x,side='right'))]


def row_profiles(o,history,source):
    y=o['origin_year'];current={};mlb=np.zeros(8);other=0.
    for r in history:
        lag=y-r['season']
        if lag==0:current[r['bucket']]=current.get(r['bucket'],0)+r['plate_appearances']
        if not 0<=lag<3:continue
        c=domestic_event_counts(r)
        if r['bucket']=='MLB':mlb+=RECENCY[lag]*c
        else:other+=RECENCY[lag]*c.sum()
    foreign,by_league=foreign_precision(source,origin=y)
    if source is not None:
        for l in ['NPB','KBO']:current[l]=source['foreign_history_counts'][l+'_0']['counts']['pa']
    nonzero=[l for l in PRIORITY if current.get(l,0)>0]
    dominant=max(nonzero,key=lambda l:(current[l],-PRIORITY.index(l))) if nonzero else 'NONE_OBSERVED'
    mass=float(mlb.sum());supported=float(np.expm1(o['count_log_exposure']*np.log(1201)))
    mlb_fraction=mass/(mass+other+foreign) if mass+other+foreign>0 else 0.
    raw_hr=float(mlb[7]/mass) if mass else None;raw_k=float(mlb[1]/mass) if mass else None
    highpower='thin_or_no_MLB' if mass<200 else 'HR4plus_K25plus' if raw_hr>=.04 and raw_k>=.25 else 'HR4plus_Kunder25' if raw_hr>=.04 else 'HRunder4'
    scout='unknown' if o['scout_list_available_0']<=0 or o['scout_rank_score_0']<0 else 'top20' if o['scout_rank_score_0']>=.8 else 'listed_other' if o['scout_listed_0']>0 else 'not_listed_in_available_list'
    return dict(dominant_current_observed_league=dominant,
        recent_MLB_mass_group=band(mass,[1e-9,200,600,1200],['none','under200','200to599','600to1199','1200plus']),
        supported_mass_group=band(supported,[1e-9,100,400,1200],['none','under100','100to399','400to1199','1200plus']),
        age_group=band(o['age'],[22,28,33],['under22','22to27','28to32','33plus']),
        MLB_fraction_group='no_production' if mass+other+foreign==0 else band(mlb_fraction,[.25,.75],['under25pct','25to74pct','75pctplus']),
        raw_MLB_HR_group='unobserved' if mass==0 else band(raw_hr,[.02,.04,.06],['under2pct','2to4pct','4to6pct','6pctplus']),
        raw_MLB_power_K_profile=highpower,scouting_group=scout,
        recent_observed_MLB_mass=mass,recent_other_domestic_mass=other,recent_foreign_mass=foreign,
        raw_recent_MLB_HR=raw_hr,raw_recent_MLB_K=raw_k,
        overseas_source='NPB' if by_league['NPB']>0 and by_league['KBO']==0 else 'KBO' if by_league['KBO']>0 and by_league['NPB']==0 else 'both' if foreign>0 else 'none')


def summarize(g):
    years=g['origin_year'].to_numpy();w=np.zeros(g.height)
    for y in np.unique(years):
        m=years==y;w[m]=1/m.sum()/len(np.unique(years))
    active=g.filter(pl.col('next_pa')>0);a={}
    for arm in ['current','count']:
        if g[arm+'_value'].null_count():
            assert g['source_addition'].all() and arm=='current'
            continue
        e=(g[arm+'_value']-g['actual_relative_value']).to_numpy();rates=[];bias=[]
        for y in sorted(active['origin_year'].unique()):
            h=active.filter(pl.col('origin_year')==y);d=(h[arm+'_rate']-h['actual_relative_rate']).to_numpy();pa=h['next_pa'].to_numpy()
            rates.append(np.sum(pa*d*d)/pa.sum());bias.append(np.sum(pa*d)/pa.sum())
        a[arm]=dict(value_rmse=float(np.sqrt(w@(e*e))),value_mae=float(w@abs(e)),
            expected_value=float(g[arm+'_value'].sum()),expected_PA=float(g[arm+'_pa'].sum()),
            rate_rmse=float(np.sqrt(np.mean(rates))) if rates else None,rate_bias=float(np.mean(bias)) if bias else None)
    ew=np.zeros(active.height)
    for y in sorted(active['origin_year'].unique()):
        m=active['origin_year'].to_numpy()==y;pa=active['next_pa'].to_numpy();ew[m]=pa[m]/pa[m].sum()/len(active['origin_year'].unique())
    event_terms={e:float(ew@active[f'error_term_{e}'].to_numpy()) for e in EVENTS} if active.height else None
    freqs={e:dict(predicted=float(ew@active[f'count_probability_{e}'].to_numpy()),actual=float(ew@(active[f'count_target_{e}']/active['next_pa']).to_numpy())) for e in ['HR','K','UBB']} if active.height else None
    delta=None if g['delivered_delta'].null_count() else dict(total=float(w@g['delivered_delta'].to_numpy()),
        active_hitting_squared=float(w@g['active_hitting_squared'].to_numpy()),
        active_hitting_workload_interaction=float(w@g['active_interaction'].to_numpy()),nonarrival=float(w@g['nonarrival'].to_numpy()))
    return dict(rows=g.height,people=g['player_id'].n_unique(),origins=len(np.unique(years)),active_rows=active.height,
        active_people=active['player_id'].n_unique(),actual_PA=int(g['next_pa'].sum()),actual_value=float(g['actual_relative_value'].sum()),
        sparse_active_warning=active['player_id'].n_unique()<20,scores=a,
        delivered_MSE_change=delta,
        count_rate_error_by_event=event_terms,count_event_frequencies=freqs)


def main():
    if OUT.exists():
        assert not any(OUT.iterdir()),'Preserve nonempty completed or partial output'
    else:OUT.mkdir(parents=True)
    final=read(COUNT/'final-review.json');verify(final['hashes']);assert final['player_walkthrough_status']=='complete'
    pre=read(COUNT/'preflight.json');verify(pre['source_hashes']);q=pl.read_parquet(COUNT/'predictions.parquet').sort('row_id')
    assert q.height==30519 and q['target_year'].max()==2025
    frames={k:pl.read_parquet(COUNT/f'features-{k}.parquet') for k in range(5)}
    parts=[]
    for k,f in frames.items():
        # Forecast scoring metadata are authoritative. Older feature matrices
        # retain a slightly different replacement denominator in some origins;
        # it is not used in these talent fits and must not re-enter evaluation.
        f=f.drop(['origin_replacement_rate','actual_relative_rate','actual_relative_value','next_pa'])
        ids=q.filter(pl.col('outer_fold')==k)['row_id'].to_list();a=f.filter(pl.col('row_id').is_in(ids))
        pred=q.filter(pl.col('outer_fold')==k).select('row_id',*[n for n in q.columns if n not in f.columns])
        parts.append(a.join(pred,on='row_id',validate='1:1'))
    f=pl.concat(parts).sort('row_id');assert f['row_id'].equals(q['row_id']) and f['next_pa'].equals(q['next_pa'])
    _,history,sources,foreign=source_data();profile=[]
    for o in f.iter_rows(named=True):profile.append(dict(row_id=o['row_id'],**row_profiles(o,history[o['player_id']],sources.get(f'{o["origin_year"]}:{o["player_id"]}'))))
    f=f.join(pl.DataFrame(profile),on='row_id',validate='1:1')
    original=f.filter(~pl.col('source_addition'));ar=original['actual_relative_rate'].to_numpy().astype(float);ar[original['next_pa'].to_numpy()==0]=np.nan
    assert original['current_pa'].equals(original['count_pa']) and original['current_rate'].null_count()==0
    decomposition=change(original['current_pa'],original['next_pa'],original['current_rate'],original['count_rate'],ar,original['origin_replacement_rate'])
    d=original.select('row_id').with_columns(pl.Series('delivered_delta',decomposition['delta']),*[pl.Series(n,decomposition[n]) for n in ['active_hitting_squared','active_interaction','nonarrival','old_hitting_error','new_hitting_error','opportunity_error']])
    assert np.allclose(decomposition['delta'],(original['count_value']-original['actual_relative_value'])**2-(original['current_value']-original['actual_relative_value'])**2)
    f=f.join(d,on='row_id',how='left',validate='1:1')
    n=f['next_pa'].to_numpy();observed=np.divide(f.select(TARGET).to_numpy(),n[:,None],out=np.zeros((f.height,8)),where=n[:,None]>0)
    p=f.select([f'count_probability_{e}' for e in EVENTS]).to_numpy();ref=f.select(REF).to_numpy();future=f.select(FUTURE).to_numpy()
    terms=(p-ref-observed+future)*VALUES[None,:]*UNIT;terms[n==0]=np.nan
    assert np.allclose(terms[n>0].sum(1),(f['count_rate']-f['actual_relative_rate']).to_numpy()[n>0],atol=1e-10)
    f=f.with_columns(*[pl.Series(f'error_term_{e}',terms[:,i]) for i,e in enumerate(EVENTS)])
    f.write_parquet(OUT/'diagnostic-rows.parquet')
    orig=f.filter(~pl.col('source_addition'));groups=[dict(family='all',group='original',**summarize(orig)),dict(family='additions',group='separate',**summarize(f.filter(pl.col('source_addition'))))]
    families=['count_branch','stage','dominant_current_observed_league','recent_MLB_mass_group','supported_mass_group','age_group','MLB_fraction_group','raw_MLB_HR_group','raw_MLB_power_K_profile','scouting_group','overseas_source','source_position']
    for family in families:
        for value in sorted(orig[family].unique()):
            g=orig.filter(pl.col(family)==value)
            groups.append(dict(family=family,group=value,**summarize(g),per_origin=[dict(origin=y,**summarize(g.filter(pl.col('origin_year')==y))) for y in sorted(g['origin_year'].unique())]))
    save('groups.json',groups)
    selected=read(COUNT/'player-walks.json')['cases'];selected_ids=[r['row_id'] for r in selected]
    walks=[]
    for r in selected:
        one=f.filter(pl.col('row_id')==r['row_id']);o=one.row(0,named=True)
        walks.append(dict(row_id=r['row_id'],player_name=o['player_name'],origin_year=o['origin_year'],
            source_walk_sha256=sha256_file(COUNT/'player-walks.json'),selection=r['why'],branch=o['count_branch'],
            profile={n:o[n] for n in families},baseline=r['past_baseline_rate'],
            hitting_error_at_expected_PA=[None if not o['next_pa'] or o['source_addition'] else o[nm] for nm in ['old_hitting_error','new_hitting_error']],
            opportunity_error_at_observed_hitting=None if not o['next_pa'] or o['source_addition'] else o['opportunity_error'],
            delta_terms={nm:o[nm] for nm in ['delivered_delta','active_hitting_squared','active_interaction','nonarrival']},
            count_rate_error_event_terms=None if not o['next_pa'] else {e:o[f'error_term_{e}'] for e in EVENTS},
            forecast={nm:o[nm] for nm in ['current_rate','count_rate','current_value','count_value','count_pa','next_pa','actual_relative_value']},
            actual_hitting_rate=o['actual_relative_rate'] if o['next_pa'] else None))
    save('player-decomposition.json',walks)
    # Inspect the three saved overseas fits without reoptimizing any parameter.
    penalties=[]
    for name,y in [('Seiya Suzuki',2021),('Jung Hoo Lee',2024),('Masataka Yoshida',2024)]:
        o=f.filter((pl.col('player_name')==name)&(pl.col('origin_year')==y)).row(0,named=True);k=o['outer_fold'];arm=o['count_branch']
        c=next(c for c in pre['cells'] if c['year']==y and c['fold']==k)
        tr=frames[k].filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id')
        names=pre['arms'][arm];m=joblib.load(COUNT/f'{arm}-rate-{y}-{k}.joblib');x=matrix(tr,names);pp=probabilities(m['beta'],x,offset(tr,True))
        cnt=tr.select(TARGET).to_numpy()*weights(tr)[:,None];mass=cnt.sum();residual=pp*cnt.sum(1,keepdims=True)-cnt
        for l in ['NPB','KBO']:
            ix=names.index('count_'+l+'_share');v=x[:,ix];beta=m['beta'][ix+1]
            grad=v@residual/mass;curv=(v*v*cnt.sum(1))@(pp*(1-pp))/mass
            assert np.max(abs(grad+.001*beta))<max(1e-5,10*m['optimizer']['maximum_gradient'])
            h=tr.filter(pl.col('count_'+l+'_share')>0)
            penalties.append(dict(player_name=name,origin=y,fold=k,arm=arm,league=l,
                active_training_people=h['player_id'].n_unique(),active_training_future_PA=int(h['next_pa'].sum()),
                coefficients=beta.tolist(),data_gradient=grad.tolist(),penalty_gradient=(.001*beta).tolist(),data_diagonal_curvature=curv.tolist(),
                penalty_to_data_curvature=np.divide(.001,curv,out=np.full(8,np.inf),where=curv>0).tolist(),
                interpretation='Coordinate diagonal, not an effective posterior precision; correlated controls and source folds remain. No alternative fit is performed.'))
    save('foreign-penalty-diagnostic.json',penalties)
    paths=[Path(__file__),ROOT/'docs/hitter-count-error-diagnosis-contract.md',ROOT/'src/universal_baseball/hitter_error_geometry.py',ROOT/'tests/test_hitter_error_geometry.py',
        COUNT/'final-review.json',COUNT/'preflight.json',COUNT/'predictions.parquet',COUNT/'player-walks.json',COUNT/'review-qualification.json',
        *[OUT/n for n in ['diagnostic-rows.parquet','groups.json','player-decomposition.json','foreign-penalty-diagnostic.json']]]
    save('receipt.json',dict(new_fits=0,rows=f.height,original_rows=orig.height,group_records=len(groups),player_cases=len(walks),
        active_decomposition_rows=int((n>0).sum()),nonarrival_rows=int((n==0).sum()),protected_outcomes_used=False,
        diagnostic_not_accuracy_improvement=True,player_walkthrough_status='pending',deployment_approved=False,
        hashes={str(p):sha256_file(p) for p in paths}))
    print(f'Diagnosed {f.height} unchanged forecasts, {len(groups)} origin-known groups and {len(walks)} saved player cases; no fits.')


if __name__=='__main__':main()
