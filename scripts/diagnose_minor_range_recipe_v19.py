"""Explain fixed-fit recipe confounding, reference instability and extrapolation."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import math

import numpy as np
import polars as pl

from review_minor_range_players_v19 import independent_prior,fixed_fit,FIELDS,CHANNELS,key
from verify_minor_range_talent_v19 import ROOT,OUT,PUBLIC,SOURCE,data,digest,near
from run_hitter_finite_return_baseline import protections


def main():
    protections();assert not (OUT/'recipe-diagnosis.json.gz').exists()
    walks=data(OUT/'player-walkthrough.json');report=data(OUT/'fit-report.json')
    for p,h in walks['hashes'].items():assert digest(Path(p))==h,p
    preds=pl.read_parquet(OUT/'predictions.parquet').to_dicts()
    origins=pl.read_parquet(SOURCE/'origins.parquet').filter(pl.col('position')>=3).to_dicts();om={key(r):r for r in origins}
    raw=pl.read_parquet(SOURCE/'counts.parquet').filter(pl.col('position_code').is_in(list(map(str,range(3,10))))).to_dicts();agg={}
    for r in raw:
        k=r['season'],r['player_id'],int(r['position_code'])
        if k not in om:continue
        lk=k+(r['normalized_level'],)
        if lk not in agg:agg[lk]=dict(origin_year=k[0],player_id=k[1],player_name=r['player_name'],position=k[2],level=lk[3],age=om[k]['age'],outs=0,**{f:0 for f in FIELDS})
        a=agg[lk];a['outs']+=r['fielding_outs']
        for f in FIELDS:a[f]+=r[f]
    levels=list(agg.values());extreme=min((r for r in preds if r['origin_year']==2022),key=lambda r:(r['candidate'],key(r)))
    eligible=[r for r in preds if r['origin_year']==extreme['origin_year'] and r['level']==extreme['level'] and r['position']==extreme['position'] and r['player_id']!=extreme['player_id']]
    peers=sorted(eligible,key=lambda t:(abs(t['age']-extreme['age']) if t['age'] is not None and extreme['age'] is not None else 999,
                                      abs(math.log1p(t['minor_outs'])-math.log1p(extreme['minor_outs'])),t['player_id']))[:3]
    native=pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').to_dicts()
    official=pl.read_parquet(ROOT/'reports/generated/defense-position-opportunity-v7/source.parquet').filter(pl.col('is_mlb')).to_dicts()
    supplemental=[]
    for r in (extreme,*peers):
        k=key(r);tag=r['cell_tag'];audit=data(OUT/f'cells/{tag}-preflight.json');fit=data(OUT/f'cells/{tag}-fit.json')
        f=pl.read_parquet(OUT/f'cells/{tag}-features.parquet').filter((pl.col('scope')=='test')&(pl.col('player_id')==r['player_id'])&(pl.col('position')==r['position'])).row(0,named=True)
        ts=json.loads(f['level_trace'])
        for t in ts:
            source=agg[k+(t['level'],)];assert source['outs']==t['outs']
            for field in FIELDS:assert source[field]==t['counts'][field]
            for s in t['signals']:
                check=independent_prior(levels,source,CHANNELS.index(s['channel']),audit['excluded_folds']);p=s['prior']
                assert check['scope']==p['scope'] and check['people']==p['people'];near(check['mean'],p['mean']);near(check['between_variance'],p['between_variance'])
                assert (check['strength'] is None)==(p['strength'] is None)
                if p['strength'] is not None:near(check['strength'],p['strength'])
                s['independent_reference']=check
        b=fixed_fit(fit['fits']['baseline-'+str(r['baseline_alpha'])],f['candidate_design'])
        c=fixed_fit(fit['fits']['candidate-'+str(r['candidate_alpha'])],f['candidate_design'])
        near(b['prediction'],r['baseline']);near(c['prediction'],r['candidate'])
        paths=[]
        for y in range(k[0]+1,k[0]+4):
            paths.append(dict(season=y,native=[v for v in native if v['player_id']==k[1] and v['season']==y],
                              official=[v for v in official if v['player_id']==k[1] and v['season']==y]))
        supplemental.append(dict(forecast=r,source=om[k],level_signals=ts,baseline_fit=b,candidate_fit=c,annual_paths=paths))
    canzone=next(w for w in walks['walks'] if w['key']==[2022,686527,9])
    signal=next(s for t in canzone['level_signals'] if t['level']=='COMPLEX' for s in t['signals'] if s['channel']=='glove_avoidance')
    refids=set(signal['independent_reference']['reference_player_ids'])
    reference=[r for r in levels if r['player_id'] in refids and r['origin_year'] in (2020,2021,2022) and r['position']==9 and r['level']=='COMPLEX' and r['age'] is not None and 23<=r['age']<=25 and r['chances']>0]
    by=defaultdict(list)
    for r in reference:by[r['player_id']].append(r)
    assert len(by)==signal['prior']['people']
    mean=np.mean([np.mean([(r['errors']-r['throwingErrors'])/r['chances'] for r in rs]) for rs in by.values()]);near(mean,signal['prior']['mean'])
    extremes=sorted(reference,key=lambda r:(-(r['errors']-r['throwingErrors'])/r['chances'],r['player_id']))[:8]
    cf=[]
    for r in preds:
        if r['origin_year']!=2022 or r['position']!=8 or r['quality_rate'] is None:continue
        b=r['baseline-'+str(r['candidate_alpha'])]
        cf.append(dict(player_id=r['player_id'],player_name=r['player_name'],baseline=r['baseline'],candidate=r['candidate'],actual=r['quality_rate'],
                       total_change=r['candidate']-r['baseline'],count_recipe_at_matched_penalty=r['candidate']-b,baseline_penalty_change=b-r['baseline']))
    coverage=[]
    for y in (2021,2022):
        rs=[r for r in preds if r['origin_year']==y];measured=[r for r in rs if r['quality_rate'] is not None]
        coverage.append(dict(origin=y,rows=len(rs),unseen_level_position=sum(r['support']['unseen_level_position'] for r in rs),
                             outside_feature_range=sum(any(r['support']['outside_feature_range']) for r in rs),
                             measured_outside_feature_range=sum(any(r['support']['outside_feature_range']) for r in measured),
                             minimum_candidate=min(r['candidate'] for r in rs),maximum_candidate=max(r['candidate'] for r in rs)))
    receipt=dict(status='diagnostic_no_new_fit_or_selection',supplemental_extreme_and_peers=supplemental,
                 supplement_selection='Most negative 2022 candidate over every forecast, including unmeasured; three origin-known same-level-position age/exposure peers.',
                 canzone_six_chance_signal=signal,canzone_reference_extreme_source_rows=extremes,center_field_change_accounting=cf,coverage=coverage,
                 earlier_cohort_count_correction=dict(global_measured_2022_people=62,level_people_sum=63,overlapping_person='Davis Schneider',
                                                    explanation='One person supplies measured positions with principal levels AA and Aplus. The sealed earlier prose said 63 distinct people; labels, folds and fitted membership are unchanged.'),
                 review_script_execution_corrections=['Independent walk initially counted a certified one-out native/official rounding difference as missing exposure; corrected to the sealed annual validity rule, not changed labels.',
                                                     'Local annual-missing variable shadowed missing fixed-name list; corrected before any walkthrough artifact was saved. No fits or scores rerun.'],
                 no_2026_outcomes=True,no_forecast_or_explorer_change=True,
                 hashes={str(p):digest(p) for p in (Path(__file__),OUT/'player-walkthrough.json',OUT/'fit-report.json',OUT/'predictions.parquet')})
    payload=(json.dumps(receipt,indent=2,allow_nan=False)+'\n').encode()
    for folder in (OUT,PUBLIC):
        path=folder/'recipe-diagnosis.json.gz';assert not path.exists();path.write_bytes(gzip.compress(payload,mtime=0))
    protections();print(json.dumps(dict(coverage=coverage,supplemental=[(r['forecast']['player_name'],r['forecast']['candidate'],r['forecast']['quality_status']) for r in supplemental],
                                      reference_extremes=[(r['player_name'],r['origin_year'],r['chances'],r['errors']) for r in extremes]),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
