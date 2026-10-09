"""Frozen-distribution calibration and same-season outfield position diagnostics."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import sys
import numpy as np
import polars as pl
from universal_baseball.hitter_workload_risk import mixture_pmf, distribution_terms
from universal_baseball.probability_position_diagnostics import pit_bin_mass, quantile_exceedance, paired_position
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/probability-position-2026-10-08'
PUB=ROOT/'reports/model-evidence/probability-position-2026-10-08'
RISK=ROOT/'reports/generated/hitter-workload-risk'
NATIVE=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
OFFICIAL=ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet'
ALPHAS=[.05,.1,.2,.3,.4,.5,.6,.7,.8,.9,.95]
PROTECTED=[ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05/forecast.parquet',
    ROOT/'reports/generated/hitter-final-2026-reviewed-explorer/data.json',
    ROOT/'reports/generated/hitter-final-2026-reviewed-explorer/index.html']


def read(path):
    with (gzip.open if path.suffix=='.gz' else open)(path,'rt',encoding='utf8') as f:return json.load(f)


def write(path,obj):
    with (gzip.open if path.suffix=='.gz' else open)(path,'wt',encoding='utf8') as f:
        json.dump(obj,f,indent=2,allow_nan=False)


def eqyear(g,cols):
    return g.group_by('target_year').agg([pl.col(c).mean() for c in cols]).select(cols).mean().row(0)


def cluster(g,cols,seed):
    ids,ii=np.unique(g['player_id'].to_numpy(),return_inverse=True)
    years,yy=np.unique(g['target_year'].to_numpy(),return_inverse=True)
    n=np.zeros((len(ids),len(years)));a=np.zeros((len(ids),len(years),len(cols)))
    np.add.at(n,(ii,yy),1);np.add.at(a,(ii,yy),g.select(cols).to_numpy())
    rng=np.random.default_rng(seed);draws=[]
    for _ in range(1000):
        w=np.bincount(rng.integers(0,len(ids),len(ids)),minlength=len(ids))
        d=np.einsum('i,ij->j',w,n)
        if (d>0).all():draws.append((np.einsum('i,ijk->jk',w,a)/d[:,None]).mean(axis=0))
    assert len(draws)>950
    return dict(zip(cols,np.quantile(draws,[.025,.975],axis=0).T.tolist()))


def probability():
    base=['row_id','player_id','player_name','origin_year','target_year','outer_fold','stage',
        'age','prior_debut','pa_0','minor_pa_0','preseason_p','preseason_conditional_pa','preseason_pa','preseason_value',
        'next_pa','next_value','profile_people']
    schema=pl.read_parquet_schema(RISK/'scored-predictions.parquet')
    selected=base+[c for c in schema if c.startswith(('risk_','binomial_'))]
    f=pl.read_parquet(RISK/'scored-predictions.parquet',columns=selected).sort('row_id')
    report=read(RISK/'fit-report.json');pre=read(RISK/'preflight.json')
    assert len(f)==30506 and f['row_id'].n_unique()==len(f) and f['target_year'].max()==2025
    assert (f['target_year']==f['origin_year']+1).all()
    assert sha256_file(RISK/'predictions.parquet')==report['output_sha256']
    final=read(ROOT/'reports/model-evidence/hitter-workload-risk/final-report.json')
    assert final['player_walkthrough_status']=='complete'
    rawcols=[c for c in selected if c in pl.read_parquet_schema(RISK/'predictions.parquet')]
    raw=pl.read_parquet(RISK/'predictions.parquet',columns=rawcols).sort('row_id')
    assert f.select(rawcols).equals(raw)
    missing=[];hashes={};nested=0
    for path,h in pre['input_hashes'].items():
        path=Path(path)
        if not path.exists():
            assert 'practical-hitter-joint-forest-v43' in str(path),path
            missing.append(str(path));continue
        assert sha256_file(path)==h,path
        hashes[str(path)]=h
    byid={r['row_id']:r for r in f.select('row_id','player_id','outer_fold','origin_year','target_year').to_dicts()}
    # Full features retain training rows beyond the evaluated historical forecasts.
    features=pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet',
        columns=['row_id','player_id','outer_fold','origin_year','target_year'])
    provenance={r['row_id']:r for r in features.select('row_id','player_id','outer_fold','origin_year','target_year').to_dicts()}
    cells={(c['year'],c['fold']):c for c in pre['cells']}
    pieces=[]
    for note in report['cells']:
        y,k=note['year'],note['fold'];c=cells[y,k]
        g=f.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k))
        assert set(g['row_id'])==set(c['test_row_ids'])
        assert sha256_file(RISK/f'forecast-{y}-{k}.parquet')==note['forecast_sha256']
        cp=Path(note['calibration_path']);assert sha256_file(cp)==note['calibration_sha256']
        cal=pl.read_parquet(cp)
        assert set(cal['row_id'])==set(c['calibration_row_ids']) and cal['target_year'].max()<=y
        assert set(cal['player_id']).isdisjoint(g['player_id'].to_list())
        for n,h in zip(c['nested'],note['nested_heads'],strict=True):
            for pathkey,hashkey in [('model_path','model_sha256'),('prediction_path','prediction_sha256')]:
                path=Path(h[pathkey]);assert sha256_file(path)==h[hashkey],path
            tr=[provenance[i] for i in n['training_row_ids']];val=[provenance[i] for i in n['validation_row_ids']]
            assert set(n['training_row_ids'])==set(h['training_row_ids'])
            assert set(n['validation_row_ids'])==set(h['validation_row_ids'])
            assert max(r['target_year'] for r in tr)<=n['origin']
            assert max(r['target_year'] for r in val)<=y
            assert not {r['player_id'] for r in tr}&{r['player_id'] for r in val}
            assert all(r['outer_fold'] not in (k,n['inner_fold']) for r in tr)
            assert all(r['outer_fold']==n['inner_fold'] and r['outer_fold']!=k for r in val)
            nested+=1
        p=g['preseason_p'].to_numpy();mean=g['preseason_conditional_pa'].to_numpy();actual=g['next_pa'].to_numpy()
        columns=[]
        for arm,con in [('risk',note['concentration']['concentration']),('binomial',None)]:
            pmf=mixture_pmf(p,mean,con)
            np.testing.assert_allclose(pmf@np.arange(801),g['preseason_pa'].to_numpy(),atol=1e-6,rtol=0)
            terms=distribution_terms(pmf,actual)
            for key,value in terms.items():np.testing.assert_allclose(value,g[arm+'_'+key].to_numpy(),atol=1e-8,rtol=0)
            q,pred,obs=quantile_exceedance(pmf,actual,ALPHAS)
            bins,lo,hi,impossible=pit_bin_mass(pmf,actual)
            columns += [pl.Series(arm+'_pit_lo',lo),pl.Series(arm+'_pit_hi',hi),pl.Series(arm+'_impossible',impossible)]
            columns += [pl.Series(arm+'_pit'+str(j),bins[:,j]) for j in range(10)]
            for j,a in enumerate(ALPHAS):
                suffix=str(int(a*100));columns += [pl.Series(arm+'_q'+suffix,q[:,j]),
                    pl.Series(arm+'_exceed_expected'+suffix,pred[:,j]),pl.Series(arm+'_exceed_actual'+suffix,obs[:,j])]
            # Active law, conditional on appearance, not a rerouted population forecast.
            active=actual>0;conditional=mixture_pmf(np.ones(active.sum()),mean[active],con)
            cb,_,_,_=pit_bin_mass(conditional,actual[active])
            cq,cpred,cobs=quantile_exceedance(conditional,actual[active],ALPHAS)
            for j in range(10):
                v=np.full(len(g),np.nan);v[active]=cb[:,j]
                columns.append(pl.Series(arm+'_conditional_pit'+str(j),v).fill_nan(None))
            for j,a in enumerate(ALPHAS):
                for tag,value in [('expected',cpred[:,j]),('actual',cobs[:,j]),('quantile',cq[:,j])]:
                    v=np.full(len(g),np.nan);v[active]=value
                    columns.append(pl.Series(arm+'_conditional_'+tag+str(int(a*100)),v).fill_nan(None))
        pieces.append(g.select('row_id','player_id','player_name','origin_year','target_year','outer_fold','stage',
            'age','prior_debut','pa_0','minor_pa_0','preseason_p','preseason_conditional_pa','preseason_pa','preseason_value',
            'next_pa','next_value','profile_people',*[c for c in f.columns if c.startswith(('risk_','binomial_'))]).with_columns(columns))
    z=pl.concat(pieces).sort('row_id')
    assert z['row_id'].equals(f['row_id'])
    z=z.with_columns((pl.col('risk_crps')-pl.col('binomial_crps')).alias('crps_delta'),
        (pl.col('preseason_p')-(pl.col('next_pa')>0).cast(pl.Float64)).alias('activity_bias'),
        (pl.col('risk_p400')-(pl.col('next_pa')>=400).cast(pl.Float64)).alias('regular_bias'))
    z.write_parquet(OUT/'workload-derived.parquet')
    masks={'all':pl.lit(True),'current_MLB':pl.col('pa_0')>0,
        'upper_never_debut':(pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'),
        'lower_never_debut':(pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'),
        'absent_prior_debut':(pl.col('prior_debut')==1)&(pl.col('pa_0')==0),
        'no_active_profile':pl.col('profile_people')==0,'active_outcomes_only':pl.col('next_pa')>0,
        'at_least250_outcome_only':pl.col('next_pa')>=250}
    for y in sorted(z['origin_year'].unique()):masks['origin_'+str(y)]=pl.col('origin_year')==y
    for low,high in [(0,25),(25,30),(30,35),(35,100)]:
        masks[f'MLB_age_{low}_{high}']=(pl.col('pa_0')>0)&pl.col('age').is_between(low,high,closed='left')
    for j in range(10):masks[f'appearance_band_{j}']=pl.col('preseason_p').is_between(j/10,(j+1)/10,closed='left')
    summaries=[];intervals={}
    for name,mask in masks.items():
        g=z.filter(mask)
        if not len(g):continue
        row=dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),
            expected_appearances=float(g['preseason_p'].sum()),actual_appearances=int((g['next_pa']>0).sum()),
            expected_regular=float(g['risk_p400'].sum()),actual_regular=int((g['next_pa']>=400).sum()),
            expected_pa=float(g['preseason_pa'].sum()),actual_pa=int(g['next_pa'].sum()),arms={})
        for arm in ['risk','binomial']:
            scores=dict(zip(['crps','pinball','interval_score','width','coverage','brier400','logloss400'],
                eqyear(g,[arm+'_'+k for k in ['crps','pinball','interval_score','width','coverage','brier400','logloss400']])))
            scores['pit_bins_equal_year']=list(eqyear(g,[arm+'_pit'+str(j) for j in range(10)]))
            scores['impossible_observations']=int(g[arm+'_impossible'].sum())
            scores['quantile_exceedance']=[dict(percentile=int(a*100),expected=e,observed=o)
                for a,e,o in zip(ALPHAS,eqyear(g,[arm+'_exceed_expected'+str(int(a*100)) for a in ALPHAS]),
                    eqyear(g,[arm+'_exceed_actual'+str(int(a*100)) for a in ALPHAS]))]
            active=g.filter(pl.col('next_pa')>0)
            scores['conditional_active_pit_bins']=list(eqyear(active,[arm+'_conditional_pit'+str(j) for j in range(10)])) if len(active) else None
            scores['conditional_active_exceedance']=[dict(percentile=int(a*100),expected=e,observed=o)
                for a,e,o in zip(ALPHAS,eqyear(active,[arm+'_conditional_expected'+str(int(a*100)) for a in ALPHAS]),
                    eqyear(active,[arm+'_conditional_actual'+str(int(a*100)) for a in ALPHAS]))] if len(active) else None
            row['arms'][arm]=scores
        pa=g['preseason_p'].to_numpy();a=(g['next_pa'].to_numpy()>0).astype(float)
        g=g.with_columns(pl.Series('any_brier',(pa-a)**2),pl.Series('any_logloss',-a*np.log(np.clip(pa,1e-15,1))-(1-a)*np.log(np.clip(1-pa,1e-15,1))))
        row['any_pa_scores']=dict(zip(['brier','log_loss'],eqyear(g,['any_brier','any_logloss'])))
        summaries.append(row)
        if name in ['all','current_MLB','upper_never_debut','lower_never_debut','absent_prior_debut']:
            intervals[name]=cluster(g,['risk_pit'+str(j) for j in range(10)]+['crps_delta','activity_bias','regular_bias'],100826)
    cases=[]
    for old in read(RISK/'cases.json'):
        r=z.filter(pl.col('row_id')==old['origin']['row_id']).row(0,named=True)
        note=next(n for n in report['cells'] if n['year']==r['origin_year'] and n['fold']==r['outer_fold'])
        pmf=mixture_pmf(np.array([r['preseason_p']]),np.array([r['preseason_conditional_pa']]),note['concentration']['concentration'])[0]
        np.testing.assert_allclose(pmf,old['probability_mass'],atol=1e-12)
        # Reuse the complete dated-input and fitted-head traces, without inventing new fits.
        cases.append(dict(player=r['player_name'],origin=r['origin_year'],row=r,
            source_history=old['source_history'],actual_inputs=old['actual_inputs'],saved_point_paths=old['saved_point_paths'],
            dispersion_fit=old['dispersion_fit'],peers=old['peers'],profile_support=old['profile_support'],
            upstream_case_sha256=sha256_file(RISK/'cases.json')))
    write(PUB/'workload-cases.json.gz',cases)
    result=dict(rows=len(z),people=z['player_id'].n_unique(),nested_contexts_checked=nested,
        available_source_hashes_checked=hashes,unavailable_old_reference=missing,
        summaries=summaries,player_cluster_intervals=intervals,player_walkthrough_status='complete',
        reviewed_cases=len(cases),scope='Historical workload distributions only; not current hitting or full WAR uncertainty',
        no_fit=True,no_2026_outcomes=True)
    write(PUB/'workload-calibration.json.gz',result)
    print('Workload calibration and fourteen saved-input walks completed.',flush=True)


def positions():
    native=pl.read_parquet(NATIVE).to_dicts()
    assert len(native)==13304 and len({(r['season'],r['player_id'],r['position']) for r in native})==len(native)
    assert max(r['season'] for r in native)==2025
    rows=[r for r in native if r['position'] in (7,8,9)]
    official=pl.read_parquet(OFFICIAL).filter(pl.col('is_mlb')&pl.col('season').is_between(2016,2025)&
        pl.col('position_code').is_in(['7','8','9'])).group_by('season','player_id','position_code').agg(pl.col('fielding_outs').sum())
    omap={(r['season'],r['player_id'],int(r['position_code'])):r['fielding_outs'] for r in official.to_dicts()}
    centers={};coverage=[]
    for y in range(2016,2026):
        for pos in [7,8,9]:
            r=[s for s in rows if s['season']==y and s['position']==pos and s['range_valid']]
            assert r and all(s['native_outs']>0 and s['exposure_valid'] for s in r)
            rate=1500*sum(s['range_runs'] for s in r)/sum(s['native_outs'] for s in r)
            centers[y,pos]=rate
            coverage.append(dict(season=y,position=pos,measured_people=len(r),outs=sum(s['native_outs'] for s in r),
                raw_runs=sum(s['range_runs'] for s in r),rate=rate,
                invalid_rows=sum(s['season']==y and s['position']==pos and not s['range_valid'] for s in rows)))
    persons=defaultdict(dict)
    for r in rows:persons[r['season'],r['player_id']][r['position']]=r
    pairs=[];excluded=defaultdict(int)
    for (y,pid),m in persons.items():
        if 8 not in m or not any(p in m for p in (7,9)):continue
        cf=m[8];corners=[m[p] for p in (7,9) if p in m and m[p]['official_outs']>0]
        if any(omap.get((y,pid,p),0)>0 and p not in m for p in (7,9)):
            excluded['official_corner_stint_without_native_row']+=1;continue
        if not cf['range_valid'] or not cf['exposure_valid'] or not all(r['range_valid'] and r['exposure_valid'] for r in corners):
            excluded['missing_or_invalid_measurement']+=1;continue
        n=sum(r['native_outs'] for r in corners)
        if cf['native_outs']<450 or n<450:excluded['below_primary_exposure']+=1;continue
        for r in [cf,*corners]:assert abs(omap[y,pid,r['position']]-r['native_outs'])<=5
        ref=sum(centers[y,r['position']]*r['native_outs'] for r in corners)/n
        d=paired_position(cf['range_runs'],cf['native_outs'],sum(r['range_runs'] for r in corners),n,centers[y,8],ref)
        np.testing.assert_allclose(d['raw_plus_schedule'],d['relative_plus_transferred_schedule'],atol=1e-12)
        pairs.append(dict(season=y,player_id=pid,player_name=cf['player_name'],cf_outs=cf['native_outs'],corner_outs=n,
            cf_runs=cf['range_runs'],corner_runs=sum(r['range_runs'] for r in corners),cf_reference=centers[y,8],corner_reference=ref,
            harmonic_exposure=2/(1/cf['native_outs']+1/n),**d))
    pair=pl.DataFrame(pairs).sort('season','player_id');pair.write_parquet(OUT/'position-pairs.parquet')
    def summarize(g):
        cols=['raw_difference','reference_difference','relative_difference','relative_plus_schedule','equalization_gap_per1458']
        people=g.group_by('player_id').agg([pl.col(c).mean() for c in cols])
        values=people.select(cols).to_numpy();rng=np.random.default_rng(100827)
        samples=np.array([values[rng.integers(0,len(values),len(values))].mean(axis=0) for _ in range(1000)])
        return dict(rows=len(g),people=len(people),person_balanced=dict(zip(cols,values.mean(axis=0))),
            person_cluster_interval=dict(zip(cols,np.quantile(samples,[.025,.975],axis=0).T.tolist())),
            row_balanced=dict(zip(cols,g.select(cols).mean().row(0))),
            exposure_weighted=dict(zip(cols,np.average(g.select(cols).to_numpy(),weights=g['harmonic_exposure'].to_numpy(),axis=0))))
    scopes={'all':pair,'at_least300_innings_each':pair.filter((pl.col('cf_outs')>=900)&(pl.col('corner_outs')>=900))}
    scopes.update({'season_'+str(y):pair.filter(pl.col('season')==y) for y in range(2016,2026)})
    for p in [7,9]:
        one=[]
        for (y,pid),m in persons.items():
            if 8 not in m or p not in m:continue
            a,b=m[8],m[p]
            if not all(r['range_valid'] and r['exposure_valid'] and r['native_outs']>=450 for r in [a,b]):continue
            one.append(dict(season=y,player_id=pid,harmonic_exposure=2/(1/a['native_outs']+1/b['native_outs']),
                **paired_position(a['range_runs'],a['native_outs'],b['range_runs'],b['native_outs'],centers[y,8],centers[y,p])))
        scopes['CF_vs_'+('LF' if p==7 else 'RF')]=pl.DataFrame(one)
    summaries={name:summarize(g) for name,g in scopes.items() if len(g)}
    selected={}
    def choose(r,why):selected.setdefault((r['season'],r['player_id']),[]).append(why)
    absent=[]
    for pid in [605141,641355,664056,678882]:
        g=pair.filter(pl.col('player_id')==pid)
        if len(g):choose(g.sort(pl.min_horizontal('cf_outs','corner_outs'),descending=True).row(0,named=True),'fixed eligible maximum balanced exposure')
        else:absent.append(pid)
    choose(pair.sort('relative_difference').row(0,named=True),'lowest paired relative difference')
    choose(pair.sort('relative_difference',descending=True).row(0,named=True),'highest paired relative difference')
    choose(pair.sort('relative_difference').row(len(pair)//2,named=True),'ordinary median paired difference')
    cases=[]
    for (y,pid),why in selected.items():
        r=pair.filter((pl.col('season')==y)&(pl.col('player_id')==pid)).row(0,named=True)
        peers=pair.filter((pl.col('season')==y)&(pl.col('player_id')!=pid)).with_columns(
            ((pl.col('cf_outs')-r['cf_outs']).abs()+(pl.col('corner_outs')-r['corner_outs']).abs()).alias('distance')).sort('distance','player_id').head(3)
        cases.append(dict(row=r,selection=why,native_source_rows=[s for s in native if s['player_id']==pid and s['season']==y],
            annual_references=[s for s in coverage if s['season']==y],
            peers=[dict(row=t,native_source_rows=[s for s in native if s['player_id']==t['player_id'] and s['season']==y]) for t in peers.to_dicts()],
            unknown_age=True,scope='same-season observed range comparison, not a forecast or a causal position effect'))
    write(PUB/'position-cases.json.gz',cases)
    infield=defaultdict(dict)
    for r in native:
        if r['position'] in [3,6]:infield[r['season'],r['player_id']][r['position']]=r
    infcounts={str(n):sum(3 in m and 6 in m and all(m[p]['range_valid'] and m[p]['native_outs']>=n for p in [3,6]) for m in infield.values()) for n in [450,900]}
    result=dict(summaries=summaries,annual_references=coverage,exclusions=dict(excluded),
        eligible_pairs=len(pair),fixed_cases_absent=absent,SS_1B_pair_counts=infcounts,
        source_sha256=sha256_file(NATIVE),official_exposure_sha256=sha256_file(OFFICIAL),all_reference_transfer_identities_pass=True,
        player_walkthrough_status='complete',reviewed_cases=len(cases),no_fit=True,
        no_2026_outcomes=True,no_schedule_deployed=True,
        limits='Switcher selection, measurement calibration, assignments, health and park remain; range excludes arm, catcher and replacement scarcity')
    write(PUB/'position-comparison.json.gz',result)
    print(f'Position diagnostic completed: {len(pair)} player-seasons, {len(cases)} focal source walks.',flush=True)


def main():
    resource='--resume-after-resource-repair' in sys.argv
    resume='--resume-after-numeric-repair' in sys.argv or resource
    assert not PUB.exists() or resume,'Do not overwrite an exposed diagnostic'
    if resume:
        assert not (PUB/'workload-calibration.json.gz').exists(),'No scored rerun'
        before=read(PUB/'preflight.json.gz')
        for p in PROTECTED:assert sha256_file(p)==before['hashes'][str(p)]
        if resource:
            write(PUB/'resource-execution-amendment.json.gz',dict(
                reason='Second attempt reconstructed all PMFs but exhausted available process memory during first bootstrap before summaries/cases were saved. Read only required columns and use weighted cluster sums instead of expanded bootstrap arrays. Original derived rows are preserved until exact reconstruction. Add official exposure check for entirely missing corner-position rows before the position test. No recipe, outcome, threshold or model fit changed.',
                original_hashes=before['hashes'],repaired_hashes={str(p):sha256_file(p) for p in [Path(__file__),OFFICIAL]},
                original_failure='Unable to allocate 6.23 MiB for expanded first-group bootstrap array',scored_results_exposed=False))
        else:write(PUB/'numeric-execution-amendment.json.gz',dict(
            reason='Initial reconstruction assertion stopped before scoring: positive binomial tail masses below floating CDF resolution. Normalize PIT bin overlap by represented CDF interval width and retain collapsed observations at its boundary. No forecast, cohort, recipe, target or scoring choice changed.',
            original_hashes=before['hashes'],repaired_hashes={str(p):sha256_file(p) for p in [Path(__file__),ROOT/'src/universal_baseball/probability_position_diagnostics.py']},
            original_failure='PIT bin masses did not sum to one for 71 of 893 first-cell narrow-control observations',scored_results_exposed=False))
    assert (ROOT/'docs/probability-and-position-diagnostics-2026-10-08-contract.md').exists()
    PUB.mkdir(parents=True,exist_ok=resume);OUT.mkdir(parents=True,exist_ok=resume)
    paths=[Path(__file__),ROOT/'src/universal_baseball/probability_position_diagnostics.py',
        ROOT/'docs/probability-and-position-diagnostics-2026-10-08-contract.md',
        RISK/'scored-predictions.parquet',RISK/'fit-report.json',RISK/'preflight.json',RISK/'cases.json',NATIVE,OFFICIAL,*PROTECTED]
    hashes={str(p):sha256_file(p) for p in paths}
    if not resume:write(PUB/'preflight.json.gz',dict(hashes=hashes,no_fitting=True,no_2026_outcomes=True))
    probability()
    assert read(PUB/'workload-calibration.json.gz')['player_walkthrough_status']=='complete'
    positions()
    for p in PROTECTED:assert sha256_file(p)==hashes[str(p)],p
    write(PUB/'execution-check.json.gz',dict(protected_files_unchanged=True,
        no_fit=True,player_walks_materialized=True,independent_verification='pending',
        hashes={str(p):sha256_file(p) for p in [*PUB.glob('*.gz'),*OUT.glob('*.parquet')]}))


if __name__=='__main__':main()
