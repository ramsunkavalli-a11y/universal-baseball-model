"""Replay the bias diagnostic without its decomposition or summary functions."""
from collections import defaultdict
from pathlib import Path
import gzip
import json
import math

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from source_defensive_positions_v2 import embedded
from run_hitter_finite_return_baseline import protections

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'reports/model-evidence/defense-component-bias-v27'


def read(path):
    with gzip.open(path,'rt',encoding='utf8') as stream:return json.load(stream)


def eq(a,b):
    assert (a is None and b is None) or (a is not None and b is not None and math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-10)),(a,b)


def main():
    dest=PUBLIC/'independent-review.json.gz';assert not dest.exists()
    protections();pre=read(PUBLIC/'preflight.json.gz');report=read(PUBLIC/'report.json.gz');walks=read(PUBLIC/'player-walks.json.gz')
    for p,h in {**pre['source_hashes'],**pre['protected_hashes']}.items():assert sha256_file(Path(p))==h,p
    channels=pl.read_parquet(ROOT/'reports/generated/defense-value-v12/channel-predictions.parquet').to_dicts()
    values=pl.read_parquet(ROOT/'reports/generated/defense-reference-history-v26/value-predictions.parquet').to_dicts()
    complete={r['row_id'] for r in values if r['actual_defense'] is not None};assert len(complete)==pre['complete_rows']
    bridges=pl.read_parquet(ROOT/'reports/generated/defense-transition-v10/predictions.parquet').to_dicts()
    bridge={r['row_id']:r for r in bridges}
    by={(r['row_id'],r['channel']):r for r in channels};assert len(by)==149184
    for s in report['scopes']:
        rs=[r for r in channels if r['origin_year']==s['origin'] and r['channel']==s['channel']]
        if s['scope']=='complete':rs=[r for r in rs if r['row_id'] in complete]
        elif s['scope']=='actual_defenders':rs=[r for r in rs if r['actual_official_exposure']>0]
        elif s['scope']=='measured_history':rs=[r for r in rs if r['quality_evidence_observed']]
        elif s['scope']=='unknown_history':rs=[r for r in rs if not r['quality_evidence_observed']]
        else:assert s['scope']=='all'
        eq(len(rs),s['rows']);known=[r for r in rs if r['actual_runs'] is not None]
        eq(len(known),s['measured']);eq(len(rs)-len(known),s['unknown'])
        eq(sum(r['actual_runs'] for r in known),s['measured_actual_runs'])
        eq(sum(r['repair_history'] for r in known),s['measured_predicted_runs'])
        eq(sum(r['repair_history'] for r in rs if r['actual_runs'] is None),s['unknown_forecast_runs'])
        pairs=[]
        for r in known:
            n=0 if r['actual_official_exposure']==0 else r['actual_native_opportunities']
            if n is not None:pairs.append((r,n*r['history_rate']/r['rate_unit']))
        eq(len(pairs),s['native_denominator_measured'])
        eq(len(known)-len(pairs),s['native_denominator_missing'])
        for field,computed in [('decomposition_actual',sum(r['actual_runs'] for r,o in pairs)),
                              ('decomposition_forecast',sum(r['repair_history'] for r,o in pairs)),
                              ('decomposition_oracle',sum(o for r,o in pairs)),
                              ('opportunity_error',sum(r['repair_history']-o for r,o in pairs)),
                              ('rate_error',sum(o-r['actual_runs'] for r,o in pairs)),
                              ('actual_official_exposure',sum(r['actual_official_exposure'] for r in rs)),
                              ('projected_native_opportunities',sum(r['repair_predicted_opportunities'] for r in rs)),
                              ('actual_native_opportunities',sum(0 if r['actual_official_exposure']==0 else r['actual_native_opportunities'] for r,o in pairs))]:eq(computed,s[field])
        for label,errors in [('forecast',[r['repair_history']-r['actual_runs'] for r,o in pairs]),
                             ('actual_opportunity',[o-r['actual_runs'] for r,o in pairs])]:
            eq(None if not errors else np.sqrt(np.mean(np.square(errors))),s[label+'_rmse'])
            eq(None if not errors else np.mean(np.abs(errors)),s[label+'_mae'])
    annual=defaultdict(list);rawhashes={};raw_verified=0
    native=pl.read_parquet(ROOT/'reports/generated/defense-native-range-v3/component-ledger.parquet').to_dicts()
    frames=pl.read_parquet(ROOT/'reports/generated/catcher-native-opportunity-v3/modern/framing-annual.parquet').to_dicts()
    for year in range(2016,2026):
        path=ROOT/f'reports/generated/defensive-talent-position-v2/position-{year}.response'
        raw={(r['id'],r['pos_id']):r for r in embedded(path.read_text(encoding='utf8'),'data')};rawhashes[str(path)]=sha256_file(path)
        for r in native:
            if r['season']!=year or r['position']!=3:continue
            source=raw[r['player_id'],3];eq(source['range_runs'],r['range_runs']);eq(source['outs_total'],r['native_outs']);raw_verified+=1
            if r['range_valid']:annual['range_3'].append((r['season'],r['player_id'],r['native_outs'],r['range_runs']))
    for year in range(2018,2026):
        path=ROOT/f'reports/generated/catcher-native-opportunity-v3/modern/framing-{year}.response'
        text=path.read_text(encoding='utf8');params=embedded(text,'serverParams')
        assert int(params['seasonStart'])==int(params['seasonEnd'])==year and params['minPitches']==1
        raw={r['id']:r for r in embedded(text,'data')};rawhashes[str(path)]=sha256_file(path)
        for r in frames:
            if r['season']!=year:continue
            source=raw[r['player_id']];eq(source['pitches'],r['pitches']);eq(source['pitches_shadow'],r['shadow_pitches']);eq(source['rv_tot'],r['framing_runs']);raw_verified+=1
            assert r['exposure_valid'] and r['framing_measurement_valid']
            annual['framing'].append((r['season'],r['player_id'],r['pitches'],r['framing_runs']))
    for s in report['qualified_native_annual']:
        rs=[r for r in annual[s['channel']] if r[0]==s['season']];unit=1500 if s['channel']=='range_3' else 1000
        eq(len(rs),s['people']);eq(sum(r[2] for r in rs),s['opportunities']);eq(sum(r[3] for r in rs),s['runs']);eq(unit*s['runs']/s['opportunities'],s['rate'])
    refs={};reference_channel_assignments=[]
    for index,s in enumerate(report['held_player_references']):
        y=s['origin_year'];fold=s['excluded_fold']
        # Original descriptive reference records omit the channel key. Identify
        # it by independent source denominator AND numerator, not list order.
        candidates=[]
        for ch,source in annual.items():
            parts=[r for r in source if y-2<=r[0]<=y and r[1]%5!=fold]
            n=sum(r[2]*2**(r[0]-y) for r in parts);runs=sum(r[3]*2**(r[0]-y) for r in parts)
            if math.isclose(n,s['opportunities'],abs_tol=1e-8) and math.isclose(runs,s['runs'],abs_tol=1e-8):candidates.append(ch)
        assert len(candidates)==1,(index,candidates)
        ch=candidates[0];unit=1500 if ch=='range_3' else 1000
        reference_channel_assignments.append(dict(record_index=index,channel=ch,identified_by='Independent source opportunities and runs; unique match'))
        rs=[r for r in annual[ch] if y-2<=r[0]<=y and r[1]%5!=fold]
        n=sum(r[2]*2**(r[0]-y) for r in rs);runs=sum(r[3]*2**(r[0]-y) for r in rs)
        eq(n,s['opportunities']);eq(runs,s['runs']);eq(unit*runs/n,s['rate']);eq(len({r[1] for r in rs}),s['people'])
        assert max(r[0] for r in rs)==s['max_source_year']<=y;refs[y,fold,ch]=s
    history_count=0
    for r in channels:
        if r['channel'] not in annual:continue
        y=r['origin_year'];ch=r['channel'];prior=3000 if ch=='range_3' else 6000;unit=1500 if ch=='range_3' else 1000
        rs=[s for s in annual[ch] if s[1]==r['player_id'] and y-2<=s[0]<=y]
        n=sum(s[2]*2**(s[0]-y) for s in rs);runs=sum(s[3]*2**(s[0]-y) for s in rs)
        eq(n,r['history_opportunities']);eq(n/(n+prior),r['reliability']);eq(unit*runs/(n+prior),r['history_rate'])
        assert r['quality_evidence_observed']==(n>0);history_count+=1
    record_count=0
    for g in walks['groups']:
        focal=bridge[g['records'][0]['row_id']]
        pool=[r for r in bridges if r['origin_year']==focal['origin_year'] and r['stage']==focal['stage']
              and r['repertoire_primary_role']==focal['repertoire_primary_role'] and r['player_id']!=focal['player_id']]
        peers=sorted(pool,key=lambda p:(abs((p['age'] if p['age'] is not None else 27)-(focal['age'] if focal['age'] is not None else 27)),abs(p['role_defensive_sample']-focal['role_defensive_sample']),p['row_id']))[:3]
        assert [r['row_id'] for r in g['records']]==[focal['row_id'],*[p['row_id'] for p in peers]]
        for w in g['records']:
            r=by[w['row_id'],w['channel']];record_count+=1
            assert w['source_history']==sorted(w['source_history'],key=lambda s:s['season'])
            eq(sum(s['audit_opportunities']*2**(s['season']-w['origin_year']) for s in w['source_history']),w['weighted_opportunities'])
            eq(sum(s['audit_runs']*2**(s['season']-w['origin_year']) for s in w['source_history']),w['weighted_runs'])
            eq(w['weighted_runs']*w['unit']/(w['prior_opportunities']+w['weighted_opportunities']),w['history_rate'])
            for a,b in [('history_rate','history_rate'),('forecast_runs','repair_history'),('forecast_opportunities','repair_predicted_opportunities'),('actual_runs','actual_runs')]:eq(w[a],r[b])
            eq(w['actual_opportunity_runs'],r['history_oracle_runs'])
            assert w['origin_held_person_reference']==refs[w['origin_year'],w['player_id']%5,w['channel']]
    for p,h in pre['protected_hashes'].items():assert sha256_file(Path(p))==h
    note=dict(execution_integrity_pass=True,fits=0,source_histories_replayed=history_count,
        scopes_replayed=len(report['scopes']),raw_native_records_verified=raw_verified,player_records_replayed=record_count,
        origin_blind_peers_verified=True,source_hashes=rawhashes,
        diagnostic_not_forecast_improvement=True,protected_forecast_and_explorer_unchanged=True,
        reference_schema_correction='Original descriptive reference entries omit channel. This additive receipt uniquely identifies each from independent native counts and runs; original evidence retained.',
        reference_channel_assignments=reference_channel_assignments,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),PUBLIC/'preflight.json.gz',PUBLIC/'report.json.gz',PUBLIC/'player-walks.json.gz']})
    with gzip.open(dest,'wt',encoding='utf8') as stream:json.dump(note,stream,allow_nan=False,separators=(',',':'))
    print(json.dumps({k:v for k,v in note.items() if k not in ('source_hashes','hashes','reference_channel_assignments')}))


if __name__=='__main__':main()
