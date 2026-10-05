"""Append completed player judgment and independently reconstruct all scores."""
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
import polars as pl

from universal_baseball.hitter_shared_events import profile
from universal_baseball.hitter_talent_bridge import EVENTS
from universal_baseball.storage import sha256_file
from prepare_hitter_shared_events import ROOT,GEN,OUT,PREVIOUS,BRIDGE,BORROWED,read,save,verify
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights


JUDGMENT={
    (670541,2018):'Yordan: source precision fixed but common events contribute only +0.018 batting wins/600; talent and unchanged opportunity still miss the breakout.',
    (701762,2024):'Kurtz: common events now contribute +0.642, not negligible; rate barely changes and unchanged 10 PA remains the dominant delivered-value miss.',
    (680757,2021):'Kwan: low translated contact risk does not offset limited hit/power and scout terms; new rate worsens. Large coarse support does not certify this fingerprint.',
    (702616,2023):'Holliday: lower optimism improves the largest value error, but still misses the observed collapse; origin peers include both breakout and non-arrival outcomes.',
    (624413,2018):'Alonso: 36 AA/AAA HR in 574 PA become too modest a shared production effect; the new forecast worsens an already low debut forecast.',
    (641553,2016):'Engel: coherent profile and apparent statistical support do not anticipate very poor MLB hitting; largest changed-cohort false high.',
    (690022,2024):'Ritter: nearly right delivered value is cancellation between too little PA and too optimistic hitting, not evidence both components are accurate.',
    (673548,2021):'Suzuki: meaningful foreign fingerprint reaches the head but event contribution is only +0.137, while generic scout/context terms dominate. PA remains low; unsupported generic peers are not comparable professionals.',
    (807799,2022):'Yoshida debut: foreign profile has an actual low-K fingerprint but little positive fitted event value; low workload plus low rate miss the actual contribution.',
    (808982,2023):'Lee debut: foreign rate is less optimistic and closer to the poor observed debut; this does not validate later talent or all KBO hitters.',
    (660271,2017):'Ohtani debut: production input is no longer zero, but shared rate and employment chance remain far too modest. Mixed role and zero matching profile remain explicit.',
    (808975,2024):'Hyeseong Kim: new talent is closer to actual, but 0.36 expected PA renders the contribution gain negligible; original missing name is not imputed.',
}


def independent_score(g,arm):
    yearly=[]
    for y in sorted(g['origin_year'].unique()):
        h=g.filter(pl.col('origin_year')==y)
        pa=h[arm+'_pa'].to_numpy();ap=h['next_pa'].to_numpy();v=h[arm+'_value'].to_numpy();av=h['actual_relative_value'].to_numpy()
        p=h[arm+'_p'].to_numpy();yes=(ap>0).astype(float);pclip=np.clip(p,1e-12,1-1e-12)
        active=ap>0
        yearly.append(dict(pa_mse=float(np.mean((pa-ap)**2)),pa_mae=float(np.mean(abs(pa-ap))),pa_bias=float(np.mean(pa-ap)),
            value_mse=float(np.mean((v-av)**2)),value_mae=float(np.mean(abs(v-av))),value_bias=float(np.mean(v-av)),
            brier=float(np.mean((p-yes)**2)),logloss=float(np.mean(-yes*np.log(pclip)-(1-yes)*np.log1p(-pclip))),
            conditional_rate_mse=float(np.mean((h[arm+'_rate'].to_numpy()[active]-h['actual_relative_rate'].to_numpy()[active])**2)) if active.any() else None,
            PA_weighted_rate_mse=float(np.average((h[arm+'_rate'].to_numpy()[active]-h['actual_relative_rate'].to_numpy()[active])**2,weights=ap[active])) if active.any() else None))
    z={}
    for metric in ['pa','value']:
        z[metric+'_rmse']=float(np.sqrt(np.mean([h[metric+'_mse'] for h in yearly])))
        for stat in ['mae','bias']:z[metric+'_'+stat]=float(np.mean([h[metric+'_'+stat] for h in yearly]))
    for n in ['brier','logloss']:z[n]=float(np.mean([h[n] for h in yearly]))
    rates=[h['conditional_rate_mse'] for h in yearly if h['conditional_rate_mse'] is not None]
    z['conditional_rate_rmse']=float(np.sqrt(np.mean(rates))) if rates else None
    for name,col in [('expected_pa','pa'),('expected_arrivals','p'),('expected_value','value')]:z[name]=float(g[arm+'_'+col].sum())
    return z,float(np.sqrt(np.mean([h['PA_weighted_rate_mse'] for h in yearly if h['PA_weighted_rate_mse'] is not None]))) if rates else None


def main():
    pre=read(OUT/'preflight.json');verify(pre['input_hashes']);review=read(OUT/'review-receipt.json');verify(review['artifact_hashes'])
    assert review['heads_replayed']==70
    for name in ['hitter-shared-event-result.md','hitter-shared-event-player-review.md']:
        assert 'Player walkthrough complete' in (ROOT/'docs'/name).read_text(encoding='utf8')
    q=pl.read_parquet(OUT/'compatible-predictions.parquet')
    f0=pl.read_parquet(OUT/'foreign-features-0.parquet')
    foreign_ids=f0.filter(pl.col('evidence_foreign_source_present')>0)['row_id'].to_list()
    checks=0
    for s in read(OUT/'scores.json')['scopes']:
        g=q.filter(pl.col('source_addition')) if s['scope']=='additions' else q.filter(~pl.col('source_addition'))
        name=s['scope']
        if name in ['upper_never_debut','lower_never_debut']:g=g.filter((pl.col('prior_debut')==0)&(pl.col('stage')==('Upper minors' if name.startswith('upper') else 'Lower minors')))
        elif name=='all_never_debut':g=g.filter(pl.col('prior_debut')==0)
        elif name=='foreign_never_debut':g=g.filter((pl.col('prior_debut')==0)&pl.col('row_id').is_in(foreign_ids))
        elif name=='original_no_arrival':g=g.filter(pl.col('next_pa')==0)
        elif name.startswith('origin_'):g=g.filter(pl.col('origin_year')==int(name[7:]))
        assert g.height==s['rows']
        for arm,old in s['scores'].items():
            z,rate=independent_score(g,arm)
            for k,v in z.items():
                assert (v is None and old[k] is None) or np.isclose(v,old[k],atol=1e-10,rtol=0),(name,arm,k)
                checks+=1
            assert (rate is None and s['PA_weighted_rate'][arm] is None) or np.isclose(rate,s['PA_weighted_rate'][arm],atol=1e-10,rtol=0)
            checks+=1
    cases=read(OUT/'reviewed-cases.json')['cases']
    history=defaultdict(list)
    for r in pl.read_parquet(GEN/'practical-hitter-v31/counts.parquet').filter(pl.col('season')<=2024).to_dicts():history[r['player_id']].append(r)
    inputs={r['candidate_key']:r for r in read(GEN/'foreign-origin-inputs/origin-inputs.json')['rows']}
    fp={(r['candidate_key'],r['outer_fold']):r for r in read(BORROWED/'profiles.json')['profiles']}
    calibrations={(r['cutoff'],tuple(r['excluded_folds'])):r for r in read(BORROWED/'fits.json')['fits']}
    graphs={k:{g['cutoff']:g for g in read(BRIDGE/f'translation-{k}.json')['graphs']} for k in range(5)}
    supplemented=[]
    for c in cases:
        r=c['origin'];y,k,pid=r['origin_year'],r['outer_fold'],r['player_id']
        if c['source'] is None:
            key=f'{y}:{pid}';arms,note=profile(history[pid],graphs[k][y],calibrations[y,tuple([k])],inputs.get(key),fp.get((key,k)),origin=y,outer_fold=k,own_fold=k)
            for a in ['domestic','foreign']:
                assert all(np.isclose(c['actual_inputs'][a][n],v,atol=1e-10) for n,v in arms[a].items())
            supplemented.append(dict(row_id=c['row_id'],profile=note))
        key=pid,y
        if key in JUDGMENT:judgment=JUDGMENT[key]
        elif r['prior_debut'] and not r['source_addition']:judgment='Original MLB route and opportunity are exactly unchanged; retain the prior source and outcome diagnosis, not a new gain claim.'
        elif c['actual']['PA']==0:judgment='Real source evidence remains, but no next-year MLB batting is observed. Small expected contribution is a retained false-positive cost, not a hitting-rate validation.'
        else:judgment='Actual source, fit terms, outputs, outcomes and origin-selected peers reviewed. Sparse professional transport and combined PA/rate errors remain; no promotion inference.'
        c['review_judgment']=judgment;c['player_walkthrough_status']='complete'
    save('source-case-supplement.json',dict(cases=supplemented,new_fits=0,source_profiles_reconstructed=True))
    # No fit: inspect common-head geometry and the training population it learned from.
    diagnosis=[]
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=2):
        for cell in pre['cells']:
            y,k=cell['year'],cell['fold'];f=pl.read_parquet(OUT/f'foreign-features-{k}.parquet')
            tr=f.filter(pl.col('row_id').is_in(cell['training_row_ids'])&(pl.col('next_pa')>0));never=tr['prior_debut'].to_numpy()==0
            w=weights(tr)*tr['next_pa'].to_numpy();w*=len(w)/w.sum()
            m=joblib.load(OUT/f'foreign-rate-{y}-{k}.joblib');co=dict(zip(pre['names'],map(float,m.coef_),strict=True))
            diagnosis.append(dict(origin=y,fold=k,all_active_people=tr['player_id'].n_unique(),never_debut_active_people=tr.filter(pl.col('prior_debut')==0)['player_id'].n_unique(),
                never_debut_weight_fraction=float(w[never].sum()/w.sum()),
                coherent_transfers={f'{a}_to_{b}':.01*(co['shared_'+b]-co['shared_'+a]) for a,b in [('other','HR'),('other','UBB'),('1B','K'),('HR','K')]},
                event_coefficients={e:co['shared_'+e] for e in EVENTS},interpretation='Conditional saved-head directions with context held fixed, not causal talent changes'))
    save('learning-diagnosis.json',dict(cells=diagnosis,new_fits=0))
    save('completed-player-review.json',dict(cases=cases,player_walkthrough_status='complete',selection_rule='Retained 41 diagnostics plus fixed outcome-rank rules; origin-only peers unchanged'))
    report=dict(player_walkthrough_status='complete',cases=len(cases),heads_replayed=70,independent_score_fields=checks,
        source_supplement_cases=len(supplemented),integrity_pass=True,support_qualified=True,
        predictive_improvement=False,baseball_review='mixed; production signal and opportunity misses remain',
        disposition='retain_current_no_shared_event_promotion',deployment_approved=False,protected_outcomes_used=False,
        candidate_frozen=False,broad_goal_complete=False,scores=read(OUT/'scores.json'),intervals=read(OUT/'intervals.json'),
        value_correction=read(OUT/'value-correction.json'),
        artifact_hashes={str(OUT/n):sha256_file(OUT/n) for n in ['compatible-predictions.parquet','completed-player-review.json','learning-diagnosis.json','source-case-supplement.json','scores.json','intervals.json']})
    save('final-review.json',report)
    public=ROOT/'reports/model-evidence/hitter-shared-events';assert not public.exists();public.mkdir(parents=True)
    for n,obj in [('final-review.json',report),('case-comparison.json',dict(cases=cases,source_supplement=supplemented)),('learning-diagnosis.json',read(OUT/'learning-diagnosis.json'))]:
        (public/n).write_text(__import__('json').dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')
    print(f'{checks} independent score fields, seventy head replays and {len(cases)} player walks complete. Current model retained.',flush=True)


if __name__=='__main__':main()
