"""Preserve stopped source seal; repair Path handling only, no new fitting."""
from pathlib import Path
import json
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from audit_overseas_opportunity_inventory import OUT, REP, ROOT, GEN, read, verify, save, totals, category
from universal_baseball.hitter_evidence_representation import job_evidence, JOB_FEATURES
from universal_baseball.histogram_prediction_trace import trace
from evaluate_hitter_readiness_v49 import logit_trace
from universal_baseball.storage import sha256_file


def saved_digest(path):
    return sha256_file(Path(path))


def main():
    if not OUT.exists() or {p.name for p in OUT.iterdir()}!={'source-seal.json'}:
        raise ValueError('Only the exact stopped source-only state may be recovered')
    verify(read(OUT/'source-seal.json')['hashes'])
    save('execution-recovery.json',dict(new_fits=0,preserved_original_seal=True,
        sole_execution_change='Convert saved model paths to Path before hashing.',
        original_completed_inventory_exists=False,
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [Path(__file__),ROOT/'docs/hitter-overseas-opportunity-inventory-recovery.md']}))
    pre=read(REP/'preflight.json'); fit=read(REP/'fit-report.json'); verify(pre['source_hashes']); verify(read(REP/'final-review.json')['hashes'])
    count=pl.read_parquet(GEN/'foreign-count-calibration/predictions.parquet').filter(pl.col('source_present'))
    q=pl.read_parquet(REP/'predictions.parquet').join(count.select('row_id','route_used'),on='row_id',how='inner',validate='1:1')
    if len(q)!=266: raise ValueError('Changed source population')
    source={r['candidate_key']:r for r in read(GEN/'foreign-origin-inputs/origin-inputs.json')['rows']}
    oldwalks=read(GEN/'foreign-count-calibration/player-walks.json')['cases']
    ids=sorted({t['forecast']['row_id'] for w in oldwalks for t in [w['trace'],*[p['trace'] for p in w['peers']]]})
    keys=set(count['profile_key'])
    status={r['candidate_key']:r for r in read(GEN/'hitter-status-evidence-v2/status-ledger.json')['rows'] if r['candidate_key'] in keys}
    job=pre['job_features']; columns=list(dict.fromkeys(['row_id','origin_year','target_year','player_id','age','outer_fold','next_pa','pa_0','prior_debut','evidence_foreign_source_present',*job]))
    frames={k:pl.read_parquet(REP/f'features-{k}.parquet',columns=columns) for k in range(5)}
    cats=frames[0].filter(pl.col('row_id').is_in(q['row_id'].to_list())).select('row_id',
        pl.when(pl.col('status_major_link')>0).then(pl.lit('major_link')).when(pl.col('status_minor_agreement')>0).then(pl.lit('minor_agreement')).when(pl.col('status_employment_unknown')>0).then(pl.lit('unknown')).otherwise(pl.lit('other')).alias('employment_category'))
    q=q.join(cats,on='row_id',validate='1:1')
    groups=[('original_foreign',q.filter(~pl.col('source_addition'))),('fresh_original',q.filter(~pl.col('source_addition')&pl.col('route_used'))),('additions',q.filter(pl.col('source_addition')))]
    groups += [('fresh_original_'+cat,q.filter(~pl.col('source_addition')&pl.col('route_used')&(pl.col('employment_category')==cat))) for cat in sorted(q['employment_category'].unique())]
    reports=[dict(scope=name,rows=len(g),people=g['player_id'].n_unique(),actual_PA=int(g['next_pa'].sum()),actual_participants=g.filter(pl.col('next_pa')>0).height,
        arms={a:totals(g,a) for a in ['current','domestic','overseas','repaired_domestic']}) for name,g in groups if len(g)]
    cells={(c['year'],c['fold']):c for c in pre['cells']}; fitted={(c['origin'],c['fold']):c for c in fit['cells']}
    models={}; walks=[]; replays=0
    with threadpool_limits(limits=2):
        for rid in ids:
            r=q.filter(pl.col('row_id')==rid).row(0,named=True); y,k=r['origin_year'],r['outer_fold']; f=frames[k].filter(pl.col('row_id')==rid).row(0,named=True)
            key=f'{y}:{r["player_id"]}'; s=source[key]; reconstructed=job_evidence(f,s)
            for n in JOB_FEATURES:
                if not np.isclose(reconstructed[n],f[n],atol=1e-12,rtol=0): raise ValueError('Professional field reconstruction failed')
            tr=frames[k].filter(pl.col('row_id').is_in(cells[y,k]['training_row_ids']))
            if tr['target_year'].max()>y or tr.filter(pl.col('outer_fold')==k).height: raise ValueError('Invalid held training')
            peers=tr.filter((pl.col('prior_debut')==f['prior_debut'])&(pl.col('evidence_foreign_source_present')>0)&(pl.col('age')//5==f['age']//5))
            peers=[v for v in peers.to_dicts() if category(v)==category(f)]
            heads=[]
            for h in [h for h in fitted[y,k]['heads'] if h['arm']=='common']:
                if h['features']!=job or saved_digest(h['path'])!=h['sha256']: raise ValueError('Wrong saved head')
                if h['path'] not in models: models[h['path']]=joblib.load(h['path'])
                m=models[h['path']]; x=np.array([f[n] for n in job]); part=h['head']=='participation'
                z=logit_trace(m,x,job) if part else trace(m,x,job)
                value=z['linked_probability'] if part else z['raw_prediction']
                if not np.isclose(value,r['repaired_domestic_raw_p' if part else 'repaired_domestic_raw_conditional_pa'],atol=1e-8,rtol=0): raise ValueError('Saved head replay failed')
                heads.append(dict(head=h['head'],model_path=h['path'],sha256=h['sha256'],trace=z)); replays+=1
            rosters=[]
            for team in s['roster_team_ids']:
                p=GEN/'hitter-preseason-population-source/captures'/f'roster-{y+1}-{team}-40Man.json'; meta=read(p.with_suffix('.json.metadata.json'))
                if meta['params']['date']!=r['ctx_information_date'] or sha256_file(p)!=meta['sha256']: raise ValueError('Roster snapshot mismatch')
                raw=[v for v in read(p)['roster'] if v['person']['id']==r['player_id']]
                if not raw: raise ValueError('Literal roster join failed')
                rosters.append(dict(params=meta['params'],sha256=meta['sha256'],raw_player_rows=raw))
            walks.append(dict(row_id=rid,forecast=r,source=s,status=status[key],actual_job_inputs={n:f[n] for n in job},
                reconstructed_professional_activity=reconstructed,employment_category=category(f),roster_evidence=rosters,
                absent_listing_is_not_verified_no_job=not bool(rosters),held_training_same_profile=dict(people=len({v['player_id'] for v in peers}),conditional_people=len({v['player_id'] for v in peers if v['next_pa']>0})),heads=heads))
    save('inventory.json',dict(source_forecasts=266,matched_existing_predictions=True,groups=reports,unique_walk_rows=len(walks),saved_head_replays=replays,
        job_features=job,foreign_production_contrasts_used_in_repaired_job_head=False,existing_candidate_has_professional_activity=True,
        new_fits=0,new_forecasts=0,new_2026_outcomes_read=False,walks=walks,human_review_status='pending'))
    print(json.dumps(dict(groups=reports,unique_walk_rows=len(walks),saved_head_replays=replays,new_fits=0,human_review_status='pending')),flush=True)


if __name__=='__main__': main()
