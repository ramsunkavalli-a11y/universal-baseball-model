"""One immutable-candidate evaluation after authorized, certified target access."""
from pathlib import Path
from datetime import datetime, timezone
import json
import numpy as np
import polars as pl
from universal_baseball.storage import sha256_file
from universal_baseball.hitter_frozen_scoring import realized, score
from universal_baseball.hitter_compatible_value import labels

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05'
SOURCE=ROOT/'reports/generated/hitter-final-2026-source'
OUT=ROOT/'reports/generated/hitter-final-2026-evaluation'


def read(path):return json.loads(path.read_text(encoding='utf8'))
def write(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=True,allow_nan=False)+'\n',encoding='utf8')


def metrics(q):
    actual={c:q[c].to_numpy() for c in ['actual_pa','actual_relative_rate','actual_common_rate','actual_relative_value','actual_common_value']}
    return score(q['participation_probability'].to_numpy(),q['expected_pa'].to_numpy(),q['hitting_wins_per_600'].to_numpy(),q['batting_contribution'].to_numpy(),actual)


def main():
    assert not OUT.exists(),'Preserve the single completed-season score'
    manifest=read(PACKAGE/'freeze-manifest.json')
    assert sha256_file(PACKAGE/'freeze-manifest.json')==(PACKAGE/'freeze-manifest.sha256').read_text().strip()
    for f in manifest['files']:assert sha256_file(PACKAGE/f['path'])==f['sha256'],f['path']
    auth=read(SOURCE/'authorization-and-freeze.json');cert=read(SOURCE/'reconciliation.json')
    assert cert['status']=='completed_MLB_target_certified' and cert['zero_outcome_assignment_allowed_for_fixed_cohort_absent_ids']
    for key in ['input_hashes','output_hashes']:
        for path,sha in cert[key].items():assert sha256_file(Path(path))==sha,path
    q=pl.read_parquet(PACKAGE/'forecast.parquet');obs=pl.read_parquet(SOURCE/'actual-player-events-2026.parquet')
    assert len(q)==manifest['population']==4030 and q['player_id'].n_unique()==4030
    assert obs['player_id'].n_unique()==len(obs)==751
    events=manifest['targets']['events']; units=manifest['targets']
    environments=pl.read_parquet(SOURCE/'league-event-environments.parquet')
    o=environments.filter(pl.col('season')==2025).select(events).to_numpy()[0].astype(float)
    t=environments.filter(pl.col('season')==2026).select(events).to_numpy()[0].astype(float)
    origin=o/o.sum();target=t/t.sum()
    assert t.sum()==cert['league_pa'] and o.sum()==cert['origin_league_pa']
    assert np.isclose(units['wins_per_600_conversion'],600/(10*units['neutral_woba_scale']))
    assert units['origin_replacement_reference']==570/182926
    actual=realized(obs.select(events).to_numpy(),origin,target,units['event_values'],units['wins_per_600_conversion'],units['origin_replacement_reference'])
    # Independent existing label implementation must agree in both references.
    independent=labels(obs.select(events).to_numpy(),np.tile(origin,(len(obs),1)),np.tile(target,(len(obs),1)),np.full(len(obs),units['origin_replacement_reference']))
    for a,b in [('actual_relative_rate','relative_rate'),('actual_common_rate','common_rate'),('actual_relative_value','relative_value'),('actual_common_value','common_value')]:
        valid=actual['actual_pa']>0 if a.endswith('rate') else np.ones(len(obs),dtype=bool)
        assert np.allclose(actual[a][valid],independent[b][valid],atol=1e-10,rtol=0)
    assert np.isnan(actual['actual_relative_rate'][actual['actual_pa']==0]).all()
    obs=obs.with_columns([pl.Series(k,v) for k,v in actual.items() if k!='actual_pa'])
    full_actual=obs['actual_relative_value'].sum()
    assert np.isclose(full_actual,cert['league_pa']*units['origin_replacement_reference'],atol=1e-10)
    joined=q.join(obs,on='player_id',how='left',validate='1:1').with_columns(pl.col(['actual_pa',*events,'actual_relative_value','actual_common_value']).fill_null(0))
    assert joined.filter(pl.col('actual_pa')==0).select((pl.col('actual_relative_rate').is_null()|pl.col('actual_relative_rate').is_nan()).all()).item()
    outside=obs.join(q.select('player_id'),on='player_id',how='anti').filter(pl.col('actual_pa')>0)
    assert joined['actual_pa'].sum()+outside['actual_pa'].sum()==cert['league_pa']
    support=pl.read_parquet(PACKAGE/'profile-support.parquet')
    flags=support.group_by('row_id').agg((pl.col('training_people')<20).any().alias('sparse_profile'),(pl.col('training_people')==0).any().alias('unseen_profile'))
    joined=joined.join(flags,on='row_id',validate='1:1').with_columns(
        (pl.col('batting_contribution')-pl.col('actual_relative_value')).alias('contribution_error'),
        (pl.col('expected_pa')-pl.col('actual_pa')).alias('pa_error'),
        pl.when(pl.col('actual_pa')==0).then(pl.lit('0')).when(pl.col('actual_pa')<200).then(pl.lit('1-199')).when(pl.col('actual_pa')<400).then(pl.lit('200-399')).otherwise(pl.lit('400+')).alias('actual_pa_band'))
    groups=[]
    for field in ['stage','prior_debut','age_unknown','translated_missing','sc_tracked','sparse_profile','unseen_profile','actual_pa_band','talent_route']:
        for val in sorted(joined[field].unique().to_list()):
            sub=joined.filter(pl.col(field)==val)
            groups.append(dict(field=field,value=val,**metrics(sub)))
    bins=[]
    for low in np.arange(0,1,.1):
        sub=joined.filter((pl.col('participation_probability')>=low)&(pl.col('participation_probability')<(low+.1 if low<.9 else 1.000001)))
        if len(sub):bins.append(dict(lower=float(low),players=len(sub),mean_prediction=float(sub['participation_probability'].mean()),observed_fraction=float((sub['actual_pa']>0).mean())))
    # Player resampling: descriptive uncertainty within this fixed season only.
    rng=np.random.default_rng(20261005);boots=[]
    err=joined['contribution_error'].to_numpy();paerr=joined['pa_error'].to_numpy()
    for _ in range(2000):
        ix=rng.integers(0,len(joined),size=len(joined))
        boots.append([np.sqrt(np.mean(err[ix]**2)),np.sqrt(np.mean(paerr[ix]**2)),np.mean(err[ix])])
    limits=np.quantile(boots,[.025,.975],axis=0)
    OUT.mkdir(parents=True)
    joined.write_parquet(OUT/'scored-fixed-cohort.parquet');outside.write_parquet(OUT/'unmodeled-actual-participants.parquet')
    report=dict(status='single_frozen_evaluation_scored_player_review_pending',scored_at_utc=datetime.now(timezone.utc).isoformat(),
        forecast_sha256=sha256_file(PACKAGE/'forecast.parquet'),freeze_manifest_sha256=sha256_file(PACKAGE/'freeze-manifest.json'),
        fixed_population=4030,headline=metrics(joined),groups=groups,probability_calibration=bins,
        descriptive_player_bootstrap=dict(draws=2000,seed=20261005,claim='Within-season player resampling, not independent future-season validation.',
            primary_rmse_95=limits[:,0].tolist(),pa_rmse_95=limits[:,1].tolist(),contribution_bias_95=limits[:,2].tolist()),
        totals=dict(full_league_pa=int(cert['league_pa']),full_league_relative_contribution=float(full_actual),
            modeled_actual_pa=int(joined['actual_pa'].sum()),unmodeled_actual_pa=int(outside['actual_pa'].sum()),
            modeled_participants=int((joined['actual_pa']>0).sum()),unmodeled_participants=len(outside),
            unmodeled_relative_contribution=float(outside['actual_relative_value'].sum())),
        unmodeled_largest_pa=outside.sort('actual_pa',descending=True).head(20).to_dicts(),
        largest_overpredictions=joined.sort('contribution_error',descending=True).select('player_id','player_name','stage','expected_pa','actual_pa','hitting_wins_per_600','actual_relative_rate','batting_contribution','actual_relative_value','contribution_error').head(12).to_dicts(),
        largest_underpredictions=joined.sort('contribution_error').select('player_id','player_name','stage','expected_pa','actual_pa','hitting_wins_per_600','actual_relative_rate','batting_contribution','actual_relative_value','contribution_error').head(12).to_dicts(),
        post_result_fit_or_tuning=False,full_war_or_trade_value_claim=False,player_walkthrough_status='pending',deployment_approved=False,
        public_2026_comparison='Unavailable: no verified genuine preseason export yet. Historical comparisons are not a same-season benchmark.',
        legacy_comparison='Not scored: legacy partial WAR is not this target; no mislabeled comparison.',
        source_qualifications=['Retrospectively assembled outcome-blinded candidate, not demonstrably published January forecast.','Retrospective source revisions qualified in immutable freeze.','Unmodeled foreign entrants and later entrants are missing forecasts, not model zeroes.','Lower-minors, unknown age and sparse profiles retained.','Conditional outcome is future MLB hitting only when a player actually plays.'],
        scorer_pre_execution_correction='The first independent-label assertion stopped before writing or exposing scores: official source includes zero-PA rows, whose rate is unobserved NaN, whereas legacy helper uses a zero placeholder. Corrected comparison checks rates only for actual participants and delivery for everyone; neither source nor forecast changed.',
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),ROOT/'src/universal_baseball/hitter_frozen_scoring.py',SOURCE/'authorization-and-freeze.json',SOURCE/'reconciliation.json',PACKAGE/'freeze-manifest.json']},
        output_hashes={str(p):sha256_file(p) for p in [OUT/'scored-fixed-cohort.parquet',OUT/'unmodeled-actual-participants.parquet']})
    write(OUT/'score-report.json',report)
    print(json.dumps(dict(headline=report['headline'],totals=report['totals'],player_review='pending'),allow_nan=False),flush=True)


if __name__=='__main__':main()
