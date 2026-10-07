"""Independent units, additive accounting, scores and clustered-interval replay."""
from collections import defaultdict
from pathlib import Path
import json

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections,save

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/defense-value-v12'
PUBLIC=ROOT/'reports/model-evidence/defense-value-v12'
SOURCE=ROOT/'reports/generated/defense-value-v11'


def read(p):return json.loads(p.read_text(encoding='utf8'))


def check(a,b):
    assert (a is None and b is None) or (a is not None and b is not None and abs(a-b)<1e-8),(a,b)


def pos(r,prefix):
    values=[12.5,-12.5,2.5,2.5,7.5,-7.5,2.5,-7.5]
    return sum(r[f'{prefix}_{p}']*v for p,v in zip(range(2,10),values))/4374.-17.5*r[f'{prefix}_10']/162.


def replay_score(rows,result,target):
    origins=defaultdict(list)
    for r in rows:
        if r[target] is not None:origins[r['origin_year']].append(r)
    for note in result['per_origin']:
        rs=origins[note['origin']]; actual=np.array([r[target] for r in rs]);pred=np.array([r[note['arm']] for r in rs]);e=pred-actual
        assert len(rs)==note['rows']
        for key,value in dict(rmse=float(np.sqrt(np.mean(e*e))),mae=float(np.mean(abs(e))),bias=float(e.mean()),
                              actual_total=float(actual.sum()),predicted_total=float(pred.sum())).items():check(value,note[key])
    for note in result['equal_origin']:
        parts=[r for r in result['per_origin'] if r['arm']==note['arm']]
        assert len(parts)==note['origins']
        for key in ('rmse','mae','bias'):check(sum(p[key] for p in parts)/len(parts),note['mean_origin_'+key])


def replay_interval(rows,note):
    rs=[r for r in rows if r[note['target']] is not None]
    ids=sorted({r['player_id'] for r in rs});years=sorted({r['origin_year'] for r in rs});ix={p:i for i,p in enumerate(ids)}
    denominators=[];left=[];right=[]
    for year in years:
        n=np.zeros(len(ids));a=np.zeros(len(ids));b=np.zeros(len(ids))
        for r in rs:
            if r['origin_year']!=year:continue
            i=ix[r['player_id']];assert n[i]==0;n[i]=1
            a[i]=(r[note['left']]-r[note['target']])**2;b[i]=(r[note['right']]-r[note['target']])**2
        denominators.append(n);left.append(a);right.append(b)
    n=np.array(denominators);a=np.array(left);b=np.array(right)
    base=float(np.mean(np.sqrt(a.sum(axis=1)/n.sum(axis=1))-np.sqrt(b.sum(axis=1)/n.sum(axis=1))))
    check(base,note['mean_origin_RMSE_difference']);rng=np.random.default_rng(note['seed']);results=[]
    for _ in range(note['draws']):
        samples=rng.integers(len(ids),size=len(ids));weights=np.bincount(samples,minlength=len(ids))
        den=np.sum(n*weights,axis=1)
        delta=np.sqrt(np.sum(a*weights,axis=1)/den)-np.sqrt(np.sum(b*weights,axis=1)/den)
        results.append(float(delta.mean()))
    assert np.allclose(np.quantile(results,[.025,.975]),note['interval_95'],atol=1e-8,rtol=0)


def main():
    protections();assert not (OUT/'independent-verification.json').exists()
    pre=read(OUT/'preflight.json');report=read(OUT/'report.json')
    for p,h in {**pre['hashes'],**pre['output_hashes'],**report['hashes']}.items():assert sha256_file(Path(p))==h,p
    q={r['row_id']:r for r in pl.read_parquet(ROOT/'reports/generated/defense-transition-v10/predictions.parquet').iter_rows(named=True)}
    ledger={(r['row_id'],r['channel']):r for r in pl.read_parquet(SOURCE/'reviewed-component-ledger.parquet').iter_rows(named=True)}
    bat={r['row_id']:r for r in pl.read_parquet(SOURCE/'batting-ledger.parquet').iter_rows(named=True)}
    all_channels=pl.read_parquet(OUT/'channel-predictions.parquet');byrow=defaultdict(list)
    arms=[o+'_'+s for o in ('ratio','repair','transition') for s in ('neutral','history','calibrated')]
    for r in all_channels.iter_rows(named=True):
        orig=ledger[r['row_id'],r['channel']];source=q[r['row_id']];byrow[r['row_id']].append(r)
        unit=1500. if r['channel'].startswith('range_') else 1000. if r['channel'] in ('framing','blocking') else 100.
        check(unit,r['rate_unit']);check(orig['actual_runs'],r['actual_runs'])
        rates={'neutral':0.,'history':orig['history_rate'],'calibrated':orig['history_rate']}
        if (r['channel'].startswith('range_') and orig['quality_evidence_observed'] and
            orig['range_calibration_fit_allowed'] and orig['saved_range_calibration'] is not None):
            rates['calibrated']=orig['saved_range_calibration']
        for skill,rate in rates.items():
            check(rate,r[skill+'_quality'])
            actual_n=orig['actual_native_opportunities'] if orig['actual_official_exposure']>0 else 0.
            check(None if actual_n is None else rate*actual_n/unit,r[skill+'_oracle_runs'])
            for o in ('ratio','repair','transition'):
                n=source[f'{o}_{r["channel"][-1]}'] if r['channel'].startswith('range_') else source[f'{o}_native_{r["channel"]}']
                check(n,r[o+'_predicted_opportunities']);check(rate*n/unit,r[o+'_'+skill])
    forecasts=pl.read_parquet(OUT/'predictions.parquet').to_dicts()
    assert len(forecasts)==12432 and set(byrow)==set(q)
    for r in forecasts:
        source=q[r['row_id']];b=bat[r['row_id']];channels=byrow[r['row_id']]
        assert len(channels)==12
        actual_values=[c['actual_runs'] for c in channels]
        actual_total=sum(actual_values) if all(v is not None for v in actual_values) else None
        check(actual_total,r['actual_defense']);check(pos(source,'actual'),r['actual_position_runs'])
        check(b['combined_value'],r['batting_forecast']);check(b['audit_relative_value'],r['actual_batting'])
        check(None if actual_total is None else b['audit_relative_value']+(actual_total+pos(source,'actual'))/10.,r['actual_expanded'])
        framing=next(c['actual_runs'] for c in channels if c['channel']=='framing')
        check(None if actual_total is None else r['actual_expanded']-framing/10.,r['actual_no_framing'])
        for arm in arms:
            o,skill=arm.split('_');total=sum(c[arm] for c in channels);predframing=next(c[arm] for c in channels if c['channel']=='framing')
            check(pos(source,o),r[o+'_position_runs']);check(total,r[arm+'_defense'])
            check(b['combined_value']+(total+pos(source,o))/10.,r[arm+'_expanded'])
            check(r[arm+'_expanded']-predframing/10.,r[arm+'_no_framing'])
    for metric,target in [('defense','actual_defense'),('expanded','actual_expanded'),('no_framing','actual_no_framing')]:
        for scope,rows in [('all_complete',forecasts),('actual_defenders',[r for r in forecasts if r['actual_fielding_outs']>0]),
                            ('known_history',[r for r in forecasts if r['known_quality_channels']>0])]:
            replay_score(rows,report['metrics'][metric][scope],target)
    replay_score(forecasts,report['position'],'actual_position_runs')
    for note in report['channel_scores']:
        rows=all_channels.filter(pl.col('channel')==note['channel']).to_dicts()
        rows=[r for r in rows if r['actual_runs'] is not None]
        if note['scope']=='actual_exposure':rows=[r for r in rows if r['actual_official_exposure']>0]
        if note['scope']=='measured_history':rows=[r for r in rows if r['quality_evidence_observed']]
        replay_score(rows,note['delivered'],'actual_runs')
        replay_score([r for r in rows if r['history_oracle_runs'] is not None],note['actual_count_diagnostic'],'actual_runs')
    for note in report['paired_intervals']:replay_interval(forecasts,note)
    result=dict(identities_replayed=len(forecasts),channel_rows_replayed=all_channels.height,
        all_nine_skill_opportunity_accounting_replayed=True,metrics_and_channel_scopes_replayed=True,
        all_six_person_bootstrap_intervals_replayed=True,replacement_not_added_twice=True,unknown_targets_not_zero_filled=True,
        fits=0,player_walkthrough_status='pending',protected_outcomes_used=False,forecast_or_explorer_changed=False,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'preflight.json',OUT/'report.json',OUT/'predictions.parquet',OUT/'channel-predictions.parquet']})
    for d in (OUT,PUBLIC):save(d/'independent-verification.json',result)
    protections();print(json.dumps(result))


if __name__=='__main__':main()
