"""Fixed construction cases, both error tails and origin-selected peer walks."""
from pathlib import Path
from types import SimpleNamespace
import json
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
from replay_hitter_production_2026 import independent_matrix
from score_hitter_final_2026 import PACKAGE,ROOT,OUT,read,write


def main():
    assert not (OUT/'player-walks.json').exists(),'Preserve final review'
    score=read(OUT/'score-report.json');q=pl.read_parquet(OUT/'scored-fixed-cohort.parquet')
    assert sha256_file(OUT/'scored-fixed-cohort.parquet')==score['output_hashes'][str(OUT/'scored-fixed-cohort.parquet')]
    m=read(PACKAGE/'freeze-manifest.json')
    for f in m['files']:assert sha256_file(PACKAGE/f['path'])==f['sha256']
    old=read(PACKAGE/'pre-freeze-player-walks.json')['walks']
    pre=read(PACKAGE/'preflight.json');support=pl.read_parquet(PACKAGE/'profile-support.parquet')
    source_path=ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    # Verify external count source against the sealed preflight, not a new version.
    source_review_path=ROOT/'reports/generated/hitter-base-inputs-2025-reviewed/review.json'
    assert sha256_file(source_review_path)==pre['input_hashes'][str(source_review_path)]
    assert sha256_file(source_path)==read(source_review_path)['input_hashes'][str(source_path)]
    counts=pl.read_parquet(source_path).filter(pl.col('season')<=2025)
    reasons={w['player_id']:['Preserved pre-freeze construction case or origin-selected peer'] for w in old}
    def choose(f,reason):
        for pid in f['player_id']:reasons.setdefault(pid,[]).append(reason)
    choose(q.sort('contribution_error',descending=True).head(6),'Six largest fixed-cohort overpredictions, outcome-selected diagnostic')
    choose(q.sort('contribution_error').head(6),'Six largest fixed-cohort underpredictions, outcome-selected diagnostic')
    choose(q.filter((pl.col('stage')=='Upper minors')&(pl.col('actual_pa')==0)).sort('batting_contribution',descending=True).head(2),'Two largest upper-minors non-arrival forecasts, outcome-selected diagnostic')
    for stage in ['Current MLB','Upper minors']:
        choose(q.filter((pl.col('stage')==stage)&(pl.col('actual_pa')>=200)).with_columns(pl.col('contribution_error').abs().alias('ae')).sort('ae','player_id').head(1),f'Ordinary {stage} case: smallest absolute delivery error among actual 200+ PA')
    focal=list(reasons);peers={}
    by_id={r['player_id']:r for r in q.iter_rows(named=True)}
    for pid in focal:
        r=by_id[pid]
        eligible=q.filter((pl.col('player_id')!=pid)&(pl.col('stage')==r['stage'])&(pl.col('prior_debut')==r['prior_debut'])&(pl.col('age_unknown')==r['age_unknown']))
        # No 2026 labels in this distance or membership rule.
        distances=[]
        for e in eligible.iter_rows(named=True):
            d=((e['age']-r['age'])/5)**2+((e['pa_0']-r['pa_0'])/600)**2+((e['minor_pa_0']-r['minor_pa_0'])/600)**2+((e['quality_0']-r['quality_0']))**2+((e['career_mlb_observed_pa']-r['career_mlb_observed_pa'])/6000)**2
            d+=int(e['source_position']!=r['source_position'])+int(e['sc_tracked']!=r['sc_tracked'])
            distances.append((float(d),e['player_id']))
        chosen=sorted(distances)[:2]
        peers[pid]=[dict(player_id=p,distance=d) for d,p in chosen]
        for _,p in chosen:reasons.setdefault(p,[]).append(f'Origin-known nearest peer of {pid}')
    write(OUT/'walk-selection.json',dict(focal_ids=focal,reasons={str(k):v for k,v in reasons.items()},peers={str(k):v for k,v in peers.items()},
        rule='Preserve all 37 pre-freeze walks; six largest errors each way; two upper-minors non-arrivals; ordinary cases; two peers each using only origin age, PA, quality, career exposure, position and tracking within same stage/debut/known-age state.',
        diagnostics_not_independent_confirmation=True,benchmark_categories='No matched 2026 public forecast: improvement/deterioration categories unavailable, not fabricated.'))
    rows=[]
    with threadpool_limits(limits=2):
        for fold in range(5):
            fq=q.filter(pl.col('outer_fold')==fold).sort('row_id')
            models={h['head']:joblib.load(PACKAGE/h['path']) for h in m['models'] if h['fold']==fold}
            matrices={head:independent_matrix(fq,pre['features'][head]) if head.startswith('rate') else fq.select(pre['features'][head]).to_numpy() for head in models}
            for i,r in enumerate(fq.iter_rows(named=True)):
                pid=r['player_id']
                if pid not in reasons:continue
                head='rate_prospect' if not r['prior_debut'] else 'rate_tracking' if r['sc_tracked'] else 'rate_numeric'
                names=pre['features'][head];model=models[head];x=matrices[head][i]
                terms=x*np.asarray(model.coef_)
                assert np.isclose(float(model.intercept_)+terms.sum(),r['hitting_wins_per_600'],atol=1e-10,rtol=0)
                cls=models['participation'];proxy=SimpleNamespace(_baseline_prediction=cls._baseline_prediction,_predictors=cls._predictors,predict=cls.decision_function)
                pt=trace(proxy,matrices['participation'][i],pre['features']['participation'])
                assert np.isclose(1/(1+np.exp(-pt['raw_prediction'])),r['raw_participation'],atol=1e-10,rtol=0)
                ct=trace(models['conditional_pa'],matrices['conditional_pa'][i],pre['features']['conditional_pa'])
                assert np.isclose(ct['raw_prediction'],r['raw_conditional_pa'],atol=1e-8,rtol=0)
                history=counts.filter((pl.col('player_id')==pid)&pl.col('season').is_between(2023,2025)).sort('season','bucket')
                for k in range(3):
                    h=history.filter(pl.col('season')==2025-k);mlb=h.filter(pl.col('bucket')=='MLB')['plate_appearances'].sum()
                    assert mlb==r[f'pa_{k}'] and h['plate_appearances'].sum()-mlb==r[f'minor_pa_{k}']
                for bucket in ['MLB','AAA','AA','DSL']:
                    h=history.filter(pl.col('bucket')==bucket)
                    assert np.isclose(sum((1.,.8,.6)[2025-v['season']]*v['plate_appearances'] for v in h.iter_rows(named=True)),r[f'pooled_{bucket}_pa'],atol=1e-10)
                career=counts.filter((pl.col('player_id')==pid)&(pl.col('bucket')=='MLB'))['plate_appearances'].sum()
                assert r['career_mlb_observed_pa']==career
                workload=(r['expected_pa']-r['actual_pa'])*(r['hitting_wins_per_600']/600+m['targets']['origin_replacement_reference'])
                performance=r['actual_pa']*(r['hitting_wins_per_600']-r['actual_relative_rate'])/600 if r['actual_pa'] else 0.
                assert np.isclose(workload+performance,r['contribution_error'],atol=1e-10)
                actual_support=support.filter(pl.col('row_id')==r['row_id']).to_dicts()
                notes=[]
                if r['sparse_profile']:notes.append('Sparse actual-head profile warning remains; correct arithmetic does not establish reliable extrapolation.')
                if r['unseen_profile']:notes.append('At least one refined actual-head profile unseen in training.')
                if r['translated_missing']:notes.append('No supported recent level translation; prior and missingness are explicit, not zero MLB ability.')
                if not r['actual_pa']:notes.append('No MLB participation: delivered outcome zero; batting talent remains unobserved, so this does not refute eventual ability.')
                if r['prior_debut']==0 and r['actual_pa']>=400:notes.append('Never-debut full-season participant: fixed next-year mean underestimation can reflect both chance of arrival and workload once arriving; check each separately.')
                if abs(performance)>abs(workload):notes.append('This delivered miss is more associated arithmetically with observed hitting rate than PA; no causal explanation or hindsight feature claim.')
                else:notes.append('This delivered miss is more associated arithmetically with PA than observed hitting rate; no injury/job cause established from these counts.')
                columns=['age','age_unknown','stage','prior_debut','elapsed','source_position','on_40man','career_mlb_observed_pa','pa_0','pa_1','pa_2','minor_pa_0','minor_pa_1','minor_pa_2','quality_0','quality_1','quality_2','draft_known','draft_rank','scout_listed_0','scout_rank_score_0','sc_tracked','translated_reliability','translation_supported_pa','translation_total_pa','translation_buckets','translated_missing','reported_retired','hard_unavailable']
                rows.append(dict(player_id=pid,name=r['player_name'],fold=fold,selection=reasons[pid],origin_peers=peers.get(pid,[]),source_history=history.to_dicts(),
                    origin_inputs={c:r[c] for c in columns},all_actual_rate_inputs={c:r[c] for c in names},
                    intermediates={c:r[c] for c in ['raw_participation','participation_override','participation_probability','raw_conditional_pa','conditional_pa','expected_pa','hitting_wins_per_600','batting_contribution','talent_route']},
                    actual={c:r[c] for c in ['actual_pa','actual_relative_rate','actual_common_rate','actual_relative_value','actual_common_value','other','K','UBB','HBP','1B','2B','3B','HR']},
                    contribution_error=r['contribution_error'],error_accounting=dict(workload_at_frozen_rate=workload,performance_at_actual_pa=performance,identity_verified=True,not_causal=True),
                    support=actual_support,participation_trace=pt,conditional_pa_trace=ct,
                    rate_intercept=float(model.intercept_),rate_terms=[dict(feature=names[j],raw_input=r[names[j]],scaled_input=float(x[j]),coefficient=float(model.coef_[j]),contribution=float(terms[j])) for j in np.argsort(-abs(terms))],
                    baseball_review_notes=notes,pre_freeze_walk=next((w for w in old if w['player_id']==pid),None)))
    assert set(reasons)=={w['player_id'] for w in rows}
    # JSON cannot describe unobserved NaN as a number; make it explicit null.
    for w in rows:
        for k,v in w['actual'].items():
            if isinstance(v,float) and not np.isfinite(v):w['actual'][k]=None
    write(OUT/'player-walks.json',dict(walks=rows,all_sources_and_saved_fit_calculations_replayed=True,selection_manifest='walk-selection.json',
        construction_review_complete=True,interpretive_review_pending=True,post_result_fit_or_tuning=False,
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),source_path,OUT/'score-report.json',OUT/'walk-selection.json',PACKAGE/'freeze-manifest.json']}))
    print(json.dumps(dict(walks=len(rows),focal=len(focal),exact_replay=True,interpretive_review='pending')),flush=True)


if __name__=='__main__':main()
