"""Replay the existing translated alternative and close the source audit."""
import json
import shutil
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
import audit_hitter_rate_support as audit

ROOT,OUT=audit.ROOT,audit.OUT
BRIDGE=ROOT/'reports/generated/hitter-talent-bridge-v74'


def main():
    report=audit.fit.read(OUT/'report.json');audit.fit.verify(report['source_hashes'])
    rows=pl.read_parquet(OUT/'rows.parquet')
    old=pl.read_parquet(BRIDGE/'scored-predictions.parquet').sort('row_id')
    assert len(old)==30506 and rows['row_id'].equals(old['row_id'])
    assert np.array_equal(rows['current_pa'].to_numpy(),old['preseason_pa'].to_numpy())
    assert np.allclose(rows['baseline_rate'],old['preseason_rate'],atol=1e-10,rtol=0)
    pre=audit.fit.read(BRIDGE/'preflight.json');features={k:pl.read_parquet(BRIDGE/f'features-{k}.parquet') for k in range(5)}
    cases=[];replays=0;hashes={}
    with threadpool_limits(limits=2):
        for c in report['cases']:
            rid=c['row_id'];r=rows.filter(pl.col('row_id')==rid).row(0,named=True);y,k=r['origin_year'],r['outer_fold']
            te=features[k].filter(pl.col('row_id')==rid);s=old.filter(pl.col('row_id')==rid).row(0,named=True)
            assert te['player_id'][0]==r['player_id'] and s['player_id']==r['player_id']
            headnote=audit.fit.read(BRIDGE/f'fit-{y}-{k}.json');traces={}
            for h in headnote['heads']:
                audit.fit.verify({h['path']:h['sha256']});hashes[h['path']]=h['sha256']
                m=joblib.load(h['path']);names=pre['features'][h['arm']];x=safe_matrix(te,names)
                pred=float(m.predict(x)[0]);assert np.isclose(pred,s[h['arm']+'_all_rate'],atol=1e-10,rtol=0)
                primary=pred if r['prior_debut']==0 else r['baseline_rate']
                assert np.isclose(primary,s[h['arm']+'_rate'],atol=1e-10,rtol=0)
                traces[h['arm']]=dict(raw_rate=pred,primary_rate=primary)
                if h['arm']!='translated_hist':
                    terms=x[0]*m.coef_;assert np.isclose(float(m.intercept_+terms.sum()),pred,atol=1e-10,rtol=0)
                    traces[h['arm']].update(intercept=float(m.intercept_),
                        age_term=float(sum(v for n,v in zip(names,terms,strict=True) if n in ['age_centered','age_squared'])),
                        ranking_term=float(sum(v for n,v in zip(names,terms,strict=True) if n.startswith('scout_'))),
                        translated_term=float(sum(v for n,v in zip(names,terms,strict=True) if n.startswith('translated_'))))
                replays+=1
            cases.append(dict(row_id=rid,player_id=r['player_id'],player_name=r['player_name'],origin_year=y,
                current_rate=r['baseline_rate'],alternative=traces,
                supported_fraction=float(te['translated_supported_fraction'][0]),
                primary_established_unchanged=bool(r['prior_debut'])))
    alternative=OUT/'alternative-replays.json'
    obj=dict(replayed_case_heads=replays,no_fits=True,no_scores_changed=True,cases=cases,head_hashes=hashes,
        comparison_limit='Selected saved-head replays, not a new global certification or untouched test')
    if alternative.exists():assert audit.fit.read(alternative)==obj
    else:alternative.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf8')
    doc=ROOT/'docs/hitter-rate-support-audit-result.md';text=doc.read_text(encoding='utf8')
    assert all(c['player_name'] in text and str(c['row_id']) in text for c in report['cases'])
    previous=audit.fit.read(audit.fit.OUT/'final-report.json')
    assert previous['player_walkthrough_status']=='complete' and previous['reviewed_cases']==16
    paths=[Path(__file__),doc,alternative,OUT/'report.json',audit.fit.OUT/'reviewed-cases.json',
        ROOT/'docs/hitter-talent-opportunity-player-walkthrough.md',BRIDGE/'score-unit-correction.json',
        ROOT/'docs/hitter-talent-bridge-v74-result.md',ROOT/'docs/practical-hitter-contact-v41-result.md']
    final=dict(no_fits=True,all_current_forecasts_exact=True,rows=30506,rate_heads_replayed=35,
        alternative_case_heads_replayed=48,player_walkthrough_status='complete',reviewed_cases=16,
        linked_stats_input_walkthrough=str(ROOT/'docs/hitter-talent-opportunity-player-walkthrough.md'),
        additional_rate_accounting_cases=report['cases'],alternative_case_artifact=str(alternative),
        disposition='Qualify unsupported lower-level MLB hitting as extrapolation; preserve the favorable translated alternative. No model or explorer promotion; proceed only under a target/support repair contract.',
        protected_outcomes_used=False,frozen_forecast_changed=False,deployment_approved=False,full_goal_complete=False,
        source_and_execution_hashes=report['source_hashes'],review_hashes={str(p):sha256_file(p) for p in paths})
    fp=OUT/'final-report.json'
    if fp.exists():assert audit.fit.read(fp)==final
    else:fp.write_text(json.dumps(final,indent=2,allow_nan=False)+'\n',encoding='utf8')
    dest=ROOT/'reports/model-evidence/hitter-rate-support-audit';dest.mkdir(parents=True,exist_ok=True)
    for name in ['report.json','alternative-replays.json','final-report.json']:
        source,target=OUT/name,dest/name
        if target.exists():assert sha256_file(target)==sha256_file(source)
        else:shutil.copyfile(source,target)
    print('Cross-level source audit complete; 35 current heads and 48 alternative case heads replayed; no forecasts changed.')
    print([(c['player_name'],c['current_rate'],c['alternative']['translated_ridge']) for c in cases if c['player_name'] in ['Nick Kurtz','Wyatt Langford','Juneiker Caceres','Jeremy Peña']])


if __name__=='__main__':main()
