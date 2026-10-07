"""Dated count/reference/fit/MLB-path walks; no new fit or score selection."""
from collections import defaultdict
from pathlib import Path
import gzip
import hashlib
import json
import math

import numpy as np
import polars as pl

from verify_minor_range_talent_v19 import ROOT,OUT,PUBLIC,SOURCE,data,digest,near
from run_hitter_finite_return_baseline import protections

FIXED=('Bobby Witt Jr.','Jeremy Peña','Anthony Volpe','CJ Abrams','Ceddanne Rafaela','Xavier Edwards','Bryce Eldridge')
CHANNELS=('glove_avoidance','throw_avoidance','infield_plays','outfield_plays')
FIELDS=('putOuts','assists','errors','chances','throwingErrors')
POSITIONS={3:'1B',4:'2B',5:'3B',6:'SS',7:'LF',8:'CF',9:'RF'}


def key(r):return r['origin_year'],r['player_id'],r['position']


def ageband(a):return 'unknown' if a is None else '<=19' if a<=19 else '20-22' if a<=22 else '23-25' if a<=25 else '26+'


def independent_prior(rows,focal,channel,excluded):
    """Raw source grouping, not ReferenceEngine or its cached fold subtraction."""
    p=focal['position'];level=focal['level'];age=ageband(focal['age']);year=focal['origin_year']
    admissible=[r for r in rows if year-2<=r['origin_year']<=year and r['position']==p
                and r['player_id']!=focal['player_id'] and r['player_id']%5 not in excluded]
    choices=[(['position_level_age',p,level,age],lambda r:r['level']==level and ageband(r['age'])==age),
             (['position_level',p,level],lambda r:r['level']==level),
             (['position_age',p,age],lambda r:ageband(r['age'])==age),(['position',p],lambda r:True)]
    for scope,eligible in choices:
        by=defaultdict(list)
        for r in admissible:
            if not eligible(r):continue
            n=r['chances'] if channel<2 else r['outs']
            x=r['errors']-r['throwingErrors'] if channel==0 else r['throwingErrors'] if channel==1 else r['assists'] if channel==2 else r['putOuts']
            if n>0:by[r['player_id']].append((x/n,(x/n)**2,1/n))
        if len(by)>=30:break
    # Equal people; equal records within each person, including level mixtures.
    people=len(by);a=np.array([np.mean(v,axis=0) for v in by.values()])
    m,second,inv=a.mean(axis=0) if people else (0.,0.,0.)
    variance=max(0.,second-m*m)*people/(people-1) if people>1 else 0.
    between=0.;strength=None
    if people>=30 and m>0 and (channel>=2 or m<1):
        if channel<2:
            between=max(0.,(variance-m*(1-m)*inv)/(1-inv)) if inv<1 else 0.
            between=min(between,m*(1-m)*(1-1e-9))
            if between>0:strength=m*(1-m)/between-1
        else:
            between=max(0.,variance-m*inv)
            if between>0:strength=m/between
    return dict(scope=scope,people=people,mean=float(m),between_variance=float(between),strength=float(strength) if strength is not None else None,
                reference_player_ids=sorted(by),reference_rows=sum(map(len,by.values())),second_moment=float(second),inverse_denominator=float(inv))


def fixed_fit(fit,x):
    z=(np.array(x[:len(fit['names'])])-fit['mean'])/fit['scale']
    terms=z*np.array(fit['coefficients'])
    return dict(target_mean=fit['target_mean'],prediction=float(fit['target_mean']+terms.sum()),
                terms=[dict(feature=n,input=float(v),center=float(m),scale=float(s),coefficient=float(c),contribution=float(t))
                       for n,v,m,s,c,t in zip(fit['names'],x,fit['mean'],fit['scale'],fit['coefficients'],terms)])


def main():
    protections();assert not (OUT/'player-walkthrough.json.gz').exists()
    verified=data(OUT/'independent-review.json')
    for p,h in verified['hashes'].items():assert digest(Path(p))==h,p
    preds=pl.read_parquet(OUT/'predictions.parquet').to_dicts();bykey={key(r):r for r in preds}
    origins=pl.read_parquet(SOURCE/'origins.parquet').filter(pl.col('position')>=3).to_dicts();originmap={key(r):r for r in origins}
    raw=pl.read_parquet(SOURCE/'counts.parquet').filter(pl.col('position_code').is_in(list(map(str,range(3,10))))).to_dicts()
    # Independently reconstruct level exposures from recorded source rows.
    levelby={};history=defaultdict(list)
    for r in raw:
        k=r['season'],r['player_id'],int(r['position_code']);history[k].append(r)
        if k not in originmap:continue
        lk=k+(r['normalized_level'],)
        if lk not in levelby:levelby[lk]=dict(origin_year=k[0],player_id=k[1],position=k[2],level=lk[3],age=originmap[k]['age'],outs=0,**{f:0 for f in FIELDS})
        levelby[lk]['outs']+=r['fielding_outs']
        for f in FIELDS:
            assert r[f+'_status']=='recorded' and r[f] is not None
            levelby[lk][f]+=r[f]
    refs=list(levelby.values());focal={};missing=[]
    def select(r,reason):
        focal.setdefault(key(r),dict(row=r,reasons=[]))['reasons'].append(reason)
    for name in FIXED:
        eligible=[r for r in preds if r['player_name']==name]
        if not eligible:missing.append(dict(name=name,reason='No eligible no-prior-MLB-fielding 2021/2022 origin; not forced into test.'));continue
        y=2022 if any(r['origin_year']==2022 for r in eligible) else 2021
        select(min((r for r in eligible if r['origin_year']==y),key=lambda r:(-r['minor_outs'],r['position'])),'fixed diagnostic name')
    measured=[r for r in preds if r['origin_year']==2022 and r['quality_rate'] is not None]
    gain=lambda r:abs(r['baseline']-r['quality_rate'])-abs(r['candidate']-r['quality_rate'])
    select(min(measured,key=lambda r:(-gain(r),key(r))),'largest absolute-error improvement')
    select(min(measured,key=lambda r:(gain(r),key(r))),'largest absolute-error deterioration')
    select(min(measured,key=lambda r:(-(r['candidate']-r['quality_rate']),key(r))),'largest false high')
    select(min(measured,key=lambda r:(r['candidate']-r['quality_rate'],key(r))),'largest false low')
    ordered=sorted(measured,key=lambda r:(abs(r['candidate']-r['quality_rate']),key(r)))
    select(ordered[len(ordered)//2],'median absolute-error case')
    # Coverage cases selected by origin metadata/exposure, never successful outcome.
    if not any(v['row']['quality_rate'] is None for v in focal.values()):
        select(min((r for r in preds if r['origin_year']==2022 and r['quality_rate'] is None),key=key),'unmeasured coverage contrast by origin ID')
    if not any(v['row']['support']['unseen_level_position'] for v in focal.values()):
        select(min((r for r in preds if r['origin_year']==2022 and r['support']['unseen_level_position']),key=key),'unsupported level contrast by origin ID')
    if not any(v['row']['minor_outs']<300 for v in focal.values()):
        select(min((r for r in preds if r['origin_year']==2022),key=lambda r:(r['minor_outs'],key(r))),'smallest current sample contrast')
    selection=[];requested=set()
    for k,v in focal.items():
        r=v['row'];peers=[t for t in preds if t['origin_year']==r['origin_year'] and t['level']==r['level'] and t['position']==r['position'] and t['player_id']!=r['player_id']]
        peers=sorted(peers,key=lambda t:(abs(t['age']-r['age']) if t['age'] is not None and r['age'] is not None else 999,
                     abs(math.log1p(t['minor_outs'])-math.log1p(r['minor_outs'])),t['player_id']))[:3]
        selection.append(dict(key=list(k),reasons=v['reasons'],peer_keys=[list(key(t)) for t in peers]))
        requested.update(key(t) for t in (r,*peers))
    # All modeled positions, not only the focal principal position.
    people_origins={(y,pid) for y,pid,pos in requested}
    requested.update(key(r) for r in preds if (r['origin_year'],r['player_id']) in people_origins)
    native=defaultdict(list);official=defaultdict(list)
    native_path=ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet'
    official_path=ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet'
    for r in pl.read_parquet(native_path).filter(pl.col('season')<=2025).to_dicts():native[r['player_id']].append(r)
    for r in pl.read_parquet(official_path).filter(pl.col('is_mlb')&(pl.col('season')<=2025)).to_dicts():official[r['player_id']].append(r)
    cells={};features={};priorcache={};walks=[];reference_checks=0
    for k in sorted(requested):
        r=bykey[k];tag=r['cell_tag']
        if tag not in cells:
            cells[tag]=(data(OUT/f'cells/{tag}-preflight.json'),data(OUT/f'cells/{tag}-fit.json'))
            features[tag]={key(t):t for t in pl.read_parquet(OUT/f'cells/{tag}-features.parquet').filter(pl.col('scope')=='test').to_dicts()}
        audit,fit=cells[tag];f=features[tag][k];traces=json.loads(f['level_trace'])
        for t in traces:
            rawlevel=levelby[k+(t['level'],)];assert rawlevel['outs']==t['outs']
            for field in FIELDS:assert rawlevel[field]==t['counts'][field]
            for s in t['signals']:
                channel=CHANNELS.index(s['channel']);cachekey=k+(t['level'],channel)
                if cachekey not in priorcache:priorcache[cachekey]=independent_prior(refs,rawlevel,channel,audit['excluded_folds'])
                check=priorcache[cachekey];p=s['prior']
                assert check['scope']==p['scope'] and check['people']==p['people']
                near(check['mean'],p['mean']);near(check['between_variance'],p['between_variance'])
                if p['strength'] is None:assert check['strength'] is None
                else:near(check['strength'],p['strength'])
                s['independent_reference']=check;reference_checks+=1
        baseline=fixed_fit(fit['fits'][f"baseline-{r['baseline_alpha']}"],f['candidate_design'])
        candidate=fixed_fit(fit['fits'][f"candidate-{r['candidate_alpha']}"],f['candidate_design'])
        near(baseline['prediction'],r['baseline'])
        near(r['candidate'],baseline['prediction'] if r['support']['unseen_level_position'] else candidate['prediction'])
        samepenalty_base=fixed_fit(fit['fits'][f"baseline-{r['candidate_alpha']}"],f['candidate_design'])
        frozen_count_delta=candidate['prediction']-samepenalty_base['prediction'] if not r['support']['unseen_level_position'] else 0.
        penalty_delta=samepenalty_base['prediction']-baseline['prediction'] if not r['support']['unseen_level_position'] else 0.
        near(r['candidate']-r['baseline'],frozen_count_delta+penalty_delta)
        paths=[];runs=0.;outs=0;measured_seasons=0;official_total=0;missing_outs=0;other_total=0
        for y in range(k[0]+1,k[0]+4):
            annual=[t for t in native[k[1]] if t['season']==y and t['position']==k[2]]
            legal=[t for t in annual if t['range_valid']]
            nr=sum(t['range_runs'] for t in legal);no=sum(t['native_outs'] for t in legal)
            of=sum(t['fielding_outs'] for t in official[k[1]] if t['season']==y and int(t['position_code'])==k[2])
            oth={pos:sum(t['fielding_outs'] for t in official[k[1]] if t['season']==y and int(t['position_code'])==pos) for pos in range(2,10) if pos!=k[2]}
            # The sealed label requires a valid annual native measurement, not
            # exact native/official integer equality. Its exposure certification
            # already permits the documented one-out rounding discrepancy.
            annual_missing=of if not legal else 0
            runs+=nr;outs+=no;measured_seasons+=int(no>0);official_total+=of;missing_outs+=annual_missing;other_total+=sum(oth.values())
            paths.append(dict(season=y,native=annual,same_position_official_outs=of,other_position_official_outs={str(p):n for p,n in oth.items() if n},
                              measured_runs=nr,measured_outs=no,unmeasured_official_outs=annual_missing,native_official_out_difference=no-of,
                              measured_annual_rate=1500*nr/no if no else None))
        near(runs,r['future_runs']);assert outs==r['future_opportunities']
        assert official_total==r['future_official_position_outs'] and other_total==r['future_other_position_outs']
        independently_measured=outs>=1500 and measured_seasons>=2 and missing_outs==0
        assert independently_measured==(r['quality_rate'] is not None)
        if independently_measured:near(1500*runs/outs,r['quality_rate'])
        walks.append(dict(key=list(k),forecast=r,origin=originmap[k],source_rows=history[k],level_signals=traces,
                     baseline_fit=baseline,candidate_fit=candidate,matched_penalty_baseline_fit=samepenalty_base,
                     change_accounting=dict(total=r['candidate']-r['baseline'],count_recipe_at_candidate_penalty=frozen_count_delta,
                                            change_of_baseline_penalty=penalty_delta,diagnostic_not_new_model_selection=True),
                     annual_MLB_paths=paths,raw_reference_and_prediction_replayed=True))
        print(f"Walked {r['player_name']} {k[0]} {POSITIONS[k[2]]}",flush=True)
    # Diagnostic matched-penalty scores of already fitted arms; no retuning.
    matched=[]
    for y in (2021,2022):
        rs=[r for r in preds if r['origin_year']==y and r['quality_rate'] is not None]
        for alpha in (10,100):
            counts=defaultdict(int)
            for r in rs:counts[r['player_id']]+=1
            w=np.array([1/counts[r['player_id']] for r in rs]);target=np.array([r['quality_rate'] for r in rs])
            scores={}
            for arm in ('baseline','candidate'):
                e=np.array([r[f'{arm}-{alpha}']-r['quality_rate'] for r in rs])
                scores[arm]=dict(rmse=float(np.sqrt(np.average(e*e,weights=w))),mae=float(np.average(abs(e),weights=w)))
            matched.append(dict(origin=y,alpha=alpha,scores=scores,diagnostic_only=True))
    artifact=dict(status='raw_reference_fit_and_paths_replayed_pending_main_review',selection=selection,missing_fixed=missing,walks=walks,
                  focal=len(selection),peer_selections=sum(len(s['peer_keys']) for s in selection),unique_player_origins=len(people_origins),
                  position_walks=len(walks),raw_reference_checks=reference_checks,matched_penalty_diagnostics=matched,
                  peer_rule='Same origin, level, position; nearest known age, then log outs, then ID. No future fields.',
                  no_2026_outcomes=True,no_forecast_or_explorer_change=True,player_walkthrough_status='pending_main_review',
                  hashes={str(p):digest(p) for p in (Path(__file__),OUT/'independent-review.json',OUT/'predictions.parquet',SOURCE/'counts.parquet',
                            SOURCE/'origins.parquet',native_path,official_path)})
    payload=(json.dumps(artifact,indent=2,allow_nan=False)+'\n').encode()
    lines=['# Minor fielding counts and future MLB range player review','',
           'The forecast is conditional same-position MLB range runs per 500 innings over the next three calendar years. Unknown quality is not zero. Matched-penalty calculations explain saved fits and are not a new candidate or a basis for tuning.','']
    walkmap={tuple(w['key']):w for w in walks}
    for selectrow in selection:
        w=walkmap[tuple(selectrow['key'])];r=w['forecast']
        lines.extend([f"## {r['player_name']} {r['origin_year']} {POSITIONS[r['position']]}",'',
                      f"Selection: {', '.join(selectrow['reasons'])}. Age {r['age']}, level {r['level']}, {r['minor_outs']} minor outs.",''])
        for kk in (selectrow['key'],*selectrow['peer_keys']):
            for current in (ww for ww in walks if ww['key'][:2]==kk[:2]):
                q=current['forecast'];ch=current['change_accounting'];support=q['support']
                lines.extend([f"### {q['player_name']} {POSITIONS[q['position']]}",'',
                              f"Age {q['age']}, {q['level']}, {q['minor_outs']} outs. Baseline {q['baseline']:.3f}, count candidate {q['candidate']:.3f}, actual quality {q['quality_rate'] if q['quality_rate'] is not None else 'unknown'} ({q['quality_status']}).",
                              '',f"Baseline/count penalties {q['baseline_alpha']}/{q['candidate_alpha']}. Of the {ch['total']:.3f} change, matched-penalty count recipe contributes {ch['count_recipe_at_candidate_penalty']:.3f}; changed baseline penalty contributes {ch['change_of_baseline_penalty']:.3f}. Training level-position/joint people {support['level_position_people']}/{support['joint_people']}; baseline fallback {support['unseen_level_position']}; outside input ranges {[i for i,v in enumerate(support['outside_feature_range']) if v]}.",''])
                for t in current['level_signals']:
                    c=t['counts'];lines.extend([f"{t['level']}: outs {t['outs']}; PO/A/E/chances/throw E {c['putOuts']}/{c['assists']}/{c['errors']}/{c['chances']}/{c['throwingErrors']}.",''])
                    for s in t['signals']:
                        p=s['prior'];lines.extend([f"- {s['channel']}: raw {s['raw_rate']}, reference {p['mean']:.6f}, reliability {s['reliability']:.4f}, favorable deviation {s['deviation']:.6f}; scope {p['scope']}, {p['people']} distinct reference people."])
                    lines.append('')
                largest=sorted(current['candidate_fit']['terms'],key=lambda t:-abs(t['contribution']))[:5]
                lines.extend([f"Candidate target mean {current['candidate_fit']['target_mean']:.3f}; largest standardized terms {[(t['feature'],round(t['contribution'],3)) for t in largest]}. These are fitted arithmetic, not causal effects.",''])
                for t in current['annual_MLB_paths']:
                    lines.append(f"- {t['season']}: native range {t['measured_runs']:.3f} / {t['measured_outs']} outs; annual rate {t['measured_annual_rate']}; official same-position outs {t['same_position_official_outs']}, unmeasured {t['unmeasured_official_outs']}; other positions {t['other_position_official_outs']}.")
                lines.append('')
    for m in missing:lines.extend([f"Missing fixed case: {m['name']}. {m['reason']}",''])
    for folder in (OUT,PUBLIC):
        path=folder/'player-walkthrough.json.gz';assert not path.exists();path.write_bytes(gzip.compress(payload,mtime=0))
        path=folder/'player-walkthrough.md';assert not path.exists();path.write_text('\n'.join(lines)+'\n',encoding='utf8',newline='\n')
    protections();print(json.dumps({k:artifact[k] for k in ('focal','peer_selections','unique_player_origins','position_walks','raw_reference_checks','missing_fixed','matched_penalty_diagnostics')}),flush=True)


if __name__=='__main__':main()
