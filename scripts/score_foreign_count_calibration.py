"""Lock scorer before evaluation; no tuning or 2026 source access."""
from collections import defaultdict
import json
from pathlib import Path

import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from run_foreign_count_calibration import ROOT, GEN, OUT, PRIOR, REP, SOURCES, read, save, verify
from prepare_hitter_overseas_integration import annual_labels
from universal_baseball.hitter_compatible_value import labels, UNIT
from universal_baseball.hitter_direct_events import convert, proper_losses
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.storage import sha256_file


def weights(frame, *, active=False):
    y = frame['origin_year'].to_numpy()
    years = np.unique(y)
    exposure = frame['next_pa'].to_numpy().astype(float) if active else np.ones(len(y))
    return np.array([n/(len(years)*exposure[y == year].sum()) for n, year in zip(exposure, y, strict=True)])


def metrics(frame, arm):
    if not len(frame):
        return dict(rows=0)
    w = weights(frame)
    v = frame[arm+'_value'].to_numpy(); a = frame['actual_relative_value'].to_numpy()
    active = frame.filter(pl.col('next_pa') > 0)
    rate_mse = float(weights(active, active=True) @ ((active[arm+'_rate']-active['actual_relative_rate']).to_numpy()**2)) if len(active) else None
    return dict(rows=len(frame), people=frame['player_id'].n_unique(), active_rows=len(active),
        predicted_PA=float(frame['fixed_pa'].sum()), actual_PA=float(frame['next_pa'].sum()),
        expected_contribution=float(v.sum()), actual_contribution=float(a.sum()),
        value_rmse=float(np.sqrt(w @ ((v-a)**2))), value_mae=float(w @ abs(v-a)),
        value_bias=float(w @ (v-a)), rate_rmse=float(np.sqrt(rate_mse)) if rate_mse is not None else None)


def interval(frame, *, rate=False, other='baseline'):
    frame = frame.filter(pl.col('next_pa') > 0) if rate else frame
    if not len(frame):
        return None
    suffix = '_rate' if rate else '_value'; actual = 'actual_relative_rate' if rate else 'actual_relative_value'
    delta = (frame['candidate'+suffix]-frame[actual]).to_numpy()**2 - (frame[other+suffix]-frame[actual]).to_numpy()**2
    w = weights(frame, active=rate)
    ids, ix = np.unique(frame['player_id'].to_numpy(), return_inverse=True)
    total = np.zeros(len(ids)); den = np.zeros(len(ids))
    np.add.at(total, ix, w*delta); np.add.at(den, ix, w)
    rng = np.random.default_rng(84); draws = []
    for i in range(2000):
        count = np.bincount(rng.integers(len(ids), size=len(ids)), minlength=len(ids))
        z = count @ total / (count @ den)
        if i < 10 and not np.isclose(z, np.sum(w*count[ix]*delta)/np.sum(w*count[ix]), atol=1e-12):
            raise ValueError('Cluster/row uncertainty disagreement')
        draws.append(z)
    return dict(change=float(w@delta), lower=float(np.quantile(draws, .025)), upper=float(np.quantile(draws, .975)),
                fixed_original_origin_weights=True, nominal_exposed_development_interval=True)


def categorical(frame, arm):
    g = frame.filter((pl.col('next_pa') > 0) & pl.col('component_supported'))
    if not len(g):
        return dict(rows=0)
    p = np.array(g[arm+'_probability'].to_list()); c = np.array(g['actual_events'].to_list())
    ll, br = proper_losses(p, c); w = weights(g, active=True)
    pred = w @ p; actual = w @ (c / c.sum(1, keepdims=True))
    return dict(rows=len(g), people=g['player_id'].n_unique(), actual_PA=int(g['next_pa'].sum()),
        logloss=float(w@ll), one_hot_brier=float(w@br), predicted_frequencies=pred.tolist(), actual_frequencies=actual.tolist(),
        K_rmse=float(np.sqrt(w@((p[:,1]-c[:,1]/c.sum(1))**2))),
        HR_rmse=float(np.sqrt(w@((p[:,7]-c[:,7]/c.sum(1))**2))))


def main():
    if (OUT/'scores.json').exists() or (OUT/'evaluation-seal.json').exists():
        raise ValueError('Inspect prior execution; do not rescore')
    pre = read(OUT/'preflight.json'); verify(pre['source_hashes'])
    fit = read(OUT/'fit-report.json'); verify(fit['hashes'])
    if sha256_file(OUT/'preflight.json') != fit['preflight_sha256']:
        raise ValueError('Changed preflight')
    save('evaluation-seal.json', dict(scorer_sha256=sha256_file(Path(__file__)),
        preflight_sha256=fit['preflight_sha256'], fit_report_sha256=sha256_file(OUT/'fit-report.json'),
        scores_not_yet_opened=True, target_year_maximum=2025))
    q = pl.read_parquet(REP/'predictions.parquet').sort('row_id')
    new = {(p['candidate_key'],p['outer_fold']):p for p in read(OUT/'profiles.json')['profiles']}
    old = {(p['candidate_key'],p['outer_fold']):p for p in read(PRIOR/'profiles.json')['profiles']}
    models = {m['fit_key']:m for m in [read(OUT/f'fit-{c["origin"]}-{c["fold"]}.json') for c in pre['cells']]}
    route = {r['row_id']:r for r in pre['routes']}
    actual, env = annual_labels(pl.read_parquet(GEN/'practical-hitter-v31/dated-stints.parquet'))
    counts = np.array([actual.get((r['target_year'],r['player_id']),np.zeros(8)) for r in q.to_dicts()])
    lab = labels(counts,np.array([env[y] for y in q['origin_year']]),np.array([env[y] for y in q['target_year']]),q['origin_replacement_rate'].to_numpy())
    if not np.array_equal(counts.sum(1),q['next_pa']) or not np.allclose(lab['relative_rate'],q['actual_relative_rate'],atol=1e-10) or not np.allclose(lab['relative_value'],q['actual_relative_value'],atol=1e-10):
        raise ValueError('Independent target reconstruction failed')
    rows=[]; probability_replays=0
    for i,r in enumerate(q.to_dicts()):
        key=f'{r["origin_year"]}:{r["player_id"]}'; p=new.get((key,r['outer_fold'])); prior=old.get((key,r['outer_fold']))
        s=route[r['row_id']]; addition=r['source_addition']; arm='domestic' if addition else 'current'
        base=r[arm+'_rate']; pa=r[arm+'_pa']; value=r[arm+'_value']
        if not np.isclose(value,pa*(base/600+r['origin_replacement_rate']),atol=1e-10):
            raise ValueError('Anchor units differ from defined PA product')
        supported=p is not None and not p['missing_translation']
        if supported != s['supported']:
            raise ValueError('Support changed after calibration')
        if p:
            m=models[p['fit_key']]; aggregated=np.zeros(8); mass=0.
            for piece in p['leagues']:
                if not piece['mover_people']:
                    continue
                z=np.log(p['MLB_reference'])+np.array(m['domestic_intercepts'])+np.array(m['foreign_offsets'][piece['league']])+np.array(m['domestic_slopes'])*np.array(piece['source_relative_clr'])
                prob=np.exp(z-z.max()); prob/=prob.sum()
                if not np.allclose(prob,piece['translated_probability'],atol=1e-12,rtol=0):
                    raise ValueError('Coefficient/profile replay failed')
                n=piece['recency_weighted_exposure']; aggregated+=n*prob; mass+=n; probability_replays+=1
            if mass and not np.allclose(aggregated/mass,p['translated_probability'],atol=1e-12,rtol=0):
                raise ValueError('League pooling replay failed')
        translated,terms=convert(p['translated_probability'],p['MLB_reference']) if supported else (None,None)
        oldrate,_=convert(prior['translated_probability'],prior['MLB_reference']) if supported else (None,None)
        used=s['eligible'] and supported
        candidate=float(translated) if used else base
        borrowed=float(oldrate) if used else base
        rows.append(dict(row_id=r['row_id'],player_id=r['player_id'],player_name=r['player_name'],
            origin_year=r['origin_year'],target_year=r['target_year'],outer_fold=r['outer_fold'],stage=r['stage'],
            prior_debut=r['prior_debut'],source_addition=addition,age=r['age'],pa_0=r['pa_0'],
            next_pa=r['next_pa'],actual_relative_rate=r['actual_relative_rate'],actual_relative_value=r['actual_relative_value'],
            actual_common_rate=float(lab['common_rate'][i]),actual_events=counts[i].tolist(),
            fixed_p=r[arm+'_p'],fixed_conditional_pa=r[arm+'_conditional_pa'],fixed_pa=pa,
            baseline_rate=base,baseline_value=value,baseline_kind='prior_dated_domestic_addition' if addition else 'unchanged_current',
            candidate_rate=candidate,candidate_value=pa*(candidate/600+r['origin_replacement_rate']),
            borrowed_rate=borrowed,borrowed_value=pa*(borrowed/600+r['origin_replacement_rate']),
            direct_rate=float(translated) if supported else None,direct_terms=terms.tolist() if supported else None,
            origin_replacement_rate=r['origin_replacement_rate'],route_eligible=s['eligible'],route_used=used,
            source_present=s['foreign_source_present'],component_supported=supported,
            recent_foreign_pa=s['recent_foreign_pa'],dated_hitter_hint=s['dated_hitter_hint'],
            latest_foreign=s['latest_substantial_foreign'],latest_domestic=s['latest_substantial_domestic'],
            same_year_ambiguous=s['same_year_ambiguous'],
            count_probability=p['translated_probability'] if supported else None,
            borrowed_probability=prior['translated_probability'] if supported else None,
            profile_key=key if p else None))
    out=pl.DataFrame(rows); out.write_parquet(OUT/'predictions.parquet')
    unchanged=out.filter(~pl.col('route_used'))
    if not np.array_equal(unchanged['baseline_rate'],unchanged['candidate_rate']) or not np.allclose(unchanged['baseline_value'],unchanged['candidate_value'],atol=1e-12):
        raise ValueError('Unrouted forecast changed')
    original=out.filter(~pl.col('source_addition')); added=out.filter(pl.col('source_addition'))
    scopes=[('original_all',original),('original_route_eligible',original.filter(pl.col('route_eligible'))),
        ('original_foreign_sources',original.filter(pl.col('source_present'))),('additions',added),
        ('original_fresh_newcomers',original.filter(pl.col('route_eligible')&(pl.col('prior_debut')==0))),
        ('original_fresh_returners',original.filter(pl.col('route_eligible')&(pl.col('prior_debut')>0))),
        ('original_route_nonarrivals',original.filter(pl.col('route_eligible')&(pl.col('next_pa')==0))),
        ('original_upper_never',original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('original_lower_never',original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors')))]
    scopes += [(f'origin_{y}_route',original.filter((pl.col('origin_year')==y)&pl.col('route_eligible'))) for y in sorted(original['origin_year'].unique())]
    scores=[]
    with threadpool_limits(limits=2):
        for name,g in scopes:
            scores.append(dict(scope=name,metrics={a:metrics(g,a) for a in ['baseline','borrowed','candidate']},
                candidate_vs_baseline_value_MSE_interval=interval(g),candidate_vs_baseline_rate_MSE_interval=interval(g,rate=True),
                categorical={a:categorical(g,a) for a in ['borrowed','count']}))
    public=original.join(pl.read_parquet(GEN/'hitter-minor-statcast-precision/scored-predictions.parquet').select(
        'row_id','steamer_index','zips_index','steamer_rate','common_zips_rate'),on='row_id',validate='1:1').filter(
            (pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    if len(public)!=2627:
        raise ValueError('Changed matched public scope')
    active=public.filter(pl.col('next_pa')>0); w=weights(active,active=True)
    public_report=dict(rows=len(public),routed_rows=public['route_used'].sum(),
        common_reference_rate_RMSE={a:float(np.sqrt(w@((active[col]-active['actual_common_rate']).to_numpy()**2)))
            for a,col in [('current','baseline_rate'),('candidate','candidate_rate'),('steamer','steamer_rate'),('zips','common_zips_rate')]},
        qualifier='Snapshot, park and environment differences remain; ZiPS PA not certified; not a new public-system superiority claim')
    save('scores.json',dict(scopes=scores,matched_public=public_report,probability_replays=probability_replays,
        forecasts=len(out),original_forecasts=len(original),source_additions=len(added),
        route_eligible=out['route_eligible'].sum(),route_used=out['route_used'].sum(),
        source_role_hints=out.filter(pl.col('route_eligible')).group_by('dated_hitter_hint').len().to_dicts(),
        scores_provisional=True,player_walkthrough_status='pending',new_opportunity_fits=0,
        deployment_approved=False,frozen_2026_forecasts_changed=False,
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [Path(__file__),OUT/'predictions.parquet',OUT/'profiles.json',OUT/'preflight.json',OUT/'fit-report.json',OUT/'evaluation-seal.json']}))
    print(json.dumps(dict(primary=scores[1],original_all=scores[0]['metrics'],public=public_report,
                         player_walkthrough_status='pending')),flush=True)


if __name__=='__main__':
    main()
