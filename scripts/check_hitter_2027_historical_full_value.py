"""Fixed chronological assembly against actual/public full WAR, no new tuning."""
from collections import defaultdict,Counter
from dataclasses import asdict
from pathlib import Path
import gzip,json,math
import numpy as np
import polars as pl
from universal_baseball.hitter_defense_rates_v1 import DefenseRates
from universal_baseball.defense_reference_history import origin_reference
from universal_baseball.minor_range_talent import design,ridge_predict
from universal_baseball.defense_opportunity_bridge import CHANNELS,native_conversion,native_from_outs
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.current_baserunning import build_steal_history,build_current_baserunning_rates
from universal_baseball.player_value_advancement_projection import PlayerSeasonAdvancementSummary
from universal_baseball.player_value_baserunning_runs import build_baserunning_reference
from universal_baseball.player_value_runs_per_win import calculate_v1_runs_per_win
from universal_baseball.defense_value import position_value
from universal_baseball.storage import sha256_file
from run_defense_jobs_v14 import inputs
from capture_hitter_2027_origin_counts import ROOT,write_once
from capture_hitter_2027_historical_war import decode

BASE=ROOT/'reports/generated/hitter-2027-base'
OUT=BASE/'historical-full-value'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'


def minor_rate(rate,model,q,history,cells):
    """Same frozen supported V19 prior used in current production assembly."""
    if rate['component']!='range' or any(r['range_valid'] and r['native_outs']>0 for r in model.by['native'][q['player_id']]):
        return rate,None
    pid=q['player_id'];pos=int(rate['context']);y=q['origin_year']
    parts=[s for s in history[pid] if s['season']==y and not s['is_mlb'] and s[f'outs_{pos}']>0]
    if not parts:return rate,None
    c=cells[pid%5];assert c['cutoff']<=y and c['held_fold']==pid%5
    fit=c['fits']['baseline-10'];levels=defaultdict(float)
    for s in parts:levels[s['normalized_level']]+=s[f'outs_{pos}']
    sample=dict(age=None if q['age_unknown'] else q['age'],minor_outs=sum(levels.values()),
        position=pos,level=max(levels,key=lambda k:(levels[k],k)))
    x=design([sample],np.zeros((1,4)),c['age_median'],False)
    outside=(x[0]<np.array(fit['training_min'])-1e-10)|(x[0]>np.array(fit['training_max'])+1e-10)
    supported=bool(c['fit_supported']) and not outside.any()
    native=float(ridge_predict(fit,x)[0]);reference=origin_reference(y,pos,pid%5,model.references)
    if supported:rate=dict(rate,runs_per_unit=native-reference,evidence_tier='translated_profile')
    return rate,dict(input=sample,native=native,reference=reference,supported=bool(supported),
        fit_cutoff=c['cutoff'],fit_held_fold=c['held_fold'],training_people=c['training_people'])


def loss(rows,arm):
    if not rows:return None
    years=sorted({r['target_year'] for r in rows});stats=[]
    for y in years:
        err=np.array([r[arm]-r['actual_WAR'] for r in rows if r['target_year']==y]);stats.append([np.mean(err**2),np.mean(abs(err)),np.mean(err)])
    v=np.mean(stats,axis=0)
    return dict(rows=len(rows),people=len({r['player_id'] for r in rows}),RMSE=float(np.sqrt(v[0])),MAE=float(v[1]),bias=float(v[2]),
        predicted_WAR=sum(r[arm] for r in rows),actual_WAR=sum(r['actual_WAR'] for r in rows),
        expected_PA=sum(r['expected_PA'] for r in rows),actual_PA=sum(r['actual_PA'] for r in rows))


def interval(rows,candidate,control):
    people=sorted({r['player_id'] for r in rows});years=sorted({r['target_year'] for r in rows})
    pi={p:i for i,p in enumerate(people)};yi={y:i for i,y in enumerate(years)}
    a=np.zeros((len(people),len(years),5))
    for r in rows:
        e=r[candidate]-r['actual_WAR'];b=r[control]-r['actual_WAR']
        a[pi[r['player_id']],yi[r['target_year']]] += [e*e,b*b,abs(e),abs(b),1]
    rng=np.random.default_rng(20271009);samples=[]
    for _ in range(1000):
        s=a[rng.integers(0,len(people),len(people))].sum(axis=0)
        means=(s[:,:4]/s[:,4,None]).mean(axis=0)
        samples.append([np.sqrt(means[0])-np.sqrt(means[1]),means[2]-means[3]])
    return dict(candidate=candidate,control=control,people=len(people),resamples=1000,
        delta_RMSE_95=np.quantile(samples,[.025,.975],axis=0)[:,0].tolist(),
        delta_MAE_95=np.quantile(samples,[.025,.975],axis=0)[:,1].tolist(),development_not_fresh_holdout=True)


def main():
    assert not (PUBLIC/'historical-full-value-scores.json').exists()
    paths=[]
    def read(p):paths.append(p);return pl.read_parquet(p)
    roles=read(BASE/'role-fallback-repair/role-budget-historical.parquet')
    bat=read(ROOT/'reports/generated/hitter-2027-translation-repair/predictions.parquet').filter(pl.col('row_id').is_in(roles['row_id'].implode()))
    assert len(bat)==len(roles)==12432 and set(bat['target_year'])=={2023,2024,2025}
    b={r['row_id']:r for r in bat.to_dicts()};q=roles.to_dicts()
    for r in q:
        a=b[r['row_id']]
        assert all(r[k]==a[k] for k in ['player_id','origin_year','target_year','outer_fold','preseason_pa','next_pa'])
        r.update(candidate_rate=a['candidate_rate'],batting_anchor=a['candidate_value'])
    inventory,delta,hist=inputs()
    source_specs=dict(native='defense-native-range-v3/component-ledger.parquet',
        framing='catcher-native-opportunity-v3/modern/framing-annual.parquet',
        catcher='catcher-throw-block-v5/extension-annual.parquet',other='arm-receiving-v6/official-scope/annual.parquet')
    sources={k:read(ROOT/'reports/generated'/p).to_dicts() for k,p in source_specs.items()}
    native=read(ROOT/'reports/generated/defense-opportunity-v8/opportunity-records.parquet').to_dicts()
    fitpath=ROOT/'reports/model-evidence/defense-minor-range-v19/fit-report.json.gz';paths.append(fitpath)
    fits=json.loads(gzip.decompress(fitpath.read_bytes()))['cells']
    cells={c['outer_fold']:c for c in fits if c['kind']=='outer' and c['cutoff']==2022};assert len(cells)==5
    stints=read(BASE/'stints.parquet').filter(pl.col('season').is_between(2020,2024))
    advances=read(ROOT/'reports/generated/multiyear-hitter-components-v1/native-advancement-history.parquet').filter(pl.col('season').is_between(2020,2024))
    actual=read(OUT/'fg-actual-hitter-war.parquet');actual_by={(r['season'],r['player_id']):r for r in actual.to_dicts()}
    pubpath=OUT/'public-preseason-WAR.json.gz';paths.append(pubpath)
    pub={(r['system'],r['season'],r['player_id']):r for r in json.loads(gzip.decompress(pubpath.read_bytes()))}
    paths.extend([Path(__file__),ROOT/'docs/hitter-2027-whole-value-check.md',ROOT/'docs/hitter-2027-full-value-review.md'])
    preflight=dict(before_assembly=True,new_model_tuning=False,
        rows=12432,identity_and_PA_equal=True,target_years=[2023,2024,2025],minor_profile_fit_cutoff=2022,
        scoring_definition='published realized FanGraphs hitter WAR',input_hashes={str(p):sha256_file(p) for p in paths})
    prepath=PUBLIC/'historical-full-value-preflight.json'
    if prepath.exists():
        old=json.loads(prepath.read_text())
        assert all(sha256_file(Path(p))==h for p,h in old['input_hashes'].items() if p!=str(Path(__file__)))
        correction=PUBLIC/'historical-full-value-execution-correction.json'
        if not correction.exists():write_once(correction,dict(before_scores=True,previous_preflight_hash=sha256_file(prepath),
            correction='Preserve unknown ages in a separate reporting group; first run stopped before scores/output at numeric age comparison.',
            estimator_or_membership_changed=False,runner_sha256=sha256_file(Path(__file__))))
    else:write_once(prepath,preflight)
    outputs=[];details={};environments=[];coverage=[]
    for y in (2022,2023,2024):
        rows=[r for r in q if r['origin_year']==y]
        past={k:[r for r in data if r['season']<=y] for k,data in sources.items()}
        model=DefenseRates(origin=y,native=past['native'],framing=past['framing'],catcher=past['catcher'],arm_receiving=past['other'])
        conversions={fold:{c:native_conversion([r for r in native if r['channel']==c],y,fold,player_fold) for c in CHANNELS} for fold in range(5)}
        mlb=stints.filter((pl.col('season')==y)&(pl.col('level_group')=='MLB'))
        src,_=decode(gzip.decompress((OUT/f'fg-batting-{y}.html.gz').read_bytes()).decode(),y)
        runs=sum(r['R'] for r in src);outs=inventory[y]['outs'][0];pa=float(mlb['plate_appearances'].sum())
        rpw=calculate_v1_runs_per_win(runs,outs/3,reference_season=y).runs_per_win;rep=570*rpw/pa
        op=float(mlb.select((pl.col('hits')-pl.col('doubles')-pl.col('triples')-pl.col('home_runs')+pl.col('base_on_balls')-pl.col('intentional_walks')+pl.col('hit_by_pitch')).sum()).item())
        reference=build_baserunning_reference(season=y,plate_appearances=pa,runs=runs,outs=outs,
            steal_opportunity_proxy=op,steal_attempts=float(mlb['stolen_bases'].sum()+mlb['caught_stealing'].sum()),
            stolen_bases=float(mlb['stolen_bases'].sum()),advancement_opportunities=float(advances.filter(pl.col('season')==y)['advancement_opportunities'].sum()))
        sh,_=build_steal_history(stints.filter(pl.col('season').is_between(y-2,y)))
        steal=defaultdict(list);advance=defaultdict(list)
        for r in sh:steal[r.player_id].append(r)
        for r in advances.filter(pl.col('season').is_between(y-2,y)).to_dicts():
            advance[r['player_id']].append(PlayerSeasonAdvancementSummary(r['player_id'],r['season'],r['advancement_runs'],r['advancement_opportunities']))
        year_rows=[];missing=[];pa_mismatches=[]
        for r in rows:
            pid=r['player_id'];rid=r['row_id'];expected=r['preseason_pa']
            slots=[r[f'joint_{p}'] for p in range(2,11)];opp=native_from_outs(slots,conversions[r['outer_fold']])
            running=build_current_baserunning_rates(pl.DataFrame({'player_id':[pid]}),steal[pid],advance[pid],forecast_seasons=(y+1,),reference=reference).row(0,named=True)
            components=dict(batting=10*r['candidate_rate']*expected/600,replacement=rep*expected,
                position=position_value({f'value_{p}':v for p,v in zip(range(2,11),slots)},'value'),
                stealing=running['steal_runs_per_600']*expected/600,advancement=running['advancement_runs_per_600']*expected/600,
                gidp=0.,double_play=0.,abs_challenge=0.,park=0.,league=0.)
            rates=[];profiles=[]
            for rate in model.player(pid):
                rate,profile=minor_rate(rate,model,r,hist,cells)
                if profile:profiles.append(profile)
                n=r[f"joint_{rate['context']}"] if rate['component']=='range' else opp[{'catcher_throwing':'throwing'}.get(rate['component'],rate['component'])]
                value=n*rate['runs_per_unit']/rate['rate_unit'];components[rate['component']]=components.get(rate['component'],0.)+value
                rates.append(dict(rate,projected_opportunities=n,projected_runs=value))
            observed=actual_by.get((y+1,pid));actualwar=None if observed is None else observed['WAR']
            if observed is None:
                if r['next_pa']==0 and sum(r[f'actual_{p}'] for p in range(2,11))==0:actualwar=0.
                else:missing.append(dict(player_id=pid,name=r['player_name'],PA=r['next_pa']))
            elif observed['PA']!=r['next_pa']:pa_mismatches.append(dict(player_id=pid,official=r['next_pa'],FG=observed['PA']))
            history=[actual_by[y-lag,pid] for lag in range(3) if (y-lag,pid) in actual_by]
            numerator=sum(.5**(y-h['season'])*h['WAR'] for h in history);denominator=sum(.5**(y-h['season'])*h['PA'] for h in history)
            simple_rate=600*(numerator+2.)/(denominator+600)
            a=dict(row_id=rid,player_id=pid,player_name=r['player_name'],origin_year=y,target_year=y+1,
                stage=r['stage'],age=r['age'],position=r['source_position'],origin_PA=r['pa_0'],expected_PA=expected,
                actual_PA=r['next_pa'],actual_WAR=actualwar,role_unknown=r['unknown'],
                batting_anchor=r['batting_anchor'],simple_history=expected*simple_rate/600,
                **{c+'_runs':v for c,v in components.items()},runs_per_win=rpw)
            for system in ('steamer','zips'):
                public=pub.get((system,y+1,pid));a[system]=None if public is None else public['WAR'];a[system+'_PA']=None if public is None else public['PA']
            year_rows.append(a)
            details[rid]=dict(origin=r,defense_rates=rates,minor_profiles=profiles,running=running,
                native_conversion=conversions[r['outer_fold']],origin_position_histories=[h for h in hist[pid] if y-2<=h['season']<=y],
                actual_source=observed,simple_history=history,
                source_batting=stints.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).to_dicts(),
                source_defense={k:[s for s in data if s['player_id']==pid and y-2<=s['season']<=y] for k,data in past.items()})
        assert not missing,('Unmeasured participating WAR labels',missing)
        origin_ids=set(mlb['player_id']);refrows=[r for r in year_rows if r['player_id'] in origin_ids]
        above=lambda r:math.fsum(v for k,v in r.items() if k.endswith('_runs') and k not in ['replacement_runs','park_runs','league_runs'])
        center=-sum(above(r) for r in refrows)/sum(r['expected_PA'] for r in refrows)
        for r in year_rows:
            r['league_runs']=center*r['expected_PA'];r['combined']=math.fsum(v for k,v in r.items() if k.endswith('_runs'))/rpw
        assert abs(sum(above(r)+r['league_runs'] for r in refrows))<1e-8
        excluded=mlb.filter(~pl.col('player_id').is_in(pl.Series([r['player_id'] for r in rows]).implode()))
        environments.append(dict(origin=y,runs_per_win=rpw,replacement_runs_per_PA=rep,centering_runs_per600=center*600,
            reference=asdict(reference),reference_people=len(origin_ids),reference_forecast_people=len(refrows),
            excluded_reference_people=excluded['player_id'].n_unique(),excluded_reference_PA=int(excluded['plate_appearances'].sum())))
        coverage.append(dict(target_year=y+1,rows=len(rows),missing_participant_labels=missing,PA_mismatches=pa_mismatches))
        outputs.extend(year_rows);print('Assembled',y+1,len(year_rows),'full WAR',round(sum(r['combined'] for r in year_rows),2),flush=True)
    assert len(outputs)==12432 and all(math.isfinite(r['combined']) for r in outputs)
    scores=[]
    groups=[('all',outputs),('public_steamer',[r for r in outputs if r['steamer'] is not None]),
        ('public_both',[r for r in outputs if r['steamer'] is not None and r['zips'] is not None]),
        ('actual_participants',[r for r in outputs if r['actual_PA']>0])]
    for field in ('target_year','stage','position'):
        groups += [(f'{field}_{v}',[r for r in outputs if r[field]==v]) for v in sorted({r[field] for r in outputs})]
    groups += [(f'age_{lo}_{hi}',[r for r in outputs if r['age'] is not None and lo<=r['age']<=hi]) for lo,hi in [(0,21),(22,25),(26,29),(30,34),(35,60)]]
    groups += [('age_unknown',[r for r in outputs if r['age'] is None])]
    for label,rr in groups:
        if not rr:continue
        arms=['combined','batting_anchor','simple_history']+([a for a in ('steamer','zips') if all(r[a] is not None for r in rr)])
        scores.append(dict(scope=label,scores={arm:loss(rr,arm) for arm in arms}))
    public=[r for r in outputs if r['steamer'] is not None]
    intervals=[dict(scope='all',**interval(outputs,'combined','simple_history')),
        dict(scope='all',**interval(outputs,'combined','batting_anchor')),
        dict(scope='public_steamer',**interval(public,'combined','steamer'))]
    chosen={}
    def select(r,reason):chosen.setdefault(r['row_id'],[]).append(reason)
    for pid in [804944,805811,808393,592450,665487,660271,672275,596019]:
        for r in outputs:
            if r['player_id']==pid:select(r,'fixed diagnostic')
    gain=lambda r:(r['simple_history']-r['actual_WAR'])**2-(r['combined']-r['actual_WAR'])**2
    select(max(outputs,key=gain),'largest gain vs simple');select(min(outputs,key=gain),'largest harm vs simple')
    select(max(outputs,key=lambda r:r['combined']-r['actual_WAR']),'false high')
    select(min(outputs,key=lambda r:r['combined']-r['actual_WAR']),'false low')
    select(min([r for r in outputs if 200<=r['actual_PA']<=600],key=lambda r:abs(r['combined']-r['actual_WAR'])),'ordinary participant')
    walks=[]
    for rid,reasons in chosen.items():
        r=next(r for r in outputs if r['row_id']==rid)
        peers=sorted([s for s in outputs if s['origin_year']==r['origin_year'] and s['stage']==r['stage'] and s['position']==r['position'] and s['player_id']!=r['player_id']],
            key=lambda s:(abs(s['origin_PA']-r['origin_PA']),abs(s['age']-r['age']),s['player_id']))[:3]
        walks.append(dict(reasons=reasons,primary=dict(forecast=r,detail=details[rid]),
            peers=[dict(forecast=s,detail=details[s['row_id']]) for s in peers],peer_rule='Same origin/stage/position, nearest origin PA then age/ID; no future outcomes'))
    result=OUT/'predictions.parquet';assert not result.exists();pl.DataFrame(outputs).write_parquet(result)
    walk=PUBLIC/'historical-full-value-player-walks.json.gz';assert not walk.exists()
    walk.write_bytes(gzip.compress(json.dumps(walks,default=str,allow_nan=False).encode(),mtime=0))
    write_once(PUBLIC/'historical-full-value-scores.json',dict(scores=scores,intervals=intervals,environments=environments,
        coverage=coverage,player_walkthrough_status='pending_written_review',release_approved=False,
        qualifications=['observed-context batting versus published full WAR','development assembly, not fresh holdout','public archive original timestamp qualified'],
        output_hashes={str(p):sha256_file(p) for p in [result,walk]}))
    print(json.dumps(scores[:3],indent=2),flush=True)
    for w in walks:
        r=w['primary']['forecast'];print(r['player_name'],r['target_year'],w['reasons'],round(r['combined'],2),round(r['simple_history'],2),round(r['actual_WAR'],2),flush=True)


if __name__=='__main__':main()
